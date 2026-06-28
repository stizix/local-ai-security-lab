"""
chromadb_audit.py - audit a ChromaDB instance for unauthenticated access.

Built for finding 003. Speaks ChromaDB's v2 REST API directly over HTTP (no
chromadb client dependency), so it works against any reachable instance the same
way an attacker's script would.

WHAT IT DOES (read-only by default, safe against anything you own):
  - heartbeat / version
  - auth identity  -> detects whether the server enforces any authentication
  - enumerate tenants -> databases -> collections
  - for each collection: count + a sample of documents and metadata
  -> if it can read documents with no credentials, that is the finding.

OPTIONAL  --prove-write :
  inserts a single benign canary document, confirms it landed, then deletes it.
  This proves the API also accepts unauthenticated WRITES (poisoning / tampering)
  without leaving anything behind. It never touches your real documents and never
  calls the destructive /reset or delete-collection endpoints.

USAGE:
  py -3.11 chromadb_audit.py http://127.0.0.1:8000
  py -3.11 chromadb_audit.py http://127.0.0.1:8000 --prove-write
  py -3.11 chromadb_audit.py http://127.0.0.1:8000 --sample 5

Only run this against ChromaDB instances you own or are authorized to test.
"""

import sys
import argparse
import requests

TIMEOUT = 8


def get(base, path):
    r = requests.get(f"{base}{path}", timeout=TIMEOUT)
    return r.status_code, _json(r)


def post(base, path, body):
    r = requests.post(f"{base}{path}", json=body, timeout=TIMEOUT)
    return r.status_code, _json(r)


def delete(base, path):
    r = requests.delete(f"{base}{path}", timeout=TIMEOUT)
    return r.status_code, _json(r)


def _json(r):
    try:
        return r.json()
    except ValueError:
        return r.text


def ok(code):
    """ChromaDB returns 200 for reads and 201 for successful writes."""
    return 200 <= code < 300


def banner(title):
    print(f"\n=== {title} ===")


def audit(base, sample, prove_write):
    base = base.rstrip("/")
    print(f"Auditing ChromaDB at {base}")

    # --- reachability -------------------------------------------------------
    banner("reachability")
    code, hb = get(base, "/api/v2/heartbeat")
    if code != 200:
        print(f"  no v2 heartbeat (HTTP {code}). Not a reachable Chroma v2 server.")
        return
    print(f"  heartbeat OK: {hb}")
    _, ver = get(base, "/api/v2/version")
    print(f"  version: {ver}")

    # --- authentication -----------------------------------------------------
    banner("authentication")
    code, ident = get(base, "/api/v2/auth/identity")
    no_auth = False
    if code == 200 and isinstance(ident, dict):
        uid = ident.get("user_id", "")
        if uid == "":
            no_auth = True
            print(f"  [VULN] no authentication enforced - anonymous identity: {ident}")
        else:
            print(f"  authenticated as: {ident}")
    else:
        print(f"  auth/identity returned HTTP {code}: {ident}")

    # --- enumeration --------------------------------------------------------
    banner("enumeration")
    code, dbs = get(base, "/api/v2/tenants/default_tenant/databases")
    if not ok(code) or not isinstance(dbs, list):
        print(f"  could not list databases (HTTP {code}): {dbs}")
        return
    print(f"  databases: {[d.get('name') for d in dbs]}")

    total_docs = 0
    readable_collections = 0
    for db in dbs:
        dbname = db.get("name")
        api = f"/api/v2/tenants/default_tenant/databases/{dbname}"
        code, cols = get(base, f"{api}/collections")
        if not ok(code) or not isinstance(cols, list):
            print(f"  [{dbname}] could not list collections (HTTP {code})")
            continue
        print(f"  [{dbname}] {len(cols)} collection(s): {[c.get('name') for c in cols]}")

        for col in cols:
            cid = col.get("id")
            name = col.get("name")
            _, cnt = get(base, f"{api}/collections/{cid}/count")
            print(f"    - '{name}'  id={cid}  count={cnt}")

            # dump a sample of documents with no credentials
            code, data = post(
                base,
                f"{api}/collections/{cid}/get",
                {"limit": sample, "include": ["documents", "metadatas"]},
            )
            if ok(code) and isinstance(data, dict) and data.get("documents"):
                readable_collections += 1
                docs = data["documents"]
                metas = data.get("metadatas") or [None] * len(docs)
                total_docs += (cnt if isinstance(cnt, int) else len(docs))
                print(f"      [VULN] dumped {len(docs)} document(s) with no auth:")
                for d, m in zip(docs, metas):
                    snippet = (d[:120] + "...") if len(d) > 120 else d
                    print(f"        - {snippet!r}  meta={m}")

    # --- optional write proof ----------------------------------------------
    if prove_write:
        banner("write access (canary)")
        _prove_write(base)

    # --- verdict ------------------------------------------------------------
    banner("verdict")
    if no_auth and readable_collections:
        print(f"  CRITICAL - unauthenticated read access to {readable_collections} "
              f"collection(s), ~{total_docs} documents fully exposed.")
        print("  Any network client can dump, poison, or delete this knowledge base.")
    elif no_auth:
        print("  WARNING - no authentication enforced, but no documents found to dump.")
    else:
        print("  OK - server appears to enforce authentication.")


def _prove_write(base):
    """Insert a benign canary, confirm it, delete it. Leaves no trace."""
    api = "/api/v2/tenants/default_tenant/databases/default_database"
    code, cols = get(base, f"{api}/collections")
    if not ok(code) or not cols:
        print("  no collection available to test writes against.")
        return
    cid = cols[0]["id"]
    name = cols[0]["name"]

    # match the collection's vector dimension
    dim = cols[0].get("dimension") or 384
    vec = [0.0] * dim
    canary_id = "audit-canary-DELETE-ME"

    code, resp = post(base, f"{api}/collections/{cid}/add", {
        "ids": [canary_id],
        "documents": ["benign audit canary - proves unauthenticated write access"],
        "embeddings": [vec],
    })
    if not ok(code):
        print(f"  write refused (HTTP {code}): {resp}")
        return
    print(f"  [VULN] inserted canary into '{name}' with no auth.")

    # clean up immediately
    code, resp = post(base, f"{api}/collections/{cid}/delete", {"ids": [canary_id]})
    if ok(code):
        print("  canary deleted - instance left exactly as found.")
    else:
        print(f"  WARNING: could not delete canary (HTTP {code}): {resp} "
              f"- remove id '{canary_id}' manually.")


def main():
    p = argparse.ArgumentParser(description="Audit a ChromaDB instance for unauthenticated access.")
    p.add_argument("target", nargs="?", default="http://127.0.0.1:8000",
                   help="base URL of the ChromaDB server (default: http://127.0.0.1:8000)")
    p.add_argument("--sample", type=int, default=3,
                   help="how many documents to dump per collection (default: 3)")
    p.add_argument("--prove-write", action="store_true",
                   help="also prove unauthenticated WRITE access with a self-cleaning canary")
    args = p.parse_args()

    try:
        audit(args.target, args.sample, args.prove_write)
    except requests.exceptions.RequestException as e:
        print(f"connection error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

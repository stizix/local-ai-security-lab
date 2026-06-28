# Finding 003 — Unauthenticated ChromaDB: dump, poison, and destroy a vector store with no credentials

**Date:** 2026-06-28
**Author:** [@prunier_issa](https://x.com/prunier_issa)
**Target:** a stock ChromaDB server in default configuration (`labs/vulnerable_chromadb`)
**Version tested:** ChromaDB 1.5.9 (v2 REST API)
**OWASP:** LLM06 (Sensitive Information Disclosure), API1 (Broken Object-Level Authorization)

> The first two findings were about *prompts*. This one isn't. ChromaDB's REST API
> ships with **no authentication by default**. Anything that can reach the port can
> list every collection, dump every document (and the secrets in them), insert
> poisoned documents, and delete entire collections — with nothing but `curl`. No
> API key, no client library, no credentials of any kind.

---

## 1. Setup

This is surface #3 / trust boundary D in
[threat-model 001](../../threat-models/001-my-lab.md). Unlike findings 001 and 002,
there is no vulnerable app to write — **the default config *is* the vulnerability.**
You run a stock server and seed it with a realistic knowledge base
([`labs/vulnerable_chromadb`](../../labs/vulnerable_chromadb)): an internal wiki note
(carrying an admin password), a public refund policy, and a non-public finance figure
— the kind of mix a real RAG app keeps in its vector store.

```bash
chroma run --host 127.0.0.1 --port 8000 --path ./chroma_data
py -3.11 seed.py
```

The attacker is assumed to reach the port — exactly what happens when ChromaDB is
re-bound to `0.0.0.0` for "remote access", a near-universal misconfiguration.

## 2. Result

Every request below is unauthenticated. First, the API confirms it has no idea who
you are and does not care:

```
GET /api/v2/auth/identity
{"user_id": "", "tenant": "default_tenant", "databases": ["default_database"]}
```

An **empty `user_id`** is the whole finding in one line: the server treats an
anonymous caller as fully authorized. From there the entire kill chain works
(`poc.py`):

| Stage | Primitive | Endpoint | Auth required |
|-------|-----------|----------|---------------|
| READ | dump all docs + metadata | `POST …/collections/{id}/get` | none |
| POISON | insert attacker document | `POST …/collections/{id}/add` | none |
| DESTROY | delete an entire collection | `DELETE …/collections/{name}` | none |

The stolen secret, pulled straight out of the victim's knowledge base:

```
>>> STOLEN SECRET: 'Internal: the admin panel is at /superadmin, password is Rocket2026.'
```

## 3. The destructive primitive — and an honest note on `/reset`

Older write-ups of this bug center on `POST /api/v1/reset`, which wiped the whole
database with one unauthenticated call. **Recent ChromaDB closes that specific hole:**

```
POST /api/v2/reset -> HTTP 403: {"error": "ChromaError", "message": "Reset is disabled by config"}
```

That is a real secure-by-default improvement and this finding does **not** rely on
reset. But it is incomplete: unauthenticated `DELETE /collections/{name}` still
deletes an entire collection, so the destructive capability stands. The PoC proves it
on a throwaway collection so the seeded lab is left untouched:

```
[3] DESTROY - delete the entire collection unauthenticated
    poc_victim deleted: True
```

## 4. Why it works

ChromaDB's default config sets no auth provider. The REST API is built to be driven by
a trusted application on `localhost`, and the project leans on **network isolation as
the only access control**. That assumption holds until someone binds it to a network
interface — which is precisely what people do to share a vector store between machines,
and precisely the moment the "trusted localhost client" model collapses. There is no
per-object authorization (OWASP API1): if you can reach the port, every collection is
yours.

This is a different *class* from findings 001/002. Those were the model trusting
attacker-controlled text. This is the *infrastructure* trusting attacker-controlled
**requests** — an authz failure, not a prompt failure. But they chain: the POISON
primitive here is how the indirect injection of [finding 002](../002-indirect-injection)
gets *planted at scale and persisted* in a real store, with no need to talk to the model.

## 5. Impact

Anyone who can reach the port can:

- **Exfiltrate the entire knowledge base** — every document a RAG app has ingested:
  internal wikis, support tickets, contracts, PII, and any secret that leaked into a
  document (as the admin password did here).
- **Poison retrieval** — insert documents engineered to be retrieved for target
  queries, turning the store into a delivery vehicle for the stored indirect injection
  of finding 002. Persistent and invisible to end users.
- **Destroy data** — delete documents or whole collections, taking the RAG app down or
  silently degrading its answers.

All without credentials, and (with `0.0.0.0`) from anywhere on the network.

## 6. Root cause

No authentication in the default configuration, and no per-object authorization at
all. Access control is delegated entirely to network reachability, which fails the
moment the service is exposed beyond `localhost`.

## 7. Fix

- **Never bind ChromaDB to `0.0.0.0` without auth.** Keep it on `127.0.0.1`, or behind
  a reverse proxy / network policy that authenticates callers.
- **Enable ChromaDB's auth providers** (static-token or basic-auth) and set an
  `X-Chroma-Token` / credential on every client. Default-deny.
- **Treat the vector store as a crown-jewel datastore**, not a cache: it holds
  everything the RAG app has ever ingested. Network-segment it like a database.
- **Keep `ALLOW_RESET` unset/false** (it is by default) — but understand that does not
  remove the deletion primitive; auth is the real fix.
- **Don't put secrets in documents** (same root lesson as 001/002): the store is
  readable, so anything embedded into it is exfiltratable.

## 8. The tool

This finding ships a reusable auditor: [`tools/chromadb_audit.py`](../../tools/chromadb_audit.py).
It is **read-only by default** (safe to point at any instance you own) and reports the
auth posture, enumerates collections, and samples documents. `--prove-write` adds a
self-cleaning canary that proves unauthenticated *write* access without leaving a trace
or touching real data.

```
$ py -3.11 tools/chromadb_audit.py http://127.0.0.1:8000 --prove-write
=== authentication ===
  [VULN] no authentication enforced - anonymous identity: {'user_id': '', ...}
=== enumeration ===
    - 'company_kb'  id=...  count=3
      [VULN] dumped 3 document(s) with no auth:
        - 'Internal: the admin panel is at /superadmin, password is Rocket2026.'  meta={'src': 'wiki'}
        ...
=== write access (canary) ===
  [VULN] inserted canary into 'company_kb' with no auth.
  canary deleted - instance left exactly as found.
=== verdict ===
  CRITICAL - unauthenticated read access to 1 collection(s), ~3 documents fully exposed.
```

## 9. Reproduce

```bash
# terminal 1 — the vulnerable target (default config)
cd labs/vulnerable_chromadb
chroma run --host 127.0.0.1 --port 8000 --path ./chroma_data
py -3.11 seed.py        # in a second shell, once the server is up

# terminal 2 — the attack
cd findings/003-chromadb-unauth
py -3.11 poc.py

# or the reusable auditor
py -3.11 tools/chromadb_audit.py http://127.0.0.1:8000 --prove-write
```

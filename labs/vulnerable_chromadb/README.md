# Lab — vulnerable ChromaDB (default config)

The target for [finding 003](../../findings/003-chromadb-unauth). Unlike the labs for
findings 001 and 002, there is **no vulnerable app to write here** — the vulnerability
*is* ChromaDB's default configuration. You run a stock ChromaDB server with the
out-of-the-box settings and it is already exploitable.

This is surface #3 / trust boundary D in
[threat-model 001](../../threat-models/001-my-lab.md).

## What's vulnerable

ChromaDB's REST API ships with **no authentication by default**. Anything that can
reach the port has full control of every collection: list them, dump every document
and its metadata, insert new (poisoned) documents, delete documents, and delete entire
collections. In the real world this port gets bound to `0.0.0.0` for "remote access"
and becomes internet-reachable with zero credentials.

## Run the target

```bash
# 1. install
py -3.11 -m pip install chromadb

# 2. run the server (default config — no auth)
chroma run --host 127.0.0.1 --port 8000 --path ./chroma_data

# 3. seed it with a realistic company knowledge base
py -3.11 seed.py
```

`seed.py` plants three documents that stand in for what a real RAG app stores: an
internal wiki note (containing an admin password), a public refund policy, and a
non-public finance figure. The point of the finding is that an unauthenticated
attacker can read the secret one and tamper with all of them.

> **Note on `/reset`.** Recent ChromaDB (1.x) disables the destructive
> `/api/v2/reset` endpoint by default — a genuine security improvement over the
> behaviour described in older write-ups. The finding does **not** rely on it.
> Unauthenticated `DELETE /collections/{name}` already wipes an entire collection,
> so the destructive impact stands without reset.

Do NOT expose this to a network. Teaching target only.

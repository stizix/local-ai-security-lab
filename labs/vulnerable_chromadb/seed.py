"""
Seed the vulnerable ChromaDB lab with a realistic company knowledge base.

This stands in for what a real RAG app stores in its vector store: a mix of
internal-only notes (one carrying a secret), public policy, and non-public
business data. The point of finding 003 is that with default config, an
unauthenticated attacker can read the secret one and tamper with all of them.

Run AFTER starting the server:
  chroma run --host 127.0.0.1 --port 8000 --path ./chroma_data
  py -3.11 seed.py
"""

import chromadb

client = chromadb.HttpClient(host="127.0.0.1", port=8000)

# get_or_create so re-running is idempotent
col = client.get_or_create_collection("company_kb")

# wipe any previous run so the seed is deterministic
existing = col.get()["ids"]
if existing:
    col.delete(ids=existing)

col.add(
    ids=["doc1", "doc2", "doc3"],
    documents=[
        # internal-only — the secret an attacker is after
        "Internal: the admin panel is at /superadmin, password is Rocket2026.",
        # public-facing policy — the kind of thing the RAG app is meant to serve
        "Customer refund policy: refunds are issued within 30 days of purchase.",
        # non-public business data
        "Q3 revenue was 1.2M EUR, not yet announced publicly.",
    ],
    metadatas=[{"src": "wiki"}, {"src": "policy"}, {"src": "finance"}],
)

print(f"Seeded 'company_kb' with {col.count()} documents.")
print("Now run the audit:  py -3.11 ../../tools/chromadb_audit.py http://127.0.0.1:8000")

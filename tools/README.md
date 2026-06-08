# Tools

Reusable auditing scripts, built as the study progresses. Each tool ships only once
it actually works against my lab — no empty placeholders.

| Tool | Purpose | Status |
|------|---------|--------|
| `injection_tester.py` | Fire categorized prompt-injection payloads at an LLM HTTP endpoint, log which succeed and why | Week 2 |
| `chromadb_audit.py` | Audit a ChromaDB instance for unauthenticated access (list/dump/insert/delete/reset) | Week 4 |

Each tool will be parameterized by a target URL so it runs against any local endpoint
I own or have permission to test.

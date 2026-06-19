# Tools

Reusable auditing scripts, built as the study progresses. Each tool ships only once
it actually works against my lab — no empty placeholders.

| Tool | Purpose | Status |
|------|---------|--------|
| `injection_tester.py` | Fire categorized prompt-injection payloads at an LLM HTTP endpoint, log which succeed and why | PoC shipped — see [finding 001](../findings/001-prompt-injection/poc.py); parameterized version next |
| `chromadb_audit.py` | Audit a ChromaDB instance for unauthenticated access (list/dump/insert/delete/reset) | Week 4 |

The Week 2 injection campaign ran as a hardcoded PoC against the local target
(`labs/vulnerable_app/`). The reusable, `--target`-parameterized version of
`injection_tester.py` will be promoted here once it is generalized beyond that lab.

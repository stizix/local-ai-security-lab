# Findings

One folder per verified vulnerability. Nothing is listed here until it has a
reproducible PoC and an honest impact statement.

## Published

| # | Finding | Target | Model |
|---|---------|--------|-------|
| [001](001-prompt-injection/) | Framing-based prompt injection leaks a system-prompt secret (translation 9/10, hypothetical 2/10; all instruction-based attacks 0/10) | local vulnerable FastAPI `/chat` | `llama3.2:3b` |
| [002](002-indirect-injection/) | Indirect prompt injection — a poisoned document leaks a secret to an innocent user (`SYSTEM:` framing 10/10, `[ADMIN NOTE]` 9/10, plain-English 2/10) | local vulnerable RAG `/chat` | `llama3.2:3b` |
| [003](003-chromadb-unauth/) | Unauthenticated ChromaDB — dump, poison, and delete a vector store with no credentials (default config, v2 API) | stock ChromaDB 1.5.9 | n/a (infra) |
| [004](004-exposed-ollama/) | Unauthenticated Ollama — enumerate models and run inference on the host's hardware with no credentials; pull/delete one call away | stock Ollama `:11434` | any installed |

Next expected Week 6 (system-prompt extraction across models).

Each finding will follow this structure:

```
findings/00X-short-name/
├── README.md   ← the write-up (setup, finding, PoC, impact, root cause, fix)
├── poc.py      ← runnable proof of concept
└── demo.gif    ← optional terminal recording
```

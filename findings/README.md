# Findings

One folder per verified vulnerability. Nothing is listed here until it has a
reproducible PoC and an honest impact statement.

## Published

| # | Finding | Target | Model |
|---|---------|--------|-------|
| [001](001-prompt-injection/) | Framing-based prompt injection leaks a system-prompt secret (translation 9/10, hypothetical 2/10; all instruction-based attacks 0/10) | local vulnerable FastAPI `/chat` | `llama3.2:3b` |

Next expected Week 3–4 (RAG poisoning, ChromaDB unauthenticated access).

Each finding will follow this structure:

```
findings/00X-short-name/
├── README.md   ← the write-up (setup, finding, PoC, impact, root cause, fix)
├── poc.py      ← runnable proof of concept
└── demo.gif    ← optional terminal recording
```

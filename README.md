# local-ai-security-lab

Security research on **local AI deployments** — Ollama, FastAPI, ChromaDB, LangChain.

I'm documenting an 8-week, hands-on study of how locally-deployed LLM stacks fail:
prompt injection, RAG poisoning, vector-store misconfiguration, agent exploitation,
and system-prompt extraction. Everything here is reproduced in my own lab or against
open-source apps I run locally.

> **Status: Week 4 complete — Week 5 in progress.** This repo grows one verified
> finding at a time. No claims without a runnable PoC. If a finding isn't here yet,
> I haven't proven it yet.

---

## Focus areas

- Prompt injection in RAG pipelines (direct & indirect)
- Vector store misconfiguration (ChromaDB unauthenticated API)
- LangChain agent exploitation (tool confusion, excessive agency)
- System prompt extraction
- Indirect prompt injection via document ingestion

Mapped to the [OWASP LLM Top 10](https://owasp.org/www-project-top-10-for-large-language-model-applications/).

---

## Findings

Each finding ships with a reproducible PoC and an honest impact statement. Full index
in [`findings/`](./findings).

| # | Title | Stack | OWASP | Status |
|---|-------|-------|-------|--------|
| [001](./findings/001-prompt-injection) | Framing-based prompt injection leaks a system-prompt secret (translation 9/10, all direct attacks 0/10) | local FastAPI `/chat` + Ollama `llama3.2:3b` | LLM01, LLM06 | Published |
| [002](./findings/002-indirect-injection) | Indirect prompt injection — a poisoned document leaks a secret to an innocent user (`SYSTEM:` framing 10/10, plain-English 2/10) | local RAG `/chat` + Ollama `llama3.2:3b` | LLM01, LLM06 | Published |
| [003](./findings/003-chromadb-unauth) | Unauthenticated ChromaDB — dump, poison & delete a vector store with no credentials (default config) | stock ChromaDB 1.5.9, v2 API | LLM06, API1 | Published |

---

## Tools

*Built as the study progresses:*

- `injection_tester.py` — fires categorized injection payloads at an LLM HTTP endpoint. Week 2 PoC shipped in [finding 001](./findings/001-prompt-injection/poc.py); a `--target`-parameterized version will be promoted to `tools/` once generalized.
- `tools/chromadb_audit.py` — audits a ChromaDB instance for unauthenticated access (auth posture, collection enumeration, document dump; `--prove-write` for a self-cleaning write canary). Shipped in [finding 003](./findings/003-chromadb-unauth).

---

## Labs

Intentionally vulnerable apps I build as attack targets, so every finding is
reproducible end-to-end.

- [`labs/vulnerable_app/`](./labs/vulnerable_app) — minimal FastAPI `/chat` endpoint that concatenates user input into a system prompt with no data/instruction separation. The target for finding 001.
- [`labs/vulnerable_rag_app/`](./labs/vulnerable_rag_app) — minimal RAG `/chat` endpoint that retrieves a document and trusts it with the same authority as its instructions. The target for finding 002.
- [`labs/vulnerable_chromadb/`](./labs/vulnerable_chromadb) — a stock ChromaDB server in default (no-auth) config plus a seed script. No vulnerable app to write — the default config *is* the vulnerability. The target for finding 003.

---

## Threat models

- [`threat-models/`](./threat-models) — attack-surface maps of the stacks I study, starting with my own lab.

---

## Lab setup

- **OS:** Windows 11, AMD Ryzen 7 8840HS, 16 GB RAM (CPU/iGPU inference, no dedicated GPU)
- **Inference:** Ollama (local models, GGUF quantized)
- **Targets built so far:** FastAPI `/chat` victim ([`labs/vulnerable_app/`](./labs/vulnerable_app)), RAG `/chat` victim ([`labs/vulnerable_rag_app/`](./labs/vulnerable_rag_app)), ChromaDB default-config target ([`labs/vulnerable_chromadb/`](./labs/vulnerable_chromadb))
- **Planned target stack:** exposed Ollama (Week 5) + LangChain agent with tools (Week 8)

Testing is performed exclusively against systems I own or open-source apps I run
locally. No unauthorized access. Disclosure follows the 90-day coordinated standard.

---

## About

Building in public. Computer science student documenting the path from "uses AI" to
"understands how it breaks."

- X / Twitter: [@prunier_issa](https://x.com/prunier_issa)

# local-ai-security-lab

Security research on **local AI deployments** — Ollama, FastAPI, ChromaDB, LangChain.

I'm documenting an 8-week, hands-on study of how locally-deployed LLM stacks fail:
prompt injection, RAG poisoning, vector-store misconfiguration, agent exploitation,
and system-prompt extraction. Everything here is reproduced in my own lab or against
open-source apps I run locally.

> **Status: Week 1 — in progress.** This repo grows one verified finding at a time.
> No claims without a runnable PoC. If a finding isn't here yet, I haven't proven it yet.

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

*None published yet — this section fills as I verify each one. Each finding ships with
a reproducible PoC and an honest impact statement.*

<!--
| # | Title | Stack | OWASP | Status |
|---|-------|-------|-------|--------|
| 001 | ... | ... | ... | Published |
-->

---

## Tools

*Built as the study progresses:*

- `tools/injection_tester.py` — fires categorized injection payloads at an LLM HTTP endpoint *(coming Week 2)*
- `tools/chromadb_audit.py` — audits a ChromaDB instance for common misconfigs *(coming Week 4)*

---

## Threat models

- [`threat-models/`](./threat-models) — attack-surface maps of the stacks I study, starting with my own lab.

---

## Lab setup

- **OS:** Windows 11, AMD Ryzen 7 8840HS, 16 GB RAM (CPU/iGPU inference, no dedicated GPU)
- **Inference:** Ollama (local models, GGUF quantized)
- **Planned target stack:** FastAPI gateway + ChromaDB vector store + LangChain agent

Testing is performed exclusively against systems I own or open-source apps I run
locally. No unauthorized access. Disclosure follows the 90-day coordinated standard.

---

## About

Building in public. Computer science student documenting the path from "uses AI" to
"understands how it breaks."

- X / Twitter: [@prunier_issa](https://x.com/prunier_issa)

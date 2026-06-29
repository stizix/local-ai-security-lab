# Threat Model 001 — My Local AI Lab

**Date:** 2026-06-08
**Author:** [@prunier_issa](https://x.com/prunier_issa)
**Scope:** My own machine. Components I currently run + the stack I'm about to build.
**Method:** Decompose the system, draw trust boundaries, enumerate attacker-controlled
inputs, state worst-case impact per component.

> You cannot attack what you haven't modeled. This is the map before the territory.

---

## 1. System overview

My current lab is an **Ollama** inference backend driving a **Streamlit** app
("AI-Playground") that includes a chat client, an in-memory RAG lab, and a model
puller. The planned target stack adds a **FastAPI** gateway, **ChromaDB** vector
store, and a **LangChain** agent — the components this 8-week study attacks.

```
                          MY MACHINE (Windows 11, localhost)
  ┌──────────────────────────────────────────────────────────────────────┐
  │                                                                        │
  │   [Browser]                                                            │
  │      │  http://localhost:8501                                          │
  │      ▼                                                                 │
  │  ┌─────────────────────┐      trust boundary A                        │
  │  │  Streamlit app      │ ── (user input → prompt construction) ──┐    │
  │  │  (AI-Playground)    │                                         │    │
  │  │  - chat             │                                         ▼    │
  │  │  - RAG lab (memory) │                              ┌────────────────┐
  │  │  - model puller     │ ──── HTTP /api/* ──────────► │  Ollama        │
  │  └─────────────────────┘      trust boundary B        │  :11434        │
  │            │                  (no auth, default)      │  NO AUTH       │
  │            │ embeddings/generate                      └────────────────┘
  │            │                                                  │         │
  │            ▼                                                  │ pulls   │
  │   ┌─────────────────┐                                         ▼         │
  │   │ in-memory vecs  │                          ┌──────────────────────┐ │
  │   │ (RAG lab)       │                          │ ollama registry      │ │
  │   └─────────────────┘                          │ (remote, internet)   │ │
  │                                                 └──────────────────────┘ │
  │                                                   trust boundary C       │
  │   ── PLANNED ──────────────────────────────────────────────────────     │
  │   FastAPI gateway :8000  →  LangChain agent (tools)  →  ChromaDB :8000   │
  └──────────────────────────────────────────────────────────────────────┘
```

---

## 2. Trust boundaries

- **A — Browser → Streamlit:** user-controlled text enters prompt construction. The
  boundary between "data" and "instruction" is crossed here.
- **B — App → Ollama:** Ollama's HTTP API on `:11434` has **no authentication by
  default**. Anything that can reach the port has full model control.
- **C — Ollama → registry:** model pulls fetch remote artifacts from the internet.
- **(Planned) D — FastAPI → agent → tools/ChromaDB:** LLM output becomes tool input;
  ChromaDB on `:8000` is unauthenticated by default.

---

## 3. Component analysis

### 3.1 Ollama HTTP API (`:11434`)
- **Exposed surface:** REST API (`/api/generate`, `/api/chat`, `/api/pull`, `/api/tags`).
  Binds to `127.0.0.1` by default, but is frequently re-bound to `0.0.0.0` via
  `OLLAMA_HOST` for remote access — at which point it is internet-reachable with no auth.
- **Trust boundary crossed:** B.
- **Attacker-controlled input:** if exposed (`0.0.0.0`), any network client can send
  prompts, pull arbitrary models, and enumerate installed models.
- **Worst-case impact:** full compute abuse (free inference on my hardware), model
  exfiltration/enumeration, disk exhaustion via repeated `/api/pull`, denial of service.
- **OWASP:** LLM02 (Insecure Output Handling downstream), API1 (Broken Object Auth).

### 3.2 Streamlit prompt construction (chat + base-model priming)
- **Exposed surface:** user text fields → prompt strings sent to Ollama. The base-model
  path uses `raw: true` and **concatenates user input into a hand-built prompt** with
  few-shot framing.
- **Trust boundary crossed:** A.
- **Attacker-controlled input:** the entire user message; in `raw` mode there is no chat
  template separating system framing from user content.
- **Worst-case impact:** prompt injection / role override (user text overrides the
  framing), system-framing extraction. Low severity here (single-user local app) but it
  is the **exact pattern** I'll exploit at scale in Weeks 2 and 7.
- **OWASP:** LLM01 (Prompt Injection), LLM06 (Sensitive Info Disclosure).

### 3.3 RAG lab (in-memory embeddings)
- **Exposed surface:** user pastes a document → chunked → embedded via Ollama →
  retrieved into a later prompt.
- **Trust boundary crossed:** A (ingested content becomes context).
- **Attacker-controlled input:** the document body. Retrieved chunks are injected into
  the generation prompt verbatim.
- **Worst-case impact:** indirect prompt injection — a poisoned document overrides the
  answer instruction when retrieved. In-memory and single-user today, but this is the
  Week 3 attack class in miniature.
- **OWASP:** LLM01, LLM06.

### 3.4 Model puller (`/api/pull`)
- **Exposed surface:** UI buttons trigger pulls of named models from the Ollama registry.
- **Trust boundary crossed:** C.
- **Attacker-controlled input:** model name (if the UI is ever exposed). Pulled GGUF
  artifacts are trusted and executed by the inference engine.
- **Worst-case impact:** disk exhaustion; supply-chain risk if a malicious/poisoned model
  is pulled. Mitigation: pin trusted models only.
- **OWASP:** LLM05 (Supply Chain).

### 3.5 (Planned) FastAPI + LangChain agent + ChromaDB
- **Exposed surface:** `/chat` endpoint (likely no auth in vibe-coded form), agent
  tool-loop, ChromaDB `:8000` REST API (`/api/v1/reset` wipes everything, no auth).
- **Trust boundary crossed:** D.
- **Attacker-controlled input:** request body → LLM → tool arguments; documents ingested
  into ChromaDB.
- **Worst-case impact:** excessive agency (agent invokes privileged tools on injected
  instructions), full vector-store dump/wipe, stored/persistent prompt injection.
- **OWASP:** LLM01, LLM08, LLM02, API1.

---

## 4. Highest-priority surfaces (what I attack first)

| Priority | Surface | Why |
|----------|---------|-----|
| 1 | Ollama exposed on `0.0.0.0` | Trivial, high impact, extremely common in the wild |
| 2 | Direct user input → prompt (no data/instruction separation) | Root cause of most LLM01 |
| 3 | ChromaDB unauthenticated API (planned) | Full DB control, default config, widespread |
| 4 | RAG ingestion → indirect injection | Invisible, persistent, hardest to detect |

---

## 5. Assumptions & out of scope

- Single-user, localhost-bound by default. Severity ratings assume the realistic
  misconfiguration of exposing services to a network.
- OS-level and network-level attacks (RCE on Windows, ARP, etc.) are out of scope —
  this model targets the **AI/ML application layer**.
- No third-party systems are tested. Everything is my own machine.

---

*Update: Week 2 exercised surface #2 — see [finding 001](../findings/001-prompt-injection)
(categorized payloads vs a local `/chat` endpoint; direct attacks refused 0/10,
framing-based attacks leak up to 90%). Week 3 exercised surface #4 — see
[finding 002](../findings/002-indirect-injection) (poisoned documents in a RAG store
leak a secret to an innocent user; `SYSTEM:`-framed injections hijack 10/10). Week 4
exercised surface #3 — see [finding 003](../findings/003-chromadb-unauth) (stock
ChromaDB in default config: unauthenticated dump, poison, and delete of a vector store;
the destructive `/reset` is now disabled by default but `DELETE /collections/{name}`
is not). Week 5 exercised surface #1 — see [finding 004](../findings/004-exposed-ollama)
(unauthenticated Ollama API: enumerate models and run inference on the host's hardware
with no credentials; `/api/pull` and `/api/delete` are one unauthenticated call away).
Next: Week 6 — system-prompt extraction across models.*

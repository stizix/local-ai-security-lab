# Finding 004 — Unauthenticated Ollama: a no-password API that runs your hardware

**Date:** 2026-06-28
**Author:** [@prunier_issa](https://x.com/prunier_issa)
**Target:** a stock Ollama server in default configuration, HTTP API on `:11434`
**Model used in PoC:** `qwen2.5:3b` (any installed model works)
**OWASP:** LLM10 (Unbounded Consumption), LLM05 (Supply Chain) — broken authentication at the API layer

> The bug is that everyone can send requests to Ollama, so an attacker can
> **generate, delete, and pull models** on your machine — no password, no token,
> no API key. Ollama ships with **no authentication at all.** By default it binds
> to `127.0.0.1` (localhost only), but it is routinely re-bound to `0.0.0.0` so
> other machines can reach it. The moment it is, the door has no lock and everyone
> can open it.

---

## 1. Setup

This is surface #1 / trust boundary B in
[threat-model 001](../../threat-models/001-my-lab.md) — and the #1-priority surface in
that model, because it is trivial and extremely common in the wild. Like finding 003,
there is no vulnerable app to write: **the default configuration *is* the
vulnerability.** You just need Ollama running — it already listens on `:11434`.

The attacker is assumed to reach the port. That is exactly what happens when Ollama is
re-bound to `0.0.0.0` via `OLLAMA_HOST` for "remote access" — a near-universal
misconfiguration whenever someone wants to drive their models from another machine, a
container, or a teammate's laptop. We test against `localhost`; the API and its missing
auth are byte-for-byte identical.

## 2. Result

Every request below is unauthenticated. There is no login endpoint to defeat because
there is no login at all — the proof is simply that every call returns `HTTP 200` with
no credentials attached.

**Beat 1 — enumerate (recon).** One GET lists every model on the box:

```
[ENUMERATE] HTTP 200, no password asked -> 6 models exposed:
   - mistral-base:latest
   - dolphin-llama3:latest
   - llama3.2:3b
   - deepseek-r1:8b
   - llama3.1:8b
   - qwen2.5:3b
```

That is a full inventory — ~23 GB of models, with exact names, sizes, and quantization
levels — handed to an anonymous caller. The attacker now knows precisely what is on the
machine and what to target (note `dolphin-llama3`, an uncensored model, sitting right
there).

**Beat 2 — steal compute.** One POST makes the victim's hardware run inference:

```
[STEAL COMPUTE] HTTP 200, no key sent -> ran 'qwen2.5:3b' on the victim's hardware
                and got back: 'Hello.'
```

The prompt is innocent on purpose (`"Say hello in one word"`). The attack is **not**
what is in the prompt — it is that a request with no password just spent the victim's
CPU/electricity running a model. The compute is the loot.

The full kill chain, all unauthenticated:

| Stage | Primitive | Endpoint | Auth required |
|-------|-----------|----------|---------------|
| ENUMERATE | list every installed model | `GET /api/tags` | none |
| STEAL COMPUTE | run inference on the victim's hardware | `POST /api/generate` | none |
| EXHAUST | pull arbitrary GBs of models → fill the disk (DoS) | `POST /api/pull` | none |
| DESTROY | delete the victim's models | `DELETE /api/delete` | none |

The PoC (`poc.py`) runs the first two (safe, repeatable). The last two are described,
not detonated — they damage the host, and one unauthenticated call is all they take.

## 3. Why it works

The Ollama API isn't a chat box — it is the **control panel for the machine's AI
engine**. Talking to a model is just one button on it. The other buttons download
models, delete models, and run inference, and **none of them check who is calling.**
Ollama is built to be driven by a trusted client on `localhost` and leans on **network
isolation as the only access control**. That assumption holds right up until the moment
someone binds it to a network interface — which is exactly what people do to share the
server, and exactly when the "trusted localhost client" model collapses.

This is the same *class* as [finding 003](../003-chromadb-unauth): infrastructure
trusting attacker-controlled **requests** — an authz failure, not a prompt failure. It
is a different class from findings 001/002, which were the model trusting
attacker-controlled **text**. Localhost was the only lock; auth should have been a
second, separate lock. Ollama ships with only one, so opening the first door for a
normal reason leaves nothing behind it.

## 4. Impact

Anyone who can reach the port can:

- **Steal compute** — run unlimited inference on the victim's hardware, for free. This
  is the documented real-world abuse: attackers scan the internet for exposed Ollama
  and run inference farms on strangers' machines (the victim pays the electricity and
  watches their box crawl).
- **Exhaust the host** — `POST /api/pull` downloads multi-GB models on demand; called
  in a loop it fills the disk and denies service (LLM10, Unbounded Consumption).
- **Destroy models** — `DELETE /api/delete` removes the victim's models, breaking any
  app that depends on them.
- **Pull from untrusted sources** — a model name the attacker controls fetches and runs
  an artifact the inference engine then trusts (LLM05, Supply Chain).
- **Reconnaissance** — `GET /api/tags` reveals the exact model inventory, useful for
  targeting follow-on attacks (e.g. an uncensored model to abuse, or a known-vulnerable
  one).

All without credentials, and — with `0.0.0.0` — from anywhere on the network.

## 5. Root cause

No authentication in the API, in any configuration. Ollama has **no built-in auth
feature at all**; access control is delegated entirely to network reachability, which
fails the moment the service is exposed beyond `localhost`.

## 6. Fix

Because Ollama has no native auth, "add a login" is not a setting you can flip — the fix
is one of two shapes:

- **Don't open the first lock.** Keep Ollama bound to `127.0.0.1` (the default). Never
  set `OLLAMA_HOST=0.0.0.0` on a machine reachable by untrusted networks.
- **Add the second lock yourself.** If the API must be reachable remotely, put a
  **reverse proxy** (nginx, Caddy, …) in front that authenticates every request
  (API key / basic auth / mTLS) *before* it reaches Ollama, and firewall `:11434` so it
  is only reachable through the proxy.
- **Network-segment it.** Treat the inference server like a database: default-deny,
  reachable only by the apps that need it.
- **Cap consumption.** Rate-limit and constrain pulls at the proxy so a single caller
  cannot exhaust disk or compute even if they get through.

## 7. Reproduce

```bash
# Ollama running in its default config (it already listens on :11434)
ollama serve            # if it isn't already running

# the attack
cd findings/004-exposed-ollama
py -3.11 poc.py
```

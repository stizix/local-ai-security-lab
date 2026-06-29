# Backlog — ideas, not commitments

This is a parking lot, not a plan. Nothing here is promised. The project ships
**one verified finding at a time**, depth over count. A finding earns a number only
when it has a runnable PoC and an honest impact statement.

The rule for pulling something off this list: it has to (1) run on my hardware
(CPU / iGPU, 16 GB, no dedicated GPU), (2) build on what I already have, and
(3) make a finding I can explain and defend myself. Quantity of reproductions is not
the signal — depth and originality are.

---

## Next up — the committed arc

- **005** — System-prompt extraction *across models* (comparative leak-rate table over
  all 6 local models). First study where the result isn't handed to me.
- **006** — Stored / persistent RAG poisoning in a real vector store (chains 002 + 003).
- **007** — Excessive agency: agent tool abuse (the portfolio centerpiece).

## Gems pulled from a brainstorm (slot in where they fit — max a handful)

- **logs/metrics leakage** — prompts, tokens, user inputs in cleartext logs. Easy, common, real.
- **undocumented inference endpoints** — OpenAI-compatible `/v1/models` etc. (vLLM, LM Studio). Pairs with finding 004.
- **many-shot jailbreaking** — documented, no GPU needed, strong write-up.
- **reasoning-trace leaking** — extract hidden reasoning from `deepseek-r1` (I already have it). Pairs with 005.
- **output-filter evasion** — direct sequel to finding 001 (exact-match filters are evadable).
- **resource-exhaustion DoS** — formalize the `/api/pull` disk-fill already noted in finding 004.

## The one that actually matters

- **A finding that's mine** — a bug, or a combination, that nobody handed me. One of
  these outweighs the rest of the list. Open question driving the whole project:
  *which finding becomes mine?*

## Deferred — needs different hardware or a research setup

- Weight/model stealing (locally the weights are already on disk — moot).
- GCG / gradient-based adversarial suffixes (needs a GPU).
- Fine-tuning / LoRA data-poisoning & backdoors (compute-heavy).
- Model inversion / membership inference (research-grade).
- Multimodal / vision jailbreaks (no vision models installed).
- Embedding side-channels, multi-agent collusion (niche / hard to demo cleanly).

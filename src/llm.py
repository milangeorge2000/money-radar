"""LLM layer: Gemini primary, OpenRouter backup. Human tone, resume-grounded.

Keys come from config.yaml (git-ignored) or env vars. Returns (text, error);
error != '' means all providers failed — UI shows it instead of fake output.
"""
from __future__ import annotations
import json
import os
import urllib.request

HUMAN = ("Write like a real human consultant, not an AI. Plain words, "
         "contractions, mixed sentence lengths. BANNED: passionate, leverage, "
         "cutting-edge, thrilled, delve, tapestry, landscape, game-changer, "
         "robust, seamless, synergy, 'I hope this finds you well'. No emojis, "
         "no bullet-point soup (short lists only when they add clarity). "
         "Concrete over generic: cite the client's actual problem and one "
         "real past result. Never invent experience.")


def _post(url, payload, headers, timeout=60):
    import ssl
    try:
        import certifi
        ctx = ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        ctx = None
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        return json.loads(r.read().decode())


def _gemini(key, model, system, user):
    from urllib.parse import urlencode
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?"
           + urlencode({"key": key}))
    d = _post(url, {"contents": [{"parts": [{"text": system + "\n\n" + user}]}],
                    "generationConfig": {"temperature": 0.6}},
              {"Content-Type": "application/json"})
    return d["candidates"][0]["content"]["parts"][0]["text"].strip()


def _openrouter(key, model, system, user):
    d = _post("https://openrouter.ai/api/v1/chat/completions",
              {"model": model,
               "messages": [{"role": "system", "content": system},
                            {"role": "user", "content": user}],
               "temperature": 0.6},
              {"Authorization": f"Bearer {key}", "Content-Type": "application/json",
               "HTTP-Referer": "https://github.com/money-radar", "X-Title": "money-radar"},
              timeout=90)
    return d["choices"][0]["message"]["content"].strip()


def chat(llm_cfg: dict, system: str, user: str) -> tuple[str, str]:
    order = []
    gk = llm_cfg.get("gemini_api_key") or os.getenv("GEMINI_API_KEY") or ""
    ok = llm_cfg.get("openrouter_api_key") or os.getenv("OPENROUTER_API_KEY") or ""
    if gk:
        order.append(("gemini", gk))
    if ok:
        order.append(("openrouter", ok))
    if not order:
        return "", "No LLM key configured (gemini_api_key / openrouter_api_key)."
    errs = []
    for name, key in order:
        try:
            if name == "gemini":
                return _gemini(key, llm_cfg.get("gemini_model") or "gemini-flash-latest",
                               system, user), ""
            return _openrouter(key, llm_cfg.get("openrouter_model") or
                               "google/gemma-4-31b-it:free", system, user), ""
        except Exception as e:
            errs.append(f"{name}: {str(e)[:120]}")
    return "", "All LLM providers failed — " + " | ".join(errs)

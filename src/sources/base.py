"""Shared HTTP helpers (stdlib only)."""
from __future__ import annotations
import json
import ssl
import urllib.request

try:
    import certifi
    CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    CTX = None

UA = {"User-Agent": "money-radar/1.0"}


def get_text(url: str, timeout: int = 30) -> str:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
        raw = r.read()
    for enc in ("utf-8", "latin-1"):
        try:
            return raw.decode(enc)
        except Exception:
            continue
    return raw.decode("utf-8", "replace")


def get_json(url: str, timeout: int = 30) -> dict | list:
    return json.loads(get_text(url, timeout))

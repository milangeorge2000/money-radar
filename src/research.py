"""Client/company enrichment via Tavily (tested working key in config)."""
from __future__ import annotations
import json
import os
import urllib.request
from .llm import _post


def enrich(company: str, tavily_key: str, max_results: int = 3) -> str:
    """One-paragraph client context: what they do, size/signals. '' on failure."""
    key = tavily_key or os.getenv("TAVILY_API_KEY") or ""
    if not key or not company:
        return ""
    try:
        d = _post("https://api.tavily.com/search",
                  {"api_key": key, "query": f"{company} company what they do funding",
                   "max_results": max_results, "include_answer": True},
                  {"Content-Type": "application/json"}, timeout=40)
        ans = d.get("answer", "")
        if ans:
            return ans[:800]
        bits = [r.get("content", "")[:300] for r in d.get("results", [])[:2]]
        return " ".join(bits)[:800]
    except Exception:
        return ""

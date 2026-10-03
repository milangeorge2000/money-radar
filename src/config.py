"""Load config.yaml (git-ignored, holds real keys)."""
from __future__ import annotations
import os
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent


def load_config(path=None) -> dict:
    p = Path(path) if path else ROOT / "config.yaml"
    if not p.exists():
        p = ROOT / "config.example.yaml"
    cfg = yaml.safe_load(p.read_text()) or {}
    llm = cfg.get("llm", {})
    if not llm.get("gemini_api_key") and os.getenv("GEMINI_API_KEY"):
        llm["gemini_api_key"] = os.environ["GEMINI_API_KEY"]
    if not llm.get("openrouter_api_key") and os.getenv("OPENROUTER_API_KEY"):
        llm["openrouter_api_key"] = os.environ["OPENROUTER_API_KEY"]
    res = cfg.get("research", {})
    if not res.get("tavily_api_key") and os.getenv("TAVILY_API_KEY"):
        res["tavily_api_key"] = os.environ["TAVILY_API_KEY"]
    return cfg

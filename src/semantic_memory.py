"""Optional semantic memory (mem0) over the SQLite opportunity store.

Why mem0 and not Zep/Letta here:
- mem0 is a memory *layer* (add/search API over any vector store incl. local
  Qdrant) — fits "recall similar past gigs" with zero infra.
- Zep's current form (Graphiti temporal KG) needs Neo4j/FalkorDB + always-on
  LLM — overkill for gig recall, right tool for cross-session agent state.
- Letta is a full agent server (Docker + Postgres) — right tool when the
  radar grows a conversational operator, not for silent recall.

Default OFF. Enable with: semantic: {enabled: true} in config.yaml.
Requires: pip install mem0ai qdrant-client. Falls back to SQLite silently.
"""
from __future__ import annotations


def available() -> bool:
    try:
        import mem0  # noqa: F401
        return True
    except ImportError:
        return False


class SemanticMemory:
    """Thin wrapper: remembers opportunity summaries, recalls similar ones."""

    def __init__(self, cfg: dict):
        from mem0 import Memory
        llm_cfg = cfg.get("llm", {})
        model = llm_cfg.get("gemini_model") or "gemini-flash-latest"
        key = llm_cfg.get("gemini_api_key") or ""
        self._mem = Memory.from_config({
            "version": "v1.1",
            "llm": {"provider": "gemini",
                    "config": {"model": model, "api_key": key}},
            "embedder": {"provider": "gemini",
                         "config": {"model": "models/text-embedding-004",
                                    "api_key": key}},
            "vector_store": {"provider": "qdrant",
                             "config": {"path": "./data/mem0_qdrant"}},
        })

    def remember(self, op) -> None:
        try:
            self._mem.add(
                f"{op.title} at {op.client or 'unknown client'} [{op.source}]. "
                f"Budget {op.budget_text or 'unstated'}. Fit {op.fit_pct}%, "
                f"action {op.action}. Skills: {', '.join(op.skills_required) or 'n/a'}. "
                f"{op.description[:600]}",
                user_id="milan", metadata={"opp_id": op.id, "action": op.action})
        except Exception:
            pass

    def similar(self, query: str, k: int = 5) -> list[dict]:
        try:
            res = self._mem.search(query, user_id="milan", limit=k)
            out = res.get("results", []) if isinstance(res, dict) else res
            return [{"text": r.get("memory", ""), "score": r.get("score", 0)}
                    for r in (out or [])]
        except Exception:
            return []

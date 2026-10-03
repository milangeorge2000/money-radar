"""Evidence-based resume matching (not keyword bingo).

For each opportunity: which profile skills show up in the posting (with the
evidence that backs them), which required skills are missing, a fit %, and a
'why would this client hire Milan' paragraph.
"""
from __future__ import annotations
import re

# Skill -> alternate spellings to look for in postings.
ALIASES = {
    "LangGraph": ["langgraph", "lang graph"],
    "MCP": ["mcp", "model context protocol"],
    "RAG": ["rag", "retrieval-augmented", "retrieval augmented"],
    "SQL agents": ["sql agent", "text-to-sql", "text to sql", "nl-to-sql", "nl to sql"],
    "Snowflake": ["snowflake"],
    "FastAPI": ["fastapi", "fast api"],
    "LLM evaluation": ["llm eval", "evals", "evaluation", "ragas", "deepeval", "judge"],
    "Observability": ["observability", "langsmith", "langfuse", "tracing", "monitoring"],
    "AI governance": ["governance", "guardrail", "rbac", "compliance", "audit"],
    "Python": ["python"],
    "Vector DBs": ["pinecone", "qdrant", "weaviate", "vector db", "vector database", "pgvector"],
    "Fine-tuning": ["fine-tun", "finetun", "lora", "peft", "vllm"],
}

# Vocabulary used to detect *required* skills named in a posting.
REQUIRED_VOCAB = {
    "voice": ["voice", "elevenlabs", "whisper", "tts", "stt", "speech", "telephony", "twilio", "vapi", "retell"],
    "frontend": ["react", "next.js", "frontend", "typescript"],
    "mobile": ["ios", "android", "flutter", "react native"],
    "databricks": ["databricks"],
    "devops": ["kubernetes", "k8s", "terraform", "mlops", "ci/cd"],
}


def _hits(text: str, keys: list[str]) -> list[str]:
    t = text.lower()
    return [k for k in keys if k in t]


def match(op, skills: dict) -> None:
    """Fills op.matched / op.missing / op.fit_pct / op.why_hire in place."""
    hay = f"{op.title}\n{op.description}"
    matched = []
    for skill, evidence in skills.items():
        if _hits(hay, ALIASES.get(skill, [skill.lower()])):
            matched.append((skill, evidence))
    op.matched = matched
    # required skills the posting names that we cannot evidence
    have = {s.lower() for s, _ in matched}
    missing = []
    for label, keys in REQUIRED_VOCAB.items():
        found = _hits(hay, keys)
        if found and label not in {s.lower() for s, _ in matched} and label not in have:
            # only count if no matched skill already covers it
            if not any(label in s.lower() for s, _ in matched):
                missing.append(f"{label} ({', '.join(found[:3])})")
    op.missing = missing
    op.fit_pct = round(100 * len(matched) / max(len(matched) + len(missing), 1))
    if op.fit_pct >= 80:
        verdict = "Strong"
    elif op.fit_pct >= 55:
        verdict = "Good"
    elif op.fit_pct >= 30:
        verdict = "Stretch"
    else:
        verdict = "Weak"
    ev = "; ".join(f"{s} — {e}" for s, e in matched[:4]) or "general AI engineering background"
    op.why_hire = (f"{verdict} fit ({op.fit_pct}%). This client would hire Milan because: {ev}."
                   + (f" Gaps to address: {'; '.join(missing[:3])}." if missing else ""))

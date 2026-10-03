"""Proposal + SOW generators. Resume-grounded, human tone, per-opportunity.

Nothing is ever sent automatically — these return drafts for YOU to approve.
"""
from __future__ import annotations
from .llm import HUMAN, chat


def _resume_block(cfg: dict) -> str:
    skills = cfg.get("skills", {})
    lines = [f"- {s}: {e}" for s, e in skills.items()]
    p = cfg.get("profile", {})
    return (f"Candidate: {p.get('full_name','')} — {p.get('title','')} "
            f"({p.get('email','')})\nProven track record:\n" + "\n".join(lines))


def generate_proposal(cfg: dict, op, client_context: str = "") -> tuple[str, str]:
    system = HUMAN + (" You write freelance proposals that win work. Structure: "
                      "opening line tied to THEIR problem, show you understand it, "
                      "relevant experience (1-2 concrete results), proposed technical "
                      "approach (3-5 sentences), deliverables, timeline, 2-3 sharp "
                      "questions, short CTA. Under 350 words. Ground every claim in "
                      "the resume below; invent nothing.")
    user = (f"Opportunity: {op.title} at {op.client or 'client (see link)'}\n"
            f"Source: {op.source} | Budget: {op.budget_text or 'not stated'} | {op.url}\n"
            f"Description:\n{op.description[:3500]}\n\n"
            f"Fit analysis: {op.why_hire}\nMissing skills: {', '.join(op.missing) or 'none'}\n"
            f"Client context: {client_context[:800] or 'n/a'}\n\n{_resume_block(cfg)}\n\n"
            "Write the proposal only.")
    return chat(cfg.get("llm", {}), system, user)


def generate_sow(cfg: dict, op, proposal: str = "") -> tuple[str, str]:
    system = HUMAN + (" You write consultant-grade Statements of Work. Sections: "
                      "Problem, Scope (in/out), Architecture, Deliverables, "
                      "Milestones, Timeline, Assumptions, Pricing (fixed fee "
                      "with the estimate below, or hourly), Acceptance criteria. "
                      "Concrete and professional. Ground claims in the resume; invent nothing.")
    user = (f"Opportunity: {op.title} at {op.client or 'client'}\n"
            f"Estimated value: ${op.value_usd:,.0f}, effort ~{op.effort_hours:.0f}h, "
            f"fit {op.fit_pct}%\nDescription:\n{op.description[:3000]}\n\n"
            f"Agreed approach (from accepted proposal):\n{proposal[:2000] or 'n/a'}\n\n"
            f"{_resume_block(cfg)}\n\nWrite the SOW only.")
    return chat(cfg.get("llm", {}), system, user)

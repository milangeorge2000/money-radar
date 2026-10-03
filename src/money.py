"""Money math: value, effort, rate, probability, competition, strategy.

Transparent heuristics (shown in the UI), not black-box scores.
"""
from __future__ import annotations
import re

RATE = re.compile(r"\$\s?([\d,]+(?:\.\d+)?)\s*(k)?\s*(?:-|–|to)?\s*\$?\s?([\d,]+(?:\.\d+)?)?\s*(k)?", re.I)
HOURLY = re.compile(r"(per|\/|\ban?\b)\s*hour|\/hr|hourly", re.I)


def parse_budget(text: str) -> tuple[float, float, bool]:
    """-> (min_usd, max_usd, is_hourly). 0,0,False when unknown."""
    t = (text or "").replace(",", "")
    m = RATE.search(t)
    if not m:
        return 0.0, 0.0, False
    def num(x, k):
        v = float(x) if x else 0.0
        return v * 1000 if k else v
    lo, hi = num(m.group(1), m.group(2)), num(m.group(3), m.group(4))
    if hi == 0:
        hi = lo
    return lo, hi, bool(HOURLY.search(t))


def estimate_effort(op) -> float:
    """Rough hours from engagement shape + description cues."""
    t = (op.title + " " + op.description).lower()
    if op.is_hourly:
        return 20.0  # evaluate first week
    if any(k in t for k in ["mvp", "prototype", "pilot", "audit", "review"]):
        return 25.0
    if any(k in t for k in ["platform", "production", "enterprise", "rebuild", "migration"]):
        return 80.0
    if any(k in t for k in ["agent", "rag", "chatbot", "automation", "integration"]):
        return 40.0
    return 30.0


def score(op, rates: dict) -> None:
    lo, hi = op.budget_min, op.budget_max
    if hi > 0:
        op.value_usd = hi if not op.is_hourly else hi * 20.0
    else:
        op.value_usd = rates.get("min_project_usd", 1500)
    op.effort_hours = estimate_effort(op)
    op.eff_rate = round(op.value_usd / max(op.effort_hours, 1), 2)
    target = rates.get("target_hourly_usd", 60)
    # probability blend: fit + rate sanity
    rate_ok = 1.0 if op.eff_rate >= target else max(0.3, op.eff_rate / target)
    op.prob = round(min(0.95, (op.fit_pct / 100) * 0.7 + rate_ok * 0.3), 2)
    src = (op.source or "").lower()
    op.competition = ("high" if src in ("upwork", "linkedin") else
                      "medium" if src in ("rss", "hackernews") else "low")
    # strategic: portfolio-worthy keywords
    t = (op.title + " " + op.description).lower()
    op.strategic = round(min(10.0, sum([
        3.0 if "agent" in t else 0, 2.0 if "mcp" in t else 0,
        2.0 if "eval" in t else 0, 2.0 if "enterprise" in t else 0,
        1.0 if "rag" in t else 0,
    ])), 1)
    money = min(10.0, op.eff_rate / max(target, 1) * 10)
    fit = op.fit_pct / 10
    career = op.strategic
    portfolio = min(10.0, career + (1 if op.fit_pct >= 70 else 0))
    effort = max(0.0, 10 - op.effort_hours / 10)
    op.scores = {"money": round(money, 1), "fit": round(fit, 1),
                 "career": career, "portfolio": round(portfolio, 1),
                 "effort": round(effort, 1)}
    avg = sum(op.scores.values()) / 5
    t = (op.title + " " + op.description).lower()
    is_job = any(k in t for k in ["full-time", "full time", "equity", "per year", "/year", "salary"])
    is_gig = any(k in t for k in ["contract", "freelance", "freelancer", "gig", "bounty", "hourly", "part-time", "sow"])
    if avg >= 7 and op.eff_rate >= target * 0.8 and op.fit_pct >= 55 and (is_gig or not is_job):
        op.action, op.action_why = "Apply", f"worth it: ~${op.value_usd:,.0f} at ${op.eff_rate:,.0f}/hr effective, {op.fit_pct}% fit"
    elif avg >= 5 and not (is_job and not is_gig):
        op.action, op.action_why = "Consider", "decent on balance — check budget/competition before pitching"
    elif is_job and not is_gig:
        op.action, op.action_why = "Skip", "full-time employment posting, not freelance — kept for reference"
    else:
        op.action, op.action_why = "Skip", "low compensation relative to effort/fit"


def apply_budget(op, rates) -> None:
    lo, hi, hourly = parse_budget(op.budget_text + " " + op.description[:500])
    op.budget_min, op.budget_max, op.is_hourly = lo, hi, hourly
    score(op, rates)

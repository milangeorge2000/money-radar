"""Core data model."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Opportunity:
    id: str
    title: str
    client: str = ""
    source: str = ""          # linkedin | upwork | github | hackernews | rss | manual ...
    url: str = ""
    posted_at: str = ""       # ISO date
    age_hours: float = 9999.0
    description: str = ""
    budget_text: str = ""
    budget_min: float = 0.0   # USD (project) or USD/hr if is_hourly
    budget_max: float = 0.0
    is_hourly: bool = False
    location: str = ""
    remote: bool = True
    skills_required: list = field(default_factory=list)
    contact: str = ""
    # scored fields (filled by matcher + money)
    matched: list = field(default_factory=list)    # [(skill, evidence)]
    missing: list = field(default_factory=list)
    fit_pct: float = 0.0
    why_hire: str = ""
    value_usd: float = 0.0
    effort_hours: float = 0.0
    eff_rate: float = 0.0
    prob: float = 0.0          # 0..1 probability of being qualified
    competition: str = "unknown"
    strategic: float = 0.0     # 0..10 career/portfolio value
    scores: dict = field(default_factory=dict)  # money/fit/career/portfolio/effort 0..10
    action: str = "Skip"
    action_why: str = ""
    status: str = "new"        # new | shortlisted | pitched | sent | won | lost | skipped

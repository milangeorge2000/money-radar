"""Assisted sources: paste text/URL -> Opportunity; search-URL builders.

Upwork/Contra/Wellfound/Toptal/LinkedIn expose no public job API, so the
radar helps you collect from them instead of pretending otherwise:
- paste a posting's text -> parsed Opportunity (LLM or heuristic)
- one-click search URLs pre-filtered to AI contract/remote work
"""
from __future__ import annotations
import re
from urllib.parse import quote_plus

from ..dedup import age_of
from ..models import Opportunity


def search_urls(query: str = "AI engineer contract remote") -> dict[str, str]:
    q = quote_plus(query)
    return {
        "upwork": f"https://www.upwork.com/nx/search/jobs/?q={q}",
        "contra": f"https://contra.com/hire?query={q}",
        "wellfound": f"https://wellfound.com/jobs?query={q}&remote=true&jobType=contract",
        "linkedin": f"https://www.linkedin.com/jobs/search/?keywords={q}&f_WT=2&f_JT=C&f_TPR=r86400",
        "toptal": "https://www.toptal.com/hire",
    }


def from_text(source: str, title: str, text: str, url: str = "",
              client: str = "", budget_text: str = "") -> Opportunity:
    text = re.sub(r"\s+", " ", text or "").strip()[:4000]
    o = Opportunity(id=f"manual-{abs(hash((title, text[:80]))) % 10**10}",
                    title=title[:180] or text[:80], client=client,
                    source=source or "manual", url=url, description=text,
                    budget_text=budget_text, location="Remote", remote=True)
    o.age_hours = 0.0
    o.posted_at = ""
    return o

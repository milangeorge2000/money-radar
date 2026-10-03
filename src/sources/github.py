"""Live: GitHub issues tagged freelance/bounty/paid (public API, 60 req/hr)."""
from __future__ import annotations
from urllib.parse import quote

from .base import get_json
from ..dedup import age_of
from ..models import Opportunity

API = ("https://api.github.com/search/issues?q={q}"
       "&sort=created&order=desc&per_page={n}")


def fetch(max_items: int = 30) -> list[Opportunity]:
    out = []
    queries = [
        "bounty label:bounty",
        "freelance label:freelance",
        "paid bounty in:title",
    ]
    seen = set()
    for raw in queries:
        q = quote(raw + " state:open type:issue")
        try:
            data = get_json(API.format(q=q, n=max_items))
        except Exception:
            continue
        for it in (data.get("items") or [])[:max_items]:
            uid = it.get("id")
            if uid in seen:
                continue
            seen.add(uid)
            body = (it.get("body") or "")[:2500]
            posted = (it.get("created_at") or "").replace("Z", "+00:00")
            o = Opportunity(id=f"gh-{it.get('number')}-{uid}",
                            title=(it.get("title") or "")[:180],
                            client=(it.get("repository_url") or "").split("/")[-1],
                            source="github", url=it.get("html_url", ""),
                            posted_at=posted, description=body,
                            location="Remote", remote=True)
            o.age_hours = age_of(posted)
            out.append(o)
    return out

"""Live: Hacker News monthly 'Who is hiring' threads (public API, no key)."""
from __future__ import annotations
import re
from datetime import datetime, timezone
from urllib.parse import quote

from .base import get_json
from ..dedup import age_of
from ..models import Opportunity

ALGOLIA = "https://hn.algolia.com/api/v1/search?query=Who%20is%20hiring%20{}&tags=story&hitsPerPage=3"
FB = "https://hacker-news.firebaseio.com/v0/item/{}.json"


def _latest_hiring_thread() -> int | None:
    ym = datetime.now(timezone.utc).strftime("%B %Y")
    try:
        data = get_json(ALGOLIA.format(quote(ym)) if "{}" in ALGOLIA else ALGOLIA.replace("{}", quote(ym)))
        hits = data.get("hits", [])
        if hits:
            return hits[0]["objectID"]
    except Exception:
        pass
    return None


def fetch(keywords: list[str], max_comments: int = 120) -> list[Opportunity]:
    out, kws = [], [k.lower() for k in keywords]
    try:
        tid = _latest_hiring_thread()
        if not tid:
            return out
        kids = (get_json(FB.format(tid)) or {}).get("kids", [])[:max_comments]
        for cid in kids:
            try:
                c = get_json(FB.format(cid)) or {}
                import html as _html
                text = re.sub(r"<[^>]+>", " ", c.get("text") or "")
                text = _html.unescape(re.sub(r"\s+", " ", text).strip())
                if not text or not any(k in text.lower() for k in kws):
                    continue
                ts = c.get("time", 0)
                posted = datetime.fromtimestamp(ts, timezone.utc).isoformat() if ts else ""
                first = text.split(".")[0][:140]
                out.append(Opportunity(
                    id=f"hn-{cid}", title=first, client="", source="hackernews",
                    url=f"https://news.ycombinator.com/item?id={cid}",
                    posted_at=posted, description=text[:2500],
                    location="Remote", remote=False))
            except Exception:
                continue
    except Exception:
        pass
    for o in out:
        o.age_hours = age_of(o.posted_at)
    return [o for o in out if o.age_hours <= 24 * 31]

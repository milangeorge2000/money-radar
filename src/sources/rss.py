"""Live RSS sources (no key): RemoteOK, We Work Remotely. Stdlib XML."""
from __future__ import annotations
import email.utils
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

from .base import get_text
from ..dedup import age_of
from ..models import Opportunity

STRIP = re.compile(r"<[^>]+>")


def _clean(html: str) -> str:
    text = STRIP.sub(" ", html or "")
    return re.sub(r"\s+", " ", text).strip()[:3000]


def _parse_date(s: str) -> str:
    try:
        dt = email.utils.parsedate_to_datetime(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    except Exception:
        return ""


def fetch_feed(feed_url: str, keywords: list[str], max_items: int = 60) -> list[Opportunity]:
    out = []
    try:
        root = ET.fromstring(get_text(feed_url))
    except Exception:
        return out
    kws = [k.lower() for k in keywords]
    n = 0
    for item in root.iter("item"):
        if n >= max_items:
            break
        n += 1
        title = (item.findtext("title") or "").strip()
        desc = _clean(item.findtext("description") or "")
        link = (item.findtext("link") or "").strip()
        posted = _parse_date(item.findtext("pubDate") or "")
        hay = f"{title} {desc}".lower()
        if kws and not any(k in hay for k in kws):
            continue
        company = ""
        m = re.split(r"\s[-–:|]\s", title, maxsplit=1)
        short = title
        if len(m) == 2:
            company, short = m[0].strip(), m[1].strip()
        op = Opportunity(id=f"rss-{abs(hash(link or title)) % 10**10}",
                         title=short or title, client=company, source="rss",
                         url=link, posted_at=posted, description=desc,
                         location="Remote", remote=True)
        op.age_hours = age_of(posted)
        out.append(op)
    return out


def fetch_all(feeds: list[str], keywords: list[str]) -> list[Opportunity]:
    out = []
    for f in feeds:
        out += fetch_feed(f, keywords)
    return out

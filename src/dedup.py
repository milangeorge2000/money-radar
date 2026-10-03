"""Freshness buckets + dedup."""
from __future__ import annotations
from datetime import datetime, timezone


def bucket(age_hours: float) -> str:
    if age_hours <= 24:
        return "24h"
    if age_hours <= 72:
        return "3d"
    if age_hours <= 168:
        return "7d"
    return "stale"


def _now():
    return datetime.now(timezone.utc)


def age_of(posted_at: str) -> float:
    try:
        dt = datetime.fromisoformat(posted_at)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return max(0.0, (_now() - dt).total_seconds() / 3600)
    except Exception:
        return 9999.0


def dedup(opps: list) -> list:
    """Drop exact URL dupes + same title+client (keep freshest)."""
    best = {}
    for o in opps:
        key = (o.url.strip().lower() if o.url else
               f"{o.title.lower()}|{o.client.lower()}")
        if key not in best or o.age_hours < best[key].age_hours:
            best[key] = o
    return sorted(best.values(), key=lambda o: o.age_hours)

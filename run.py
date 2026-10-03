#!/usr/bin/env python3
"""CLI: scan | stats. UI: `streamlit run app.py` or `./money-radar start`."""
from __future__ import annotations
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.config import load_config
from src.dedup import bucket, dedup
from src.matcher import match
from src.memory import Memory
from src.money import apply_budget
from src.sources import assisted, github, hackernews, rss


def scan(cfg) -> list:
    s = cfg.get("sources", {})
    kws = s.get("keywords", [])
    opps = []
    if s.get("rss_feeds"):
        opps += rss.fetch_all(s["rss_feeds"], kws)
    if s.get("hackernews", True):
        opps += hackernews.fetch(kws)
    if s.get("github_bounty", True):
        opps += github.fetch()
    opps = dedup(opps)
    mem = Memory(cfg.get("memory", {}).get("db_path", "./data/radar.db"))
    today = date.today().isoformat()
    for o in opps:
        if bucket(o.age_hours) == "stale":
            continue
        match(o, cfg.get("skills", {}))
        apply_budget(o, cfg.get("rates", {}))
        mem.save(o, today)
    return [o for o in opps if bucket(o.age_hours) != "stale"]


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "scan"
    cfg = load_config()
    if cmd == "scan":
        opps = scan(cfg)
        counts = {}
        for o in opps:
            counts[o.action] = counts.get(o.action, 0) + 1
        print(f"scanned={len(opps)} " + " ".join(f"{k}={v}" for k, v in counts.items()))
        for o in sorted(opps, key=lambda x: -x.fit_pct)[:5]:
            if o.action == "Apply":
                print(f"APPLY [{o.fit_pct}%] ${o.value_usd:,.0f} :: {o.title} ({o.source}) :: {o.url}")
    elif cmd == "stats":
        st = Memory(cfg.get("memory", {}).get("db_path", "./data/radar.db")).stats()
        print(f"scanned={st['scanned']} strong={st['strong']} avg_budget=${st['avg_budget']:,}")
        print("demand:", ", ".join(f"{k}={v}" for k, v in st["demand"]))
        print(f"top_category={st['top_category']} top_missing={st['top_missing']}")
    else:
        print("usage: run.py [scan|stats]")


if __name__ == "__main__":
    main()

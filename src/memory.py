"""SQLite opportunity memory + 30-day market stats."""
from __future__ import annotations
import sqlite3
from pathlib import Path
from .models import Opportunity

SCHEMA = """
CREATE TABLE IF NOT EXISTS opportunities (
    id TEXT PRIMARY KEY, title TEXT, client TEXT, source TEXT, url TEXT,
    posted_at TEXT, age_hours REAL, description TEXT, budget_text TEXT,
    budget_min REAL, budget_max REAL, is_hourly INT, location TEXT,
    skills_required TEXT, fit_pct REAL, value_usd REAL, effort_hours REAL,
    eff_rate REAL, prob REAL, competition TEXT, strategic REAL,
    scores TEXT, action TEXT, action_why TEXT, status TEXT, scanned_day TEXT
);
"""


class Memory:
    def __init__(self, db_path: str):
        self.p = Path(db_path)
        self.p.parent.mkdir(parents=True, exist_ok=True)
        self.c = sqlite3.connect(self.p)
        self.c.execute(SCHEMA)
        self.c.commit()

    def save(self, o: Opportunity, day: str) -> None:
        import json
        self.c.execute(
            """INSERT INTO opportunities VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(id) DO UPDATE SET status=excluded.status,
               fit_pct=excluded.fit_pct, action=excluded.action, action_why=excluded.action_why""",
            (o.id, o.title, o.client, o.source, o.url, o.posted_at, o.age_hours,
             o.description[:2000], o.budget_text, o.budget_min, o.budget_max,
             int(o.is_hourly), o.location, ",".join(o.skills_required), o.fit_pct,
             o.value_usd, o.effort_hours, o.eff_rate, o.prob, o.competition,
             o.strategic, json.dumps(o.scores), o.action, o.action_why, o.status, day))
        self.c.commit()

    def set_status(self, oid: str, status: str) -> None:
        self.c.execute("UPDATE opportunities SET status=? WHERE id=?", (status, oid))
        self.c.commit()

    def stats(self, days: int = 30) -> dict:
        import json
        from datetime import date, timedelta
        since = (date.today() - timedelta(days=days)).isoformat()
        rows = self.c.execute(
            "SELECT title, description, budget_max, is_hourly, fit_pct, action, status, scanned_day "
            "FROM opportunities WHERE scanned_day >= ?", (since,)).fetchall()
        demand: dict[str, int] = {}
        vocab = ["agent", "rag", "mcp", "automation", "voice", "chatbot", "eval", "fine-tun", "mlops"]
        budgets, strong, cats = [], 0, {}
        for title, desc, bmax, hourly, fit, action, status, _ in rows:
            t = f"{title} {desc}".lower()
            for v in vocab:
                if v in t:
                    demand[v] = demand.get(v, 0) + 1
            if (bmax or 0) > 0:
                budgets.append(bmax if not hourly else bmax * 20)
            if (fit or 0) >= 70:
                strong += 1
            for v in vocab:
                if v in t:
                    cats[v] = cats.get(v, 0) + 1
        missing = {}
        for title, desc, *_ in rows:
            t = f"{title} {desc}".lower()
            for m in ["voice", "databricks", "react", "mobile"]:
                if m in t:
                    missing[m] = missing.get(m, 0) + 1
        avg = round(sum(budgets) / len(budgets)) if budgets else 0
        top_cat = max(cats, key=cats.get) if cats else "—"
        top_missing = max(missing, key=missing.get) if missing else "—"
        return {"scanned": len(rows), "strong": strong, "avg_budget": avg,
                "demand": sorted(demand.items(), key=lambda x: -x[1])[:5],
                "top_category": top_cat, "top_missing": top_missing}

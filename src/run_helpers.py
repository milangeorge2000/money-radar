"""Load scored opportunities back from memory for the dashboard."""
from __future__ import annotations
import json
from .models import Opportunity


def current_opps(cfg, mem) -> list:
    rows = mem.c.execute(
        "SELECT id,title,client,source,url,posted_at,age_hours,description,budget_text,"
        "budget_min,budget_max,is_hourly,location,fit_pct,value_usd,effort_hours,"
        "eff_rate,prob,competition,strategic,scores,action,action_why,status,"
        "skills_required FROM opportunities ORDER BY fit_pct DESC LIMIT 200").fetchall()
    out = []
    prof = cfg.get("skills", {})
    for r in rows:
        o = Opportunity(id=r[0], title=r[1], client=r[2], source=r[3], url=r[4],
                        posted_at=r[5], age_hours=r[6] or 9999, description=r[7],
                        budget_text=r[8], budget_min=r[9], budget_max=r[10],
                        is_hourly=bool(r[11]), location=r[12], fit_pct=r[13],
                        value_usd=r[14], effort_hours=r[15], eff_rate=r[16], prob=r[17],
                        competition=r[18], strategic=r[19],
                        scores=json.loads(r[20] or "{}"), action=r[21],
                        action_why=r[22], status=r[23])
        # re-derive evidence lines for display
        from .matcher import match
        match(o, prof)
        o.fit_pct, o.action, o.action_why, o.status = r[13], r[21], r[22], r[23]
        out.append(o)
    return out

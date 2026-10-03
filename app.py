#!/usr/bin/env python3
"""Money Radar dashboard: Discover -> Filter -> Research -> Personalize -> Draft -> YOU approve."""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st

from src.config import load_config
from src.dedup import bucket
from src.memory import Memory
from src.run_helpers import current_opps

st.set_page_config(page_title="Money Radar", page_icon="💰", layout="wide")
cfg = load_config()
mem = Memory(cfg.get("memory", {}).get("db_path", "./data/radar.db"))

if "opps" not in st.session_state:
    st.session_state["opps"] = current_opps(cfg, mem)
if "drafts" not in st.session_state:
    st.session_state["drafts"] = {}

# ── Sidebar ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 💰 Money Radar")
    if st.button("▶ Start scan", use_container_width=True):
        from run import scan
        with st.spinner("Scanning sources..."):
            st.session_state["opps"] = scan(cfg)
        st.rerun()
    st.divider()
    st.markdown("**Assisted sources** (no public API — open + paste back)")
    from src.sources import assisted
    for name, url in assisted.search_urls().items():
        st.link_button(f"Search {name.title()}", url)
    with st.expander("➕ Paste a posting"):
        psrc = st.selectbox("Source", ["upwork", "linkedin", "contra", "wellfound", "manual"])
        ptitle = st.text_input("Title")
        pclient = st.text_input("Client")
        ptext = st.text_area("Posting text", height=150)
        pbudget = st.text_input("Budget text (e.g. $3k–$6k)")
        if st.button("Add opportunity"):
            from src.matcher import match
            from src.memory import Memory as M
            from src.money import apply_budget
            from datetime import date
            o = assisted.from_text(psrc, ptitle, ptext, client=pclient, budget_text=pbudget)
            match(o, cfg.get("skills", {}))
            apply_budget(o, cfg.get("rates", {}))
            mem.save(o, date.today().isoformat())
            st.session_state["opps"] = current_opps(cfg, mem)
            st.rerun()
    st.divider()
    st.markdown("**30-day memory**")
    st.write(mem.stats())

opps = st.session_state["opps"]
fresh = [o for o in opps if bucket(o.age_hours) != "stale"]
strong = sum(1 for o in fresh if o.fit_pct >= 70)
applies = sum(1 for o in fresh if o.action == "Apply")

st.markdown("# 💰 MONEY RADAR")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Opportunities scanned", len(opps))
c2.metric("New today (<24h)", sum(1 for o in fresh if o.age_hours <= 24))
c3.metric("Strong matches", strong)
c4.metric("Worth applying", applies)

order = {"Apply": 0, "Consider": 1, "Skip": 2}
fresh.sort(key=lambda o: (order.get(o.action, 3), -o.fit_pct))
EMO = {"Apply": "🔥", "Consider": "🟢", "Skip": "⚪"}

for i, o in enumerate(fresh):
    d = st.session_state["drafts"].setdefault(o.id, {"proposal": "", "sow": "", "context": ""})
    age = f"{o.age_hours:.0f}h ago" if o.age_hours < 72 else f"{o.age_hours/24:.0f}d ago"
    with st.container(border=True):
        st.markdown(f"### {EMO.get(o.action,'⚪')} #{i+1} {o.title}")
        st.caption(f"{o.source} • {age} • {o.client or 'client undisclosed'} • {o.location}")
        m1, m2, m3 = st.columns(3)
        m1.metric("Estimated value", f"${o.value_usd:,.0f}" + (" total" if not o.is_hourly else " (@20h)"))
        m2.metric("Match", f"{o.fit_pct}%")
        m3.metric("Effective rate", f"${o.eff_rate:,.0f}/hr")
        st.markdown(f"**Why you fit:** {o.why_hire}")
        if o.missing:
            st.caption("Missing: " + ", ".join(o.missing))
        bars = "  ".join(f"{k} {'█'*int(round(v/2))}{'░'*(5-int(round(v/2)))} {v}" for k, v in o.scores.items())
        st.code(bars)
        st.markdown(f"**Recommended: {o.action}** — {o.action_why}")
        b1, b2, b3, b4, b5 = st.columns(5)
        if o.url:
            b1.link_button("View Post", o.url)
        if b2.button("🔍 Research client", key=f"r{i}"):
            from src.research import enrich
            with st.spinner("Researching..."):
                d["context"] = enrich(o.client, cfg.get("research", {}).get("tavily_api_key", ""))
            st.rerun()
        if b3.button("✍ Generate Proposal", key=f"p{i}"):
            from src.proposals import generate_proposal
            with st.spinner("Drafting (human tone, resume-grounded)..."):
                text, err = generate_proposal(cfg, o, d["context"])
            if err:
                st.error(err)
            else:
                d["proposal"] = text
                st.rerun()
        if b4.button("📄 Generate SOW", key=f"s{i}"):
            from src.proposals import generate_sow
            with st.spinner("Drafting SOW..."):
                text, err = generate_sow(cfg, o, d["proposal"])
            if err:
                st.error(err)
            else:
                d["sow"] = text
                st.rerun()
        stt = b5.selectbox("Status", ["new", "shortlisted", "pitched", "sent", "won", "lost", "skipped"],
                           index=["new","shortlisted","pitched","sent","won","lost","skipped"].index(o.status) if o.status in ["new","shortlisted","pitched","sent","won","lost","skipped"] else 0,
                           key=f"st{i}")
        if stt != o.status:
            mem.set_status(o.id, stt)
            o.status = stt
        if d["context"]:
            with st.expander("Client research"):
                st.write(d["context"])
        if d["proposal"]:
            d["proposal"] = st.text_area("Proposal (edit, then YOU send it)", value=d["proposal"], height=300, key=f"pv{i}")
            st.caption("Send it yourself — email/Upwork DM. This tool never auto-sends.")
        if d["sow"]:
            d["sow"] = st.text_area("SOW (edit before sharing)", value=d["sow"], height=300, key=f"sow{i}")

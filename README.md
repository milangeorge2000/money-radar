# 💰 Money Radar — Freelance & Money Radar for AI Engineering

Press Start → fresh opportunities ranked by fit and money, with human-sounding
proposals and consultant-grade SOWs. **You approve everything — nothing auto-applies or auto-sends.**

## Quick start

```bash
cd money-radar
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp config.example.yaml config.yaml   # add keys (git-ignored)
./money-radar start                  # scan + dashboard
# or headless:  python3 run.py scan  |  python3 run.py stats
```

## How it works

```
START -> Source Agents -> Parser -> Dedup+Freshness -> Matcher -> Ranker -> SQLite + UI
                                                                    -> Pitch / SOW (you approve)
```

- **Live sources (no key):** RemoteOK + WeWorkRemotely RSS, Hacker News hiring threads, GitHub bounty/freelance issues.
- **Assisted sources (no public API exists):** Upwork / Contra / Wellfound / LinkedIn / Toptal via one-click search URLs + paste-a-posting importer in the sidebar.
- **Freshness:** 24h → 3d → 7d buckets, stale ignored, URL+title dedup.
- **Fit:** evidence-based (`LangGraph — shipped X`, …), missing-skill gaps, fit %, "why hire Milan" paragraph. Full-time salary posts are auto-flagged as non-freelance.
- **Money:** budget parse → value/effort/effective-rate → 5 score bars (money/fit/career/portfolio/effort) → Apply / Consider / Skip with reasons.
- **Memory:** every scan stored in SQLite; sidebar shows 30-day demand, avg budget, top category, top missing skill.
- **LLM:** Gemini primary, OpenRouter backup (keys in git-ignored `config.yaml` or env). Tavily enriches client context. Drafts are editable; sending is always manual.

## Layout

`app.py` (dashboard) · `run.py` (scan/stats CLI) · `src/sources/` · `src/matcher.py` · `src/money.py` · `src/proposals.py` (proposal+SOW) · `src/research.py` (Tavily) · `src/memory.py` · `resume.txt`

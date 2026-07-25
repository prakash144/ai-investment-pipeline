# Demo Script (~5 min walkthrough)

One startup end-to-end: **sourcing → analysis → memo**.

---

## 0. Setup (30s)

> Open terminal. Repo root.

```
code .
ls
```

"Here's the repo — `cli.py` is the single entry point, three independent stages in `sourcing/`, `analysis/`, `memo/`, tests in `tests/`. Let's run it."

---

## 1. Run the pipeline (60s)

```
make run-default
```

> Show the CLI output streaming in — truncated names, scores, memos appearing.

"29 candidates found from HN + YC. Enrichment scrapes YC company pages for founder data. LLM analyzes each one in parallel — 5 workers by default. Takes about 45 seconds cold, 2 seconds cached."

> After it finishes, scroll to the bottom:

```
Report: ...reports/executive-summary.md
Report: ...reports/pipeline-report.md
```

"Two reports generated. Let's open the executive summary."

---

## 2. Executive summary — partner view (45s)

```
open reports/executive-summary.md
```

> Show the rendered markdown (VS Code preview or浏览器).

"This is the partner-facing report. Top of the page: query, date, thesis. Summary table — 4 Take a Meeting, 21 Watch, 4 Pass."

> Scroll down to the ranked table.

"Every company ranked by score with a 📄 memo link. Click opens the full memo."

> Scroll to Next Steps.

"Immediate founder meetings with checkboxes that are linked to their memos. Companies to monitor. A partner can skim this in 30 seconds and know where to spend time."

---

## 3. Open one memo — Bland AI (75, Take a meeting) (90s)

> Click the 📄 link for Bland AI (or open `data/memos/bland-ai.md`).

"One company: Bland AI. Score 75, Take a meeting, Medium confidence."

> Scroll through the memo sections slowly.

- **Executive Summary** — "5 lines: what they do, why they fit the thesis, the call."
- **Investment Recommendation** — "Score breakdown: Team 20, Product 20, Traction 25, Risk 10. You can see exactly why each dimension scored what it did."
- **Company Snapshot** — "Founded 2023, YC W25, team size 12. This comes from enrichment — we scraped the YC company page."
- **Founders** — "Founder info with bios, scraped from the YC page."
- **Traction Signals** — "YC batch + HN activity. Every signal has a source URL."
- **Risks** — "3 specific risks grounded in available data."
- **Change My Mind** — "3 things that would change the call — specific, actionable."

"Every claim in this memo traces back to sourced data. The LLM is instructed never to fabricate — if data is missing it says 'Not available from sourced data.'"

---

## 4. Process visibility — how it was built (45s)

```
open docs/PROCESS.md
```

> Show a few key sections.

"PROCESS.md documents every decision: why HN + YC over Product Hunt, why flat files over a database, what AI drafted vs. what I wrote."

```
open docs/THESIS.md
```

"Thesis is deliberately narrow — AI-agent tooling for SMBs, technical founder, traction in 12-18 months. Not 'good companies.'"

```
head -3 logs/prompts.jsonl | python -m json.tool
```

"Every LLM call is logged — full prompt, response, tokens, cost. You can audit any claim back to the prompt that produced it."

---

## 5. Pipeline report — engineering view (30s)

```
open reports/pipeline-report.md
```

"Engineering-facing report: run ID, exactly 29 candidates found and analyzed, average score 57.2, median 55, highest 75, lowest 45. Output locations and file counts."

---

## 6. Tests & code quality (30s)

```
make test
```

> Show tests passing.

"53 tests covering every module — sourcing, normalization, enrichment, schema, analysis, rendering, CLI. Parallel execution, cache hit/miss, network failures, malformed responses all tested."

---

## 7. Close (15s)

"That's it — one command, 29 memos, two summary reports, full process visibility. The repo and walkthrough are ready for review."

---

## Timing summary

| Section | Time |
|---------|------|
| 0. Setup | 30s |
| 1. Run pipeline | 60s |
| 2. Executive summary | 45s |
| 3. One memo deep-dive | 90s |
| 4. Process visibility | 45s |
| 5. Pipeline report | 30s |
| 6. Tests & code | 30s |
| 7. Close | 15s |
| **Total** | **~5:45** |

Trim by combining sections 5+6 or skipping one if over 5 minutes.

---

## What to show on screen

- **Terminal** for running the pipeline, `make test`
- **VS Code / Markdown preview** for reports and memos
- **Browser** (optional) for rendered markdown

## What to NOT do

- Don't read every memo line — scroll and summarize
- Don't explain every test — just show them passing
- Don't open more than one memo — deep on one is better than shallow on three
- Don't show code except docs and entry points

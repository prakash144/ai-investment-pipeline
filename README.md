# AI-Augmented Investment Pipeline

Automates the first-pass research on early-stage startups: discovers candidates from **Hacker News** + **YC batches**, analyzes them against a stated investment thesis via LLM, and produces a one-page **Pass / Watch / Take a Meeting** memo per startup.

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set your LLM API key (copy and edit)
cp .env.example .env
# Edit .env → set LLM_API_KEY=sk-...

# 3. Run the pipeline
make run-default
# or: PYTHONPATH=. python cli.py --topic "AI agents for SMBs" --limit 15
```

**No API key needed to read existing results** — all output is committed to the repo. You only need a key when analyzing a startup that isn't already cached.

---

## Usage

```bash
python cli.py --topic "<search topic>" [options]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--topic` | `AI agents for SMBs` | Search topic for sourcing |
| `--limit` | `20` | Max candidates per source (HN + YC) |
| `--workers` | `5` | Parallel workers for enrichment & analysis |
| `--no-enrich` | (enrich on) | Skip YC company-page founder scraping |

**Examples:**

```bash
# Full run: 15 candidates, 5 parallel workers
make run

# Quick re-run against cached analysis only (no API calls)
make run

# Sequential (1 worker, for debugging)
python cli.py --topic "AI code generation" --workers 1

# Test with no enrichment (no YC page scraping)
python cli.py --topic "AI agents" --limit 5 --no-enrich
```

---

## What This Pipeline Does

- **Discovers** startups from two free, reliable sources (Hacker News Algolia API + YC batch listing)
- **Deduplicates** companies that appear on both sources
- **Enriches** YC companies with founder names, titles, founding year, batch, and team size by scraping individual YC company pages
- **Scores** each startup (0–100) against a weighted investment thesis using an LLM with structured JSON output
- **Generates** markdown investment memos with executive summary, company snapshot, team/product/market analysis, traction signals, risks, thesis alignment, and a clear call
- **Caches** everything — re-running is instant for already-analyzed candidates
- **Produces** two summary reports:
  - `reports/executive-summary.md` — partner-facing: top opportunities, distribution, next steps
  - `reports/pipeline-report.md` — engineering-facing: run stats, timing, file inventory

---

## What This Pipeline Does NOT Do

| Constraint | Why |
|---|---|
| **Does not recommend actual investments** | It's a first-pass triage tool, not a replacement for due diligence, founder calls, or financial analysis. |
| **Does not scrape behind login walls** | Only uses public, free APIs (HN Algolia) and hardcoded public lists (YC batch). Product Hunt, Crunchbase, and Twitter/X require auth or paid tiers. |
| **Does not use a database or job queue** | The pipeline runs ≤20 candidates per invocation. Flat JSON files on disk keep it simple, replayable, and zero-infrastructure. |
| **Does not support multiple LLM providers** | One model (configurable via `LLM_MODEL`). Cache-based fallback handles missing keys instead of multi-provider abstraction. |
| **Does not guarantee accurate founder data** | YC company pages are scraped from public HTML; structure may change. Falls back gracefully to "not available." |
| **Does not run on its own schedule** | Manual CLI invocation only. No daemon, cron, or CI scheduler included. |

---

## How It Works

Three independent stages, connected by flat JSON files:

```
SOURCING                  ANALYSIS                  RECOMMENDATION
┌─────────────┐          ┌──────────────┐           ┌──────────────┐
│ HN Algolia  │          │  LLM call    │           │  Jinja2      │
│ YC batch    ├─JSON────►│  + cache     ├─JSON─────►│  template    ├─MD──► memos/
│ normalize/  │          │  + prompt    │           │  render      │
│ dedupe      │          │  log         │           │              │
│ enrichment  │          │              │           │              │
└─────────────┘          └──────────────┘           └──────────────┘
                               │
                         reports/
                         executive-summary.md
                         pipeline-report.md
```

Each stage is independently re-runnable: re-render memos without re-analyzing, or re-analyze without re-scraping. See [`docs/architecture.md`](docs/architecture.md) for the full data-flow diagram.

---

## Output

After a run, three deliverables exist:

| Location | Format | Audience |
|----------|--------|----------|
| `reports/executive-summary.md` | Markdown | **VC Partner** — top opportunities, distribution, next steps with memo links |
| `reports/pipeline-report.md` | Markdown | **Engineering** — run stats, timing, file inventory |
| `data/memos/*.md` | Markdown | One per startup, linked from executive summary |

Each memo contains: Executive Summary → Investment Recommendation (call + confidence + score breakdown) → Company Snapshot (founded, batch, team size) → Product → Team → Market → Traction Signals → Risks → Thesis Alignment → Change My Mind → Sources.

---

## Configuration

All configuration is via environment variables (or `.env` file):

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LLM_API_KEY` | Yes* | — | OpenAI or OpenRouter API key |
| `LLM_API_BASE` | No | `https://api.openai.com/v1` | API base URL override |
| `LLM_MODEL` | No | `gpt-4o-mini` | Model name |

\* Only required when analyzing a startup not already cached in `data/analysis/`.

Copy `.env.example` → `.env` to get started.

---

## Project Structure

```
├── cli.py                    # Main entry point
├── config.py                 # Shared config: slugify, API key, env vars
├── Makefile                  # make test / make run / make clean
├── requirements.txt
├── .env.example
│
├── analysis/
│   ├── schema.py             # Pydantic model (Analysis, score, recommendation)
│   └── analyze.py            # LLM call, prompt building, caching, log
│
├── memo/
│   ├── template.md           # Jinja2 memo template
│   └── render.py             # Template renderer
│
├── sourcing/
│   ├── hn_source.py          # Hacker News Algolia API
│   ├── yc_source.py          # YC W25 company list
│   ├── normalize.py          # Dedup, merge, enrichment orchestration
│   └── enrichment.py         # YC company page scraping
│
├── reports/                  # Generated summary reports
│   ├── executive-summary.md
│   └── pipeline-report.md
│
├── data/                     # Committed pipeline outputs
│   ├── candidates/           # Raw sourced startup data
│   ├── analysis/             # LLM analysis results
│   ├── enrichment/           # YC page scrape cache
│   └── memos/                # Final investment memos
│
├── docs/
│   ├── architecture.md       # HLD, data flow, design rationale
│   ├── THESIS.md             # Investment thesis + scoring rubric
│   ├── PROCESS.md            # Decision log (what/why, AI vs. manual)
│   ├── PROBLEM-UNDERSTANDING.md
│   └── specs/                # Design spec + implementation plan
│
├── tests/                    # Test suite (53 tests, one file per module)
│   ├── test_hn_source.py
│   ├── test_yc_source.py
│   ├── test_normalize.py
│   ├── test_enrichment.py
│   ├── test_schema.py
│   ├── test_analyze.py
│   ├── test_render.py
│   ├── test_config.py
│   └── test_cli.py
│
└── logs/
    └── prompts.jsonl         # Every LLM call logged (prompt, response, tokens, cost)
```

---

## Testing

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run a single test file
PYTHONPATH=. pytest tests/test_enrichment.py -v
```

The test suite covers:
- Sourcing: HN API params, limit enforcement, missing fields, empty responses
- YC: field presence, optional website, unknown batch
- Normalize: dedup merge, missing founders, empty inputs, required keys
- Enrichment: cache hit/miss, network failure, HTML parsing, metadata extraction
- Schema: score range, recommendation enum, confidence enum, round-trip
- Analysis: prompt content, cache hit/miss, API key handling, malformed LLM response
- Render: all sections present, missing founders, sources, length bounds, extra data
- CLI: file creation, API key error recovery

---

## Documentation Index

| Document | Audience | What it covers |
|----------|----------|----------------|
| [`docs/architecture.md`](docs/architecture.md) | Engineering | HLD, data-flow diagram, design rationale, running without API key |
| [`docs/THESIS.md`](docs/THESIS.md) | VC Partner | Investment thesis definition, scoring rubric, recommendation mapping |
| [`docs/PROCESS.md`](docs/PROCESS.md) | Reviewer | Decision log: how the pipeline was built, where AI helped, what was rejected |
| [`docs/PROBLEM-UNDERSTANDING.md`](docs/PROBLEM-UNDERSTANDING.md) | Reviewer | Deep analysis of the take-home requirements, grading rubric, anti-patterns |
| [`docs/specs/investment-pipeline-design.md`](docs/specs/investment-pipeline-design.md) | Engineering | Approved design spec — the "what" before code |
| [`docs/specs/investment-pipeline-plan.md`](docs/specs/investment-pipeline-plan.md) | Engineering | Task-by-task implementation plan — the "how" |

---

## Latency

A full run against 29 candidates takes approximately:

| Phase | Serial | Parallel (5 workers) |
|-------|--------|----------------------|
| YC enrichment (scraping) | ~5s | ~1s |
| LLM analysis (29 calls) | ~45s | ~10s |
| Total | ~50s | ~11s |

Cached runs (re-running with existing analysis) complete in <1s.

Use `--workers N` to control parallelism. Set `--workers 1` for deterministic sequential execution.

---

## Requirements

- Python 3.10+
- An LLM API key (OpenAI, OpenRouter, or compatible)
- Internet access for sourcing and enrichment

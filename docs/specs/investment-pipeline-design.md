# Design Spec: AI-Augmented Investment Pipeline

Date: 2026-07-25
Status: Approved, ready for implementation plan

## Problem

Partners manually scan Product Hunt/YC/HN/Twitter/Crunchbase (~10 hrs/week) to
find promising startups, then hand-write memos. Build a pipeline that
automates the triage layer: source candidates, analyze them against a stated
thesis, produce a Pass/Watch/Meet memo per candidate.

Graded roughly equally on the output itself and on the visible trail of how
it was built and worked with AI.

## Scope

- Sourcing: Hacker News (Algolia API) + YC batch page. Two sources, chosen
  for reliability (no auth, no paid API) over breadth.
- Analysis: structured (Pydantic) output — Team / Product / Market / Risks /
  Score(0-100) — against one specific thesis, not general "company quality."
- Recommendation: one memo per candidate, template-driven, ending in
  Pass / Watch / Take a meeting, with 2-3 things that would change the call.
- Out of scope (explicitly): job queue, vector DB, frontend, multi-LLM-
  provider abstraction. See [PROCESS.md](../PROCESS.md) for why each was
  rejected.

## Architecture

Three stages connected only by flat JSON files on disk — no queue, no
database, no server. See [architecture.md](../architecture.md) for the full
diagram and data-flow table. Each stage is independently re-runnable.

```
sourcing/ hn_source.py, yc_source.py, normalize.py
analysis/ schema.py (Pydantic models), analyze.py (LLM call)
memo/ render.py, template.md
data/ candidates/ analysis/ memos/ <- committed
logs/ prompts.jsonl <- committed
cli.py entrypoint
tests/
```

## Thesis and scoring

See [THESIS.md](../THESIS.md). Summary: seed/pre-seed AI-agent tooling for
SMBs, technical founder required, traction in the last 12-18 months.
Weighted score: Team 30 / SMB fit 25 / Traction 25 / inverse-Risk 20.

## Memo contents (per candidate)

Fixed sections, in this order: Company snapshot, Team, Product, Market,
Risks, Score + rationale, Call (Pass/Watch/Meet), 2-3 things that would
change the call, Sources. Every factual claim carries a source reference
back to Stage 1/2 data — no unsourced claims in a memo.

## Robustness requirements

- A candidate with missing founder info, no traction signal, or a failed
  scrape must still produce a memo — with those gaps stated explicitly
  ("no traction signal found"), not fabricated or silently dropped.
- Sourcing dedupes by normalized name/domain before analysis runs.

## Running without an LLM API key

- Sourcing never needs a key (plain HTTP calls).
- Analysis checks for a cached `data/analysis/<slug>.json` before calling
  the LLM; a cache hit skips the API call entirely, so re-running against
  the committed dataset needs no key.
- A cache miss with no key set fails with a clear message, not a stack
  trace or a silent fallback to a second provider.

## Process visibility plan (40% of grade)

- `docs/PROCESS.md` — decision log in the author's own words: key decisions,
  rejected alternatives, where AI drafted vs. reviewed code, what changed
  mid-build. Not AI-ghostwritten.
- `logs/prompts.jsonl` — every pipeline LLM call logged (prompt, response,
  model, tokens, estimated cost) — doubles as claim traceability and
  cost/token tracking.
- Git history: small, honest commits as the build progresses, not one
  squashed commit at the end.
- `docs/specs/` — this file — captures the design before code, so intent is
  checkable independent of the implementation.

## Build order

1. Repo scaffold + THESIS.md + architecture.md (done)
2. This spec (done)
3. HN Algolia sourcing, then YC batch page sourcing; normalize/dedupe →
   commit raw candidates JSON
4. Pydantic schema + thesis-driven prompt + LLM call → commit analysis JSON,
   with prompt logging and the cache-check described above
5. Memo renderer (template.md) → commit markdown memos
6. CLI entrypoint tying stages together
7. Tests: normalization, schema validation, memo rendering with
   missing/partial data
8. Fill remaining `docs/PROCESS.md` sections as built
9. Loom walkthrough of one candidate end-to-end

## Working style

Author writes each module from a short spec; AI reviews for bugs/style and
explains LLM-specific patterns (structured output, handling malformed API
responses, caching). Attribution per module tracked in PROCESS.md as it
happens.

## Open items for implementation plan

- Exact HN Algolia query params and YC batch page selector — decide during
  step 3, since YC's page structure may require inspection first.
- Exact Pydantic schema fields for Analysis — decide during step 4 against
  the thesis rubric above.
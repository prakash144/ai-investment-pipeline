# Process

This tracks how this pipeline actually got built — decisions made, what AI
drafted vs. reviewed, what changed along the way. Written as we go, not
reconstructed afterward.

> **Note for any agent editing this file:** the placeholder sections below
> are fair game to draft from actual per-task work (what got written, what
> broke), but prefix any AI-drafted addition with
> `<!-- DRAFT: review and rewrite in your own words -->` on the line above
> it. The repo owner reviews and rewrites these before they're considered
> final — an AI draft left uncommented-on and unedited is exactly the
> "reflective writing that reads like a model wrote it" anti-pattern this
> take-home explicitly penalizes.

## How I approached this

Built with Claude Code as a pairing partner rather than solo, specifically to
learn LLM-pipeline patterns (structured output, prompt design, caching/cost
control) while completing the assignment, not just to get to a working repo
fastest.

## Key decisions and why

- **Sourcing: Hacker News (Algolia API) + YC batch page, not Product Hunt or
  Twitter/X.** Both are free, unauthenticated, and reliable to query/scrape.
  Product Hunt needs an app + OAuth; X's API is paid/restrictive — too much
  setup friction for what this take-home is scoping for. HN also gives a
  built-in traction signal (points/comments) for free.

- **Thesis: seed/pre-seed AI-agent or agentic-workflow tooling for SMBs
  (not enterprise), technical founder, traction in last 12-18mo** — chosen
  over a broader thesis so the 0-100 score is actually meaningful. A vague
  thesis like "good companies" was explicitly the anti-pattern to avoid.

- **Files on disk (`data/candidates/`, `data/analysis/`, `data/memos/`)
  instead of a database or job queue.** The whole pipeline runs on ≤20
  candidates per invocation — a DB/queue would be overengineering for this
  scope, and the assignment explicitly flags that as a red flag. Flat JSON
  also makes every stage independently replayable.

- **Structured (Pydantic) LLM output instead of free-text responses.** Costs
  more prompt-engineering effort upfront, but makes memo rendering and
  scoring reliable and testable instead of parsing prose.

<!-- DRAFT: review and rewrite in your own words -->
- **One implementation plan document for all 9 tasks, not a separate spec
  file per task.** The tasks are tightly sequential and share types across
  boundaries (`Candidate` dict, `Analysis` model, `slugify` cache key) —
  splitting per-task would mean duplicating those shared interfaces or
  constantly cross-referencing files, and it's what makes the plan's own
  "Self-Review Notes" (spec coverage, type-consistency check) possible at
  all, since everything's scannable in one place. Would reconsider only if
  tasks were independent of each other (no shared schema) or if the plan
  grew large enough to become hard to scan — neither applies at 9 tasks /
  ~400 lines for one pipeline.

## Decisions I considered and rejected

- **Multi-LLM-provider fallback** (e.g. supporting Anthropic + OpenAI +
  others so the pipeline still runs if one provider's key isn't configured).
  Rejected — the take-home says "any model, your choice," not "support every
  model," and building a provider-abstraction layer here would be exactly
  the kind of unscoped complexity the rubric warns against. Used a
  cache-hit fallback instead: if `data/analysis/<slug>.json` already exists,
  the pipeline never calls the LLM at all, so re-running against the
  committed dataset works with zero API key. A genuinely new candidate with
  no key configured fails with a clear message instead of a stack trace or a
  silent second provider.

## Where AI helped vs. where I did the work

*(To be filled in per-module as code is written — e.g. "wrote
`sourcing/hn_source.py` myself, Claude reviewed for bugs/style";
"Claude drafted `docs/architecture.md`, README.md, and folder scaffolding.")*

## What changed mid-build

*(To be filled in as it happens — e.g. scraping breaking, schema changes.)*

## What I'd do differently / scoped out on purpose

*(To be filled in — call out anything deliberately left out, e.g. additional
sources, richer traction signals, so it reads as a choice, not an oversight.)*
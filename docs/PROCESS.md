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

Built with OpenCode and an open-source LLM (DeepSeek V4 Flash Free) as a pairing partner rather 
than solo, specifically to learn LLM-pipeline patterns (structured output, prompt 
design, caching/cost control) while completing the assignment, not just to get to 
a working repo fastest.

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

- **`config.py`, `requirements.txt`, `.gitignore`**: implemented by me. AI suggested the unicode normalization fix after the first test failed on accented characters.
- **`sourcing/hn_source.py`**: implemented by me. AI reviewed the mock setup in tests to verify the `story_url` fallback.
- **`sourcing/yc_source.py`**: wrote the test spec myself; the YC batch page turned out to be a JS-rendered React SPA, so I used a hardcoded list of ~15 real YC W25 companies (the spec explicitly allows this). AI helped format the list.
- **`sourcing/normalize.py`**: implemented by me. AI caught that the dedup merge order was wrong (was overwriting YC data with HN data instead of the reverse).
- **`analysis/schema.py`**: implemented by me — straightforward Pydantic model.
- **`analysis/analyze.py`**: AI drafted the system prompt and cost-estimate helper; I wrote the caching/logging logic and the prompt builder.
- **`memo/template.md` and `render.py`**: implemented by me — simple Jinja2 template.
- **`cli.py`**: implemented by me; AI helped debug the mock signatures in tests.
- **`.env` support**: I added it after the initial run failed due to API key not being found — the pipeline originally only checked `os.environ`, not `.env` files.
- **All tests**: I wrote the test cases; AI verified they covered the spec's criteria.

## What changed mid-build

- **YC sourcing**: The YC batch page is a JS-rendered React app, not server-side HTML. No amount of BeautifulSoup parsing would work. I switched to a hardcoded list of 15 real YC W25 companies, which the spec explicitly calls out as a legitimate fallback.
- **OpenRouter integration**: Used OpenRouter with `gpt-4o-mini` instead of direct OpenAI because it supports multiple providers through one key. Had to switch from `gpt-4o` to `gpt-4o-mini` after hitting credit limits on the larger model.
- **`.env` loading**: Added after the first pipeline run failed to find `LLM_API_KEY` — the key was in a `.env` file but `config.py` only checked `os.environ`. Added a simple `.env` parser (no `python-dotenv` dependency) as a fallback.
- **`max_tokens` limit**: OpenRouter's default `max_tokens` exceeds the free tier; added an explicit `max_tokens=2000` to the LLM call.
- **Parallel enrichment + analysis**: After audit, the serial loop over 29 candidates took ~50s. Added `ThreadPoolExecutor` to both enrichment (in `normalize.py`) and analysis (in `cli.py`), controlled by `--workers` (default 5). Thread-safe log writing via `threading.Lock` in `analyze.py`. Full run now ~11s.
- **YC enrichment tests (+17)**: Enrichment was the only module with zero test coverage. Added `tests/test_enrichment.py` covering cache hit/miss, network failure, non-200 responses, HTML parsing, metadata extraction, founder title cleaning, and slugify.
- **`__init__.py` files**: Added to all packages so Python treats them as proper packages, enabling cleaner imports and tooling support.

## What I'd do differently / scoped out on purpose

- **YC company page enrichment**: Initially scoped out because individual page scraping seemed too complex for the take-home scope. Later added it (along with caching) to fix the all-Pass bug — without founder info the LLM scores Team at zero regardless of company quality. The scraping approach is robust: BeautifulSoup on server-rendered HTML with regex extraction, ~0.3s per page with parallel workers.
- **Product Hunt sourcing**: PH has an API but requires OAuth setup. Given the take-home's scope guidance ("pick one or two sources"), HN + YC is the right depth-vs-breadth call.
- **Product Hunt sourcing**: PH has an API but requires OAuth setup. Given the take-home's scope guidance ("pick one or two sources"), HN + YC is the right depth-vs-breadth call.
- **Better traction signals**: For YC companies, batch alone is a weak traction signal. A future improvement would cross-reference each YC company against HN/Product Hunt to find launches or discussions.
- **Multi-model support**: The pipeline hardcodes one model (configurable via `LLM_MODEL`). Supporting multiple providers in parallel was rejected as overengineering for a 20-candidate pipeline.
- **Synthetic fallback analysis**: If no LLM API key is available, the pipeline gracefully skips analysis rather than generating fake data. This is intentional — the committed `data/analysis/` already contains real results.
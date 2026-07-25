# Investment Pipeline Implementation Plan

> **Format note:** By explicit choice, this plan is spec-only, not fully-coded.
> Each task defines file paths, function interfaces, and what each test must
> verify in plain language — the author writes the actual implementation and
> test code themselves, then it's reviewed. This deviates from the standard
> writing-plans format (which pre-writes all code) on purpose, to support the
> stated learning goal.
>
> **Portability note:** This plan is designed to be handed to any coding
> agent (OpenCode, or otherwise) and executed task-by-task
> independently of which tool wrote it — see the Git Workflow section below
> for the exact repo/commit/push discipline every task must follow, and
> `docs/PROCESS.md` for how per-task AI-drafted process notes get reviewed.

**Goal:** Build the sourcing → analysis → memo pipeline described in
`docs/specs/investment-pipeline-design.md`.

**Architecture:** Three CLI-orchestrated stages connected by flat JSON files
in `data/`. No queue, no database. See `docs/architecture.md`.

**Tech Stack:** Python 3.11+, `requests` (HTTP), `beautifulsoup4` (YC page
scrape), `pydantic` (structured LLM output), `jinja2` (memo template),
`pytest`. LLM client library depends on the provider chosen for
`LLM_API_KEY` (decide at Task 5).

## Global Constraints

- All committed outputs live under `data/candidates/`, `data/analysis/`,
  `data/memos/` — reviewer must be able to read results with zero API key.
- Every LLM call must be logged to `logs/prompts.jsonl` (prompt, response,
  model, tokens, estimated cost).
- Analysis stage must check for a cached `data/analysis/<slug>.json` before
  calling the LLM; only call the LLM on a cache miss.
- No candidate may be silently dropped for missing data — gaps are stated
  explicitly in the memo, not fabricated.
- Every claim in a memo must trace back to sourced data (a URL or a field
  from Stage 1/2 output).
- No multi-LLM-provider abstraction; one provider, cache-based fallback only.
- Every task ends with the Git Workflow below — no task is "done" until its
  commit exists on `main` (and is pushed, once a remote is configured).

## Git Workflow (applies before Task 1, and at the end of every task)

**Before Task 1 (one-time, idempotent):**
1. Check whether this is already a git repo: `git rev-parse --is-inside-work-tree`.
2. If it isn't, run `git init`. (Already done for this repo — `main` branch,
   history starts at the docs/scaffolding commit.)
3. Check for a remote: `git remote -v`. The remote is added manually by the
   repo owner (not by the agent) — if none exists yet, later steps 4-5 below
   are skipped with a printed note (`"no origin remote configured, skipping
 pull/push"`), not treated as a failure.

**At the end of every task, in this order:**
1. `git remote -v` — if `origin` exists, continue to step 2; if not, skip to
   step 4 and print `"no origin remote configured — commit made locally
 only, push once origin is added"`.
2. `git pull --rebase origin main` — pick up any changes made elsewhere
   (e.g. by the repo owner) before adding this task's commit on top.
3. Resolve any conflicts before proceeding (stop and surface to the user —
   do not force-resolve silently).
4. `git add <exact files listed under that task's **Files** section>` —
   never `git add -A`/`git add .`, to avoid sweeping up unrelated in-progress
   files.
5. `git commit -m "<type>: <short description>"` using the message given in
   that task's own Commit step (conventional-commit style: `feat`/`test`/
   `docs`/`chore`/`data`, matching the style already used in this repo's
   history).
6. If `origin` exists (from step 1): `git push origin main`.
7. If this task touched `docs/PROCESS.md` sections that are meant to be
   filled in the author's own words (see Task 9 and the note below), leave
   those sections as an AI-drafted note prefixed `<!-- DRAFT: review and
 rewrite in your own words -->` rather than committing them as final prose
   — the repo owner reviews/edits before it's considered done, so drafting
   is fine but silently finalizing someone else's reflection is not.

---

### Task 1: Project setup (deps, config, cache-key helper)

**Files:**
- Create: `requirements.txt`
- Create: `config.py`
- Create: `.gitignore`
- Test: `tests/test_config.py`

**Interfaces:**
- Produces: `config.slugify(name: str) -> str` — normalizes a startup name
  into a filesystem-safe, stable key (lowercase, spaces/punctuation to
  hyphens) used as the shared cache key across sourcing/analysis/memo
  stages.
- Produces: `config.get_llm_api_key() -> str | None` — reads `LLM_API_KEY`
  from environment, returns `None` if unset (never raises).

**Test must verify:**
- `slugify` is stable and collision-resistant for realistic inputs: `"Acme
 Inc."` and `"acme inc"` produce the same slug; `"Acme"` and `"Acme Co"`
  produce different slugs.
- `slugify` handles empty string and unicode without raising.
- `get_llm_api_key` returns `None` when env var unset, returns the value
  when set (use `monkeypatch` to set/unset in the test).

- [x] Write the failing tests in `tests/test_config.py` per the criteria above
- [x] Run: `pytest tests/test_config.py -v` — expect FAIL (module doesn't exist)
- [x] Implement `config.py` with `slugify` and `get_llm_api_key`
- [x] Add `requirements.txt` (requests, beautifulsoup4, pydantic, jinja2,
  pytest, plus whatever LLM client library Task 5 needs)
- [x] Add `.gitignore` (`.env`, `__pycache__/`, `*.pyc`, venv dirs) — do
  **not** ignore `data/` or `logs/`, those are committed outputs
- [x] Run: `pytest tests/test_config.py -v` — expect PASS
- [x] Run the Git Workflow above: `git pull --rebase origin main` (if origin exists), then `git add requirements.txt config.py .gitignore tests/test_config.py && git commit -m "chore: project setup, config helpers"`, then `git push origin main` (if origin exists)

---

### Task 2: HN sourcing

**Files:**
- Create: `sourcing/hn_source.py`
- Test: `tests/test_hn_source.py`

**Interfaces:**
- Consumes: nothing from other modules (talks directly to the HN Algolia
  API: `https://hn.algolia.com/api/v1/search`).
- Produces: `fetch_hn_candidates(query: str, limit: int = 20) -> list[dict]`.
  Each dict: `{title: str, url: str | None, points: int, num_comments: int,
 created_at: str, objectID: str, source: "hn"}`.

**Test must verify:**
- Mocks the HTTP call (don't hit the real API in tests) — verify the
  function builds the correct request params from `query`/`limit`.
- Returns a list no longer than `limit`.
- Given a mocked response missing optional fields (e.g. no `url`), returns
  dicts with `url: None` instead of raising `KeyError`.
- Given a mocked empty-hits response, returns `[]` without raising.

- [x] Write failing tests per criteria above (mock `requests.get`)
- [x] Run: `pytest tests/test_hn_source.py -v` — expect FAIL
- [x] Implement `fetch_hn_candidates`
- [x] Run: `pytest tests/test_hn_source.py -v` — expect PASS
- [x] Run the Git Workflow above: `git pull --rebase origin main` (if origin exists), then `git add sourcing/hn_source.py tests/test_hn_source.py && git commit -m "feat: HN Algolia sourcing"`, then `git push origin main` (if origin exists)

---

### Task 3: YC sourcing

**Files:**
- Create: `sourcing/yc_source.py`
- Create: `tests/fixtures/yc_batch_sample.html` (hand-saved HTML fixture)
- Test: `tests/test_yc_source.py`

**Interfaces:**
- Consumes: nothing from other modules (scrapes YC's public batch page).
- Produces: `fetch_yc_candidates(batch: str = "W25", limit: int = 20) ->
 list[dict]`. Each dict: `{name: str, website: str | None, description:
 str, batch: str, source: "yc"}`.

**Test must verify:**
- Mocks the HTTP response with a small saved HTML fixture (save one under
  `tests/fixtures/yc_batch_sample.html` — grab it from the real page once,
  by hand, and commit it) — verify parsing extracts name/website/description
  correctly from that fixture.
- Given a fixture with one entry missing a website link, returns `website:
 None` for that entry instead of raising.
- Returns no more than `limit` entries.
- **If live scraping proves brittle during implementation** (YC's page is
  JS-rendered or structure differs from the fixture), fall back to a
  hardcoded list of 10-15 real YC W25 companies (name/website/description
  filled in by hand) returned by this same function signature — note this
  fallback explicitly in `docs/PROCESS.md` if used, it's a legitimate
  scoping call, not a shortcut to hide.

- [x] Manually fetch the YC batch page once, save the relevant HTML section as `tests/fixtures/yc_batch_sample.html`
- [x] Write failing tests against that fixture per criteria above
- [x] Run: `pytest tests/test_yc_source.py -v` — expect FAIL
- [x] Implement `fetch_yc_candidates` (BeautifulSoup parse, or hardcoded fallback list — decide based on what the real page looks like)
- [x] Run: `pytest tests/test_yc_source.py -v` — expect PASS
- [x] Run the Git Workflow above: `git pull --rebase origin main` (if origin exists), then `git add sourcing/yc_source.py tests/test_yc_source.py tests/fixtures/yc_batch_sample.html && git commit -m "feat: YC batch page sourcing"`, then `git push origin main` (if origin exists)

---

### Task 4: Normalize & dedupe

**Files:**
- Create: `sourcing/normalize.py`
- Test: `tests/test_normalize.py`

**Interfaces:**
- Consumes: the list-of-dicts shapes from Task 2 (`hn_source`) and Task 3
  (`yc_source`).
- Produces: `normalize_candidates(hn_raw: list[dict], yc_raw: list[dict]) ->
 list[dict]`. Output "Candidate" shape (this is the shared contract every
  later stage relies on):
 ```
 {
 "slug": str, # from config.slugify(name)
 "name": str,
 "website": str | None,
 "description": str,
 "founders": str | None, # None if not findable from source data
 "traction_signal": {"type": str, "detail": str, "source_url": str} | None,
 "source": "hn" | "yc",
 "source_url": str, # link back to the original HN/YC listing
 }
 ```
- Produces: `slugify` is reused from `config.py` (Task 1) — do not
  redefine it here.

**Test must verify:**
- Given one HN item and one YC item with the same underlying company name
  (different casing/punctuation), dedupe merges them into a single
  Candidate (prefer YC's `description`/`website` if both present, keep HN's
  data as the `traction_signal`).
- Given an HN item with no discoverable founder info, output has
  `founders: None`, not a fabricated string.
- Output list length is `<=` the combined input length (dedup never
  increases count).
- Every output dict has all required keys, even when input data is sparse.

- [x] Write failing tests per criteria above
- [x] Run: `pytest tests/test_normalize.py -v` — expect FAIL
- [x] Implement `normalize_candidates`
- [x] Run: `pytest tests/test_normalize.py -v` — expect PASS
- [x] Run the Git Workflow above: `git pull --rebase origin main` (if origin exists), then `git add sourcing/normalize.py tests/test_normalize.py && git commit -m "feat: candidate normalization and dedup"`, then `git push origin main` (if origin exists)

---

### Task 5: Analysis schema

**Files:**
- Create: `analysis/schema.py`
- Test: `tests/test_schema.py`

**Interfaces:**
- Consumes: nothing (pure data model).
- Produces: Pydantic model `Analysis` with fields:
- `team: str`
- `product: str`
- `market: str`
- `risks: list[str]`
- `score: int` (validated 0-100)
- `score_breakdown: dict[str, int]` — keys `team`, `product_fit`,
  `traction`, `risk`, matching the weights in `docs/THESIS.md` (30/25/25/20)
- `recommendation: Literal["Pass", "Watch", "Take a meeting"]`
- `change_my_mind: list[str]` (2-3 items)
- `sources: list[str]` (URLs referenced in team/product/market/risks)

**Test must verify:**
- A dict with a `score` of 150 or -10 fails validation (raises
  `pydantic.ValidationError`).
- A `recommendation` value outside the three allowed strings fails
  validation.
- `score_breakdown` values summing to something other than `score` is
  **not** enforced as an error here — note in a comment why (LLM-estimated
  sub-scores won't always sum exactly; that's fine, `score` is the
  authoritative field).
- A fully-populated valid dict constructs successfully and round-trips
  through `.model_dump()`.

- [x] Write failing tests per criteria above
- [x] Run: `pytest tests/test_schema.py -v` — expect FAIL
- [x] Implement the `Analysis` Pydantic model
- [x] Run: `pytest tests/test_schema.py -v` — expect PASS
- [x] Run the Git Workflow above: `git pull --rebase origin main` (if origin exists), then `git add analysis/schema.py tests/test_schema.py && git commit -m "feat: Analysis output schema"`, then `git push origin main` (if origin exists)

---

### Task 6: LLM analysis call, caching, prompt logging

**Files:**
- Create: `analysis/analyze.py`
- Test: `tests/test_analyze.py`

**Interfaces:**
- Consumes: `Candidate` dicts from Task 4, `Analysis` model from Task 5,
  `config.slugify` / `config.get_llm_api_key` from Task 1, thesis text read
  from `docs/THESIS.md`.
- Produces:
- `build_prompt(candidate: dict, thesis: str) -> str` — must explicitly
  state which candidate fields are missing (e.g. "No founder information
  was found for this company") rather than omitting them silently, so the
  LLM doesn't fabricate detail for gaps.
- `class NoApiKeyError(Exception)` — raised when there's a cache miss and
  no `LLM_API_KEY` is set.
- `log_prompt_call(candidate_slug: str, prompt: str, response: str,
 model: str, input_tokens: int, output_tokens: int, cost_usd: float) ->
 None` — appends one JSON line to `logs/prompts.jsonl`.
- `get_or_analyze(candidate: dict, thesis: str, cache_dir: Path =
 Path("data/analysis")) -> Analysis`:
1. If `cache_dir / f"{candidate['slug']}.json"` exists, load and
   return it (no LLM call, no log entry).
2. Else, if no API key, raise `NoApiKeyError` with a message naming the
   candidate.
3. Else, call the LLM with `build_prompt(...)`, parse into `Analysis`,
   write it to the cache path, call `log_prompt_call(...)`, return it.

**Test must verify:**
- `build_prompt` output contains the thesis text and an explicit
  "no founder information" style phrase when `candidate["founders"] is None`.
- `get_or_analyze` returns cached data and makes **zero** LLM calls when
  the cache file exists (mock the LLM client, assert it was never called).
- `get_or_analyze` raises `NoApiKeyError` on a cache miss with no key set
  (monkeypatch `get_llm_api_key` to return `None`).
- `get_or_analyze` on a cache miss with a key set: calls the mocked LLM
  client once, writes the cache file, and appends exactly one line to a
  temp `logs/prompts.jsonl`.
- A malformed/unparseable mocked LLM response results in a clear raised
  error, not a silent bad `Analysis` object.

- [x] Write failing tests per criteria above, mocking the LLM client entirely (no real API calls in tests)
- [x] Run: `pytest tests/test_analyze.py -v` — expect FAIL
- [x] Implement `build_prompt`, `NoApiKeyError`, `log_prompt_call`, `get_or_analyze` — pick and wire in the actual LLM client library here (this is where the model/provider choice from Task setup gets used)
- [x] Run: `pytest tests/test_analyze.py -v` — expect PASS
- [x] Run the Git Workflow above: `git pull --rebase origin main` (if origin exists), then `git add analysis/analyze.py tests/test_analyze.py requirements.txt && git commit -m "feat: LLM analysis with caching and prompt logging"`, then `git push origin main` (if origin exists)

---

### Task 7: Memo rendering

**Files:**
- Create: `memo/template.md`
- Create: `memo/render.py`
- Test: `tests/test_render.py`

**Interfaces:**
- Consumes: a `Candidate` dict (Task 4 shape) and an `Analysis` object
  (Task 5 model).
- Produces: `render_memo(candidate: dict, analysis: Analysis) -> str` —
  fills `memo/template.md` (Jinja2) and returns the rendered markdown.

**Test must verify:**
- Rendered output contains the candidate name, the recommendation string,
  and all of team/product/market/risks/score/change_my_mind content.
- Given `candidate["founders"] is None`, rendered output states team info
  is unavailable rather than rendering `"None"` literally or an empty gap.
- Output includes a "Sources" section listing every URL from
  `analysis.sources` plus `candidate["source_url"]`.
- Rendered markdown is non-empty and under some sane length bound (e.g.
  < 500 words) — catches a runaway/duplicated template bug.

- [x] Write failing tests per criteria above (construct an `Analysis` instance directly in the test, don't call the LLM)
- [x] Run: `pytest tests/test_render.py -v` — expect FAIL
- [x] Write `memo/template.md` with the fixed section order from the spec (Company snapshot, Team, Product, Market, Risks, Score + rationale, Call, Change my mind, Sources)
- [x] Implement `render_memo`
- [x] Run: `pytest tests/test_render.py -v` — expect PASS
- [x] Run the Git Workflow above: `git pull --rebase origin main` (if origin exists), then `git add memo/template.md memo/render.py tests/test_render.py && git commit -m "feat: memo rendering"`, then `git push origin main` (if origin exists)

---

### Task 8: CLI entrypoint

**Files:**
- Create: `cli.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: `fetch_hn_candidates`, `fetch_yc_candidates`,
  `normalize_candidates`, `get_or_analyze`, `render_memo` from all prior
  tasks.
- Produces: a `main(topic: str, limit: int = 20)` function and a
  `if __name__ == "__main__":` argparse wrapper exposing `--topic` and
  `--limit`, runnable as `python cli.py --topic "AI agents for SMBs"`.
  For each candidate: writes `data/candidates/<slug>.json`,
  `data/analysis/<slug>.json` (via `get_or_analyze`, which already writes
  this — `main` just calls it), and `data/memos/<slug>.md`.
- On a `NoApiKeyError` for a given candidate, `main` must catch it, print a
  clear message naming the candidate, and continue to the next candidate
  rather than crashing the whole run.

**Test must verify:**
- Given mocked sourcing functions returning 2 fixture candidates, and a
  mocked `get_or_analyze` returning a fixed `Analysis`, `main` writes 2
  files under each of `data/candidates/`, `data/analysis/`, `data/memos/`
  (use a temp directory, not the real `data/`).
- If one candidate's `get_or_analyze` raises `NoApiKeyError`, the other
  candidate's memo still gets written (run doesn't abort).

- [x] Write failing tests per criteria above, mocking every prior-task function
- [x] Run: `pytest tests/test_cli.py -v` — expect FAIL
- [x] Implement `cli.py`
- [x] Run: `pytest tests/test_cli.py -v` — expect PASS
- [x] Run the Git Workflow above: `git pull --rebase origin main` (if origin exists), then `git add cli.py tests/test_cli.py && git commit -m "feat: CLI entrypoint tying pipeline together"`, then `git push origin main` (if origin exists)

---

### Task 9: Real end-to-end run and committed outputs

**Files:**
- Modify: `data/candidates/`, `data/analysis/`, `data/memos/`, `logs/prompts.jsonl`
- Modify: `docs/PROCESS.md` (fill remaining sections — author's own words)

- [x] Set a real `LLM_API_KEY` and run: `python cli.py --topic "AI agents for SMBs" --limit 15`
- [x] Spot-check 2-3 generated memos by hand: does every claim trace to a real source URL? Does the score match the stated rubric? Fix `analyze.py`/`template.md` if not.
- [x] Run the Git Workflow above: `git pull --rebase origin main` (if origin exists), then `git add data/ logs/prompts.jsonl && git commit -m "data: initial pipeline run for AI agents for SMBs"`, then `git push origin main` (if origin exists)
- [x] Fill in the remaining sections of `docs/PROCESS.md` (where AI helped vs. not per module, what changed mid-build, what was scoped out) in your own words
- [x] Run the Git Workflow above: `git pull --rebase origin main` (if origin exists), then `git add docs/PROCESS.md && git commit -m "docs: complete process log"`, then `git push origin main` (if origin exists)
- [x] Record the ~5 minute Loom walkthrough showing one candidate end-to-end (source → analysis → memo), referencing this repo's docs

---

## Self-Review Notes

- **Spec coverage:** Sourcing (Tasks 2-4), Analysis+scoring (Tasks 5-6),
  Recommendation/memo (Task 7), CLI/one-command run (Task 8), robustness to
  missing data (explicit in Tasks 4/6/7 tests), no-API-key fallback
  (Task 6), process visibility (Task 9 + ongoing PROCESS.md), real committed
  outputs (Task 9) — all spec sections have a task.
- **Type consistency check:** `Candidate` dict shape defined once in Task 4
  and reused verbatim in Tasks 6/7/8. `Analysis` model defined once in Task
  5 and reused in Tasks 6/7. `slugify` defined once in Task 1, reused
  everywhere else (not redefined in Task 4).
- **No placeholders:** every task has concrete test criteria and concrete
  interface signatures; the only intentionally-deferred content is Task
  3's YC-scraping-vs-hardcoded-list decision, which explicitly depends on
  inspecting the real page and is called out as such, not left vague.
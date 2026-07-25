import argparse
import json
import sys
from pathlib import Path

from analysis.analyze import get_or_analyze, NoApiKeyError
from memo.render import render_memo
from sourcing.hn_source import fetch_hn_candidates
from sourcing.normalize import normalize_candidates
from sourcing.yc_source import fetch_yc_candidates

DATA_DIR = Path("data")
CANDIDATES_DIR = DATA_DIR / "candidates"
ANALYSIS_DIR = DATA_DIR / "analysis"
MEMOS_DIR = DATA_DIR / "memos"
THESIS_PATH = Path("docs/THESIS.md")


def _read_thesis() -> str:
    if THESIS_PATH.exists():
        return THESIS_PATH.read_text().strip()
    return ""


def _write_json(directory: Path, slug: str, data: dict):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{slug}.json").write_text(json.dumps(data, indent=2))


def main():
    parser = argparse.ArgumentParser(description="AI-Augmented Investment Pipeline")
    parser.add_argument("--topic", default="AI agents for SMBs", help="Search topic for sourcing")
    parser.add_argument("--limit", type=int, default=20, help="Max candidates per source")
    args = parser.parse_args()

    thesis = _read_thesis()

    print(f"Sourcing startups for topic: {args.topic}")
    hn_raw = fetch_hn_candidates(args.topic, limit=args.limit)
    yc_raw = fetch_yc_candidates(batch="W25", limit=args.limit)
    candidates = normalize_candidates(hn_raw, yc_raw)
    print(f"Found {len(candidates)} unique candidates")

    for candidate in candidates:
        slug = candidate["slug"]
        _write_json(CANDIDATES_DIR, slug, candidate)

        try:
            analysis = get_or_analyze(candidate, thesis, cache_dir=ANALYSIS_DIR)
        except NoApiKeyError as e:
            print(f"  Skipping '{candidate['name']}': {e}", file=sys.stderr)
            continue

        memo = render_memo(candidate, analysis)
        MEMOS_DIR.mkdir(parents=True, exist_ok=True)
        (MEMOS_DIR / f"{slug}.md").write_text(memo)
        print(f"  ✓ {candidate['name']} ({analysis.recommendation})")

    print(f"\nDone. {len(candidates)} candidates processed.")
    print(f"  Memos: {MEMOS_DIR}/")


if __name__ == "__main__":
    main()

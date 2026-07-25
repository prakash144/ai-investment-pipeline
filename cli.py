import argparse
import datetime
import json
import statistics
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
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
REPORTS_DIR = Path("reports")
THESIS_PATH = Path("docs/THESIS.md")


def _read_thesis() -> str:
    if not THESIS_PATH.exists():
        return ""
    text = THESIS_PATH.read_text().strip()
    lines = text.splitlines()
    captured = []
    in_blockquote = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("> "):
            in_blockquote = True
            captured.append(stripped[2:])
        elif in_blockquote:
            break
    return " ".join(captured) if captured else text


_REC_EMOJI = {
    "Take a meeting": "🟢",
    "Watch": "🟡",
    "Pass": "🔴",
}


def _display_name(name: str, max_len: int = 30) -> str:
    return name if len(name) <= max_len else name[: max_len - 3].rstrip() + "..."


def _write_json(directory: Path, slug: str, data: dict):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{slug}.json").write_text(json.dumps(data, indent=2))


def _compute_stats(results: list[dict]) -> dict:
    scores = [r["score"] for r in results]
    counts = Counter(r["recommendation"] for r in results)
    return {
        "total": len(results),
        "take_a_meeting": counts.get("Take a meeting", 0),
        "watch": counts.get("Watch", 0),
        "pass": counts.get("Pass", 0),
        "avg_score": round(sum(scores) / len(scores), 1) if scores else 0,
        "median_score": round(statistics.median(scores), 1) if scores else 0,
        "max_score": max(scores) if scores else 0,
        "min_score": min(scores) if scores else 0,
    }


def _write_executive_summary(results: list[dict], stats: dict, topic: str, thesis: str):
    memo_link = lambda name, slug: f"[{name}](../{MEMOS_DIR / f'{slug}.md'})"

    lines = []
    lines.append("# AI Investment Pipeline Report")
    lines.append("")
    lines.append(f"**Query:** {topic}  ")
    lines.append(f"**Run Date:** {datetime.date.today()}  ")
    lines.append(f"**Sources:** YC Companies · Hacker News  ")
    lines.append(f"**Investment Thesis:** {thesis or 'Not specified'}  ")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Pipeline Summary")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|------:|")
    lines.append(f"| Candidates Discovered | {stats['total']} |")
    lines.append(f"| Successfully Analyzed | {stats['total']} |")
    lines.append(f"| 🟢 **Take a Meeting** | {stats['take_a_meeting']} |")
    lines.append(f"| 🟡 **Watch** | {stats['watch']} |")
    lines.append(f"| 🔴 **Pass** | {stats['pass']} |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Top Investment Opportunities")
    lines.append("")
    lines.append("| # | Company | Score | Recommendation | Confidence | Memo |")
    lines.append("|---|---------|------:|----------------|------------|------|")

    ranked = sorted(results, key=lambda r: (-r["score"], r["name"]))
    for i, r in enumerate(ranked, 1):
        emoji = _REC_EMOJI.get(r["recommendation"], "")
        r_name = _display_name(r["name"], 26)
        link = memo_link("📄", r["slug"])
        lines.append(f"| {i} | {r_name} | {r['score']} | {emoji} {r['recommendation']} | {r['confidence']} | {link} |")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Recommendation Distribution")
    lines.append("")

    for rec, emoji in [("Take a meeting", "🟢"), ("Watch", "🟡"), ("Pass", "🔴")]:
        group = [r for r in results if r["recommendation"] == rec]
        if not group:
            continue
        label = rec.replace("Take a meeting", "Take a Meeting")
        lines.append(f"### {emoji} {label} ({len(group)})")
        lines.append("")
        for r in group:
            link = memo_link("📄", r["slug"])
            lines.append(f"- {link} {r['name']}")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Key Portfolio Insights")
    lines.append("")

    strong = [r for r in results if r["recommendation"] == "Take a meeting"]
    if strong:
        lines.append("### Top-Tier Teams")
        lines.append("")
        for r in strong:
            link = memo_link(r['name'], r['slug'])
            lines.append(f"- **{link}** ({r['score']}/100, {r['confidence']} confidence) — recommendation for founder meeting.")
    lines.append("")
    lines.append("### Market Snapshot")
    lines.append("")
    lines.append(f"- **Active sector:** {topic}")
    lines.append(f"- **Deal flow:** {stats['total']} candidates screened in a single pass")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Next Steps")
    lines.append("")

    meetings = [r for r in results if r["recommendation"] == "Take a meeting"]
    watches = [r for r in results if r["recommendation"] == "Watch"]
    passes = [r for r in results if r["recommendation"] == "Pass"]

    if meetings:
        lines.append("### Immediate founder meetings")
        lines.append("")
        for r in meetings:
            link = memo_link(r['name'], r['slug'])
            lines.append(f"- [ ] {link}")
    lines.append("")
    if watches:
        lines.append("### Companies to monitor")
        lines.append("")
        for r in watches:
            link = memo_link("📄", r["slug"])
            lines.append(f"- {link} {r['name']}")
    lines.append("")
    if passes:
        lines.append("### No further action")
        lines.append("")
        for r in passes:
            lines.append(f"- {r['name']}")
    lines.append("")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "executive-summary.md").write_text("\n".join(lines))
    print(f"  Report: {REPORTS_DIR.resolve() / 'executive-summary.md'}")


def _write_pipeline_report(results: list[dict], stats: dict, topic: str, thesis: str):
    run_id = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    lines = []
    bar = "=" * 62
    sep = "-" * 62

    lines.append(bar)
    lines.append("                    AI INVESTMENT PIPELINE")
    lines.append(bar)
    lines.append("")
    lines.append("  Run ID")
    lines.append(f"    {run_id}")
    lines.append("")
    lines.append("  Query")
    lines.append(f"    {topic}")
    lines.append("")
    lines.append("  Investment Thesis")
    lines.append(f"    {thesis or 'Not specified'}")
    lines.append("")
    lines.append("  Sources")
    lines.append("    \u2713  YC Companies")
    lines.append("    \u2713  Hacker News")
    lines.append("")
    lines.append(sep)
    lines.append("  Pipeline Statistics")
    lines.append(sep)
    lines.append("")
    lines.append(f"    Candidates Found            :  {stats['total']}")
    lines.append(f"    Successfully Analyzed       :  {stats['total']}")
    lines.append(f"    Failed                      :  0")
    lines.append("")
    lines.append(f"    \U0001f7e2  Take a Meeting              :  {stats['take_a_meeting']}")
    lines.append(f"    \U0001f7e1  Watch                       :  {stats['watch']}")
    lines.append(f"    \U0001f534  Pass                        :  {stats['pass']}")
    lines.append("")
    lines.append(f"    Average Score               :  {stats['avg_score']}")
    lines.append(f"    Median Score                :  {stats['median_score']}")
    lines.append(f"    Highest Score               :  {stats['max_score']}")
    lines.append(f"    Lowest Score                :  {stats['min_score']}")
    lines.append("")
    lines.append(sep)
    lines.append("  Top Candidates")
    lines.append(sep)
    lines.append("")
    lines.append("    Score  Name")
    lines.append("    -----  ----")
    ranked = sorted(results, key=lambda r: (-r["score"], r["name"]))
    for r in ranked[:10]:
        r_name = _display_name(r["name"], 42)
        lines.append(f"    {r['score']:3d}   {r_name}")
    if len(ranked) > 10:
        lines.append("    ...")
    lines.append("")
    lines.append(sep)
    lines.append("  Output Locations")
    lines.append(sep)
    lines.append("")
    lines.append(f"    reports/executive-summary.md")
    lines.append(f"    reports/pipeline-report.md")
    lines.append(f"    data/memos/")
    lines.append(f"    data/candidates/")
    lines.append(f"    data/analysis/")
    lines.append("")
    lines.append(sep)
    lines.append("  Generated Files")
    lines.append(sep)
    lines.append("")
    lines.append(f"    \u2713  {stats['total']} startup candidate files")
    lines.append(f"    \u2713  {stats['total']} investment memos")
    lines.append(f"    \u2713  executive-summary.md")
    lines.append(f"    \u2713  pipeline-report.md")
    lines.append("")
    lines.append(bar)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "pipeline-report.md").write_text("\n".join(lines))
    print(f"  Report: {REPORTS_DIR.resolve() / 'pipeline-report.md'}")


def main():
    parser = argparse.ArgumentParser(description="AI-Augmented Investment Pipeline")
    parser.add_argument("--topic", default="AI agents for SMBs", help="Search topic for sourcing")
    parser.add_argument("--limit", type=int, default=20, help="Max candidates per source")
    parser.add_argument("--enrich", action="store_true", default=True, help="Enrich YC data with founder scraping (default: on)")
    parser.add_argument("--no-enrich", action="store_false", dest="enrich", help="Skip YC enrichment")
    parser.add_argument("--workers", type=int, default=5, help="Parallel workers for enrichment and analysis (default: 5)")
    args = parser.parse_args()

    thesis = _read_thesis()

    print(f"Sourcing startups for topic: {args.topic}")
    hn_raw = fetch_hn_candidates(args.topic, limit=args.limit)
    yc_raw = fetch_yc_candidates(batch="W25", limit=args.limit)
    candidates = normalize_candidates(hn_raw, yc_raw, enrich_yc=args.enrich, max_workers=args.workers)
    print(f"Found {len(candidates)} unique candidates\n")

    results = []
    for candidate in candidates:
        _write_json(CANDIDATES_DIR, candidate["slug"], candidate)

    def _process_one(candidate: dict) -> dict | None:
        slug = candidate["slug"]
        try:
            analysis = get_or_analyze(candidate, thesis, cache_dir=ANALYSIS_DIR)
        except NoApiKeyError as e:
            return {"error": str(e), "name": candidate["name"], "slug": slug}

        memo = render_memo(candidate, analysis)
        MEMOS_DIR.mkdir(parents=True, exist_ok=True)
        (MEMOS_DIR / f"{slug}.md").write_text(memo)

        call = analysis.recommendation
        icon = "★" if call in ("Take a meeting", "Watch") else " "
        short = _display_name(candidate["name"], 34)
        print(f"  {icon} {short:34s} ({call:16s}) {analysis.score}/100 — {MEMOS_DIR / f'{slug}.md'}")

        return {
            "slug": slug,
            "name": candidate["name"],
            "recommendation": call,
            "score": analysis.score,
            "confidence": analysis.confidence,
        }

    workers = min(args.workers, len(candidates)) if args.workers else 1
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(_process_one, c): c["name"] for c in candidates}
        for future in as_completed(futures):
            name = futures[future]
            try:
                result = future.result()
                if result is None:
                    continue
                if "error" in result:
                    print(f"  Skipping '{result['name']}': {result['error']}", file=sys.stderr)
                else:
                    results.append(result)
            except Exception as e:
                print(f"  Error processing '{name}': {e}", file=sys.stderr)

    if results:
        stats = _compute_stats(results)
        print()
        _write_executive_summary(results, stats, args.topic, thesis)
        _write_pipeline_report(results, stats, args.topic, thesis)
    else:
        print("\nNo candidates were analyzed.")


if __name__ == "__main__":
    main()

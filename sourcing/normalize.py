from concurrent.futures import ThreadPoolExecutor, as_completed

from config import slugify
from sourcing.enrichment import enrich_company


def _extract_name_from_hn_title(title: str) -> str:
    for prefix in ["Show HN: ", "Ask HN: ", "Launch HN: ", "Tell HN: "]:
        if title.startswith(prefix):
            title = title[len(prefix) :]
    for sep in [" – ", " - ", ": "]:
        parts = title.split(sep, 1)
        if len(parts) > 1:
            name = parts[0].strip()
            return _truncate_sentence_name(name)
    if title.endswith(")") and "(" in title:
        title = title[: title.rindex("(")].strip()
    return _truncate_sentence_name(title.strip())


def _truncate_sentence_name(name: str) -> str:
    if len(name) <= 30:
        return name
    lower = name.lower()
    sentence_starts = {"how ", "what ", "why ", "who ", "should ", "is ", "are ", "can ", "we ", "our ", "the ", "a "}
    if any(lower.startswith(s) for s in sentence_starts) or "?" in name:
        words = name.split()
        short = " ".join(words[:5]).rstrip(",").rstrip("?")
        return short + "..." if short != name else short
    for sep in [": ", " – "]:
        if sep in name:
            name = name.split(sep)[0]
    if len(name) > 30:
        words = name.split()
        truncated = []
        for w in words:
            if len(" ".join(truncated + [w])) > 30:
                break
            truncated.append(w)
        if truncated != words:
            return " ".join(truncated).rstrip(",") + "..."
    return name


def _enrich_yc_item(item: dict) -> tuple[str, str | None, dict]:
    name = item["name"]
    enriched = enrich_company(name, website=item.get("website"))
    founders_str = None
    if enriched.get("founders"):
        founders_str = "; ".join(
            f"{f['name']} ({f['title']})" for f in enriched["founders"]
        )
    extra = {k: v for k, v in enriched.items() if v and k != "founders"}
    return founders_str, extra


def normalize_candidates(hn_raw: list[dict], yc_raw: list[dict], enrich_yc: bool = True, max_workers: int = 5) -> list[dict]:
    seen_slugs = {}
    candidates = []

    enrichment_results = {}
    if enrich_yc and yc_raw:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(_enrich_yc_item, item): item["name"] for item in yc_raw}
            for future in as_completed(futures):
                name = futures[future]
                try:
                    enrichment_results[name] = future.result()
                except Exception:
                    enrichment_results[name] = (None, {})

    for item in yc_raw:
        name = item["name"]
        slug = slugify(name)
        founders_str = None
        extra = {}

        if enrich_yc and name in enrichment_results:
            founders_str, extra = enrichment_results[name]

        candidate = {
            "slug": slug,
            "name": name,
            "website": item.get("website"),
            "description": item.get("description", ""),
            "founders": founders_str or item.get("founders"),
            "traction_signal": {
                "type": "yc_batch",
                "detail": f"YC {item.get('batch', '')}",
                "source_url": f"https://www.ycombinator.com/companies?batch={item.get('batch', '')}",
            },
            "source": "yc",
            "source_url": f"https://www.ycombinator.com/companies?batch={item.get('batch', '')}",
            "extra": extra if extra else None,
        }
        seen_slugs[slug] = candidate
        candidates.append(candidate)

    for item in hn_raw:
        name = _extract_name_from_hn_title(item.get("title", ""))
        slug = slugify(name)
        points = item.get("points", 0)
        num_comments = item.get("num_comments", 0)
        traction = None
        if points > 0 or num_comments > 0:
            traction = {
                "type": "hacker_news",
                "detail": f"{points} points, {num_comments} comments",
                "source_url": f"https://news.ycombinator.com/item?id={item.get('objectID', '')}",
            }
        candidate = {
            "slug": slug,
            "name": name,
            "website": item.get("url"),
            "description": item.get("title", ""),
            "founders": item.get("founders"),
            "traction_signal": traction,
            "source": "hn",
            "source_url": f"https://news.ycombinator.com/item?id={item.get('objectID', '')}",
            "extra": None,
        }

        if slug in seen_slugs:
            existing = seen_slugs[slug]
            if traction:
                existing["traction_signal"] = traction
            if existing["source"] == "yc" and candidate.get("website") and not existing.get("website"):
                existing["website"] = candidate["website"]
        else:
            seen_slugs[slug] = candidate
            candidates.append(candidate)

    return candidates

from config import slugify


def _extract_name_from_hn_title(title: str) -> str:
    for prefix in ["Show HN: ", "Ask HN: ", "Launch HN: ", "Tell HN: "]:
        if title.startswith(prefix):
            title = title[len(prefix) :]
    parts = title.split(" – ")
    if len(parts) > 1:
        return parts[0].strip()
    parts = title.split(" - ")
    if len(parts) > 1:
        return parts[0].strip()
    parts = title.split(": ")
    if len(parts) > 1:
        return parts[0].strip()
    if title.endswith(")") and "(" in title:
        title = title[: title.rindex("(")].strip()
    return title.strip()


def normalize_candidates(hn_raw: list[dict], yc_raw: list[dict]) -> list[dict]:
    seen_slugs = {}
    candidates = []

    for item in yc_raw:
        name = item["name"]
        slug = slugify(name)
        candidate = {
            "slug": slug,
            "name": name,
            "website": item.get("website"),
            "description": item.get("description", ""),
            "founders": item.get("founders"),
            "traction_signal": {"type": "yc_batch", "detail": f"YC {item.get('batch', '')}", "source_url": f"https://www.ycombinator.com/companies?batch={item.get('batch', '')}"},
            "source": "yc",
            "source_url": f"https://www.ycombinator.com/companies?batch={item.get('batch', '')}",
        }
        seen_slugs[slug] = candidate
        candidates.append(candidate)

    for item in hn_raw:
        name = _extract_name_from_hn_title(item.get("title", ""))
        slug = slugify(name)
        traction = None
        points = item.get("points", 0)
        num_comments = item.get("num_comments", 0)
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

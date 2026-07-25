import json
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ENRICHMENT_CACHE_DIR = Path("data/enrichment")
YC_COMPANY_URL = "https://www.ycombinator.com/companies/{slug}"
_REQUEST_DELAY = 0.3


def _slugify_company_name(name: str) -> str:
    slug = name.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


def _get_cached(slug: str) -> dict | None:
    path = ENRICHMENT_CACHE_DIR / f"{slug}.json"
    if path.exists():
        return json.loads(path.read_text())
    return None


def _save_cache(slug: str, data: dict):
    ENRICHMENT_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    (ENRICHMENT_CACHE_DIR / f"{slug}.json").write_text(json.dumps(data, indent=2))


def _clean_founder_title(raw: str, founder_name: str = "") -> str:
    raw = raw.replace("\xa0", " ").strip()
    known_authors = {"Latest News", "See original launch post", "TL;DR"}
    text = raw
    for token in known_authors:
        if token in text:
            text = text.split(token)[0]
    if founder_name and founder_name in text:
        idx = text.index(founder_name)
        if idx > 0:
            text = text[:idx]
    text = re.sub(r"(Founder)([A-Z])", r"\1 \2", text)
    text = re.sub(r"\s+", " ", text).strip()
    max_len = 250
    if len(text) > max_len:
        text = text[:max_len].rsplit(". ", 1)[0] + "."
    return text


def _extract_founders_from_html(soup: BeautifulSoup) -> list[dict]:
    text = soup.get_text().replace("\xa0", " ")

    parts = text.split("Active Founders")
    if len(parts) < 2:
        return []

    block = parts[1].split("About")[0] if "About" in parts[1] else parts[1]
    block = block.split("Y Combinator")[0]

    pattern = r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s+(Founder[^\n]*)"
    seen = set()
    founders = []
    for match in re.finditer(pattern, block):
        name = match.group(1).strip()
        title = _clean_founder_title(match.group(2), founder_name=name)
        known_bad = {"Paul Graham", "Diana Hu"}
        if name not in seen and name not in known_bad and len(title) > 7:
            seen.add(name)
            founders.append({"name": name, "title": title})
    return founders


def _extract_metadata(text: str) -> dict:
    clean = text.replace("\xa0", " ")
    meta = {}
    founded = re.search(r"Founded[:\s]*(\d{4})", clean)
    if founded:
        meta["founded"] = founded.group(1)
    batch = re.search(r"Batch[:\s]*([A-Za-z]+\s+\d{4})", clean)
    if batch:
        meta["batch"] = batch.group(1)
    team = re.search(r"Team Size[:\s]*(\d+)", clean)
    if team:
        meta["team_size"] = team.group(1)
    return meta


def enrich_company(name: str, website: str | None = None) -> dict:
    slug = _slugify_company_name(name)
    cached = _get_cached(slug)
    if cached:
        return cached

    result = {"founders": [], "founded": None, "batch": None, "team_size": None}

    try:
        time.sleep(_REQUEST_DELAY)
        response = requests.get(
            YC_COMPANY_URL.format(slug=slug),
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10,
        )
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            raw = soup.get_text()
            result["founders"] = _extract_founders_from_html(soup)
            result.update(_extract_metadata(raw))
    except Exception:
        pass

    _save_cache(slug, result)
    return result

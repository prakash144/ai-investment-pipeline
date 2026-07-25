import requests

HN_ALGOLIA_URL = "https://hn.algolia.com/api/v1/search"


def fetch_hn_candidates(query: str, limit: int = 20) -> list[dict]:
    params = {
        "query": query,
        "hitsPerPage": limit,
        "tags": "story",
    }
    response = requests.get(HN_ALGOLIA_URL, params=params)
    response.raise_for_status()
    data = response.json()
    hits = data.get("hits", [])

    results = []
    for hit in hits:
        results.append(
            {
                "title": hit.get("title", ""),
                "url": hit.get("url") or hit.get("story_url"),
                "points": hit.get("points", 0),
                "num_comments": hit.get("num_comments", 0),
                "created_at": hit.get("created_at", ""),
                "objectID": hit.get("objectID", ""),
                "source": "hn",
            }
        )
    return results

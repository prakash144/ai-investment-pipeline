import os
import re
import unicodedata


def slugify(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name.strip().lower())
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    normalized = re.sub(r"[^\w\s-]", "", normalized)
    normalized = re.sub(r"[\s_]+", "-", normalized)
    normalized = re.sub(r"-+", "-", normalized)
    return normalized.strip("-")


def get_llm_api_key() -> str | None:
    return os.environ.get("LLM_API_KEY")

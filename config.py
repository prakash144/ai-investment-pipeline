import os
import re
import unicodedata
from pathlib import Path


def slugify(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name.strip().lower())
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    normalized = re.sub(r"[^\w\s-]", "", normalized)
    normalized = re.sub(r"[\s_]+", "-", normalized)
    normalized = re.sub(r"-+", "-", normalized)
    return normalized.strip("-")


def _load_dotenv():
    dotenv_path = Path(".env")
    if dotenv_path.exists():
        for line in dotenv_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip().strip("\"'")
            if key not in os.environ:
                os.environ[key] = value


def get_llm_api_key() -> str | None:
    _load_dotenv()
    return os.environ.get("LLM_API_KEY")


def get_llm_api_base() -> str:
    _load_dotenv()
    return os.environ.get("LLM_API_BASE", "https://api.openai.com/v1")

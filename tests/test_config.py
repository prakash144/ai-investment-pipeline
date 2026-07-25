import pytest
import config
from config import slugify, get_llm_api_key


class TestSlugify:
    def test_stable_and_collision_resistant(self):
        assert slugify("Acme Inc.") == slugify("acme inc")
        assert slugify("Acme") != slugify("Acme Co")

    def test_handles_empty_string(self):
        assert slugify("") == ""

    def test_handles_unicode(self):
        assert slugify("Café Start-up") == "cafe-start-up"


class TestGetLlmApiKey:
    def test_returns_none_when_unset(self, monkeypatch):
        monkeypatch.delenv("LLM_API_KEY", raising=False)
        monkeypatch.setattr(config, "_load_dotenv", lambda: None)
        assert get_llm_api_key() is None

    def test_returns_value_when_set(self, monkeypatch):
        monkeypatch.setenv("LLM_API_KEY", "sk-test-key")
        assert get_llm_api_key() == "sk-test-key"

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from analysis.analyze import build_prompt, get_or_analyze, NoApiKeyError
from analysis.schema import Analysis

THESIS_TEXT = "Seed/pre-seed AI-agent tooling for SMBs with technical founder"


class TestBuildPrompt:
    def test_contains_thesis_text(self):
        candidate = {"slug": "test-co", "name": "Test Co", "website": "https://test.co", "description": "AI tool", "founders": "John Doe", "traction_signal": {"type": "hn", "detail": "100 points", "source_url": "https://example.com"}, "source": "hn", "source_url": "https://example.com"}
        prompt = build_prompt(candidate, THESIS_TEXT)
        assert THESIS_TEXT in prompt

    def test_mentions_missing_founder_info(self):
        candidate = {"slug": "test-co", "name": "Test Co", "website": "https://test.co", "description": "AI tool", "founders": None, "traction_signal": None, "source": "hn", "source_url": "https://example.com"}
        prompt = build_prompt(candidate, THESIS_TEXT)
        assert "no founder" in prompt.lower() or "not found" in prompt.lower()


class TestGetOrAnalyze:
    def test_returns_cached_data_no_llm_call(self, tmp_path, monkeypatch):
        cache_dir = tmp_path / "analysis"
        cache_dir.mkdir()
        cached = {
            "team": "Strong team",
            "product": "Good product",
            "market": "Large market",
            "risks": ["Competition"],
            "score": 70,
            "score_breakdown": {"team": 20, "product_fit": 20, "traction": 15, "risk": 15},
            "recommendation": "Watch",
            "change_my_mind": ["Need traction"],
            "sources": ["https://example.com"],
        }
        (cache_dir / "test-co.json").write_text(json.dumps(cached))

        candidate = {"slug": "test-co", "name": "Test Co", "website": None, "description": "", "founders": None, "traction_signal": None, "source": "hn", "source_url": ""}

        mock_client = MagicMock()
        result = get_or_analyze(candidate, THESIS_TEXT, cache_dir=cache_dir, llm_client=mock_client)
        assert result.score == 70
        mock_client.assert_not_called()

    def test_raises_no_api_key_on_cache_miss(self, tmp_path, monkeypatch):
        cache_dir = tmp_path / "analysis"
        cache_dir.mkdir()
        monkeypatch.delenv("LLM_API_KEY", raising=False)

        candidate = {"slug": "new-co", "name": "New Co", "website": None, "description": "", "founders": None, "traction_signal": None, "source": "hn", "source_url": ""}

        with pytest.raises(NoApiKeyError):
            get_or_analyze(candidate, THESIS_TEXT, cache_dir=cache_dir, llm_client=None)

    def test_calls_llm_and_caches_on_miss(self, tmp_path, monkeypatch):
        cache_dir = tmp_path / "analysis"
        cache_dir.mkdir()
        monkeypatch.setenv("LLM_API_KEY", "sk-test")

        candidate = {"slug": "new-co", "name": "New Co", "website": "https://new.co", "description": "AI tool for SMBs", "founders": "Jane Smith", "traction_signal": {"type": "hn", "detail": "50 points", "source_url": "https://example.com"}, "source": "hn", "source_url": "https://example.com"}

        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = json.dumps({
            "team": "Jane Smith previously founded Acme",
            "product": "AI agent for SMB invoicing",
            "market": "Large SMB market, growing",
            "risks": ["Competition from incumbents"],
            "score": 75,
            "score_breakdown": {"team": 25, "product_fit": 20, "traction": 15, "risk": 15},
            "recommendation": "Watch",
            "change_my_mind": ["Paying customers", "Revenue growth"],
            "sources": ["https://news.ycombinator.com/item?id=123"],
        })
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_response.model = "gpt-4o-mini"
        mock_response.usage = MagicMock(prompt_tokens=500, completion_tokens=200)

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()
        monkeypatch.chdir(tmp_path)

        result = get_or_analyze(candidate, THESIS_TEXT, cache_dir=cache_dir, llm_client=mock_client)
        assert result.score == 75
        assert result.recommendation == "Watch"
        assert (cache_dir / "new-co.json").exists()
        mock_client.chat.completions.create.assert_called_once()

    def test_malformed_llm_response_raises_error(self, tmp_path, monkeypatch):
        cache_dir = tmp_path / "analysis"
        cache_dir.mkdir()
        monkeypatch.setenv("LLM_API_KEY", "sk-test")

        candidate = {"slug": "bad-co", "name": "Bad Co", "website": None, "description": "", "founders": None, "traction_signal": None, "source": "hn", "source_url": ""}

        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "This is not valid JSON"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_response.usage = MagicMock(prompt_tokens=100, completion_tokens=50)

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()
        monkeypatch.chdir(tmp_path)

        with pytest.raises(Exception):
            get_or_analyze(candidate, THESIS_TEXT, cache_dir=cache_dir, llm_client=mock_client)

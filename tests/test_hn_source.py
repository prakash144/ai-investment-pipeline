import pytest
import requests
from sourcing.hn_source import fetch_hn_candidates


class TestFetchHnCandidates:
    def test_builds_correct_request_params(self, monkeypatch):
        responses = []

        def mock_get(url, params):
            responses.append((url, params))
            return MockResponse({"hits": []})

        monkeypatch.setattr(requests, "get", mock_get)
        fetch_hn_candidates("AI agents", limit=10)
        url, params = responses[0]
        assert "hn.algolia.com" in url
        assert params["query"] == "AI agents"
        assert params["hitsPerPage"] == 10

    def test_respects_limit(self, monkeypatch):
        hits = [{"title": f"item {i}", "objectID": str(i), "points": 1, "num_comments": 0, "created_at": "2025-01-01"} for i in range(30)]

        def mock_get(url, params):
            return MockResponse({"hits": hits[: params["hitsPerPage"]]})

        monkeypatch.setattr(requests, "get", mock_get)
        result = fetch_hn_candidates("test", limit=10)
        assert len(result) <= 10

    def test_missing_optional_fields_returns_none(self, monkeypatch):
        hits = [{"title": "No URL item", "objectID": "abc123", "points": 5, "num_comments": 2, "created_at": "2025-06-01"}]

        def mock_get(url, params):
            return MockResponse({"hits": hits})

        monkeypatch.setattr(requests, "get", mock_get)
        result = fetch_hn_candidates("test", limit=10)
        assert result[0]["url"] is None

    def test_empty_hits_returns_empty_list(self, monkeypatch):
        def mock_get(url, params):
            return MockResponse({"hits": []})

        monkeypatch.setattr(requests, "get", mock_get)
        result = fetch_hn_candidates("test", limit=10)
        assert result == []


class MockResponse:
    def __init__(self, json_data):
        self._json = json_data

    def json(self):
        return self._json

    def raise_for_status(self):
        pass

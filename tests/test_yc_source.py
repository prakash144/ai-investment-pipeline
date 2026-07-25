import pytest
from sourcing.yc_source import fetch_yc_candidates


class TestFetchYcCandidates:
    def test_respects_limit(self):
        result = fetch_yc_candidates(batch="W25", limit=5)
        assert len(result) <= 5

    def test_all_entries_have_required_fields(self):
        result = fetch_yc_candidates(batch="W25", limit=20)
        for entry in result:
            assert "name" in entry and entry["name"]
            assert "description" in entry and entry["description"]
            assert "batch" in entry and entry["batch"] == "W25"
            assert "source" in entry and entry["source"] == "yc"

    def test_website_is_optional(self):
        result = fetch_yc_candidates(batch="W25", limit=20)
        typo = [e for e in result if e["name"] == "Typo"][0]
        assert typo["website"] is None

    def test_empty_batch_returns_empty_list(self):
        result = fetch_yc_candidates(batch="NONEXISTENT", limit=20)
        assert result == []

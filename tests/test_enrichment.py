import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from bs4 import BeautifulSoup

from sourcing.enrichment import (
    _clean_founder_title,
    _extract_founders_from_html,
    _extract_metadata,
    _get_cached,
    _save_cache,
    _slugify_company_name,
    enrich_company,
)

SAMPLE_HTML = """
<html><body>
<h2>Active Founders</h2>
<div>
  <span>Kevin Michael</span>
  <span>Founder Spent the last 5 years at Perpetua ($150M exit).</span>
</div>
<div>
  <span>Peter Gokhshteyn</span>
  <span>Founder Passionate about building great products.</span>
</div>
<h2>About</h2>
<div>Founded: 2023</div>
<div>Batch: Summer 2023</div>
<div>Team Size: 8</div>
</body></html>
"""


class TestSlugifyCompanyName:
    def test_basic_slug(self):
        assert _slugify_company_name("Tempo Labs") == "tempo-labs"

    def test_special_chars_removed(self):
        assert _slugify_company_name("Acme, Inc.") == "acme-inc"

    def test_empty_string(self):
        assert _slugify_company_name("") == ""


class TestCleanFounderTitle:
    def test_adds_space_after_founder(self):
        result = _clean_founder_title("FounderLed the team")
        assert result == "Founder Led the team"

    def test_truncates_at_duplicate_name(self):
        result = _clean_founder_title("Founder Good stuff. Peter Also some extra", founder_name="Peter")
        assert "Peter" not in result or result.index("Peter") == 0

    def test_truncates_at_known_noise(self):
        result = _clean_founder_title("Founder Great bio. Latest News Some article")
        assert "Latest News" not in result

    def test_reasonable_max_length(self):
        long = "Founder " + "word " * 100
        result = _clean_founder_title(long)
        assert len(result) <= 260


class TestExtractMetadata:
    def test_extracts_founded_year(self):
        meta = _extract_metadata("Founded: 2023\nBatch: Summer 2023\nTeam Size: 8")
        assert meta.get("founded") == "2023"

    def test_extracts_batch(self):
        meta = _extract_metadata("Founded: 2023\nBatch: Summer 2023\nTeam Size: 8")
        assert meta.get("batch") == "Summer 2023"

    def test_extracts_team_size(self):
        meta = _extract_metadata("Founded: 2023\nBatch: Summer 2023\nTeam Size: 8")
        assert meta.get("team_size") == "8"

    def test_missing_fields_return_empty_dict(self):
        meta = _extract_metadata("No structured data here")
        assert meta == {}


class TestExtractFoundersFromHtml:
    def test_extracts_founders_from_active_founders_section(self):
        soup = BeautifulSoup(SAMPLE_HTML, "html.parser")
        founders = _extract_founders_from_html(soup)
        assert len(founders) >= 1

    def test_no_active_founders_section_returns_empty(self):
        soup = BeautifulSoup("<html><body>No founders here</body></html>", "html.parser")
        assert _extract_founders_from_html(soup) == []


class TestEnrichCompany:
    def test_cache_hit_returns_cached_without_network(self, tmp_path):
        slug = "test-co"
        cache_dir = tmp_path / "enrichment"
        cache_dir.mkdir(parents=True)
        cached = {"founders": [{"name": "T", "title": "F"}], "founded": "2023", "batch": None, "team_size": None}
        (cache_dir / f"{slug}.json").write_text(json.dumps(cached))

        with patch("sourcing.enrichment.ENRICHMENT_CACHE_DIR", cache_dir):
            with patch("sourcing.enrichment.requests.get") as mock_get:
                result = enrich_company("Test Co")
                mock_get.assert_not_called()
                assert result == cached

    def test_cache_miss_fetches_and_caches(self, tmp_path):
        slug = "tempo-labs"
        cache_dir = tmp_path / "enrichment"

        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.text = SAMPLE_HTML

        with patch("sourcing.enrichment.ENRICHMENT_CACHE_DIR", cache_dir):
            with patch("sourcing.enrichment.requests.get", return_value=mock_resp):
                with patch("sourcing.enrichment.time.sleep"):
                    result = enrich_company("Tempo Labs")

        assert cache_dir.joinpath(f"{slug}.json").exists()
        assert "founders" in result
        assert result.get("founded") == "2023"

    def test_network_failure_returns_default(self, tmp_path):
        cache_dir = tmp_path / "enrichment"
        with patch("sourcing.enrichment.ENRICHMENT_CACHE_DIR", cache_dir):
            with patch("sourcing.enrichment.requests.get", side_effect=Exception("Connection error")):
                with patch("sourcing.enrichment.time.sleep"):
                    result = enrich_company("Tempo Labs")

        assert result["founders"] == []
        assert result["founded"] is None
        assert result["batch"] is None
        assert result["team_size"] is None

    def test_non_200_response_returns_default(self, tmp_path):
        cache_dir = tmp_path / "enrichment"
        mock_resp = Mock()
        mock_resp.status_code = 404

        with patch("sourcing.enrichment.ENRICHMENT_CACHE_DIR", cache_dir):
            with patch("sourcing.enrichment.requests.get", return_value=mock_resp):
                with patch("sourcing.enrichment.time.sleep"):
                    result = enrich_company("Tempo Labs")

        assert result["founders"] == []

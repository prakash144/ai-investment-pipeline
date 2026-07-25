import pytest
from sourcing.normalize import normalize_candidates


class TestNormalizeCandidates:
    def test_dedupe_merges_same_company(self):
        hn_raw = [
            {
                "title": "Show HN: Resend – Email API for developers",
                "url": "https://resend.com",
                "points": 120,
                "num_comments": 45,
                "created_at": "2025-06-01T12:00:00Z",
                "objectID": "12345",
                "source": "hn",
            }
        ]
        yc_raw = [
            {
                "name": "Resend",
                "website": "https://resend.com",
                "description": "Email API for developers to send transactional emails",
                "batch": "W25",
                "source": "yc",
            }
        ]
        result = normalize_candidates(hn_raw, yc_raw)
        assert len(result) == 1
        assert result[0]["name"] == "Resend"
        assert result[0]["description"] == "Email API for developers to send transactional emails"
        assert result[0]["traction_signal"] is not None
        assert result[0]["traction_signal"]["type"] == "hacker_news"

    def test_missing_founders_is_none(self):
        hn_raw = [
            {
                "title": "Some random tech post",
                "url": "https://example.com",
                "points": 10,
                "num_comments": 2,
                "created_at": "2025-06-01T12:00:00Z",
                "objectID": "67890",
                "source": "hn",
            }
        ]
        result = normalize_candidates(hn_raw, [])
        assert result[0]["founders"] is None

    def test_output_length_never_exceeds_input_sum(self):
        hn_raw = [{"title": f"Item {i}", "url": None, "points": 1, "num_comments": 0, "created_at": "", "objectID": str(i), "source": "hn"} for i in range(5)]
        yc_raw = [{"name": f"Company {i}", "website": None, "description": "test", "batch": "W25", "source": "yc"} for i in range(3)]
        result = normalize_candidates(hn_raw, yc_raw)
        assert len(result) <= len(hn_raw) + len(yc_raw)

    def test_all_output_dicts_have_required_keys(self):
        hn_raw = [{"title": "Test startup", "url": "https://example.com", "points": 5, "num_comments": 1, "created_at": "", "objectID": "1", "source": "hn"}]
        yc_raw = []
        result = normalize_candidates(hn_raw, yc_raw)
        required_keys = {"slug", "name", "website", "description", "founders", "traction_signal", "source", "source_url"}
        assert required_keys.issubset(result[0].keys())

    def test_handles_empty_inputs(self):
        assert normalize_candidates([], []) == []

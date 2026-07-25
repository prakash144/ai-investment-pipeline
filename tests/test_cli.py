import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from analysis.schema import Analysis
from analysis.analyze import NoApiKeyError


def _mock_analysis():
    return Analysis(executive_summary="Summary", team="Team", product="Product", market="Market", traction_signals="None", risks=["Risk"], thesis_alignment="Fits", score=60, score_breakdown={"team": 15, "product_fit": 15, "traction": 15, "risk": 15}, confidence="Medium", recommendation="Watch", change_my_mind=["X"], sources=["https://example.com"])


class TestCliMain:
    def test_writes_files_for_each_candidate(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "data/candidates").mkdir(parents=True)
        (tmp_path / "data/analysis").mkdir(parents=True)
        (tmp_path / "data/memos").mkdir(parents=True)
        monkeypatch.setattr("sys.argv", ["cli.py", "--topic", "AI agents", "--limit", "5", "--no-enrich"])

        monkeypatch.setattr("cli.fetch_hn_candidates", lambda query, limit: [{"title": f"Startup {i}", "url": None, "points": 10, "num_comments": 2, "created_at": "", "objectID": str(i), "source": "hn"} for i in range(3)])
        monkeypatch.setattr("cli.fetch_yc_candidates", lambda batch, limit: [{"name": f"YC Co {i}", "website": None, "description": "AI startup", "batch": "W25", "source": "yc"} for i in range(2)])

        def mock_analyze(candidate, thesis, **kwargs):
            return _mock_analysis()

        monkeypatch.setattr("cli.get_or_analyze", mock_analyze)

        from cli import main
        main()

        assert len(list((tmp_path / "data/candidates").iterdir())) > 0
        assert len(list((tmp_path / "data/memos").iterdir())) > 0

    def test_no_api_key_skips_candidate_continues(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "data/candidates").mkdir(parents=True)
        (tmp_path / "data/analysis").mkdir(parents=True)
        (tmp_path / "data/memos").mkdir(parents=True)
        monkeypatch.setattr("sys.argv", ["cli.py", "--topic", "AI agents", "--limit", "3", "--no-enrich"])

        monkeypatch.setattr("cli.fetch_hn_candidates", lambda query, limit: [{"title": f"Startup {i}", "url": None, "points": 10, "num_comments": 2, "created_at": "", "objectID": str(i), "source": "hn"} for i in range(2)])
        monkeypatch.setattr("cli.fetch_yc_candidates", lambda batch, limit: [])

        call_count = [0]

        def mock_analyze(candidate, thesis, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise NoApiKeyError(f"No key for {candidate['name']}")
            return _mock_analysis()

        monkeypatch.setattr("cli.get_or_analyze", mock_analyze)

        from cli import main
        main()

        assert call_count[0] > 1

import pytest
from analysis.schema import Analysis
from memo.render import render_memo


class TestRenderMemo:
    def test_contains_all_sections(self):
        candidate = {"slug": "test-co", "name": "Test Co", "website": "https://test.co", "description": "An AI tool for SMBs", "founders": "John Doe", "traction_signal": {"type": "hacker_news", "detail": "100 points", "source_url": "https://example.com"}, "source": "hn", "source_url": "https://news.ycombinator.com/item?id=123", "extra": None}
        analysis = Analysis(executive_summary="Strong AI tool for SMBs", team="Founder previously at OpenAI", product="AI agent for customer support", market="Growing SMB automation market", traction_signals="100 HN points", risks=["Depends on OpenAI API pricing", "Easy to copy"], thesis_alignment="Fits thesis well", score=84, score_breakdown={"team": 30, "product_fit": 20, "traction": 20, "risk": 14}, confidence="High", recommendation="Take a meeting", change_my_mind=["Loses key founder", "No revenue growth in 6 months"], sources=["https://example.com"])
        output = render_memo(candidate, analysis)
        assert "Investment Memo" in output
        assert "Test Co" in output
        assert "Take a meeting" in output
        assert "Executive Summary" in output
        assert "Company Snapshot" in output
        assert "Product" in output
        assert "Team" in output
        assert "Market" in output
        assert "Traction Signals" in output
        assert "Risks" in output
        assert "Thesis Alignment" in output
        assert "What Would Change My Mind" in output
        assert "Sources" in output

    def test_missing_founders_shows_unavailable(self):
        candidate = {"slug": "test-co", "name": "Test Co", "website": None, "description": "AI tool", "founders": None, "traction_signal": None, "source": "hn", "source_url": "", "extra": None}
        analysis = Analysis(executive_summary="Summary", team="No founder information available", product="Good product", market="Large market", traction_signals="None found", risks=["Competition"], thesis_alignment="Unclear fit", score=50, score_breakdown={"team": 10, "product_fit": 15, "traction": 10, "risk": 15}, confidence="Low", recommendation="Pass", change_my_mind=["Traction", "Founder background"], sources=[])
        output = render_memo(candidate, analysis)
        assert "Not available from sourced data" in output

    def test_includes_sources_section(self):
        candidate = {"slug": "test-co", "name": "Test Co", "website": "https://test.co", "description": "AI tool", "founders": "John", "traction_signal": None, "source": "hn", "source_url": "https://news.ycombinator.com/item?id=123", "extra": None}
        analysis = Analysis(executive_summary="Summary", team="Team", product="Product", market="Market", traction_signals="None", risks=["Risk"], thesis_alignment="Fits", score=60, score_breakdown={"team": 15, "product_fit": 15, "traction": 15, "risk": 15}, confidence="Medium", recommendation="Watch", change_my_mind=["X"], sources=["https://example.com", "https://other.com"])
        output = render_memo(candidate, analysis)
        assert "https://example.com" in output
        assert "https://other.com" in output

    def test_reasonable_length(self):
        candidate = {"slug": "test-co", "name": "Test Co", "website": "https://test.co", "description": "AI tool", "founders": "John", "traction_signal": None, "source": "hn", "source_url": "", "extra": None}
        analysis = Analysis(executive_summary="Summary " * 5, team="Team background here " * 10, product="Product desc " * 10, market="Market analysis " * 10, traction_signals="Traction " * 5, risks=["Risk 1", "Risk 2", "Risk 3"], thesis_alignment="Fits " * 5, score=70, score_breakdown={"team": 20, "product_fit": 20, "traction": 15, "risk": 15}, confidence="Medium", recommendation="Watch", change_my_mind=["Signal A", "Signal B"], sources=["https://example.com"])
        output = render_memo(candidate, analysis)
        word_count = len(output.split())
        assert word_count < 600

    def test_extra_data_renders_in_snapshot(self):
        candidate = {"slug": "test-co", "name": "Test Co", "website": "https://test.co", "description": "AI tool", "founders": "John", "traction_signal": None, "source": "yc", "source_url": "", "extra": {"founded": "2023", "batch": "W25", "team_size": "10"}}
        analysis = Analysis(executive_summary="Summary", team="Team", product="Product", market="Market", traction_signals="None", risks=["Risk"], thesis_alignment="Fits", score=60, score_breakdown={"team": 15, "product_fit": 15, "traction": 15, "risk": 15}, confidence="Medium", recommendation="Watch", change_my_mind=["X"], sources=[])
        output = render_memo(candidate, analysis)
        assert "2023" in output
        assert "W25" in output
        assert "10" in output

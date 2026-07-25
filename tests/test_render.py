import pytest
from analysis.schema import Analysis
from memo.render import render_memo


class TestRenderMemo:
    def test_contains_all_sections(self):
        candidate = {"slug": "test-co", "name": "Test Co", "website": "https://test.co", "description": "An AI tool for SMBs", "founders": "John Doe", "traction_signal": {"type": "hacker_news", "detail": "100 points", "source_url": "https://example.com"}, "source": "hn", "source_url": "https://news.ycombinator.com/item?id=123"}
        analysis = Analysis(team="Founder previously at OpenAI", product="AI agent for customer support", market="Growing SMB automation market", risks=["Depends on OpenAI API pricing", "Easy to copy"], score=84, score_breakdown={"team": 30, "product_fit": 20, "traction": 20, "risk": 14}, recommendation="Take a meeting", change_my_mind=["Loses key founder", "No revenue growth in 6 months"], sources=["https://example.com"])
        output = render_memo(candidate, analysis)
        assert "Test Co" in output
        assert "Take a meeting" in output
        assert "Team" in output
        assert "Product" in output
        assert "Market" in output
        assert "Risks" in output
        assert "Score" in output
        assert "Change my mind" in output or "change_my_mind" in output
        assert "Sources" in output

    def test_missing_founders_shows_unavailable(self):
        candidate = {"slug": "test-co", "name": "Test Co", "website": None, "description": "AI tool", "founders": None, "traction_signal": None, "source": "hn", "source_url": ""}
        analysis = Analysis(team="No founder information available", product="Good product", market="Large market", risks=["Competition"], score=50, score_breakdown={"team": 10, "product_fit": 15, "traction": 10, "risk": 15}, recommendation="Pass", change_my_mind=["Traction", "Founder background"], sources=[])
        output = render_memo(candidate, analysis)
        assert "None" not in output.split("Team")[0] if "Team" in output else True
        assert "no founder information" in output.lower()

    def test_includes_sources_section(self):
        candidate = {"slug": "test-co", "name": "Test Co", "website": "https://test.co", "description": "AI tool", "founders": "John", "traction_signal": None, "source": "hn", "source_url": "https://news.ycombinator.com/item?id=123"}
        analysis = Analysis(team="Team", product="Product", market="Market", risks=["Risk"], score=60, score_breakdown={"team": 15, "product_fit": 15, "traction": 15, "risk": 15}, recommendation="Watch", change_my_mind=["X"], sources=["https://example.com", "https://other.com"])
        output = render_memo(candidate, analysis)
        assert "https://example.com" in output
        assert "https://other.com" in output
        assert "https://news.ycombinator.com/item?id=123" in output

    def test_reasonable_length(self):
        candidate = {"slug": "test-co", "name": "Test Co", "website": "https://test.co", "description": "AI tool", "founders": "John", "traction_signal": None, "source": "hn", "source_url": ""}
        analysis = Analysis(team="Team background here " * 10, product="Product desc " * 10, market="Market analysis " * 10, risks=["Risk 1", "Risk 2", "Risk 3"], score=70, score_breakdown={"team": 20, "product_fit": 20, "traction": 15, "risk": 15}, recommendation="Watch", change_my_mind=["Signal A", "Signal B"], sources=["https://example.com"])
        output = render_memo(candidate, analysis)
        word_count = len(output.split())
        assert word_count < 500

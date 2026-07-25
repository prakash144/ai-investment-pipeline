import pytest
from pydantic import ValidationError
from analysis.schema import Analysis


class TestAnalysisSchema:
    def test_score_out_of_range_raises(self):
        for bad_score in [150, -10]:
            with pytest.raises(ValidationError):
                Analysis(
                    team="Strong team",
                    product="Good product",
                    market="Large market",
                    risks=["Competition"],
                    score=bad_score,
                    score_breakdown={"team": 30, "product_fit": 25, "traction": 25, "risk": 20},
                    recommendation="Pass",
                    change_my_mind=["Need traction"],
                    sources=["https://example.com"],
                )

    def test_invalid_recommendation_raises(self):
        with pytest.raises(ValidationError):
            Analysis(
                team="Strong team",
                product="Good product",
                market="Large market",
                risks=["Competition"],
                score=70,
                score_breakdown={"team": 30, "product_fit": 25, "traction": 25, "risk": 20},
                recommendation="Maybe",
                change_my_mind=["Need traction"],
                sources=["https://example.com"],
            )

    def test_score_breakdown_sum_not_enforced(self):
        analysis = Analysis(
            team="Strong team",
            product="Good product",
            market="Large market",
            risks=["Competition"],
            score=70,
            score_breakdown={"team": 30, "product_fit": 20, "traction": 10, "risk": 5},
            recommendation="Watch",
            change_my_mind=["Need traction"],
            sources=["https://example.com"],
        )
        assert analysis.score == 70

    def test_valid_analysis_round_trips(self):
        data = {
            "team": "Founder previously at OpenAI",
            "product": "AI agent for customer support",
            "market": "Growing SMB automation market",
            "risks": ["Depends on OpenAI API pricing", "Easy to copy"],
            "score": 84,
            "score_breakdown": {"team": 30, "product_fit": 20, "traction": 20, "risk": 14},
            "recommendation": "Take a meeting",
            "change_my_mind": ["Loses key founder", "No revenue growth in 6 months"],
            "sources": ["https://example.com", "https://news.ycombinator.com/item?id=123"],
        }
        analysis = Analysis(**data)
        dumped = analysis.model_dump()
        assert dumped["score"] == 84
        assert dumped["recommendation"] == "Take a meeting"
        assert len(dumped["change_my_mind"]) == 2

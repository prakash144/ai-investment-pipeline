import pytest
from pydantic import ValidationError
from analysis.schema import Analysis


class TestAnalysisSchema:
    def test_score_out_of_range_raises(self):
        for bad_score in [150, -10]:
            with pytest.raises(ValidationError):
                Analysis(
                    executive_summary="Good company",
                    team="Strong team",
                    product="Good product",
                    market="Large market",
                    traction_signals="100 HN points",
                    risks=["Competition"],
                    thesis_alignment="Fits thesis well",
                    score=bad_score,
                    score_breakdown={"team": 30, "product_fit": 25, "traction": 25, "risk": 20},
                    confidence="High",
                    recommendation="Pass",
                    change_my_mind=["Need traction"],
                    sources=["https://example.com"],
                )

    def test_invalid_recommendation_raises(self):
        with pytest.raises(ValidationError):
            Analysis(
                executive_summary="Good company",
                team="Strong team",
                product="Good product",
                market="Large market",
                traction_signals="None",
                risks=["Competition"],
                thesis_alignment="Fits",
                score=70,
                score_breakdown={"team": 30, "product_fit": 25, "traction": 25, "risk": 20},
                confidence="High",
                recommendation="Maybe",
                change_my_mind=["Need traction"],
                sources=["https://example.com"],
            )

    def test_invalid_confidence_raises(self):
        with pytest.raises(ValidationError):
            Analysis(
                executive_summary="Summary",
                team="Team",
                product="Product",
                market="Market",
                traction_signals="None",
                risks=["Risk"],
                thesis_alignment="Fits",
                score=70,
                score_breakdown={"team": 20, "product_fit": 20, "traction": 15, "risk": 15},
                confidence="Very High",
                recommendation="Watch",
                change_my_mind=["X"],
                sources=["https://example.com"],
            )

    def test_valid_analysis_round_trips(self):
        data = {
            "executive_summary": "Resend is an email API for developers. Founded by Zeno Rocha (ex-WorkOS) with strong technical credentials and a clear SMB use case.",
            "team": "Founder previously at WorkOS and Liferay Cloud. Strong developer-tools background.",
            "product": "Email API for developers to send transactional emails at scale.",
            "market": "Large email API market with incumbents like SendGrid and AWS SES.",
            "traction_signals": "YC W23, 5.1k GitHub stars on react.email, launched 7 weeks ago with strong signups.",
            "risks": ["Depends on developer adoption", "Competition from incumbents"],
            "thesis_alignment": "Strong fit — developer tools for SMBs with technical founder and clear traction.",
            "score": 84,
            "score_breakdown": {"team": 30, "product_fit": 20, "traction": 20, "risk": 14},
            "confidence": "High",
            "recommendation": "Take a meeting",
            "change_my_mind": ["Loses key founder", "No revenue growth in 6 months"],
            "sources": ["https://example.com", "https://news.ycombinator.com/item?id=123"],
        }
        analysis = Analysis(**data)
        dumped = analysis.model_dump()
        assert dumped["score"] == 84
        assert dumped["recommendation"] == "Take a meeting"
        assert dumped["confidence"] == "High"
        assert dumped["executive_summary"] == data["executive_summary"]
        assert dumped["thesis_alignment"] == data["thesis_alignment"]

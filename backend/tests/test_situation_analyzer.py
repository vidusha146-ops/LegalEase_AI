"""
LegalEase AI - Automated Tests for Intelligent Situation Analyzer & Gap Detection Engine
"""

import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.services.gap_detector import LegalGapDetector
from app.services.situation_analyzer import get_situation_analyzer


@pytest.fixture(scope="session", autouse=True)
def anyio_backend():
    return "asyncio"


def test_gap_detector():
    """Verifies that the Gap Detector identifies missing ingredients and generates follow-ups."""
    # Scenario: Consumer dispute with invoice mentioned, but opposite party address & prior notice missing
    text = "I ordered a mobile phone with invoice INV-9988 on 15th August 2024, but the screen was completely broken."
    report = LegalGapDetector.detect_gaps(text, "CONSUMER_PROTECTION")

    assert report["total_ingredients"] == 4
    assert report["provided_count"] >= 1
    assert report["missing_count"] >= 1
    assert 0.0 < report["completeness_ratio"] < 1.0

    # Ensure follow up questions are generated for missing items
    assert len(report["follow_up_questions"]) == report["missing_count"]
    for q in report["follow_up_questions"]:
        assert "question" in q
        assert "rationale" in q
        assert "severity" in q


def test_situation_analyzer_end_to_end():
    """Verifies end-to-end situation analysis synthesizing ML, RAG, gaps, and scoring."""
    analyzer = get_situation_analyzer()

    narrative = (
        "On 12th August 2024, my landlord disconnected water and electricity to our rented flat "
        "and locked the main gate to forcefully evict us without any court order or notice."
    )
    analysis = analyzer.analyze_situation(
        narrative=narrative,
        incident_date="2024-08-12",
        preferred_language="en",
    )

    assert analysis["predicted_domain"] == "PROPERTY_TENANCY"
    assert analysis["classification_confidence"] > 0.0
    assert len(analysis["applicable_statutes"]) > 0

    # Information Quality Score verification
    iq = analysis["information_quality"]
    assert 0.0 <= iq["score"] <= 1.0
    assert iq["badge"] in ["COMPREHENSIVE_QUALITY", "MODERATE_QUALITY_GAPS", "LOW_QUALITY_INCOMPLETE"]
    assert iq["badge_color"].startswith("#")

    # Components verification
    comp = iq["component_scores"]
    assert 0.0 <= comp["statutory_grounding"] <= 1.0
    assert 0.0 <= comp["factual_completeness"] <= 1.0
    assert 0.0 <= comp["citation_validity"] <= 1.0

    # Recommended actions & emergency helplines
    assert len(analysis["recommended_actions"]) >= 2
    assert "NATIONAL_CONSUMER_HELPLINE" in analysis["emergency_helplines"]
    assert "NALSA_LEGAL_AID_HELPLINE" in analysis["emergency_helplines"]
    assert "Advocates Act, 1961" in analysis["statutory_disclaimer"]


@pytest.mark.asyncio
async def test_analyzer_api_endpoints():
    """Verifies HTTP status and payload formats across all Phase 3 analyzer endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. POST /predict-domain
        pred_resp = await client.post(
            "/api/v1/analyzer/predict-domain",
            json={"narrative": "A cheque of Rs 50,000 bounced with remarks funds insufficient."},
        )
        assert pred_resp.status_code == 200
        pred_data = pred_resp.json()
        assert pred_data["predicted_domain"] == "CHEQUE_BOUNCE_NI_ACT"
        assert len(pred_data["top_domains"]) > 0

        # 2. POST /detect-gaps
        gap_resp = await client.post(
            "/api/v1/analyzer/detect-gaps",
            json={
                "narrative": "A cheque bounced yesterday.",
                "domain": "CHEQUE_BOUNCE_NI_ACT",
            },
        )
        assert gap_resp.status_code == 200
        gap_data = gap_resp.json()
        assert gap_data["domain"] == "CHEQUE_BOUNCE_NI_ACT"
        assert len(gap_data["follow_up_questions"]) > 0

        # 3. POST /analyze-situation
        ana_resp = await client.post(
            "/api/v1/analyzer/analyze-situation",
            json={
                "narrative": "Someone cloned my SIM card and stole Rs 80,000 through unauthorized UPI transfers.",
                "incident_date": "2024-09-15",
                "is_continuing_offense": False,
                "preferred_language": "en",
            },
        )
        assert ana_resp.status_code == 200
        ana_data = ana_resp.json()
        assert ana_data["predicted_domain"] == "CYBER_LAW_IT_ACT"
        assert ana_data["information_quality"]["score"] > 0
        assert len(ana_data["recommended_actions"]) > 0

        # 4. GET /model-metrics
        met_resp = await client.get("/api/v1/analyzer/model-metrics")
        assert met_resp.status_code == 200
        met_data = met_resp.json()
        assert met_data["cv_splits"] == 5
        assert met_data["macro_f1"] > 0
        assert len(met_data["confusion_matrix"]) == 10

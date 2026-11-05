"""
LegalEase AI - Automated Tests for Phase 4:
Explainable Legal Intelligence, Interactive Gap Resolution & Grounded AI Guidance
"""

import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.services.explainability import ExplainableLegalIntelligenceEngine
from app.services.gemini_analyzer import GroundedGeminiAnalyzer


@pytest.fixture(scope="session", autouse=True)
def anyio_backend():
    return "asyncio"


def test_explainable_engine_theft():
    """Verifies that BNS Section 303(1) is decomposed into elements and mapped to facts."""
    narrative = (
        "Someone broke into my locked hostel room and stole my laptop and gold ring "
        "without my consent while I was at lectures."
    )
    res = ExplainableLegalIntelligenceEngine.explain_statute_mapping(
        narrative=narrative,
        act_code="BNS_2023",
        section_number="303(1)",
    )

    assert res["act_code"] == "BNS_2023"
    assert res["section_number"] == "303(1)"
    assert res["total_elements"] == 5
    assert res["fulfilled_elements"] >= 4
    assert res["fulfillment_ratio"] >= 0.80

    # Ensure elements have evidence excerpts
    fulfilled = [e for e in res["elements_breakdown"] if e["fulfilled"]]
    assert len(fulfilled) >= 4
    for elem in fulfilled:
        assert elem["evidence_excerpt"] is not None
        assert len(elem["explanation"]) > 0


def test_explainable_engine_cheque_bounce():
    """Verifies statutory element decomposition for Section 138 of NI Act."""
    narrative = (
        "Client issued a business cheque towards pending invoice debt which bounced with memo "
        "funds insufficient. I dispatched a legal notice giving 15 days, but drawer failed to pay."
    )
    res = ExplainableLegalIntelligenceEngine.explain_statute_mapping(
        narrative=narrative,
        act_code="NI_ACT_1881",
        section_number="138",
    )

    assert res["total_elements"] == 5
    assert res["fulfilled_elements"] >= 4
    assert res["fulfillment_ratio"] >= 0.80


@pytest.mark.asyncio
async def test_grounded_gemini_analyzer_fallback():
    """Verifies deterministic grounded guidance generation when API key is unconfigured."""
    guidance = await GroundedGeminiAnalyzer.generate_grounded_explanation(
        narrative="Cheque of Rs 1,00,000 bounced due to insufficient funds.",
        predicted_domain="CHEQUE_BOUNCE_NI_ACT",
        retrieved_statutes=[
            {
                "act_title": "Negotiable Instruments Act, 1881",
                "section_number": "138",
                "section_title": "Dishonour of cheque for insufficiency of funds",
            }
        ],
        missing_ingredients=[{"name": "Date of Bank Return Memo"}],
        language="en",
    )

    assert guidance["source"] in ["DETERMINISTIC_GROUNDED_TEMPLATE", "GEMINI_1_5_FLASH_STRUCTURED"]
    assert len(guidance["plain_language_summary"]) > 0
    assert len(guidance["citizen_rights"]) >= 3
    assert len(guidance["immediate_steps"]) >= 3
    assert "Advocates Act, 1961" in guidance["statutory_disclaimer"]


@pytest.mark.asyncio
async def test_phase4_api_endpoints():
    """Verifies explain-statute, resolve-gaps, and generate-ai-explanation API endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. POST /explain-statute
        exp_resp = await client.post(
            "/api/v1/analyzer/explain-statute",
            json={
                "narrative": "A man snatched my mother's gold chain in the market and stole it.",
                "act_code": "BNS_2023",
                "section_number": "303(1)",
            },
        )
        assert exp_resp.status_code == 200
        exp_data = exp_resp.json()
        assert exp_data["act_code"] == "BNS_2023"
        assert exp_data["fulfilled_elements"] > 0

        # 2. POST /resolve-gaps (Testing dynamic score elevation)
        resolve_resp = await client.post(
            "/api/v1/analyzer/resolve-gaps",
            json={
                "original_narrative": "My cheque bounced yesterday.",
                "domain": "CHEQUE_BOUNCE_NI_ACT",
                "incident_date": "2024-08-15",
                "answers": {
                    "RETURN_MEMO_DATE": "Dated 15th August 2024",
                    "CHEQUE_NUMBER_AMOUNT": "Cheque No 987654 for Rs 1,50,000 on SBI",
                    "STATUTORY_NOTICE_SERVED": "Sent formal demand notice via speed post on 20th August 2024 giving 15 days",
                    "ENFORCEABLE_DEBT_PROOF": "Tax invoices for building materials supplied",
                },
            },
        )
        assert resolve_resp.status_code == 200
        res_data = resolve_resp.json()
        # Verify score elevation
        assert res_data["elevated_score"] > res_data["previous_score"]
        assert res_data["score_delta"] > 0
        assert res_data["resolved_count"] == 4
        assert res_data["upgraded_badge"] in ["COMPREHENSIVE_QUALITY", "MODERATE_QUALITY_GAPS"]

        # 3. POST /generate-ai-explanation
        ai_resp = await client.post(
            "/api/v1/analyzer/generate-ai-explanation",
            json={
                "narrative": "I received an SMS and Rs 50,000 was debited via unauthorized UPI transfers.",
                "incident_date": "2024-09-01",
                "preferred_language": "en",
            },
        )
        assert ai_resp.status_code == 200
        ai_data = ai_resp.json()
        assert "grounded_ai_guidance" in ai_data
        assert len(ai_data["grounded_ai_guidance"]["citizen_rights"]) >= 3


def test_uncertainty_vague_phrasing_and_ambiguity():
    """Verifies that vague phrasing and missing ingredients trigger uncertainty warnings."""
    from app.services.uncertainty import UncertaintyDetectionEngine

    vague_narrative = "Someone did something bad and I have some financial money issue recently."
    profile = UncertaintyDetectionEngine.analyze_uncertainty(
        narrative=vague_narrative,
        predicted_domain="CONSUMER_PROTECTION",
        classification_confidence=0.18,
        top_domains=[
            {"domain": "CONSUMER_PROTECTION", "confidence": 0.18},
            {"domain": "CYBER_LAW_IT_ACT", "confidence": 0.17},
        ],
        missing_ingredients=[
            {"name": "Proof of Purchase"},
            {"name": "Date of Purchase"},
            {"name": "Opposite Party Details"},
        ],
    )

    assert profile["uncertainty_level"] in ["HIGH_UNCERTAINTY", "MODERATE_UNCERTAINTY"]
    assert profile["uncertainty_score"] > 0.30
    assert len(profile["detected_ambiguities"]) >= 1
    assert "High" in profile["communicated_advisory"] or "Moderate" in profile["communicated_advisory"]


def test_uncertainty_contradiction_future_date():
    """Verifies that an impossible future incident date triggers contradiction detection."""
    from app.services.uncertainty import UncertaintyDetectionEngine

    narrative = "On 2035-12-25, my car was stolen from the parking lot."
    profile = UncertaintyDetectionEngine.analyze_uncertainty(
        narrative=narrative,
        predicted_domain="CRIMINAL_LAW_BNS",
        classification_confidence=0.45,
        top_domains=[{"domain": "CRIMINAL_LAW_BNS", "confidence": 0.45}],
        missing_ingredients=[],
        incident_date="2035-12-25",
    )

    assert len(profile["detected_contradictions"]) >= 1
    assert profile["detected_contradictions"][0]["type"] == "FUTURE_DATE_INVERSION"


def test_uncertainty_unsupported_assumptions():
    """Verifies that assuming immediate police arrest for cheque bounce is flagged."""
    from app.services.uncertainty import UncertaintyDetectionEngine

    narrative = "My client's cheque bounced, I want police to arrest him immediately and put him in jail."
    profile = UncertaintyDetectionEngine.analyze_uncertainty(
        narrative=narrative,
        predicted_domain="CHEQUE_BOUNCE_NI_ACT",
        classification_confidence=0.50,
        top_domains=[{"domain": "CHEQUE_BOUNCE_NI_ACT", "confidence": 0.50}],
        missing_ingredients=[],
    )

    assert len(profile["unsupported_assumptions"]) >= 1
    assert "Section 138" in profile["unsupported_assumptions"][0]["correction"]

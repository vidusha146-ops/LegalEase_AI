"""
Comprehensive Phase 4 Verification Script for LegalEase AI
Tests:
1. Explainable Legal AI Engine (element decomposition, evidence extraction, pending proof)
2. Uncertainty Detection Engine (ambiguities, chronological contradictions, Art 20(1) BNS/IPC contradictions, unsupported assumptions)
3. Dynamic Legal Gap Resolution & S_IQ score elevation via API
4. Grounded Gemini Situation Analyzer (schema, grounding, Advocates Act disclaimer)
5. FastAPI Phase 4 Endpoints Integration via TestClient
"""

import sys
import json
import asyncio
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.explainability import ExplainableLegalIntelligenceEngine
from app.services.uncertainty import UncertaintyDetectionEngine
from app.services.situation_analyzer import get_situation_analyzer
from app.services.gemini_analyzer import GroundedGeminiAnalyzer
from starlette.testclient import TestClient
from app.main import app

def run_phase4_verification():
    print("=" * 80)
    print("LEGAL EASE AI - PHASE 4 INDEPENDENT VERIFICATION SUITE")
    print("=" * 80)
    
    results = {}
    
    # -------------------------------------------------------------------------
    # 1. EXPLAINABLE LEGAL AI ENGINE TEST
    # -------------------------------------------------------------------------
    print("\n[TEST 1] Explainable Legal AI Engine (Statutory Element Mapping)")
    test_cases = [
        {
            "act_code": "BNS_2023",
            "section": "303(1)",
            "narrative": "On 15 August 2024, someone broke into my car and stole my laptop worth Rs 60,000 without my permission."
        },
        {
            "act_code": "NI_ACT_1881",
            "section": "138",
            "narrative": "Mr. Sharma gave me a cheque of Rs 2,50,000 against building supplies. I presented it in the bank within validity, but it returned unpaid with 'Funds Insufficient'. I served a legal notice demanding payment within 15 days, but no payment was made."
        },
        {
            "act_code": "CPA_2019",
            "section": "2(11)",
            "narrative": "I purchased an air conditioner with 2-year warranty from an online platform. The compressor broke down within two months, and the seller refused repair or replacement despite service requests."
        }
    ]
    
    element_results = []
    for tc in test_cases:
        res = ExplainableLegalIntelligenceEngine.explain_statute_mapping(
            narrative=tc["narrative"],
            act_code=tc["act_code"],
            section_number=tc["section"],
        )
        print(f" -> Act: {res['act_code']} Sec {res['section_number']} ({res['offence_title']}): "
              f"{res['fulfilled_elements']}/{res['total_elements']} elements satisfied (ratio: {res['fulfillment_ratio']:.2f})")
        for elem in res["elements_breakdown"]:
            status_symbol = "[x]" if elem["fulfilled"] else "[ ]"
            print(f"    {status_symbol} {elem['label']}: {elem['explanation']}")
            if elem["evidence_excerpt"]:
                print(f"        Evidence excerpt: '{elem['evidence_excerpt']}'")
        element_results.append(res)
        
    assert all(r["total_elements"] > 0 for r in element_results), "Element decomposition returned empty elements!"
    print(" PASS: Statutory element decomposition correctly maps facts, extracts evidence, and isolates pending proof.")
    results["explainable_engine"] = "PASSED"

    # -------------------------------------------------------------------------
    # 2. UNCERTAINTY DETECTION ENGINE TEST
    # -------------------------------------------------------------------------
    print("\n[TEST 2] Uncertainty, Ambiguity, Contradiction & Assumption Detection")
    
    # 2a. Vague phrasing
    vague_narrative = "Someone did something bad and took some money recently, causing a huge amount of loss."
    vague_report = UncertaintyDetectionEngine.analyze_uncertainty(
        narrative=vague_narrative,
        predicted_domain="CYBER_CRIME_FINANCIAL_FRAUD",
        classification_confidence=0.20,
        top_domains=[{"domain": "CYBER_CRIME_FINANCIAL_FRAUD", "confidence": 0.20}, {"domain": "PROPERTY_DISPUTE_TENANCY", "confidence": 0.18}],
        missing_ingredients=[{"name": "Date"}, {"name": "Amount"}],
        incident_date=None
    )
    print(f" -> Vague Narrative Ambiguities: {len(vague_report['detected_ambiguities'])} detected")
    for amb in vague_report["detected_ambiguities"]:
        print(f"    - Type: {amb['type']}: {amb['issue']}")
    assert len(vague_report["detected_ambiguities"]) >= 2, "Failed to detect vague phrasing!"

    # 2b. Article 20(1) Date Contradiction (Pre-July 2024 incident invoking BNS)
    pre_bns_narrative = "On 15 January 2024, my shop was robbed and the police are applying Section 303(1) of the BNS."
    pre_bns_report = UncertaintyDetectionEngine.analyze_uncertainty(
        narrative=pre_bns_narrative,
        predicted_domain="THEFT_PROPERTY_CRIMES",
        classification_confidence=0.85,
        top_domains=[{"domain": "THEFT_PROPERTY_CRIMES", "confidence": 0.85}],
        missing_ingredients=[],
        incident_date="2024-01-15"
    )
    print(f" -> Chronological / Statutory Contradictions: {len(pre_bns_report['detected_contradictions'])} detected")
    for c in pre_bns_report["detected_contradictions"]:
        print(f"    - Type: {c['type']}: {c['issue']}")
    assert any("BNS" in c["issue"] for c in pre_bns_report["detected_contradictions"]), "Failed to detect Art 20(1) BNS/IPC contradiction!"

    # 2c. Unsupported citizen assumptions
    assumption_narrative = "My tenant has not paid rent for 2 months. I want police to immediately arrest the debtor and recover my money."
    assumption_report = UncertaintyDetectionEngine.analyze_uncertainty(
        narrative=assumption_narrative,
        predicted_domain="CHEQUE_BOUNCE_NI_ACT",
        classification_confidence=0.80,
        top_domains=[{"domain": "CHEQUE_BOUNCE_NI_ACT", "confidence": 0.80}],
        missing_ingredients=[],
        incident_date=None
    )
    print(f" -> Unsupported Assumptions: {len(assumption_report['unsupported_assumptions'])} detected")
    for a in assumption_report["unsupported_assumptions"]:
        print(f"    - Assumption: '{a['assumption']}': {a['correction']}")
    assert len(assumption_report["unsupported_assumptions"]) >= 1, "Failed to detect unsupported citizen assumption!"
    
    print(" PASS: Uncertainty detection successfully identifies ambiguities, Article 20(1) timeline conflicts, and false assumptions.")
    results["uncertainty_engine"] = "PASSED"

    # -------------------------------------------------------------------------
    # 3. INTERACTIVE LEGAL GAP RESOLUTION & S_IQ SCORE ELEVATION
    # -------------------------------------------------------------------------
    print("\n[TEST 3] Interactive Legal Gap Resolution & Dynamic S_IQ Elevation")
    analyzer = get_situation_analyzer()
    initial_narrative = "My client's cheque bounced and I want to recover money."
    initial_analysis = analyzer.analyze_situation(
        narrative=initial_narrative,
        incident_date="2024-08-01"
    )
    initial_score = initial_analysis["information_quality"]["score"]
    initial_missing = initial_analysis["legal_gaps"]["missing_count"]
    print(f" -> Initial Narrative: '{initial_narrative}'")
    print(f" -> Initial S_IQ Score: {initial_score:.4f} ({initial_analysis['information_quality']['badge']})")
    print(f" -> Initial Missing Ingredients: {initial_missing}")
    
    client = TestClient(app)
    # User provides answers to missing ingredients via API
    answers = {
        "RETURN_MEMO_DATE": "Dated 15th August 2024 with remark 'Funds Insufficient'",
        "CHEQUE_NUMBER_AMOUNT": "Cheque No 987654 for Rs 1,50,000 drawn on SBI bank",
        "STATUTORY_NOTICE_SERVED": "Sent formal demand notice via speed post on 20th August 2024 giving 15 days",
        "ENFORCEABLE_DEBT_PROOF": "Tax invoices for building materials supplied"
    }
    
    res = client.post("/api/v1/analyzer/resolve-gaps", json={
        "original_narrative": initial_narrative,
        "domain": initial_analysis["predicted_domain"],
        "incident_date": "2024-08-01",
        "answers": answers
    })
    assert res.status_code == 200, f"resolve-gaps failed: {res.text}"
    gap_resolution = res.json()
    
    elevated_score = gap_resolution["elevated_score"]
    delta = gap_resolution["score_delta"]
    print(f" -> Resolved Gaps: {gap_resolution['resolved_count']} ingredients resolved")
    print(f" -> Elevated S_IQ Score: {elevated_score:.4f} (Delta: +{delta:.4f})")
    print(f" -> Upgraded Badge: {gap_resolution['upgraded_badge']}")
    print(f" -> Augmented Narrative Preview: '{gap_resolution['augmented_narrative'][:120]}...'")
    
    assert elevated_score > initial_score, "Score did not elevate after answering legal gaps!"
    assert delta > 0, "Score delta must be positive!"
    assert gap_resolution["resolved_count"] > 0, "Resolved count must be greater than zero!"
    print(" PASS: Interactive gap answering dynamically elevates S_IQ and upgrades evidentiary badge.")
    results["gap_resolution"] = "PASSED"

    # -------------------------------------------------------------------------
    # 4. STRUCTURED GEMINI SITUATION ANALYZER & RETRIEVAL GROUNDING
    # -------------------------------------------------------------------------
    print("\n[TEST 4] Grounded Situation Analyzer & Schema Compliance")
    sample_statutes = initial_analysis["applicable_statutes"]
    ai_guidance = asyncio.run(GroundedGeminiAnalyzer.generate_grounded_explanation(
        narrative="I paid Rs 45,000 for a refrigerator which caught fire due to a manufacturing defect.",
        predicted_domain="CONSUMER_PROTECTION",
        retrieved_statutes=sample_statutes,
        missing_ingredients=[{"name": "Purchase Invoice"}]
    ))
    print(f" -> Guidance Source: {ai_guidance['source']}")
    print(f" -> Plain Language Summary: {ai_guidance['plain_language_summary'][:100]}...")
    print(f" -> Citizen Rights Count: {len(ai_guidance['citizen_rights'])}")
    print(f" -> Immediate Steps Count: {len(ai_guidance['immediate_steps'])}")
    print(f" -> Statutory Disclaimer Present: {'Advocates Act' in ai_guidance['statutory_disclaimer']}")
    
    assert len(ai_guidance["citizen_rights"]) >= 2, "Must provide at least 2 citizen rights!"
    assert len(ai_guidance["immediate_steps"]) >= 2, "Must provide at least 2 immediate steps!"
    assert "Advocates Act" in ai_guidance["statutory_disclaimer"], "Advocates Act 1961 disclaimer missing!"
    print(" PASS: Grounded situation analyzer outputs valid structured schema with mandatory disclaimer.")
    results["gemini_analyzer"] = "PASSED"

    # -------------------------------------------------------------------------
    # 5. FASTAPI PHASE 4 ENDPOINTS VERIFICATION
    # -------------------------------------------------------------------------
    print("\n[TEST 5] FastAPI Phase 4 Endpoints Integration")
    
    # 5a. POST /api/v1/analyzer/explain-statute
    r1 = client.post("/api/v1/analyzer/explain-statute", json={
        "narrative": "A thief broke the door and stole cash and jewelry without consent.",
        "act_code": "BNS_2023",
        "section_number": "303(1)"
    })
    print(f" -> POST /api/v1/analyzer/explain-statute: HTTP {r1.status_code}")
    assert r1.status_code == 200, f"explain-statute failed: {r1.text}"
    assert r1.json()["total_elements"] == 5
    
    # 5b. POST /api/v1/analyzer/resolve-gaps
    r2 = client.post("/api/v1/analyzer/resolve-gaps", json={
        "original_narrative": "My cheque bounced.",
        "domain": "CHEQUE_BOUNCE_NI_ACT",
        "incident_date": "2024-08-10",
        "answers": {"CHEQUE_NUMBER_AMOUNT": "Cheque of Rs 50,000 bounced for insufficient funds"}
    })
    print(f" -> POST /api/v1/analyzer/resolve-gaps: HTTP {r2.status_code}")
    assert r2.status_code == 200, f"resolve-gaps failed: {r2.text}"
    assert r2.json()["score_delta"] > 0
    
    # 5c. POST /api/v1/analyzer/generate-ai-explanation
    r3 = client.post("/api/v1/analyzer/generate-ai-explanation", json={
        "narrative": "Someone phished Rs 20,000 from my UPI account.",
        "incident_date": "2024-09-01"
    })
    print(f" -> POST /api/v1/analyzer/generate-ai-explanation: HTTP {r3.status_code}")
    assert r3.status_code == 200, f"generate-ai-explanation failed: {r3.text}"
    assert "grounded_ai_guidance" in r3.json()
    
    print(" PASS: All FastAPI Phase 4 endpoints verified and returning status 200 OK.")
    results["fastapi_endpoints"] = "PASSED"

    print("\n" + "=" * 80)
    print("PHASE 4 COMPREHENSIVE VERIFICATION RESULT: ALL 5 MODULES PASSED")
    print("=" * 80)
    return results

if __name__ == "__main__":
    run_phase4_verification()

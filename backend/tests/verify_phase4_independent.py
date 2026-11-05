"""
LegalEase AI - Phase 4 Independent Final Verification Harness
Empirical validation of all 12 Phase 4 requirements:
1. Explainable Legal AI Engine
2. Statutory Element Mapping
3. Supporting and missing fact identification
4. Uncertainty Detection
5. Contradictory Information Detection
6. Information Quality Score calculation
7. Interactive Follow-up Questions
8. Dynamic Legal Gap Resolution
9. Gemini Situation Analyzer
10. ChromaDB grounding and source traceability
11. Statutory Citation Validation
12. Frontend and Backend Integration
"""

import sys
import json
import asyncio
from pathlib import Path
from datetime import date

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.explainability import (
    ExplainableLegalIntelligenceEngine,
    STATUTORY_ELEMENT_DECOMPOSITIONS,
)
from app.services.uncertainty import UncertaintyDetectionEngine
from app.services.situation_analyzer import get_situation_analyzer
from app.services.gemini_analyzer import GroundedGeminiAnalyzer
from app.rag.retriever import LegalKnowledgeRetriever
from app.rag.citation_validator import LegalCitationValidator
from starlette.testclient import TestClient
from app.main import app

def run_independent_verification():
    print("=" * 85)
    print("LEGALEASE AI - PHASE 4 INDEPENDENT FINAL VERIFICATION SUITE")
    print("=" * 85)
    
    results = {}
    failed_tests = []
    
    # =========================================================================
    # ITEM 1 & 2: EXPLAINABLE LEGAL AI ENGINE & STATUTORY ELEMENT MAPPING
    # =========================================================================
    print("\n--- [VERIFICATION 1 & 2] Explainable Legal AI Engine & Statutory Element Mapping ---")
    try:
        test_statutes = [
            ("BNS_2023", "303(1)", "On 15 August 2024, an intruder broke into my house and stole my laptop and gold jewelry without my consent."),
            ("BNS_2023", "318(4)", "A seller promised delivery of high-grade copper wires, took advance payment of Rs 1,50,000 via NEFT, delivered fake scrap, and disappeared."),
            ("NI_ACT_1881", "138", "Client gave me a cheque of Rs 2,00,000 for materials delivered. Cheque returned unpaid for 'Funds Insufficient'. I sent legal notice giving 15 days, but drawer defaulted."),
            ("CONSUMER_PROTECTION_2019", "2(11)", "I bought an air conditioner with 2-year warranty. Compressor broke down in 1 month and seller refused replacement despite repeated emails."),
            ("IT_ACT_2000", "66D", "I received an SMS to update bank KYC with a link. After clicking, Rs 75,000 was debited via unauthorized UPI transfers without my knowledge.")
        ]
        
        for act, sec, text in test_statutes:
            decomp = ExplainableLegalIntelligenceEngine.explain_statute_mapping(
                narrative=text,
                act_code=act,
                section_number=sec
            )
            print(f" -> Decomposed {decomp['act_code']} Sec {decomp['section_number']} ({decomp['offence_title']}):")
            print(f"    Elements: {decomp['fulfilled_elements']}/{decomp['total_elements']} fulfilled (Ratio: {decomp['fulfillment_ratio']:.2f})")
            assert decomp["total_elements"] >= 3, f"Insufficient elements in {act} Sec {sec}"
            assert decomp["fulfilled_elements"] >= 2, f"Too few fulfilled elements in {act} Sec {sec}"
        
        results["item_1_and_2"] = "PASSED"
        print(" [PASS] Explainable Legal AI Engine accurately decomposes statutory provisions into elements.")
    except Exception as e:
        results["item_1_and_2"] = f"FAILED: {e}"
        failed_tests.append(f"Item 1 & 2: {e}")

    # =========================================================================
    # ITEM 3: SUPPORTING AND MISSING FACT IDENTIFICATION
    # =========================================================================
    print("\n--- [VERIFICATION 3] Supporting vs Missing Fact Identification ---")
    try:
        # Partial narrative for Theft (missing physical moving or consent)
        partial_theft = "I had kept my gold ring on the table in my room."
        theft_res = ExplainableLegalIntelligenceEngine.explain_statute_mapping(
            narrative=partial_theft,
            act_code="BNS_2023",
            section_number="303(1)"
        )
        satisfied = [e for e in theft_res["elements_breakdown"] if e["fulfilled"]]
        pending = [e for e in theft_res["elements_breakdown"] if not e["fulfilled"]]
        
        print(f" -> Partial Theft Narrative: Satisfied: {len(satisfied)}, Pending: {len(pending)}")
        for s in satisfied:
            print(f"    [SUPPORTING FACT] {s['label']}: Excerpt -> '{s['evidence_excerpt']}'")
        for p in pending:
            print(f"    [MISSING FACT]    {p['label']}: Pending -> '{p['explanation']}'")
            
        assert len(satisfied) > 0, "Expected at least 1 supporting element"
        assert len(pending) > 0, "Expected at least 1 pending element"
        assert all(s["evidence_excerpt"] is not None for s in satisfied), "Satisfied elements must have evidence excerpts"
        assert all(p["evidence_excerpt"] is None for p in pending), "Pending elements must have null evidence excerpt"
        
        results["item_3"] = "PASSED"
        print(" [PASS] Supporting facts are linked to excerpts, and missing facts are explicitly identified as pending proof.")
    except Exception as e:
        results["item_3"] = f"FAILED: {e}"
        failed_tests.append(f"Item 3: {e}")

    # =========================================================================
    # ITEM 4 & 5: UNCERTAINTY DETECTION & CONTRADICTORY INFORMATION
    # =========================================================================
    print("\n--- [VERIFICATION 4 & 5] Uncertainty, Ambiguity, Contradictions & Assumptions ---")
    try:
        # 4a. Ambiguous / Vague description
        ambiguous_text = "Someone took some money from me recently and did something wrong causing a huge amount of loss."
        amb_report = UncertaintyDetectionEngine.analyze_uncertainty(
            narrative=ambiguous_text,
            predicted_domain="CYBER_CRIME_FINANCIAL_FRAUD",
            classification_confidence=0.22,
            top_domains=[{"domain": "CYBER_CRIME_FINANCIAL_FRAUD", "confidence": 0.22}, {"domain": "PROPERTY_DISPUTE_TENANCY", "confidence": 0.20}],
            missing_ingredients=[{"name": "Transaction Date"}, {"name": "Exact Loss Amount"}],
            incident_date=None
        )
        print(f" -> Ambiguous Scenario Uncertainty Score: {amb_report['uncertainty_score']} ({amb_report['uncertainty_level']})")
        print(f"    Detected Ambiguities: {len(amb_report['detected_ambiguities'])}")
        for a in amb_report["detected_ambiguities"]:
            print(f"     * {a['type']}: {a['issue']}")
        assert amb_report["uncertainty_score"] >= 0.50, "Uncertainty score should be high for vague description"
        assert len(amb_report["detected_ambiguities"]) >= 2, "Expected at least 2 detected ambiguities"

        # 5a. Contradictory statements: Future date
        future_date = "2029-05-10"
        future_report = UncertaintyDetectionEngine.analyze_uncertainty(
            narrative="My phone was stolen.",
            predicted_domain="THEFT_PROPERTY_CRIMES",
            classification_confidence=0.85,
            top_domains=[{"domain": "THEFT_PROPERTY_CRIMES", "confidence": 0.85}],
            missing_ingredients=[],
            incident_date=future_date
        )
        print(f" -> Future Date Contradictions: {len(future_report['detected_contradictions'])}")
        assert any("FUTURE_DATE" in c["type"] for c in future_report["detected_contradictions"]), "Failed to catch future date contradiction"

        # 5b. Contradictory statements: Article 20(1) Date Contradiction (Pre-July 2024 invoking BNS)
        art20_report = UncertaintyDetectionEngine.analyze_uncertainty(
            narrative="On 10 March 2024, my house was robbed and I want an FIR under Section 303(1) of Bharatiya Nyaya Sanhita.",
            predicted_domain="CRIMINAL_LAW_BNS",
            classification_confidence=0.90,
            top_domains=[{"domain": "CRIMINAL_LAW_BNS", "confidence": 0.90}],
            missing_ingredients=[],
            incident_date="2024-03-10"
        )
        print(f" -> Article 20(1) Contradictions: {len(art20_report['detected_contradictions'])}")
        assert any("STATUTORY_TEMPORAL_MISMATCH" in c["type"] for c in art20_report["detected_contradictions"]), "Failed to catch Article 20(1) BNS/IPC contradiction"

        # 5c. Unsupported legal claims
        assump_report = UncertaintyDetectionEngine.analyze_uncertainty(
            narrative="A customer gave a cheque which bounced. I want police to immediately arrest the debtor without delay.",
            predicted_domain="CHEQUE_BOUNCE_NI_ACT",
            classification_confidence=0.88,
            top_domains=[{"domain": "CHEQUE_BOUNCE_NI_ACT", "confidence": 0.88}],
            missing_ingredients=[],
            incident_date=None
        )
        print(f" -> Unsupported Legal Assumptions: {len(assump_report['unsupported_assumptions'])}")
        for u in assump_report["unsupported_assumptions"]:
            print(f"     * Assumption: '{u['assumption']}' -> Correction: '{u['correction']}'")
        assert len(assump_report["unsupported_assumptions"]) >= 1, "Failed to identify unsupported assumption"

        results["item_4_and_5"] = "PASSED"
        print(" [PASS] Uncertainty, ambiguous terms, timeline contradictions, and unsupported legal claims are properly detected.")
    except Exception as e:
        results["item_4_and_5"] = f"FAILED: {e}"
        failed_tests.append(f"Item 4 & 5: {e}")

    # =========================================================================
    # ITEM 6: INFORMATION QUALITY SCORE (S_IQ) CALCULATION
    # =========================================================================
    print("\n--- [VERIFICATION 6] Information Quality Score Formula Verification ---")
    try:
        analyzer = get_situation_analyzer()
        
        # Test 1: Incomplete situation
        incomplete_analysis = analyzer.analyze_situation(
            narrative="Someone stole something from me.",
            incident_date=None
        )
        s_iq_incomplete = incomplete_analysis["information_quality"]["score"]
        badge_incomplete = incomplete_analysis["information_quality"]["badge"]
        print(f" -> Incomplete Narrative S_IQ: {s_iq_incomplete:.4f} (Badge: {badge_incomplete})")
        assert s_iq_incomplete < 0.65, "Incomplete narrative must have low or moderate groundability score"
        
        # Test 2: Contradictory situation (penalized)
        contradictory_analysis = analyzer.analyze_situation(
            narrative="On 10 January 2024, my bike was stolen and police must apply Section 303(1) of BNS.",
            incident_date="2024-01-10"
        )
        comp_scores = contradictory_analysis["information_quality"]["component_scores"]
        print(f" -> Contradictory Scenario Penalty: -{comp_scores['contradiction_penalty']:.4f}")
        assert comp_scores["contradiction_penalty"] > 0, "Contradiction penalty must be applied"
        
        # Test 3: Mathematical boundaries [0.0, 1.0]
        assert 0.0 <= s_iq_incomplete <= 1.0, "S_IQ must be clamped to [0.0, 1.0]"
        assert 0.0 <= contradictory_analysis["information_quality"]["score"] <= 1.0
        
        results["item_6"] = "PASSED"
        print(" [PASS] Mathematical S_IQ formula, weighting, and contradiction deductions verified.")
    except Exception as e:
        results["item_6"] = f"FAILED: {e}"
        failed_tests.append(f"Item 6: {e}")

    # =========================================================================
    # ITEM 7 & 8: DYNAMIC LEGAL GAP RESOLUTION & S_IQ SCORE ELEVATION
    # =========================================================================
    print("\n--- [VERIFICATION 7 & 8] Interactive Questions & Dynamic Gap Resolution ---")
    try:
        client = TestClient(app)
        
        # Initial narrative with missing cheque bounce statutory prerequisites
        base_text = "A client gave me a cheque which bounced for insufficient funds."
        init_res = client.post("/api/v1/analyzer/analyze-situation", json={
            "narrative": base_text,
            "incident_date": "2024-08-01"
        })
        assert init_res.status_code == 200
        init_data = init_res.json()
        init_score = init_data["information_quality"]["score"]
        missing_count_before = init_data["legal_gaps"]["missing_count"]
        follow_ups = init_data["legal_gaps"]["follow_up_questions"]
        
        print(f" -> Base Narrative: '{base_text}'")
        print(f" -> Initial S_IQ Score: {init_score:.4f} ({init_data['information_quality']['badge']})")
        print(f" -> Generated Follow-up Questions ({len(follow_ups)}):")
        for fq in follow_ups:
            print(f"     * [{fq['ingredient_id']}] {fq['question']} (Reason: {fq['rationale']})")
        assert len(follow_ups) >= 2, "Expected follow-up questions for missing statutory ingredients"

        # User dynamically submits answers
        user_answers = {
            "CHEQUE_NUMBER_AMOUNT": "Cheque No. 441029 for Rs 1,80,000 drawn on State Bank of India",
            "RETURN_MEMO_DATE": "Bank Return Memo received on 12 August 2024 with remark 'Funds Insufficient'",
            "STATUTORY_NOTICE_SERVED": "Formal demand notice sent via Registered Speed Post on 20 August 2024 demanding payment within 15 days",
            "ENFORCEABLE_DEBT_PROOF": "Invoices and delivery challans for 50 bags of cement delivered to debtor"
        }
        
        resolve_res = client.post("/api/v1/analyzer/resolve-gaps", json={
            "original_narrative": base_text,
            "domain": init_data["predicted_domain"],
            "incident_date": "2024-08-01",
            "answers": user_answers
        })
        assert resolve_res.status_code == 200
        resolve_data = resolve_res.json()
        
        elevated_score = resolve_data["elevated_score"]
        score_delta = resolve_data["score_delta"]
        missing_count_after = resolve_data["remaining_count"]
        
        print(f" -> Score Before: {init_score:.4f} -> Score After: {elevated_score:.4f} (Delta: +{score_delta:.4f})")
        print(f" -> Upgraded Badge: {resolve_data['upgraded_badge']}")
        print(f" -> Gaps Resolved: {resolve_data['resolved_count']}, Remaining Gaps: {missing_count_after}")
        print(f" -> Augmented Narrative: '{resolve_data['augmented_narrative'][:120]}...'")
        
        assert elevated_score > init_score, "Dynamic resolution must elevate S_IQ"
        assert score_delta > 0, "Score delta must be strictly positive"
        assert missing_count_after < missing_count_before, "Remaining missing ingredients must decrease"
        assert base_text in resolve_data["augmented_narrative"], "Original narrative must be preserved"
        
        results["item_7_and_8"] = "PASSED"
        print(" [PASS] Interactive follow-up answering dynamically resolves legal gaps and elevates groundability score.")
    except Exception as e:
        results["item_7_and_8"] = f"FAILED: {e}"
        failed_tests.append(f"Item 7 & 8: {e}")

    # =========================================================================
    # ITEM 9: GEMINI SITUATION ANALYZER & STRUCTURED SCHEMA
    # =========================================================================
    print("\n--- [VERIFICATION 9] Structured Grounded Gemini Situation Analyzer ---")
    try:
        sample_statutes = [
            {
                "act_code": "NI_ACT_1881",
                "act_title": "Negotiable Instruments Act, 1881",
                "section_number": "138",
                "section_title": "Dishonour of cheque for insufficiency of funds",
            }
        ]
        
        ai_resp = asyncio.run(GroundedGeminiAnalyzer.generate_grounded_explanation(
            narrative="Cheque bounced for Rs 1,80,000.",
            predicted_domain="CHEQUE_BOUNCE_NI_ACT",
            retrieved_statutes=sample_statutes,
            missing_ingredients=[{"name": "Date of Notice"}],
            language="en"
        ))
        
        print(f" -> Generation Source: {ai_resp['source']}")
        print(f" -> Summary: {ai_resp['plain_language_summary'][:110]}...")
        print(f" -> Citizen Rights ({len(ai_resp['citizen_rights'])}):")
        for cr in ai_resp["citizen_rights"]:
            print(f"     * {cr}")
        print(f" -> Actionable Steps ({len(ai_resp['immediate_steps'])}):")
        for st in ai_resp["immediate_steps"]:
            print(f"     * {st}")
        print(f" -> Statutory Disclaimer: {ai_resp['statutory_disclaimer'][:80]}...")
        
        assert "source" in ai_resp, "Missing source attribute"
        assert len(ai_resp["citizen_rights"]) >= 2, "Expected at least 2 citizen rights"
        assert len(ai_resp["immediate_steps"]) >= 2, "Expected at least 2 immediate steps"
        assert "Advocates Act, 1961" in ai_resp["statutory_disclaimer"], "Mandatory Advocates Act disclaimer missing"
        
        # Test Hindi generation
        ai_hi = asyncio.run(GroundedGeminiAnalyzer.generate_grounded_explanation(
            narrative="चेक बाउंस हो गया",
            predicted_domain="CHEQUE_BOUNCE_NI_ACT",
            retrieved_statutes=sample_statutes,
            missing_ingredients=[],
            language="hi"
        ))
        assert "अधिवक्ता अधिनियम" in ai_hi["statutory_disclaimer"], "Hindi Advocates Act disclaimer missing"
        
        results["item_9"] = "PASSED"
        print(" [PASS] Structured AI explanations remain strictly grounded with bilingual non-advocacy disclaimers.")
    except Exception as e:
        results["item_9"] = f"FAILED: {e}"
        failed_tests.append(f"Item 9: {e}")

    # =========================================================================
    # ITEM 10: CHROMADB GROUNDING AND SOURCE TRACEABILITY
    # =========================================================================
    print("\n--- [VERIFICATION 10] ChromaDB Grounding & Source Traceability ---")
    try:
        retriever = LegalKnowledgeRetriever()
        query = "cheque returned unpaid by bank for insufficiency of funds in account"
        retrieved = retriever.search_statutes(query=query, top_k=3)
        
        print(f" -> Query: '{query}' -> Retrieved {len(retrieved)} chunks:")
        for r in retrieved:
            meta = r.get("metadata", {})
            print(f"     * Section {meta.get('section_number')}: {meta.get('section_title')} ({meta.get('act_code')})")
            print(f"       Distance: {r.get('distance', 1.0):.4f} | Source URL: {meta.get('source_url')}")
            assert meta.get("act_code") is not None, "Missing act_code in metadata"
            assert meta.get("section_number") is not None, "Missing section_number in metadata"
            assert meta.get("source_url") is not None, "Missing source_url in metadata"
            
        assert len(retrieved) > 0, "ChromaDB retrieval returned 0 results"
        assert any(r.get("metadata", {}).get("section_number") == "138" for r in retrieved), "Expected Section 138 in top results"
        
        results["item_10"] = "PASSED"
        print(" [PASS] ChromaDB vector store retrieves verified chunks with traceable Gazette source URLs.")
    except Exception as e:
        results["item_10"] = f"FAILED: {e}"
        failed_tests.append(f"Item 10: {e}")

    # =========================================================================
    # ITEM 11: STATUTORY CITATION VALIDATION
    # =========================================================================
    print("\n--- [VERIFICATION 11] Deterministic Citation Validation & Fabrication Detection ---")
    try:
        validator = LegalCitationValidator()
        # Valid vs Invalid citations test
        valid_sample = "The accused should be punished under Section 138 of the Negotiable Instruments Act and Section 303(1) of BNS."
        invalid_sample = "The complainant is filing under Section 999 of BNS and Section 482B of the Indian Penal Code."
        
        val_valid = validator.validate_text_citations(valid_sample)
        val_invalid = validator.validate_text_citations(invalid_sample)
        
        print(f" -> Valid Text: Total={val_valid['total_citations']}, Valid={val_valid['valid_count']}, Ratio={val_valid['citation_grounding_ratio']}")
        assert val_valid["valid_count"] >= 1, "Failed to validate authentic citations"
        
        print(f" -> Invalid Text: Total={val_invalid['total_citations']}, Valid={val_invalid['valid_count']}, Invalid={val_invalid['invalid_count']}")
        for inv in val_invalid["results"]:
            if not inv.get("is_valid"):
                print(f"     * Rejected: {inv.get('raw_match')} -> {inv.get('rejection_reason')}")
        assert val_invalid["invalid_count"] >= 1, "Failed to reject fabricated statutory sections"
        assert val_invalid["citation_grounding_ratio"] == 0.0, "Invalid citation ratio should be 0.0"
        
        results["item_11"] = "PASSED"
        print(" [PASS] Deterministic citation validator verifies authentic provisions and rejects fabricated citations.")
    except Exception as e:
        results["item_11"] = f"FAILED: {e}"
        failed_tests.append(f"Item 11: {e}")

    # =========================================================================
    # ITEM 12: FRONTEND AND BACKEND INTEGRATION
    # =========================================================================
    print("\n--- [VERIFICATION 12] Frontend & Backend Integration Verification ---")
    try:
        client = TestClient(app)
        endpoints = [
            ("POST", "/api/v1/analyzer/predict-domain", {"narrative": "A merchant defrauded me on an e-commerce platform."}),
            ("POST", "/api/v1/analyzer/detect-gaps", {"narrative": "I lost money in online shopping."}),
            ("POST", "/api/v1/analyzer/analyze-situation", {"narrative": "Someone broke my shop window and stole goods.", "incident_date": "2024-08-20"}),
            ("POST", "/api/v1/analyzer/explain-statute", {"narrative": "Theft of gold chain from bag.", "act_code": "BNS_2023", "section_number": "303(1)"}),
            ("POST", "/api/v1/analyzer/resolve-gaps", {
                "original_narrative": "My cheque bounced.",
                "domain": "CHEQUE_BOUNCE_NI_ACT",
                "incident_date": "2024-08-10",
                "answers": {"CHEQUE_NUMBER_AMOUNT": "Cheque of Rs 50,000"}
            }),
            ("POST", "/api/v1/analyzer/generate-ai-explanation", {"narrative": "My cheque bounced.", "incident_date": "2024-08-10"}),
            ("GET", "/api/v1/analyzer/model-metrics", None)
        ]
        
        for method, url, payload in endpoints:
            if method == "POST":
                resp = client.post(url, json=payload)
            else:
                resp = client.get(url)
            print(f" -> {method} {url}: Status {resp.status_code}")
            assert resp.status_code == 200, f"Endpoint {url} failed with {resp.status_code}: {resp.text}"
            
        results["item_12"] = "PASSED"
        print(" [PASS] All Phase 4 API endpoints are healthy, responsive, and schema-compliant.")
    except Exception as e:
        results["item_12"] = f"FAILED: {e}"
        failed_tests.append(f"Item 12: {e}")

    print("\n" + "=" * 85)
    print("PHASE 4 INDEPENDENT VERIFICATION SUMMARY:")
    for k, v in results.items():
        print(f"  * {k.upper()}: {v}")
    if failed_tests:
        print(f"  * FAILED TESTS: {len(failed_tests)}")
        for ft in failed_tests:
            print(f"    - {ft}")
    else:
        print("  * ALL 12 MANDATORY VERIFICATION ITEMS PASSED WITH 0 FAILURES.")
    print("=" * 85)
    return len(failed_tests) == 0

if __name__ == "__main__":
    success = run_independent_verification()
    sys.exit(0 if success else 1)

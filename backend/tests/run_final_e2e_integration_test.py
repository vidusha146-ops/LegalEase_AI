"""
LegalEase AI - Final End-to-End Integration Verification Harness
Executes all 10 comprehensive cross-phase workflows across Phases 1 through 7.
"""

import asyncio
import io
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from httpx import ASGITransport, AsyncClient
import fitz
from sqlalchemy import select

from app.main import app
from app.core.database import AsyncSessionLocal, init_db, get_db
from app.models.user import User
from app.models.case import LegalCase
from app.models.evidence import EvidenceDocument
from app.models.draft import LegalDraft
from app.models.search_query import CaseSimilarityQuery
from app.core.security import get_password_hash, create_access_token
from app.services.vault_encryption import VaultEncryptionService

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("final_e2e_integration")


async def run_e2e_integration():
    report: Dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "workflows": {},
        "summary": {"total": 10, "passed": 0, "failed": 0},
    }

    print("================================================================================")
    print("        LEGALEASE AI - FINAL COMPREHENSIVE INTEGRATION TESTING (PHASES 1-7)      ")
    print("================================================================================")

    # Clean dependency overrides to ensure standard database is used
    app.dependency_overrides.pop(get_db, None)
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", timeout=30.0) as client:

        # -----------------------------------------------------------------------------
        # WORKFLOW 1: AUTHENTICATION AND USER DASHBOARD
        # -----------------------------------------------------------------------------
        wf1 = {"name": "Authentication and user dashboard", "steps": []}
        try:
            print("\n[Workflow 1/10] Testing Authentication & User Dashboard...")
            user_email = f"e2e_citizen_{int(datetime.now().timestamp())}@legalease.in"
            reg_payload = {
                "email": user_email,
                "password": "StrongPassword123!",
                "full_name": "Pooja V. Deshmukh",
                "preferred_language": "mr",
            }
            reg_resp = await client.post("/api/v1/auth/register", json=reg_payload)
            assert reg_resp.status_code == 201, f"Registration failed: {reg_resp.text}"
            token = reg_resp.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            wf1["steps"].append({"step": "Register Citizen", "status": "PASSED", "user": user_email})

            me_resp = await client.get("/api/v1/auth/me", headers=headers)
            assert me_resp.status_code == 200
            user_data = me_resp.json()
            assert user_data["email"] == user_email
            citizen_id = user_data["id"]
            wf1["steps"].append({"step": "Verify Profile (me)", "status": "PASSED", "user_id": citizen_id})

            dash_resp = await client.get("/api/v1/dashboard/summary", headers=headers)
            assert dash_resp.status_code == 200
            dash_data = dash_resp.json()
            assert dash_data["vault_encryption_algorithm"] == "AES-256-GCM"
            assert len(dash_data["tenant_pseudonym"]) == 16
            wf1["steps"].append({
                "step": "Dashboard Summary",
                "status": "PASSED",
                "pseudonym": dash_data["tenant_pseudonym"],
                "encryption": dash_data["vault_encryption_algorithm"],
            })
            wf1["status"] = "PASSED"
            report["summary"]["passed"] += 1
            print("  --> Workflow 1 PASSED")
        except Exception as e:
            wf1["status"] = "FAILED"
            wf1["error"] = str(e)
            report["summary"]["failed"] += 1
            print(f"  --> Workflow 1 FAILED: {e}")
        report["workflows"]["1_auth_and_dashboard"] = wf1

        # -----------------------------------------------------------------------------
        # WORKFLOW 2: LEGAL SITUATION ANALYSIS
        # -----------------------------------------------------------------------------
        wf2 = {"name": "Legal situation analysis", "steps": []}
        case_id = None
        grievance = (
            "I purchased a commercial split air conditioner for my shop from CoolAir Pvt Ltd on 12th January 2024 "
            "paying Rs. 48,000. Within two weeks the cooling coil failed completely. Despite multiple emails, "
            "the dealer refused warranty replacement stating commercial use exclusion."
        )
        try:
            print("\n[Workflow 2/10] Testing Legal Situation Analysis...")
            # First, create an active case in the citizen dashboard
            case_payload = {
                "title": "CoolAir Air Conditioner Defect",
                "raw_description": grievance,
                "category": "CONSUMER_PROTECTION",
            }
            case_resp = await client.post("/api/v1/dashboard/cases", json=case_payload, headers=headers)
            assert case_resp.status_code == 201
            case_id = case_resp.json()["id"]

            analysis_payload = {
                "narrative": grievance,
                "incident_date": "2024-01-12",
                "is_continuing_offense": False,
                "preferred_language": "en",
            }
            an_resp = await client.post("/api/v1/analyzer/analyze-situation", json=analysis_payload, headers=headers)
            assert an_resp.status_code == 200, f"Analysis failed: {an_resp.text}"
            an_data = an_resp.json()
            assert an_data["predicted_domain"] == "CONSUMER_PROTECTION"
            assert len(an_data["applicable_statutes"]) >= 1
            assert an_data["information_quality"]["score"] > 0
            wf2["steps"].append({
                "step": "Analyze Situation",
                "status": "PASSED",
                "case_id": case_id,
                "domain": an_data["predicted_domain"],
                "statutes_found": len(an_data["applicable_statutes"]),
                "iq_score": an_data["information_quality"]["score"],
            })
            wf2["status"] = "PASSED"
            report["summary"]["passed"] += 1
            print("  --> Workflow 2 PASSED")
        except Exception as e:
            wf2["status"] = "FAILED"
            wf2["error"] = str(e)
            report["summary"]["failed"] += 1
            print(f"  --> Workflow 2 FAILED: {e}")
        report["workflows"]["2_situation_analysis"] = wf2

        # -----------------------------------------------------------------------------
        # WORKFLOW 3: BARE ACT RETRIEVAL & STATUTORY CITATION VERIFICATION
        # -----------------------------------------------------------------------------
        wf3 = {"name": "Bare Act retrieval and statutory citation verification", "steps": []}
        try:
            print("\n[Workflow 3/10] Testing Bare Act Retrieval & Citation Verification...")
            search_resp = await client.get("/api/v1/statutes/search?query=deficiency+of+service&top_k=2")
            assert search_resp.status_code == 200
            s_data = search_resp.json()
            assert s_data["total_retrieved"] >= 1
            wf3["steps"].append({"step": "ChromaDB Statute Search", "status": "PASSED", "count": len(s_data["results"])})

            # Verify citations in narrative text
            v_payload = {
                "text": "Accused committed fraud under Section 420 IPC and Section 318(4) of Bharatiya Nyaya Sanhita, but falsely cited Section 9999 BNS."
            }
            v_resp = await client.post("/api/v1/statutes/verify-citations", json=v_payload)
            assert v_resp.status_code == 200
            v_data = v_resp.json()
            assert v_data["total_citations"] == 3
            assert v_data["valid_count"] == 2
            assert v_data["invalid_count"] == 1
            wf3["steps"].append({
                "step": "Deterministic Citation Verification",
                "status": "PASSED",
                "valid": v_data["valid_count"],
                "invalid": v_data["invalid_count"],
            })

            cw_resp = await client.post(
                "/api/v1/statutes/crosswalk/temporal-applicability",
                json={"date_of_incident": "2024-08-15", "is_continuing": False},
            )
            assert cw_resp.status_code == 200
            cw_data = cw_resp.json()
            assert cw_data["status"] == "MODERN_BNS"
            assert "BNS" in cw_data["substantive_code"]
            wf3["steps"].append({"step": "BNS-IPC Temporal Crosswalk", "status": "PASSED"})

            wf3["status"] = "PASSED"
            report["summary"]["passed"] += 1
            print("  --> Workflow 3 PASSED")
        except Exception as e:
            wf3["status"] = "FAILED"
            wf3["error"] = str(e)
            report["summary"]["failed"] += 1
            print(f"  --> Workflow 3 FAILED: {e}")
        report["workflows"]["3_statutory_verification"] = wf3

        # -----------------------------------------------------------------------------
        # WORKFLOW 4: LEGAL PROBLEM CLASSIFICATION
        # -----------------------------------------------------------------------------
        wf4 = {"name": "Legal problem classification", "steps": []}
        try:
            print("\n[Workflow 4/10] Testing ML Problem Classification Pipeline...")
            from app.ml.classifier import LegalProblemClassifier
            classifier = LegalProblemClassifier()
            samples = [
                ("I bought an electric scooter and battery exploded", "CONSUMER_PROTECTION"),
                ("Cheque returned by bank with signature differs memo", "CHEQUE_BOUNCE_NI_ACT"),
                ("Received phishing email stealing bank credentials", "CYBER_LAW_IT_ACT"),
            ]
            for query, expected_domain in samples:
                pred = classifier.predict(query)
                assert pred["predicted_domain"] == expected_domain, f"Query '{query}' predicted {pred['predicted_domain']}"
            wf4["steps"].append({"step": "Multi-Class Domain Routing", "status": "PASSED", "tested_domains": 3})
            wf4["status"] = "PASSED"
            report["summary"]["passed"] += 1
            print("  --> Workflow 4 PASSED")
        except Exception as e:
            wf4["status"] = "FAILED"
            wf4["error"] = str(e)
            report["summary"]["failed"] += 1
            print(f"  --> Workflow 4 FAILED: {e}")
        report["workflows"]["4_problem_classification"] = wf4

        # -----------------------------------------------------------------------------
        # WORKFLOW 5: EXPLAINABILITY & FOLLOW-UP QUESTIONS
        # -----------------------------------------------------------------------------
        wf5 = {"name": "Explainability and follow-up questions", "steps": []}
        try:
            print("\n[Workflow 5/10] Testing Explainability & Interactive Gap Resolution...")
            statute_payload = {
                "narrative": grievance,
                "act_code": "CONSUMER_PROTECTION_2019",
                "section_number": "35",
            }
            exp_resp = await client.post("/api/v1/analyzer/explain-statute", json=statute_payload)
            assert exp_resp.status_code == 200
            exp_data = exp_resp.json()
            assert exp_data["total_elements"] >= 1
            assert len(exp_data["elements_breakdown"]) >= 1
            wf5["steps"].append({"step": "Statute Element Decomposition", "status": "PASSED", "elements": exp_data["total_elements"]})

            gap_payload = {
                "original_narrative": grievance,
                "domain": "CONSUMER_PROTECTION",
                "incident_date": "2024-01-12",
                "answers": {
                    "COMMERCIAL_PURPOSE": "Used strictly for personal livelihood, not large scale commercial trade."
                },
            }
            gap_resp = await client.post("/api/v1/analyzer/resolve-gaps", json=gap_payload)
            assert gap_resp.status_code == 200
            gap_data = gap_resp.json()
            assert gap_data["elevated_score"] >= gap_data["previous_score"]
            wf5["steps"].append({
                "step": "Resolve Gaps & Elevate IQ Score",
                "status": "PASSED",
                "previous_score": gap_data["previous_score"],
                "elevated_score": gap_data["elevated_score"],
            })

            wf5["status"] = "PASSED"
            report["summary"]["passed"] += 1
            print("  --> Workflow 5 PASSED")
        except Exception as e:
            wf5["status"] = "FAILED"
            wf5["error"] = str(e)
            report["summary"]["failed"] += 1
            print(f"  --> Workflow 5 FAILED: {e}")
        report["workflows"]["5_explainability_and_gaps"] = wf5

        # -----------------------------------------------------------------------------
        # WORKFLOW 6: EVIDENCE UPLOAD, OCR & TIMELINE CONSTRUCTION
        # -----------------------------------------------------------------------------
        wf6 = {"name": "Evidence upload, OCR and timeline construction", "steps": []}
        try:
            print("\n[Workflow 6/10] Testing Evidence Document Ingestion & Timeline Engine...")
            doc = fitz.open()
            page = doc.new_page()
            page.insert_text(
                (50, 72),
                "TAX INVOICE - COOL AIR PVT LTD\nDate: 12/01/2024\nInvoice No: INV-44910\n"
                "Buyer: Pooja Deshmukh\nDescription: Split Air Conditioner 1.5 Ton\nAmount: Rs. 48,000.00\n",
            )
            pdf_bytes = doc.tobytes()
            doc.close()
            files = [("files", ("invoice_ac.pdf", pdf_bytes, "application/pdf"))]
            data = {"case_id": case_id}
            up_resp = await client.post("/api/v1/evidence/upload", data=data, files=files, headers=headers)
            assert up_resp.status_code == 200, f"Upload failed: {up_resp.text}"
            up_data = up_resp.json()
            assert len(up_data) >= 1
            doc_id = up_data[0]["document_id"]
            wf6["steps"].append({"step": "Upload & Extract Text", "status": "PASSED", "doc_id": doc_id})

            tl_resp = await client.get(f"/api/v1/timeline/case/{case_id}", headers=headers)
            assert tl_resp.status_code == 200
            tl_data = tl_resp.json()
            assert "chronological_events" in tl_data
            wf6["steps"].append({"step": "Chronological Timeline Construction", "status": "PASSED", "events": tl_data["total_events"]})

            wf6["status"] = "PASSED"
            report["summary"]["passed"] += 1
            print("  --> Workflow 6 PASSED")
        except Exception as e:
            wf6["status"] = "FAILED"
            wf6["error"] = str(e)
            report["summary"]["failed"] += 1
            print(f"  --> Workflow 6 FAILED: {e}")
        report["workflows"]["6_evidence_and_timeline"] = wf6

        # -----------------------------------------------------------------------------
        # WORKFLOW 7: LEGAL DOCUMENT GENERATION & EXPORT
        # -----------------------------------------------------------------------------
        wf7 = {"name": "Legal document generation and export", "steps": []}
        draft_id = None
        try:
            print("\n[Workflow 7/10] Testing Document Generation Studio & PDF/DOCX Export...")
            draft_payload = {
                "case_id": case_id,
                "draft_type": "CONSUMER_COMPLAINT",
                "title": "Consumer Complaint Against CoolAir Pvt Ltd",
                "narrative": "Defective air conditioner cooling coil breakdown within 14 days.",
                "complainant": {"name": "Pooja Deshmukh", "address": "Dadar West, Mumbai - 400028"},
                "opposite_party": {"name": "CoolAir Pvt Ltd", "address": "Andheri East, Mumbai - 400069"},
                "incident_date": "2024-01-12",
                "incident_location": "Mumbai",
                "jurisdiction_forum": "DCDRC Mumbai Suburban",
                "monetary_claim": 48000.0,
            }
            d_resp = await client.post("/api/v1/drafts/generate", json=draft_payload, headers=headers)
            assert d_resp.status_code == 201, f"Draft generation failed: {d_resp.text}"
            d_data = d_resp.json()
            draft_id = d_data["id"]
            assert "Pooja Deshmukh" in d_data["content_markdown"]
            assert "Section 35" in d_data["content_markdown"]
            wf7["steps"].append({"step": "Generate Consumer Complaint", "status": "PASSED", "draft_id": draft_id})

            pdf_resp = await client.get(f"/api/v1/drafts/{draft_id}/export/pdf")
            assert pdf_resp.status_code == 200
            assert pdf_resp.content.startswith(b"%PDF-1.")
            wf7["steps"].append({"step": "Export PDF (Verified Magic Bytes)", "status": "PASSED", "size": len(pdf_resp.content)})

            docx_resp = await client.get(f"/api/v1/drafts/{draft_id}/export/docx")
            assert docx_resp.status_code == 200
            assert docx_resp.content.startswith(b"PK\x03\x04")
            wf7["steps"].append({"step": "Export DOCX (Verified Magic Bytes)", "status": "PASSED", "size": len(docx_resp.content)})

            wf7["status"] = "PASSED"
            report["summary"]["passed"] += 1
            print("  --> Workflow 7 PASSED")
        except Exception as e:
            wf7["status"] = "FAILED"
            wf7["error"] = str(e)
            report["summary"]["failed"] += 1
            print(f"  --> Workflow 7 FAILED: {e}")
        report["workflows"]["7_draft_generation_and_export"] = wf7

        # -----------------------------------------------------------------------------
        # WORKFLOW 8: SIMILAR CASE SEARCH
        # -----------------------------------------------------------------------------
        wf8 = {"name": "Similar case search", "steps": []}
        try:
            print("\n[Workflow 8/10] Testing Case Similarity Search & Precedent Intelligence...")
            sim_payload = {
                "narrative": "Comprehensive vehicle insurance claim rejected by insurer citing commercial hire after car theft.",
                "domain": "CONSUMER_PROTECTION",
                "jurisdiction_state": "Maharashtra",
                "case_id": case_id,
                "limit": 5,
            }
            s_resp = await client.post("/api/v1/cases/similar", json=sim_payload, headers=headers)
            assert s_resp.status_code == 200, f"Case similarity search failed: {s_resp.text}"
            s_data = s_resp.json()
            assert s_data["total_matches"] >= 1
            top_match = s_data["matches"][0]
            assert top_match["judgment_key"] == "SC_2008_NITIN_KHANDELWAL"
            assert 0.0 <= top_match["factual_alignment_index"] <= 100.0
            assert top_match["precedential_authority"] == "TIER_2_SUPREME_COURT_DIVISION_BENCH"
            assert top_match["jurisdictional_applicability"] == "BINDING_CONSTITUTIONAL"
            assert "Article 141" in s_data["mandatory_precedent_notice"]
            wf8["steps"].append({
                "step": "Search Landmark Precedent",
                "status": "PASSED",
                "matched_key": top_match["judgment_key"],
                "score": top_match["factual_alignment_index"],
                "authority": top_match["precedential_authority"],
            })

            j_resp = await client.get("/api/v1/cases/judgments/SC_2008_NITIN_KHANDELWAL")
            assert j_resp.status_code == 200
            j_data = j_resp.json()
            assert j_data["canonical_citation"] == "(2008) 11 SCC 259"
            assert j_data["ratio_paragraph_pinpoint"] == "paras 12-14"
            wf8["steps"].append({"step": "Canonical Judgment Detail Lookup", "status": "PASSED"})

            wf8["status"] = "PASSED"
            report["summary"]["passed"] += 1
            print("  --> Workflow 8 PASSED")
        except Exception as e:
            wf8["status"] = "FAILED"
            wf8["error"] = str(e)
            report["summary"]["failed"] += 1
            print(f"  --> Workflow 8 FAILED: {e}")
        report["workflows"]["8_similar_case_search"] = wf8

        # -----------------------------------------------------------------------------
        # WORKFLOW 9: MULTILINGUAL LEGAL ASSISTANCE
        # -----------------------------------------------------------------------------
        wf9 = {"name": "Multilingual legal assistance", "steps": []}
        try:
            print("\n[Workflow 9/10] Testing Multilingual Legal Assistant (6 Languages)...")
            det_resp = await client.post(
                "/api/v1/multilingual/detect-language",
                json={"text": "ग्राहकाने सेवेतील त्रुटीमुळे न्यायालयात तक्रार दाखल केली आहे"}
            )
            assert det_resp.status_code == 200
            assert det_resp.json()["detected_language"] == "mr"
            wf9["steps"].append({"step": "Script & Language Detection", "status": "PASSED", "lang": "mr"})

            trans_payload = {
                "text": "विपक्षी पक्षकाराने Section 35 of Consumer Protection Act चे उल्लंघन केले आणि आधार ५४३२ ८७६५ ४३२१ आहे",
                "target_language": "en",
                "consent_for_external_processing": True,
            }
            trans_resp = await client.post("/api/v1/multilingual/translate-query", json=trans_payload)
            assert trans_resp.status_code == 200
            tr_data = trans_resp.json()
            assert "Section 35" in tr_data["translated_text"]
            assert "Consumer Protection Act" in tr_data["translated_text"]
            assert "[REDACTED_AADHAAR]" in tr_data["translated_text"]
            assert "Article 348" in tr_data["uncertified_translation_disclaimer"]
            wf9["steps"].append({
                "step": "Token-Locked Citation Translation & PII Redaction",
                "status": "PASSED",
                "pii_scrubbed": tr_data["pii_scrubbed"],
            })

            explain_multi_payload = {
                "narrative": grievance,
                "target_language": "mr",
                "domain": "CONSUMER_PROTECTION",
                "consent_for_external_processing": False,
            }
            exp_multi_resp = await client.post("/api/v1/multilingual/explain", json=explain_multi_payload)
            assert exp_multi_resp.status_code == 200
            assert exp_multi_resp.json()["target_language"] == "mr"
            wf9["steps"].append({"step": "Multilingual Rights Guidance (Marathi)", "status": "PASSED"})

            gloss_resp = await client.get("/api/v1/multilingual/glossary?domain=CONSUMER_PROTECTION")
            assert gloss_resp.status_code == 200
            assert len(gloss_resp.json()) >= 1
            wf9["steps"].append({"step": "Verified Legislative Glossary", "status": "PASSED"})

            wf9["status"] = "PASSED"
            report["summary"]["passed"] += 1
            print("  --> Workflow 9 PASSED")
        except Exception as e:
            wf9["status"] = "FAILED"
            wf9["error"] = str(e)
            report["summary"]["failed"] += 1
            print(f"  --> Workflow 9 FAILED: {e}")
        report["workflows"]["9_multilingual_assistance"] = wf9

        # -----------------------------------------------------------------------------
        # WORKFLOW 10: EVIDENCE VAULT, QUERY HISTORY & PRIVACY CONTROLS
        # -----------------------------------------------------------------------------
        wf10 = {"name": "Evidence vault, query history and privacy controls", "steps": []}
        try:
            print("\n[Workflow 10/10] Testing Evidence Vault, Privacy Controls & Tenant Isolation...")
            vault_resp = await client.get("/api/v1/dashboard/vault/documents", headers=headers)
            assert vault_resp.status_code == 200
            v_docs = vault_resp.json()
            assert len(v_docs) >= 1
            assert v_docs[0]["is_encrypted"] is True
            wf10["steps"].append({"step": "Encrypted Evidence Vault Listing", "status": "PASSED", "count": len(v_docs)})

            queries_resp = await client.get("/api/v1/dashboard/queries", headers=headers)
            assert queries_resp.status_code == 200
            q_list = queries_resp.json()
            assert len(q_list) >= 1
            wf10["steps"].append({"step": "Persistent Query History Listing", "status": "PASSED", "count": len(q_list)})

            priv_resp = await client.get("/api/v1/dashboard/privacy/summary", headers=headers)
            assert priv_resp.status_code == 200
            priv_info = priv_resp.json()
            assert "AES-256-GCM" in priv_info["encryption_profile"]["algorithm"]
            wf10["steps"].append({"step": "Privacy Posture & DPDPA Readiness", "status": "PASSED"})

            export_resp = await client.post("/api/v1/dashboard/privacy/export", headers=headers)
            assert export_resp.status_code == 200
            exp_data = export_resp.json()
            assert len(exp_data["export_sha256_hash"]) == 64
            wf10["steps"].append({
                "step": "Voluntary JSON Export with SHA-256",
                "status": "PASSED",
                "hash": exp_data["export_sha256_hash"][:16] + "...",
            })

            # Tenant Isolation Cross-Check: User B attempts access to User A's case
            user_b_email = f"attacker_{int(datetime.now().timestamp())}@fake.in"
            reg_b = await client.post(
                "/api/v1/auth/register",
                json={"email": user_b_email, "password": "Pass123!Password", "full_name": "User B"}
            )
            token_b = reg_b.json()["access_token"]
            headers_b = {"Authorization": f"Bearer {token_b}"}

            cross_resp = await client.get(f"/api/v1/dashboard/cases/{case_id}", headers=headers_b)
            assert cross_resp.status_code == 403, f"Expected 403, got {cross_resp.status_code}"
            wf10["steps"].append({"step": "Backend Tenant Isolation Enforcement (403)", "status": "PASSED"})

            wf10["status"] = "PASSED"
            report["summary"]["passed"] += 1
            print("  --> Workflow 10 PASSED")
        except Exception as e:
            wf10["status"] = "FAILED"
            wf10["error"] = str(e)
            report["summary"]["failed"] += 1
            print(f"  --> Workflow 10 FAILED: {e}")
        report["workflows"]["10_vault_and_privacy"] = wf10

    print("\n================================================================================")
    print(f"  FINAL INTEGRATION RESULTS: {report['summary']['passed']}/10 Workflows Passed ({report['summary']['failed']} Failed)")
    print("================================================================================")

    output_file = Path(__file__).resolve().parent / "final_integration_report.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"[OK] Saved detailed test evidence report to: {output_file}")


if __name__ == "__main__":
    asyncio.run(run_e2e_integration())

"""
LegalEase AI - Automated Tests for Phase 5:
Document Intelligence, Information Extraction, Evidence Classification,
Chronological Timeline Engine, Consistency Analyzer & Statutory Fact Mapping
"""

import io
import json
import pytest
import fitz
import docx
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.document_intelligence import (
    DocumentIntelligenceService,
    EncryptedDocumentError,
    CorruptedDocumentError,
    UnsupportedDocumentError,
)
from app.services.information_extraction import LegalInformationExtractor
from app.services.evidence_classifier import EvidenceClassifierService
from app.services.timeline_engine import ChronologicalTimelineEngine
from app.services.consistency_analyzer import EvidenceConsistencyAnalyzer
from app.services.evidence_mapper import EvidenceToLegalFactMapper


@pytest.fixture(scope="session", autouse=True)
def anyio_backend():
    return "asyncio"


def create_sample_pdf_bytes(text: str = "Tax Invoice No INV-2024-001 dated 10/08/2024 for Rs 1,50,000.") -> bytes:
    """Helper creating an authentic PDF in-memory using PyMuPDF."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def create_sample_docx_bytes(text: str = "Statutory Demand Notice under Section 138 NI Act dated 20th August 2024.") -> bytes:
    """Helper creating an authentic DOCX in-memory using python-docx."""
    doc = docx.Document()
    doc.add_heading("LEGAL DEMAND NOTICE", 0)
    doc.add_paragraph(text)
    table = doc.add_table(rows=1, cols=2)
    table.rows[0].cells[0].text = "Noticee: Ramesh Kumar"
    table.rows[0].cells[1].text = "Amount: ₹ 2,50,000"
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


# =============================================================================
# 1. DOCUMENT INTELLIGENCE TESTS
# =============================================================================

def test_document_intelligence_pdf_extraction():
    """Verifies PyMuPDF text extraction, page counting, and SHA-256 calculation."""
    content = "Bank Return Memo: Cheque No 441029 returned unpaid for Funds Insufficient on 12-08-2024."
    pdf_bytes = create_sample_pdf_bytes(content)

    res = DocumentIntelligenceService.extract_document_text(pdf_bytes, "bank_memo.pdf")
    assert res["file_type"] == "PDF"
    assert res["total_pages"] == 1
    assert "Funds Insufficient" in res["full_text"]
    assert "441029" in res["full_text"]
    assert len(res["sha256_hash"]) == 64


def test_document_intelligence_docx_extraction():
    """Verifies python-docx extraction of paragraphs and tables."""
    docx_bytes = create_sample_docx_bytes()
    res = DocumentIntelligenceService.extract_document_text(docx_bytes, "legal_notice.docx")
    assert res["file_type"] == "DOCX"
    assert "LEGAL DEMAND NOTICE" in res["full_text"]
    assert "₹ 2,50,000" in res["full_text"]


def test_document_intelligence_corrupted_and_unsupported():
    """Verifies safe error handling on corrupted bytes and unsupported file extensions."""
    # Corrupted
    with pytest.raises(CorruptedDocumentError):
        DocumentIntelligenceService.extract_document_text(b"not a valid pdf", "test.pdf")

    # Unsupported extension
    with pytest.raises(UnsupportedDocumentError):
        DocumentIntelligenceService.extract_document_text(b"echo 1", "script.exe")


# =============================================================================
# 2. INFORMATION EXTRACTION TESTS
# =============================================================================

def test_information_extraction_dates_amounts_identifiers():
    """Verifies extraction of dates, monetary amounts, and legal references."""
    pages = [
        {
            "page_number": 1,
            "text": (
                "On 15th August 2024, client gave Cheque No 441029 of Rs 2,50,000 drawn on HDFC Bank. "
                "The cheque was dishonoured with remarks 'Funds Insufficient' on 20/08/2024. "
                "Notice sent via Speed Post ED987654321IN."
            )
        }
    ]
    extracted = LegalInformationExtractor.extract_entities_from_pages(pages, "dispute.pdf")

    # Dates
    dates = [d["iso_date"] for d in extracted["dates"]]
    assert "2024-08-15" in dates
    assert "2024-08-20" in dates

    # Amounts
    amounts = [a["amount"] for a in extracted["monetary_amounts"]]
    assert 250000.0 in amounts

    # Identifiers
    id_types = [i["type"] for i in extracted["identifiers"]]
    assert "CHEQUE_NUMBER" in id_types
    assert "SPEED_POST_TRACKING_ID" in id_types
    assert "BANK_RETURN_REASON" in id_types

    # Banks & Parties
    parties = [p["value"] for p in extracted["parties"]]
    assert "HDFC Bank" in parties or "HDFC" in parties


# =============================================================================
# 3. EVIDENCE CLASSIFICATION TESTS
# =============================================================================

def test_evidence_classification_categories_and_reclassify():
    """Verifies heuristic evidence classification and user reclassification."""
    invoice_text = "Tax Invoice GSTIN 07AAAAA0000A1Z5 Total Amount ₹ 45,000 Bill of supply item description"
    cls_inv = EvidenceClassifierService.classify_document(invoice_text, "invoice.pdf")
    assert cls_inv["category"] == "INVOICE_BILL"
    assert cls_inv["confidence"] >= 0.60

    notice_text = "Legal Demand Notice under Section 138 Negotiable Instruments Act. We call upon you within 15 days failing which legal proceedings will be initiated."
    cls_not = EvidenceClassifierService.classify_document(notice_text, "notice.pdf")
    assert cls_not["category"] == "LEGAL_NOTICE"

    # User reclassification override
    reclassified = EvidenceClassifierService.reclassify("AGREEMENT_CONTRACT")
    assert reclassified["category"] == "AGREEMENT_CONTRACT"
    assert reclassified["confidence"] == 1.0
    assert reclassified["is_user_corrected"] is True


# =============================================================================
# 4. CHRONOLOGICAL TIMELINE ENGINE TESTS
# =============================================================================

def test_chronological_timeline_sorting_and_gap_detection():
    """Verifies event ordering and detection of temporal gaps."""
    doc_events = [
        {"title": "Cheque Dishonoured", "date": "2024-08-10", "source_document": "memo.pdf", "page_number": 1},
        {"title": "Goods Delivered", "date": "2024-01-15", "source_document": "invoice.pdf", "page_number": 1},
        {"title": "Demand Notice Dispatched", "date": "2024-08-20", "source_document": "notice.pdf", "page_number": 1},
    ]

    timeline = ChronologicalTimelineEngine.build_timeline(doc_events)
    assert timeline["total_events"] == 3
    assert timeline["dated_events_count"] == 3

    # Check ascending sequence
    events = timeline["chronological_events"]
    assert events[0]["title"] == "Goods Delivered"
    assert events[0]["event_date"] == "2024-01-15"
    assert events[1]["title"] == "Cheque Dishonoured"
    assert events[2]["title"] == "Demand Notice Dispatched"

    # Check temporal gap warning (> 90 days between Jan 15 and Aug 10)
    assert len(timeline["temporal_warnings"]) >= 1
    assert timeline["temporal_warnings"][0]["gap_days"] > 90


# =============================================================================
# 5. EVIDENCE CONSISTENCY ANALYZER TESTS
# =============================================================================

def test_consistency_analyzer_sequence_and_amount_discrepancies():
    """Verifies sequence anomalies (notice before bounce) and amount variances."""
    docs = [
        {
            "filename": "notice.pdf",
            "category": "LEGAL_NOTICE",
            "dates": [{"iso_date": "2024-08-01", "page_number": 1}],
            "monetary_amounts": [{"amount": 250000.0, "formatted": "₹ 2,50,000.00"}],
        },
        {
            "filename": "memo.pdf",
            "category": "BANK_RECORD",
            "dates": [{"iso_date": "2024-08-15", "page_number": 1}],
            "monetary_amounts": [{"amount": 200000.0, "formatted": "₹ 2,00,000.00"}],
        }
    ]

    analysis = EvidenceConsistencyAnalyzer.analyze_consistency(
        documents_metadata=docs,
        narrative="Cheque bounced and I served notice.",
        predicted_domain="CHEQUE_BOUNCE_NI_ACT"
    )

    assert analysis["is_consistent"] is False
    assert analysis["discrepancies_count"] >= 2

    types = [d["type"] for d in analysis["discrepancies"]]
    assert "MONETARY_AMOUNT_VARIANCE" in types
    assert "CHRONOLOGICAL_SEQUENCE_DISCREPANCY" in types


# =============================================================================
# 6. EVIDENCE TO LEGAL FACT MAPPING TESTS
# =============================================================================

def test_evidence_mapper_substantiates_elements():
    """Verifies that uploaded documents satisfy statutory requirements under NI Act 138."""
    uploaded_docs = [
        {"filename": "bank_return_memo.pdf", "category": "BANK_RECORD"},
        {"filename": "statutory_notice.pdf", "category": "LEGAL_NOTICE"},
        {"filename": "tax_invoice.pdf", "category": "INVOICE_BILL"},
    ]

    narrative = "My client's cheque bounced."
    mapped = EvidenceToLegalFactMapper.map_evidence_to_statute(
        narrative=narrative,
        act_code="NI_ACT_1881",
        section_number="138",
        uploaded_documents=uploaded_docs,
    )

    assert mapped["document_substantiated_count"] >= 3
    # Check that elements have supporting document names
    substantiated = [e for e in mapped["elements_breakdown"] if e.get("substantiated_by_document")]
    assert len(substantiated) >= 3
    for s in substantiated:
        assert s["supporting_document"] in ["bank_return_memo.pdf", "statutory_notice.pdf", "tax_invoice.pdf"]
        assert s["evidence_verification_status"] == "VERIFIED_BY_DOCUMENTARY_PROOF"


# =============================================================================
# 7. FASTAPI API INTEGRATION TESTS (PHASE 5 ENDPOINTS)
# =============================================================================

@pytest.mark.asyncio
async def test_phase5_api_endpoints():
    """Verifies evidence upload, listing, timeline, and consistency check endpoints."""
    from app.core.database import init_db
    app.dependency_overrides.clear()
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Upload sample PDF
        pdf_bytes = create_sample_pdf_bytes("Tax Invoice No INV-9901 dated 15/07/2024 for Rs 85,000.")
        files = [
            ("files", ("invoice_sample.pdf", pdf_bytes, "application/pdf"))
        ]
        data = {"case_id": 999}

        upload_resp = await client.post(
            "/api/v1/evidence/upload",
            data=data,
            files=files,
        )
        assert upload_resp.status_code == 200, f"Upload failed: {upload_resp.text}"
        uploaded_docs = upload_resp.json()
        assert len(uploaded_docs) == 1
        doc_id = uploaded_docs[0]["document_id"]
        assert uploaded_docs[0]["category"] == "INVOICE_BILL"

        # 2. List case evidence
        list_resp = await client.get("/api/v1/evidence/case/999")
        assert list_resp.status_code == 200
        assert len(list_resp.json()) >= 1

        # 3. Add manual timeline event
        man_ev_resp = await client.post(
            "/api/v1/timeline/event",
            json={
                "case_id": 999,
                "event_date": "2024-07-20",
                "event_title": "Product Delivered to Buyer",
                "event_description": "Goods delivered via courier service",
            }
        )
        assert man_ev_resp.status_code == 200
        event_id = man_ev_resp.json()["id"]

        # 4. Get case timeline
        tl_resp = await client.get("/api/v1/timeline/case/999")
        assert tl_resp.status_code == 200
        tl_data = tl_resp.json()
        assert tl_data["case_id"] == 999
        assert tl_data["total_events"] >= 1

        # 5. Check consistency endpoint
        cons_resp = await client.post(
            "/api/v1/evidence/consistency-check",
            json={
                "case_id": 999,
                "narrative": "Purchased equipment for Rs 85,000",
                "predicted_domain": "CONSUMER_PROTECTION",
                "narrative_amount": 85000.0,
            }
        )
        assert cons_resp.status_code == 200
        assert "is_consistent" in cons_resp.json()

        # 6. Reclassify document
        reclass_resp = await client.patch(
            f"/api/v1/evidence/{doc_id}/reclassify",
            json={"new_category": "OTHER_EVIDENCE"}
        )
        assert reclass_resp.status_code == 200
        assert reclass_resp.json()["updated_category"] == "OTHER_EVIDENCE"

        # 7. Clean up timeline event & evidence document
        del_ev = await client.delete(f"/api/v1/timeline/event/{event_id}")
        assert del_ev.status_code == 200

        del_doc = await client.delete(f"/api/v1/evidence/{doc_id}")
        assert del_doc.status_code == 200

"""
LegalEase AI - AI Legal Document Generation Studio Automated Test Suite (Phase 6)
Validates Consumer Complaints, Legal Notices, RTI Applications, Police Complaints,
Missing Information Detection, Canonical Citation Validation, Evidence-Linked Exhibits,
PDF/DOCX Exports, and FastAPI Endpoints.
"""

import os
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.core.database import init_db
from app.services.legal_drafting_studio import LegalDraftingStudioService, NON_ADVOCACY_DISCLAIMER_TEXT
from app.services.document_export import DocumentExportService
from app.schemas.draft import (
    DraftGenerateRequest,
    PartyDetails,
    MissingInfoItem,
)


@pytest.fixture(scope="session", autouse=True)
def anyio_backend():
    return "asyncio"


# =============================================================================
# 1. MISSING-INFORMATION DETECTION & NO-HALLUCINATION TESTS
# =============================================================================

def test_missing_information_detection():
    """Verifies that missing critical facts are detected without fabricating data."""
    # Incomplete request: no complainant name, no noticee address, no monetary claim
    incomplete_req = DraftGenerateRequest(
        draft_type="CONSUMER_COMPLAINT",
        narrative="I bought a refrigerator and it stopped working after 3 days.",
        complainant=PartyDetails(name="", address=None),
        opposite_party=PartyDetails(name="Cool Electronics Store", address=None),
        monetary_claim=None,
        incident_date=None,
    )

    missing = LegalDraftingStudioService.detect_missing_information("CONSUMER_COMPLAINT", incomplete_req)
    missing_fields = [m.field for m in missing]

    assert "complainant_name" in missing_fields
    assert "complainant_address" in missing_fields
    assert "opposite_party_address" in missing_fields
    assert "monetary_claim" in missing_fields
    assert "transaction_date" in missing_fields

    # Verify suggested prompts and statutory rationales exist
    for m in missing:
        assert len(m.rationale) > 10
        assert len(m.suggested_prompt) > 5


# =============================================================================
# 2. STATUTORY CITATION VALIDATION IN DRAFTING
# =============================================================================

def test_canonical_statutory_citation_validation():
    """Verifies that drafting citations are grounded in verified Bare Acts."""
    service = LegalDraftingStudioService()

    # Consumer Complaint citations
    copra_cits = service.get_verified_statutory_citations("CONSUMER_COMPLAINT", "defective goods")
    assert len(copra_cits) >= 3
    copra_sections = [c.section_number for c in copra_cits]
    assert "2(7)" in copra_sections
    assert "2(11)" in copra_sections
    assert "35" in copra_sections
    for c in copra_cits:
        assert c.is_verified is True
        assert "http" in c.source_url

    # Legal Notice citations (NI Act 138)
    notice_cits = service.get_verified_statutory_citations("LEGAL_NOTICE", "cheque bounce")
    assert any(c.section_number == "138" and c.act_code == "NI_ACT_1881" for c in notice_cits)

    # Police Complaint citations (BNSS 173(1), BNS 303(1))
    police_cits = service.get_verified_statutory_citations("POLICE_COMPLAINT", "theft")
    assert any("173" in c.section_number and c.act_code == "BNSS_2023" for c in police_cits)
    assert any(c.section_number == "303(1)" and c.act_code == "BNS_2023" for c in police_cits)


# =============================================================================
# 3. EVIDENCE-LINKED EXHIBITS BINDING TESTS
# =============================================================================

def test_evidence_linked_exhibits():
    """Verifies binding of uploaded evidence documents into formal legal annexures."""
    mock_docs = [
        {"id": 1, "filename": "tax_invoice_2024.pdf", "category": "INVOICE_BILL"},
        {"id": 2, "filename": "bank_return_memo.pdf", "category": "BANK_RECORD"},
        {"id": 3, "filename": "demand_notice_served.pdf", "category": "LEGAL_NOTICE"},
    ]

    exhibits = LegalDraftingStudioService.bind_evidence_exhibits(mock_docs)
    assert len(exhibits) == 3
    assert exhibits[0].exhibit_label == "Exhibit A"
    assert exhibits[0].filename == "tax_invoice_2024.pdf"
    assert "Commercial Transaction" in exhibits[0].relevance

    assert exhibits[1].exhibit_label == "Exhibit B"
    assert exhibits[1].filename == "bank_return_memo.pdf"
    assert "Banking Presentation" in exhibits[1].relevance

    assert exhibits[2].exhibit_label == "Exhibit C"


# =============================================================================
# 4. CONSUMER COMPLAINT GENERATION TESTS
# =============================================================================

def test_consumer_complaint_generation():
    """Verifies generation of District Consumer Commission complaint."""
    service = LegalDraftingStudioService()
    req = DraftGenerateRequest(
        draft_type="CONSUMER_COMPLAINT",
        narrative="Purchased enterprise software license for Rs 3,50,000 on 12/03/2024 which failed to activate.",
        complainant=PartyDetails(
            name="Ramesh Sharma",
            address="Flat 402, Lotus Apartments, Connaught Place, New Delhi - 110001",
            phone="9876543210",
            email="ramesh@example.in",
        ),
        opposite_party=PartyDetails(
            name="Apex Infotech Solutions Pvt Ltd",
            address="Tower B, Tech Park, Outer Ring Road, Bengaluru - 560103",
        ),
        incident_date="2024-03-12",
        incident_location="New Delhi",
        jurisdiction_forum="DISTRICT CONSUMER DISPUTES REDRESSAL COMMISSION, NEW DELHI",
        monetary_claim=350000.0,
    )

    result = service.generate_legal_draft(req)
    md = result["content_markdown"]

    assert "DISTRICT CONSUMER DISPUTES REDRESSAL COMMISSION" in md
    assert "Ramesh Sharma" in md
    assert "Apex Infotech Solutions" in md
    assert "SECTION 35 OF THE CONSUMER PROTECTION ACT, 2019" in md
    assert "₹ 350,000.00" in md
    assert "SOLEMN VERIFICATION AFFIDAVIT" in md
    assert "ADVOCATES ACT, 1961" in md or "Advocates Act, 1961" in md
    assert len(result["verified_citations"]) >= 3


# =============================================================================
# 5. LEGAL DEMAND NOTICE GENERATION TESTS
# =============================================================================

def test_legal_demand_notice_generation():
    """Verifies Section 138 NI Act statutory demand notice generation with 15-day timeline."""
    service = LegalDraftingStudioService()
    req = DraftGenerateRequest(
        draft_type="LEGAL_NOTICE",
        narrative="Cheque No. 441029 issued towards supply of building materials returned unpaid for insufficient funds.",
        complainant=PartyDetails(
            name="Harish Chandra",
            address="15, G.T. Road, Ghaziabad, UP",
            phone="9811002233",
        ),
        opposite_party=PartyDetails(
            name="Vijay Logistics Pvt Ltd",
            address="Plot 88, Sector 18, Gurugram, Haryana",
        ),
        incident_date="2024-08-15",
        monetary_claim=250000.0,
    )

    result = service.generate_legal_draft(req)
    md = result["content_markdown"]

    assert "FORMAL LEGAL DEMAND NOTICE" in md
    assert "SECTION 138 OF THE NEGOTIABLE INSTRUMENTS ACT, 1881" in md
    assert "FIFTEEN (15) DAYS" in md
    assert "₹ 250,000.00" in md
    assert "Harish Chandra" in md
    assert "Vijay Logistics" in md


# =============================================================================
# 6. RTI APPLICATION & POLICE COMPLAINT TESTS
# =============================================================================

def test_rti_application_and_police_complaint_generation():
    """Verifies RTI Form A and Police Complaint (FIR) generation."""
    service = LegalDraftingStudioService()

    # RTI
    rti_req = DraftGenerateRequest(
        draft_type="RTI_APPLICATION",
        narrative="Certified copies of tender allocation documents for Road Repair Project 2023-24.",
        complainant=PartyDetails(name="Sunita Devi", address="Ward 12, Patna, Bihar", phone="9988776655"),
        jurisdiction_forum="MUNICIPAL CORPORATION OF PATNA",
    )
    rti_res = service.generate_legal_draft(rti_req)
    assert "SECTION 6(1) OF THE RTI ACT, 2005" in rti_res["content_markdown"]
    assert "Indian Citizen" in rti_res["content_markdown"]
    assert "₹ 10/-" in rti_res["content_markdown"]

    # Police Complaint
    police_req = DraftGenerateRequest(
        draft_type="POLICE_COMPLAINT",
        narrative="Gold jewellery and Rs 50,000 cash stolen from residence by breaking front door lock.",
        complainant=PartyDetails(name="Vikram Malhotra", address="Sector 4, Rohini, Delhi"),
        incident_date="2024-09-10",
        incident_location="Rohini, Delhi",
        jurisdiction_forum="POLICE STATION ROHINI NORTH",
        monetary_claim=150000.0,
    )
    police_res = service.generate_legal_draft(police_req)
    assert "SECTION 173 OF BHARATIYA NAGARIK SURAKSHA SANHITA, 2023" in police_res["content_markdown"]
    assert "Section 303(1)" in police_res["content_markdown"]
    assert "Register a regular First Information Report (FIR)" in police_res["content_markdown"]


# =============================================================================
# 7. DOCUMENT EXPORT GENERATION TESTS (PDF & DOCX)
# =============================================================================

def test_document_export_pdf_and_docx():
    """Verifies that DocumentExportService generates valid PDF and DOCX files."""
    sample_md = (
        "# CONSUMER COMPLAINT\n\n"
        "## 1. PARTIES\nComplainant vs Opposite Party.\n\n"
        "## 2. PRAYER\nRefund of ₹ 50,000 along with interest.\n"
    )

    # 1. PDF Generation
    pdf_bytes, pdf_sha, pdf_path = DocumentExportService.generate_pdf(
        draft_id=901,
        title="Test Consumer Complaint",
        content_markdown=sample_md,
        draft_type="CONSUMER_COMPLAINT",
        save_to_disk=False,
    )
    assert len(pdf_bytes) > 500
    assert pdf_bytes.startswith(b"%PDF-1.")
    assert len(pdf_sha) == 64

    # 2. DOCX Generation
    docx_bytes, docx_sha, docx_path = DocumentExportService.generate_docx(
        draft_id=901,
        title="Test Consumer Complaint",
        content_markdown=sample_md,
        draft_type="CONSUMER_COMPLAINT",
        save_to_disk=False,
    )
    assert len(docx_bytes) > 1000
    assert docx_bytes.startswith(b"PK\x03\x04")  # Standard ZIP magic header for DOCX
    assert len(docx_sha) == 64


# =============================================================================
# 8. FASTAPI API INTEGRATION TESTS (PHASE 6 ENDPOINTS)
# =============================================================================

@pytest.mark.asyncio
async def test_drafts_api_lifecycle():
    """Verifies complete API lifecycle: generate, read, update, export PDF/DOCX, and delete."""
    app.dependency_overrides.clear()
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Generate Legal Draft
        gen_payload = {
            "case_id": 777,
            "draft_type": "CONSUMER_COMPLAINT",
            "title": "Grievance against Defective Appliance",
            "narrative": "Purchased washing machine which flooded kitchen on first cycle.",
            "complainant": {
                "name": "Ananya Sen",
                "address": "B-12, Salt Lake, Kolkata - 700064",
                "phone": "9830012345",
            },
            "opposite_party": {
                "name": "Great Home Appliances Ltd",
                "address": "Park Street, Kolkata - 700016",
            },
            "incident_date": "2024-04-10",
            "incident_location": "Kolkata",
            "jurisdiction_forum": "DCDRC Kolkata North",
            "monetary_claim": 42000.0,
        }

        gen_resp = await client.post("/api/v1/drafts/generate", json=gen_payload)
        assert gen_resp.status_code == 201, f"Generate failed: {gen_resp.text}"
        draft_data = gen_resp.json()
        draft_id = draft_data["id"]
        assert draft_data["draft_type"] == "CONSUMER_COMPLAINT"
        assert "Ananya Sen" in draft_data["content_markdown"]

        # 2. Get Draft
        get_resp = await client.get(f"/api/v1/drafts/{draft_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == draft_id

        # 3. List Case Drafts
        list_resp = await client.get("/api/v1/drafts/case/777")
        assert list_resp.status_code == 200
        assert len(list_resp.json()) >= 1

        # 4. Update Draft (Editable Preview)
        updated_content = draft_data["content_markdown"] + "\n\n## 8. ADDENDUM\nAdditional evidence provided."
        put_resp = await client.put(
            f"/api/v1/drafts/{draft_id}",
            json={"title": "Updated Grievance Title", "content_markdown": updated_content},
        )
        assert put_resp.status_code == 200
        assert "ADDENDUM" in put_resp.json()["content_markdown"]
        assert put_resp.json()["title"] == "Updated Grievance Title"

        # 5. Export PDF
        pdf_resp = await client.get(f"/api/v1/drafts/{draft_id}/export/pdf")
        assert pdf_resp.status_code == 200
        assert pdf_resp.headers["content-type"] == "application/pdf"
        assert pdf_resp.content.startswith(b"%PDF-1.")

        # 6. Export DOCX
        docx_resp = await client.get(f"/api/v1/drafts/{draft_id}/export/docx")
        assert docx_resp.status_code == 200
        assert "wordprocessingml.document" in docx_resp.headers["content-type"]
        assert docx_resp.content.startswith(b"PK\x03\x04")

        # 7. Delete Draft
        del_resp = await client.delete(f"/api/v1/drafts/{draft_id}")
        assert del_resp.status_code == 200

        # Verify 404 after deletion
        get_again = await client.get(f"/api/v1/drafts/{draft_id}")
        assert get_again.status_code == 404

"""
LegalEase AI - Legal Drafting Studio Schemas (Phase 6)
Pydantic schemas for Consumer Complaints, Legal Notices, RTI Applications,
Police Complaints (FIR), Missing Information, and Document Exports.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class PartyDetails(BaseModel):
    name: str = Field(..., description="Full Name of Citizen / Entity")
    address: Optional[str] = Field(None, description="Complete Postal Address with Pin Code")
    phone: Optional[str] = Field(None, description="Contact Telephone / Mobile")
    email: Optional[str] = Field(None, description="Email Address")
    designation: Optional[str] = Field(None, description="Designation (e.g. Managing Director, PIO)")
    role: Optional[str] = Field(None, description="Role in legal draft (e.g. Complainant, Accused)")


class DraftGenerateRequest(BaseModel):
    case_id: Optional[int] = Field(None, description="Associated Legal Case ID (optional)")
    draft_type: str = Field(
        ...,
        description="Type of draft: CONSUMER_COMPLAINT, LEGAL_NOTICE, RTI_APPLICATION, POLICE_COMPLAINT",
    )
    title: Optional[str] = Field(None, description="Custom title for legal draft")
    narrative: Optional[str] = Field(None, description="Factual grievance narrative from citizen")
    complainant: Optional[PartyDetails] = Field(None, description="Complainant / Applicant / Sender details")
    opposite_party: Optional[PartyDetails] = Field(None, description="Opposite Party / Accused / Noticee details")
    incident_date: Optional[str] = Field(None, description="Date of occurrence / transaction (YYYY-MM-DD)")
    incident_location: Optional[str] = Field(None, description="City / District / Police Station jurisdiction")
    jurisdiction_forum: Optional[str] = Field(None, description="Forum/Court name (e.g. DCDRC New Delhi)")
    monetary_claim: Optional[float] = Field(None, description="Monetary claim / compensation / disputed amount in INR")
    custom_prayers: Optional[List[str]] = Field(None, description="Specific remedies or prayers sought by citizen")
    selected_evidence_ids: Optional[List[int]] = Field(None, description="IDs of uploaded evidence to link as exhibits")
    additional_facts: Optional[str] = Field(None, description="Additional verified context or timeline data")


class DraftUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, description="Updated draft title")
    content_markdown: str = Field(..., description="Edited document content in Markdown")


class MissingInfoItem(BaseModel):
    field: str
    rationale: str
    impact: str
    suggested_prompt: str


class VerifiedCitationItem(BaseModel):
    act_code: str
    act_title: str
    section_number: str
    section_title: str
    source_url: str
    is_verified: bool = True


class ExhibitItem(BaseModel):
    exhibit_label: str
    filename: str
    category: str
    relevance: str


class DraftResponse(BaseModel):
    id: int
    case_id: int
    draft_type: str
    title: str
    content_markdown: str
    pdf_path: Optional[str] = None
    docx_path: Optional[str] = None
    missing_information: List[MissingInfoItem] = []
    verified_citations: List[VerifiedCitationItem] = []
    exhibits: List[ExhibitItem] = []
    disclaimer: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class DraftExportResponse(BaseModel):
    draft_id: int
    format: str
    filename: str
    file_sha256: str
    file_size_bytes: int
    download_url: str

"""
LegalEase AI - Evidence & Timeline Pydantic Schemas (Phase 5)
Defines request and response models for document ingestion, OCR, entity extraction,
chronological timeline building, and cross-document consistency checks.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class EvidenceUploadResponse(BaseModel):
    document_id: int
    case_id: int
    filename: str
    file_type: str
    file_size_bytes: int
    sha256_hash: str
    category: str
    category_title: str
    classification_confidence: float
    total_pages: int
    is_scanned: bool
    ocr_performed: bool
    extracted_entities: Dict[str, Any]
    extracted_text_preview: str


class ReclassifyRequest(BaseModel):
    new_category: str = Field(..., description="Target canonical evidence category")


class ReclassifyResponse(BaseModel):
    document_id: int
    previous_category: str
    updated_category: str
    category_title: str
    is_user_corrected: bool


class ManualTimelineEventRequest(BaseModel):
    case_id: int
    event_date: str = Field(..., description="Date of the event (ISO YYYY-MM-DD or DD/MM/YYYY)")
    event_title: str = Field(..., min_length=2, max_length=255)
    event_description: str = Field(..., min_length=2)
    source_reference: Optional[str] = "Citizen Statement"
    confidence_level: Optional[str] = "HIGH"


class TimelineEventResponse(BaseModel):
    id: int
    case_id: int
    evidence_id: Optional[int] = None
    event_date: str
    event_title: str
    event_description: str
    source_reference: Optional[str] = None
    confidence_level: str


class CaseTimelineResponse(BaseModel):
    case_id: int
    total_events: int
    dated_events_count: int
    undated_events_count: int
    earliest_date: Optional[str] = None
    latest_date: Optional[str] = None
    chronological_events: List[Dict[str, Any]]
    undated_events: List[Dict[str, Any]]
    temporal_warnings: List[Dict[str, Any]]


class ConsistencyCheckRequest(BaseModel):
    case_id: int
    narrative: str
    predicted_domain: Optional[str] = None
    narrative_amount: Optional[float] = None
    narrative_date: Optional[str] = None


class ConsistencyCheckResponse(BaseModel):
    case_id: int
    is_consistent: bool
    discrepancies_count: int
    discrepancies: List[Dict[str, Any]]
    documentary_gaps_count: int
    documentary_gaps: List[Dict[str, Any]]
    summary: str


class EvidenceToStatuteRequest(BaseModel):
    narrative: str
    act_code: str
    section_number: str
    case_id: Optional[int] = None
    uploaded_documents: Optional[List[Dict[str, Any]]] = None

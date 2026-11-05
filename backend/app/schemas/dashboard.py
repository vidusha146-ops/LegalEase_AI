"""
LegalEase AI - Citizen User Dashboard & Privacy Schemas (Phase 7 Module 3)
Pydantic v2 schemas for:
- Dashboard summary & user profile management
- Case lifecycle tracking & query history
- AES-256-GCM encrypted evidence vault & document archive
- DPDPA privacy controls, voluntary data export & multi-layer deletion
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class UserProfileUpdate(BaseModel):
    """Payload for updating citizen profile preferences."""
    full_name: Optional[str] = Field(None, min_length=2, max_length=150)
    preferred_language: Optional[str] = Field(None, max_length=10)


class DashboardSummaryResponse(BaseModel):
    """Consolidated citizen dashboard overview metrics."""
    user_id: int
    email: str
    full_name: str
    tenant_pseudonym: str
    preferred_language: str
    total_cases: int
    active_cases: int
    closed_cases: int
    total_evidence_documents: int
    total_drafts_generated: int
    total_queries_logged: int
    vault_encryption_algorithm: str = "AES-256-GCM"
    dpdpa_privacy_mode: str
    last_activity_at: Optional[str] = None


class CaseCreateRequest(BaseModel):
    """Payload to initiate a new legal case/grievance."""
    title: str = Field(..., min_length=3, max_length=255)
    raw_description: str = Field(..., min_length=10)
    category: Optional[str] = Field(None, max_length=100)


class CaseProgressUpdateRequest(BaseModel):
    """Payload for updating case progression status."""
    status: str = Field(
        ...,
        description="NEW | ACTIVE | DOCUMENTED | DRAFTED | RESOLVED | CLOSED"
    )


class CaseSummaryItem(BaseModel):
    """Summary item for case listing."""
    id: int
    title: str
    category: Optional[str] = None
    status: str
    evidence_count: int = 0
    drafts_count: int = 0
    created_at: str
    updated_at: str

    model_config = ConfigDict(from_attributes=True)


class CaseDetailResponse(BaseModel):
    """Full detail view for citizen case."""
    id: int
    user_id: int
    title: str
    raw_description: str
    category: Optional[str] = None
    status: str
    confidence_score: Optional[float] = None
    evidence_count: int
    drafts_count: int
    applicable_laws: List[Dict[str, Any]] = Field(default_factory=list)
    citizen_rights: List[str] = Field(default_factory=list)
    missing_info: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: str
    updated_at: str


class QueryHistoryItem(BaseModel):
    """Citizen query search log entry."""
    id: int
    query_text: str
    legal_domain: Optional[str] = None
    matched_judgment_count: int = 0
    created_at: str


class VaultDocumentItem(BaseModel):
    """Document in encrypted evidence vault."""
    id: int
    case_id: int
    case_title: str
    filename: str
    file_type: str
    file_size_bytes: int
    is_encrypted: bool = True
    encryption_algorithm: str = "AES-256-GCM"
    uploaded_at: str


class ArchiveDraftItem(BaseModel):
    """Generated legal notice or complaint draft in archive."""
    id: int
    case_id: int
    case_title: str
    draft_type: str
    title: str
    has_pdf: bool = True
    has_docx: bool = True
    created_at: str


class PrivacySummaryResponse(BaseModel):
    """Data privacy and DPDPA posture disclosure."""
    tenant_pseudonym: str
    encryption_profile: Dict[str, Any]
    stored_entity_counts: Dict[str, int]
    dpdpa_compliance_readiness: str
    backup_retention_notice: str
    crypto_shredding_disclosure: str


class VoluntaryDataExportResponse(BaseModel):
    """Structured voluntary JSON export payload."""
    export_id: str
    generated_at: str
    tenant_pseudonym: str
    user_profile: Dict[str, Any]
    cases: List[Dict[str, Any]]
    query_history: List[Dict[str, Any]]
    export_sha256_hash: str
    export_notice: str


class MultiLayerDeletionResponse(BaseModel):
    """Result of multi-layer cascading account deletion and crypto-shredding."""
    status: str
    tenant_pseudonym: str
    relational_records_deleted: int
    vault_files_destroyed: int
    draft_files_destroyed: int
    chroma_entries_purged: int
    crypto_shredding_status: str
    backup_expiry_notice: str

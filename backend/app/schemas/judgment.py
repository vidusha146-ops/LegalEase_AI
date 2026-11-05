"""
LegalEase AI - Court Judgment & Case Similarity Schemas (Phase 7 Module 1)
Pydantic v2 schemas for landmark judgment indexing, proposition-level treatment,
similarity requests, and multi-axial relevance responses.
"""

from datetime import date, datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class PropositionTreatmentItem(BaseModel):
    """Subsequent judicial treatment record for an individual legal proposition."""
    proposition_id: str
    subsequent_judgment_citation: str
    subsequent_judgment_court: str
    subsequent_bench_size: int = 2
    exact_paragraph_pinpoint: str
    treatment_type: str = Field(
        ..., description="AFFIRMED | OVERRULED | NARROWED_MODIFIED | DISTINGUISHED | QUESTIONED"
    )
    treatment_explanation: str
    verification_status: str = Field(
        default="UNVERIFIED_TREATMENT", description="UNVERIFIED_TREATMENT | VERIFIED_TREATMENT"
    )
    reviewer_identifier: Optional[str] = None
    verification_timestamp: Optional[datetime] = None
    source_document_reference: str


class StatutoryLanguageProfile(BaseModel):
    """Constitutional & statutory language profile under Article 348 and court rules."""
    original_enacted_text: str
    original_enacted_language: str
    has_official_english_translation: bool = False
    english_translation_text: Optional[str] = None
    gazette_publication_details: Optional[str] = None
    publishing_authority: Optional[str] = None
    is_article_348_3_authoritative: bool = False
    conflict_detected: bool = False
    conflict_judicial_precedents: List[str] = Field(default_factory=list)


class JudgmentMatchItem(BaseModel):
    """Individual retrieved judgment match with decoupled factual, precedential, and jurisdictional scores."""
    judgment_key: str
    case_title: str
    canonical_citation: str
    court: str
    bench_type: str
    bench_size: int
    coram: str
    judgment_date: str
    legal_domain: str
    jurisdiction_state: Optional[str] = None

    # Multi-Axial Decoupled Metrics
    factual_alignment_index: float = Field(
        ..., ge=0.0, le=100.0, description="Normalized Cosine Similarity Indicator strictly in [0.0, 100.0]"
    )
    precedential_authority: str = Field(
        ..., description="TIER_1_SUPREME_COURT_CONSTITUTION_BENCH | TIER_2_SUPREME_COURT_DIVISION_BENCH | TIER_3_HIGH_COURT_FULL_BENCH | TIER_4_HIGH_COURT_DIVISION_BENCH | TIER_5_HIGH_COURT_SINGLE_BENCH | TIER_6_SPECIALIZED_TRIBUNAL"
    )
    jurisdictional_applicability: str = Field(
        ..., description="BINDING_CONSTITUTIONAL | BINDING_TERRITORIAL | PERSUASIVE_TERRITORIAL | SPECIALIZED_TRIBUNAL_GUIDANCE"
    )
    judgment_verification_status: str
    landmark_designation_status: str
    precedent_status: str

    # Overruling Alert
    is_overruled: bool = False
    overruling_citation: Optional[str] = None
    overruling_bench_size: Optional[int] = None
    overruling_paragraph_pinpoint: Optional[str] = None

    # Legal Content & Paragraph Pinpoints
    ratio_decidendi: str
    ratio_pinpoint: str
    factual_summary: str
    facts_pinpoint: str
    disposition_held: str

    # Structured Relevance Explainer
    factual_overlap_points: List[str] = Field(default_factory=list)
    shared_statutory_provisions: List[str] = Field(default_factory=list)
    distinguishing_factors: List[str] = Field(default_factory=list)

    # Proposition-Level Treatments & Provenance
    propositions: List[PropositionTreatmentItem] = Field(default_factory=list)
    source_url: str

    model_config = ConfigDict(from_attributes=True)


class CaseSearchRequest(BaseModel):
    """Citizen inquiry payload for case similarity search."""
    narrative: str = Field(..., min_length=10, description="Citizen dispute factual statement")
    case_id: Optional[int] = Field(None, description="Optional ID of active legal case (enforces user ownership)")
    domain: Optional[str] = Field(None, description="Optional domain filter (e.g. CONSUMER_PROTECTION)")
    jurisdiction_state: Optional[str] = Field(None, description="Citizen's state jurisdiction for binding/persuasive tagging")
    limit: int = Field(default=5, ge=1, le=20, description="Maximum number of matched judgments")
    include_unverified: bool = Field(default=False, description="Whether to include provisional/unverified research entries")


class CaseSearchResponse(BaseModel):
    """Response payload containing ranked judgment matches and mandatory Article 141 notice."""
    query_summary: str
    total_matches: int
    matches: List[JudgmentMatchItem]
    mandatory_precedent_notice: str
    evaluation_benchmark_note: str


class JudgmentDetailResponse(BaseModel):
    """Full detail view for a specific canonical judgment."""
    judgment_key: str
    case_title: str
    canonical_citation: str
    court: str
    bench_type: str
    bench_size: int
    coram: str
    judgment_date: str
    legal_domain: str
    jurisdiction_state: Optional[str] = None
    authoritative_language: str
    factual_summary: str
    facts_paragraph_pinpoint: str
    ratio_decidendi: str
    ratio_paragraph_pinpoint: str
    obiter_dicta: Optional[str] = None
    dicta_paragraph_pinpoint: Optional[str] = None
    disposition_held: str
    judgment_verification_status: str
    landmark_designation_status: str
    precedent_status: str
    overruling_citation: Optional[str] = None
    overruling_bench_size: Optional[int] = None
    overruling_paragraph_pinpoint: Optional[str] = None
    subsequent_propositions: List[PropositionTreatmentItem] = Field(default_factory=list)
    acts_cited: List[str] = Field(default_factory=list)
    source_url: str
    verified_at: Optional[datetime] = None
    verified_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

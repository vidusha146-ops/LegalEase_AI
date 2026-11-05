"""
LegalEase AI - Pydantic Schemas for Legal Problem Classifier & Situation Analyzer
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class PredictDomainRequest(BaseModel):
    narrative: str = Field(..., min_length=5, description="Citizen's legal grievance narrative")


class PredictDomainResponse(BaseModel):
    predicted_domain: str
    confidence: float
    probabilities: Dict[str, float]
    top_domains: List[Dict[str, Any]]


class GapDetectionRequest(BaseModel):
    narrative: str = Field(..., min_length=5)
    domain: Optional[str] = None


class GapItem(BaseModel):
    id: str
    name: str
    severity: str
    rationale: str


class FollowUpQuestionItem(BaseModel):
    ingredient_id: str
    name: str
    severity: str
    question: str
    rationale: str


class GapDetectionResponse(BaseModel):
    domain: str
    total_ingredients: int
    provided_count: int
    missing_count: int
    completeness_ratio: float
    provided_ingredients: List[GapItem]
    missing_ingredients: List[GapItem]
    follow_up_questions: List[FollowUpQuestionItem]


class AnalyzeSituationRequest(BaseModel):
    narrative: str = Field(..., min_length=10, description="Detailed legal problem narrative")
    incident_date: Optional[str] = Field(None, description="Date of incident in YYYY-MM-DD format")
    is_continuing_offense: bool = Field(False, description="Whether the offense spans multiple dates")
    preferred_language: str = Field("en", description="'en' for English or 'hi' for Hindi")


class InformationQualityScores(BaseModel):
    statutory_grounding: float
    factual_completeness: float
    citation_validity: float
    contradiction_penalty: float


class InformationQualityResponse(BaseModel):
    score: float
    badge: str
    badge_color: str
    summary: str
    component_scores: InformationQualityScores


class SituationAnalysisResponse(BaseModel):
    narrative: str
    predicted_domain: str
    classification_confidence: float
    top_candidate_domains: List[Dict[str, Any]]
    applicable_statutes: List[Dict[str, Any]]
    temporal_applicability: Optional[Dict[str, Any]]
    legal_gaps: Dict[str, Any]
    citation_verification: Dict[str, Any]
    uncertainty_analysis: Optional[Dict[str, Any]] = None
    statute_element_mapping: Optional[Dict[str, Any]] = None
    information_quality: InformationQualityResponse
    recommended_actions: List[Dict[str, str]]
    emergency_helplines: Dict[str, str]
    statutory_disclaimer: str


class ModelMetricsResponse(BaseModel):
    n_samples: int
    n_classes: int
    classes: List[str]
    cv_splits: int
    macro_precision: float
    macro_recall: float
    macro_f1: float
    weighted_f1: float
    fold_f1_scores: List[float]
    confusion_matrix: List[List[int]]
    dataset_limitations: List[str]


class StatuteExplanationRequest(BaseModel):
    narrative: str = Field(..., min_length=10)
    act_code: str = Field(...)
    section_number: str = Field(...)


class StatuteElementItem(BaseModel):
    id: str
    label: str
    statutory_text: str
    fulfilled: bool
    evidence_excerpt: Optional[str] = None
    explanation: str


class StatuteExplanationResponse(BaseModel):
    act_code: str
    section_number: str
    offence_title: str
    total_elements: int
    fulfilled_elements: int
    unfulfilled_elements: int
    fulfillment_ratio: float
    elements_breakdown: List[StatuteElementItem]


class ResolveGapsRequest(BaseModel):
    original_narrative: str = Field(..., min_length=10)
    domain: str = Field(...)
    incident_date: Optional[str] = None
    is_continuing_offense: bool = False
    preferred_language: str = "en"
    answers: Dict[str, str] = Field(..., description="Mapping of ingredient_id to user's answer")


class ResolveGapsResponse(BaseModel):
    augmented_narrative: str
    previous_score: float
    elevated_score: float
    score_delta: float
    resolved_count: int
    remaining_count: int
    upgraded_badge: str
    upgraded_badge_color: str
    updated_analysis: SituationAnalysisResponse
    statute_explanation: Optional[StatuteExplanationResponse] = None

"""
LegalEase AI - Multilingual Legal Assistant Schemas (Phase 7 Module 2)
Pydantic v2 validation models for language detection, query translation,
token-locked citation preservation, PII scrubbing verification, and glossary lookups.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class LanguageDetectionRequest(BaseModel):
    """Citizen input text for language and script identification."""
    text: str = Field(..., min_length=2, description="Text for script and language detection")


class LanguageDetectionResponse(BaseModel):
    """Language detection result with script metadata and confidence."""
    detected_language: str = Field(..., description="ISO 639-1 code: en | hi | bn | mr | ta | te | gu")
    language_name: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    script_name: str
    supported: bool


class QueryTranslationRequest(BaseModel):
    """Payload for translating citizen legal queries with token locking and PII scrubbing."""
    text: str = Field(..., min_length=3, description="Legal text or query to translate")
    source_language: Optional[str] = Field(None, description="Source language ISO code (auto-detected if None)")
    target_language: str = Field(default="en", description="Target language ISO code (e.g. en, hi, bn, mr, ta, te, gu)")
    consent_for_external_processing: bool = Field(
        default=False,
        description="Explicit citizen consent to transmit scrubbed text to external LLM provider. Fails closed to local offline if False."
    )


class QueryTranslationResponse(BaseModel):
    """Response containing token-preserved translation, provider tracking, and Article 348 notice."""
    original_text: str
    detected_source_language: str
    target_language: str
    translated_text: str
    locked_citations: List[str] = Field(default_factory=list)
    provider_used: str = Field(..., description="LOCAL_OFFLINE_GLOSSARY | EXTERNAL_GROUNDED_LLM")
    pii_scrubbed: bool
    redacted_pii_types: List[str] = Field(default_factory=list)
    fail_closed_triggered: bool = False
    blocking_reason: Optional[str] = None
    uncertified_translation_disclaimer: str


class MultilingualExplanationRequest(BaseModel):
    """Request for multilingual rights guidance grounded in verified legal knowledge base."""
    narrative: str = Field(..., min_length=10, description="Citizen dispute narrative")
    target_language: str = Field(default="hi", description="Citizen preferred regional language (hi, bn, mr, ta, te, gu, en)")
    domain: Optional[str] = Field(None, description="Optional legal domain filter")
    consent_for_external_processing: bool = Field(
        default=False,
        description="Citizen consent for external LLM processing. If False, strictly executes local offline template engine."
    )


class MultilingualExplanationResponse(BaseModel):
    """Multilingual legal advice payload with locked statutory citations and verified glossary."""
    target_language: str
    language_name: str
    translated_summary: str
    applicable_statutory_provisions: List[str] = Field(default_factory=list)
    procedural_steps: List[str] = Field(default_factory=list)
    verified_glossary_terms: List[Dict[str, Any]] = Field(default_factory=list)
    provider_used: str
    uncertified_translation_disclaimer: str
    mandatory_advocates_act_notice: str


class GlossaryItemResponse(BaseModel):
    """Verified legislative glossary item."""
    term_id: str
    english_term: str
    domain: str
    legal_definition: str
    statutory_context: str
    official_reference: str
    translations: Dict[str, str]

    model_config = ConfigDict(from_attributes=True)

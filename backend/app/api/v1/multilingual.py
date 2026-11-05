"""
LegalEase AI - Multilingual Legal Assistant Router (Phase 7 Module 2)
FastAPI endpoints for language detection, query translation,
token-locked citation preservation, verified glossary lookup, and multilingual legal guidance.
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, status

from app.services.multilingual_assistant import (
    MultilingualAssistantService,
    SUPPORTED_LANGUAGES,
)
from app.services.legal_glossary import LegalGlossaryService
from app.schemas.multilingual import (
    LanguageDetectionRequest,
    LanguageDetectionResponse,
    QueryTranslationRequest,
    QueryTranslationResponse,
    MultilingualExplanationRequest,
    MultilingualExplanationResponse,
    GlossaryItemResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/multilingual", tags=["Multilingual Legal Assistant"])


@router.post("/detect-language", response_model=LanguageDetectionResponse, status_code=status.HTTP_200_OK)
async def detect_language_endpoint(request: LanguageDetectionRequest):
    """
    Detects script and language for input text across supported Indian languages
    (Hindi, Bengali, Marathi, Tamil, Telugu, Gujarati, and English).
    """
    return MultilingualAssistantService.detect_language(request.text)


@router.post("/translate-query", response_model=QueryTranslationResponse, status_code=status.HTTP_200_OK)
async def translate_query_endpoint(request: QueryTranslationRequest):
    """
    Translates citizen legal query into English for semantic vector search,
    preserving legal citations via token locking and applying deterministic PII scrubbing.
    Fails closed to local offline processing if ambiguous numeric sequences (>= 9 digits)
    are detected or if explicit user consent is False.
    """
    return await MultilingualAssistantService.translate_query(
        text=request.text,
        source_language=request.source_language,
        target_language=request.target_language,
        consent_for_external_processing=request.consent_for_external_processing,
    )


@router.post("/explain", response_model=MultilingualExplanationResponse, status_code=status.HTTP_200_OK)
async def explain_grievance_multilingual(request: MultilingualExplanationRequest):
    """
    Generates plain-language rights guidance in the citizen's chosen Indian language,
    grounded in the verified knowledge base with locked statutory citations and verified glossary definitions.
    """
    if request.target_language not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Language '{request.target_language}' is not supported. Supported: {list(SUPPORTED_LANGUAGES.keys())}",
        )

    return await MultilingualAssistantService.generate_multilingual_explanation(
        narrative=request.narrative,
        target_language=request.target_language,
        domain=request.domain,
        consent_for_external_processing=request.consent_for_external_processing,
    )


@router.get("/glossary", response_model=List[GlossaryItemResponse], status_code=status.HTTP_200_OK)
async def get_legal_glossary(
    domain: Optional[str] = Query(None, description="Optional domain filter"),
    query: Optional[str] = Query(None, description="Search term in English or regional language"),
):
    """
    Retrieves verified legislative legal terminology translated across 6 Indian regional languages,
    sourced from Official Languages Commission / Vidhi Sahitya Prakashan.
    """
    if query:
        return LegalGlossaryService.search_glossary(query)
    if domain:
        return LegalGlossaryService.get_terms_by_domain(domain)
    return LegalGlossaryService.get_all_terms()


@router.get("/languages", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def get_supported_languages():
    """
    Lists all supported Indian languages with their ISO codes, native names, and scripts.
    """
    return {
        "supported_languages": SUPPORTED_LANGUAGES,
        "total_supported": len(SUPPORTED_LANGUAGES),
        "article_348_advisory": (
            "Under Article 348 of the Constitution of India, translations provided are non-certified "
            "advisory aids for citizen comprehension. Authoritative Bare Act text remains legally controlling."
        ),
    }

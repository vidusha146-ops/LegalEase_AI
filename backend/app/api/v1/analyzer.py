"""
LegalEase AI - API Endpoints for ML Classifier & Situation Analyzer
"""

import json
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status

from app.schemas.analyzer import (
    PredictDomainRequest,
    PredictDomainResponse,
    GapDetectionRequest,
    GapDetectionResponse,
    AnalyzeSituationRequest,
    SituationAnalysisResponse,
    ModelMetricsResponse,
    StatuteExplanationRequest,
    StatuteExplanationResponse,
    ResolveGapsRequest,
    ResolveGapsResponse,
)
from app.ml.classifier import get_classifier, METRICS_PATH
from app.services.gap_detector import LegalGapDetector
from app.services.situation_analyzer import get_situation_analyzer
from app.services.explainability import ExplainableLegalIntelligenceEngine
from app.services.gemini_analyzer import GroundedGeminiAnalyzer

router = APIRouter(prefix="/analyzer", tags=["Situation Analyzer & ML Classifier"])


@router.post(
    "/predict-domain",
    response_model=PredictDomainResponse,
    summary="Predict Legal Problem Domain via ML",
    description="Uses trained TF-IDF + Logistic Regression pipeline to classify citizen text into 10 Indian legal domains.",
)
async def predict_domain(payload: PredictDomainRequest) -> Dict[str, Any]:
    try:
        classifier = get_classifier()
        prediction = classifier.predict(payload.narrative)
        return prediction
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Classification failed: {str(e)}",
        )


@router.post(
    "/detect-gaps",
    response_model=GapDetectionResponse,
    summary="Statutory Gap Detection & Follow-up Questions",
    description="Identifies missing factual ingredients against statutory checklists and returns prioritized interactive follow-up questions.",
)
async def detect_gaps(payload: GapDetectionRequest) -> Dict[str, Any]:
    try:
        domain = payload.domain
        if not domain:
            classifier = get_classifier()
            pred = classifier.predict(payload.narrative)
            domain = pred["predicted_domain"]

        report = LegalGapDetector.detect_gaps(
            text=payload.narrative,
            domain=domain,
        )
        return report
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gap detection failed: {str(e)}",
        )


@router.post(
    "/analyze-situation",
    response_model=SituationAnalysisResponse,
    summary="Comprehensive Legal Situation Analysis",
    description="Synthesizes ML classification, ChromaDB Bare Act retrieval, BNS-IPC crosswalk, gap detection, and mathematical information quality scoring.",
)
async def analyze_situation(payload: AnalyzeSituationRequest) -> Dict[str, Any]:
    try:
        analyzer = get_situation_analyzer()
        analysis = analyzer.analyze_situation(
            narrative=payload.narrative,
            incident_date=payload.incident_date,
            is_continuing_offense=payload.is_continuing_offense,
            preferred_language=payload.preferred_language,
        )
        return analysis
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Situation analysis failed: {str(e)}",
        )


@router.get(
    "/model-metrics",
    response_model=ModelMetricsResponse,
    summary="ML Model Cross-Validation Metrics & Confusion Matrix",
    description="Returns empirical Stratified 5-Fold Cross-Validation evaluation metrics, class-wise F1, and confusion matrix.",
)
async def get_model_metrics() -> Dict[str, Any]:
    try:
        if not METRICS_PATH.exists():
            classifier = get_classifier()
            classifier.ensure_model_loaded()

        with open(METRICS_PATH, "r", encoding="utf-8") as f:
            metrics = json.load(f)
        return metrics
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not retrieve model metrics: {str(e)}",
        )


@router.post(
    "/explain-statute",
    response_model=StatuteExplanationResponse,
    summary="Statutory Element Decomposition & Mapping",
    description="Decomposes a specific Indian statutory section into elemental ingredients and maps user facts to each requirement.",
)
async def explain_statute(payload: StatuteExplanationRequest) -> Dict[str, Any]:
    try:
        explanation = ExplainableLegalIntelligenceEngine.explain_statute_mapping(
            narrative=payload.narrative,
            act_code=payload.act_code,
            section_number=payload.section_number,
        )
        return explanation
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Statute explanation failed: {str(e)}",
        )


@router.post(
    "/resolve-gaps",
    response_model=ResolveGapsResponse,
    summary="Interactive Legal Gap Resolution & Score Elevation",
    description="Merges citizen answers to follow-up questions, recalculates gap completeness, and elevates the Information Quality score.",
)
async def resolve_gaps(payload: ResolveGapsRequest) -> Dict[str, Any]:
    try:
        analyzer = get_situation_analyzer()

        # Step 1: Initial analysis score baseline
        initial_analysis = analyzer.analyze_situation(
            narrative=payload.original_narrative,
            incident_date=payload.incident_date,
            is_continuing_offense=payload.is_continuing_offense,
            preferred_language=payload.preferred_language,
        )
        prev_score = initial_analysis["information_quality"]["score"]

        # Step 2: Augment narrative with citizen's answers
        supplementary_lines = []
        for ing_id, ans in payload.answers.items():
            if ans and ans.strip():
                supplementary_lines.append(f"{ing_id.replace('_', ' ').title()}: {ans.strip()}")

        supplementary_text = " [SUPPLEMENTARY DETAILS PROVIDED BY CITIZEN]: " + "; ".join(supplementary_lines)
        augmented = payload.original_narrative + " " + supplementary_text

        # Step 3: Recalculate full situation analysis on augmented narrative
        updated_analysis = analyzer.analyze_situation(
            narrative=augmented,
            incident_date=payload.incident_date,
            is_continuing_offense=payload.is_continuing_offense,
            preferred_language=payload.preferred_language,
        )

        elevated_score = updated_analysis["information_quality"]["score"]
        score_delta = round(elevated_score - prev_score, 4)

        # Step 4: Optional Explainability breakdown on primary statute
        statute_expl = None
        if updated_analysis["applicable_statutes"]:
            top_st = updated_analysis["applicable_statutes"][0]
            if top_st.get("act_code") and top_st.get("section_number"):
                statute_expl = ExplainableLegalIntelligenceEngine.explain_statute_mapping(
                    narrative=augmented,
                    act_code=top_st["act_code"],
                    section_number=top_st["section_number"],
                )

        resolved_count = len(payload.answers)
        remaining_count = updated_analysis["legal_gaps"]["missing_count"]

        return {
            "augmented_narrative": augmented,
            "previous_score": prev_score,
            "elevated_score": elevated_score,
            "score_delta": score_delta,
            "resolved_count": resolved_count,
            "remaining_count": remaining_count,
            "upgraded_badge": updated_analysis["information_quality"]["badge"],
            "upgraded_badge_color": updated_analysis["information_quality"]["badge_color"],
            "updated_analysis": updated_analysis,
            "statute_explanation": statute_expl,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gap resolution failed: {str(e)}",
        )


@router.post(
    "/generate-ai-explanation",
    summary="Structured Grounded AI Explanation (Gemini API)",
    description="Generates plain-language rights and procedural roadmap grounded strictly in retrieved Bare Acts.",
)
async def generate_ai_explanation(payload: AnalyzeSituationRequest) -> Dict[str, Any]:
    try:
        analyzer = get_situation_analyzer()
        base_analysis = analyzer.analyze_situation(
            narrative=payload.narrative,
            incident_date=payload.incident_date,
            is_continuing_offense=payload.is_continuing_offense,
            preferred_language=payload.preferred_language,
        )

        ai_explanation = await GroundedGeminiAnalyzer.generate_grounded_explanation(
            narrative=payload.narrative,
            predicted_domain=base_analysis["predicted_domain"],
            retrieved_statutes=base_analysis["applicable_statutes"],
            missing_ingredients=base_analysis["legal_gaps"]["missing_ingredients"],
            language=payload.preferred_language,
        )

        return {
            "domain": base_analysis["predicted_domain"],
            "information_quality": base_analysis["information_quality"],
            "grounded_ai_guidance": ai_explanation,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI generation failed: {str(e)}",
        )

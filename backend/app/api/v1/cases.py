"""
LegalEase AI - Case Similarity Search Router (Phase 7 Module 1)
Endpoints for precedent research, judicial hierarchy assessment,
ratio decidendi pinpoints, and citation verification under Indian law.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.case import LegalCase
from app.models.user import User
from app.api.deps import get_current_user_optional
from app.services.case_similarity import CaseSimilaritySearchService
from app.schemas.judgment import (
    CaseSearchRequest,
    CaseSearchResponse,
    JudgmentDetailResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cases", tags=["Case Similarity Search & Precedent Intelligence"])
similarity_service = CaseSimilaritySearchService()


@router.post("/similar", response_model=CaseSearchResponse, status_code=status.HTTP_200_OK)
async def search_similar_precedents(
    request: CaseSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Performs multi-axial similarity search across canonical Indian landmark court judgments.
    Computes Normalized Cosine Similarity strictly in [0.0, 100.0], precedent hierarchy tier,
    and Article 141 binding vs territorial applicability.
    """
    # Enforce case ownership validation if case_id is provided
    if request.case_id is not None:
        case_stmt = select(LegalCase).where(LegalCase.id == request.case_id)
        res = await db.execute(case_stmt)
        case = res.scalar_one_or_none()
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Legal case with ID {request.case_id} not found.",
            )
        if current_user is not None and case.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: Case does not belong to the authenticated citizen.",
            )

    user_id = current_user.id if current_user else None
    return await similarity_service.search_similar_cases(
        request=request,
        session=db,
        current_user_id=user_id,
    )


@router.get("/judgments", response_model=List[JudgmentDetailResponse], status_code=status.HTTP_200_OK)
async def list_canonical_judgments(
    domain: Optional[str] = Query(None, description="Optional domain filter"),
    limit: int = Query(50, ge=1, le=100, description="Page limit"),
    offset: int = Query(0, ge=0, description="Page offset"),
    db: AsyncSession = Depends(get_db),
):
    """
    Lists canonical landmark court judgments stored in the precedent registry.
    """
    return await similarity_service.list_judgments(
        session=db,
        domain=domain,
        limit=limit,
        offset=offset,
    )


@router.get("/judgments/{judgment_key}", response_model=JudgmentDetailResponse, status_code=status.HTTP_200_OK)
async def get_judgment_details(
    judgment_key: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieves complete verified details, paragraph pinpoints, subsequent judicial treatments,
    and authoritative source reference for a specific canonical landmark judgment.
    """
    judgment = await similarity_service.get_judgment_by_key(judgment_key, db)
    if not judgment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Canonical judgment '{judgment_key}' not found in precedent registry.",
        )
    return judgment

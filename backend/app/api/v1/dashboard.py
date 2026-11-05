"""
LegalEase AI - Citizen User Dashboard & Privacy Router (Phase 7 Module 3)
Endpoints for:
- Protected dashboard metrics & profile updates
- Citizen case lifecycle management
- Persistent search query history
- Encrypted evidence vault & document archive
- DPDPA privacy summary, voluntary data export & multi-layer deletion
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.user import UserResponse
from app.services.dashboard_service import DashboardService
from app.schemas.dashboard import (
    DashboardSummaryResponse,
    UserProfileUpdate,
    CaseSummaryItem,
    CaseCreateRequest,
    CaseProgressUpdateRequest,
    CaseDetailResponse,
    QueryHistoryItem,
    VaultDocumentItem,
    ArchiveDraftItem,
    PrivacySummaryResponse,
    VoluntaryDataExportResponse,
    MultiLayerDeletionResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["Citizen User Dashboard & Privacy Management"])


# =============================================================================
# 1. DASHBOARD OVERVIEW & PROFILE
# =============================================================================

@router.get("/summary", response_model=DashboardSummaryResponse, status_code=status.HTTP_200_OK)
async def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves consolidated overview metrics for the citizen dashboard."""
    return await DashboardService.get_dashboard_summary(current_user, db)


@router.put("/profile", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def update_profile(
    update: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Updates citizen profile preferences (e.g. name, language)."""
    updated_user = await DashboardService.update_user_profile(current_user, update, db)
    return UserResponse.model_validate(updated_user)


# =============================================================================
# 2. CASE MANAGEMENT & LIFECYCLE PROGRESSION
# =============================================================================

@router.get("/cases", response_model=List[CaseSummaryItem], status_code=status.HTTP_200_OK)
async def list_user_cases(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lists all legal matters / situations belonging to the authenticated citizen."""
    return await DashboardService.get_user_cases(current_user.id, db)


@router.post("/cases", response_model=CaseSummaryItem, status_code=status.HTTP_201_CREATED)
async def create_user_case(
    req: CaseCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Creates a new legal case container for the authenticated citizen."""
    return await DashboardService.create_user_case(current_user.id, req, db)


@router.get("/cases/{case_id}", response_model=CaseDetailResponse, status_code=status.HTTP_200_OK)
async def get_case_detail(
    case_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves full case details with ownership verification (403 on tenant mismatch)."""
    detail, is_forbidden = await DashboardService.get_case_detail(case_id, current_user.id, db)
    if is_forbidden:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Case does not belong to the authenticated citizen.",
        )
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Legal case #{case_id} not found.",
        )
    return detail


@router.patch("/cases/{case_id}/status", response_model=CaseSummaryItem, status_code=status.HTTP_200_OK)
async def update_case_status(
    case_id: int,
    req: CaseProgressUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Updates case progression status (e.g. NEW -> ACTIVE -> DOCUMENTED -> DRAFTED -> RESOLVED)."""
    summary, is_forbidden = await DashboardService.update_case_status(case_id, current_user.id, req.status, db)
    if is_forbidden:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Case does not belong to the authenticated citizen.",
        )
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Legal case #{case_id} not found.",
        )
    return summary


@router.delete("/cases/{case_id}", status_code=status.HTTP_200_OK)
async def delete_user_case(
    case_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Permanently deletes a legal case and shreds all associated evidence files."""
    deleted, is_forbidden = await DashboardService.delete_user_case(case_id, current_user.id, db)
    if is_forbidden:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Case does not belong to the authenticated citizen.",
        )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Legal case #{case_id} not found.",
        )
    return {"status": "success", "message": f"Case #{case_id} and associated documents permanently deleted."}


# =============================================================================
# 3. PERSISTENT QUERY HISTORY
# =============================================================================

@router.get("/queries", response_model=List[QueryHistoryItem], status_code=status.HTTP_200_OK)
async def get_query_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetches citizen's persistent search and precedent inquiry history."""
    return await DashboardService.get_query_history(current_user.id, db)


@router.delete("/queries/{query_id}", status_code=status.HTTP_200_OK)
async def delete_single_query(
    query_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Deletes a specific query log entry."""
    rows = await DashboardService.delete_query_history(current_user.id, db, query_id=query_id)
    if rows == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Query entry not found.")
    return {"status": "success", "message": f"Query #{query_id} deleted."}


@router.delete("/queries", status_code=status.HTTP_200_OK)
async def clear_all_queries(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Clears all query history entries for the authenticated citizen."""
    rows = await DashboardService.delete_query_history(current_user.id, db)
    return {"status": "success", "message": f"Cleared {rows} search query records."}


# =============================================================================
# 4. EVIDENCE VAULT & DOCUMENT ARCHIVE
# =============================================================================

@router.get("/vault/documents", response_model=List[VaultDocumentItem], status_code=status.HTTP_200_OK)
async def get_vault_documents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lists citizen's encrypted evidence documents across all cases."""
    return await DashboardService.get_vault_documents(current_user.id, db)


@router.get("/archive/drafts", response_model=List[ArchiveDraftItem], status_code=status.HTTP_200_OK)
async def get_archive_drafts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lists citizen's generated legal drafts (PDF/DOCX) across all cases."""
    return await DashboardService.get_archive_drafts(current_user.id, db)


# =============================================================================
# 5. PRIVACY CONTROLS, EXPORT & DELETION
# =============================================================================

@router.get("/privacy/summary", response_model=PrivacySummaryResponse, status_code=status.HTTP_200_OK)
async def get_privacy_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns data privacy posture, entity counts, encryption profile, and DPDPA notice."""
    return await DashboardService.get_privacy_summary(current_user.id, db)


@router.post("/privacy/export", response_model=VoluntaryDataExportResponse, status_code=status.HTTP_200_OK)
async def voluntary_data_export(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Produces a structured voluntary JSON data export with cryptographic integrity signature."""
    return await DashboardService.generate_voluntary_export(current_user, db)


@router.delete("/privacy/account", response_model=MultiLayerDeletionResponse, status_code=status.HTTP_200_OK)
async def delete_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Executes multi-layer cascading account deletion, physical file shredding, and DEK crypto-shredding."""
    return await DashboardService.execute_multi_layer_deletion(current_user, db)

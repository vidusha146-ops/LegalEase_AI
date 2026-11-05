"""
LegalEase AI - AI Legal Document Generation Studio Router (Phase 6)
FastAPI endpoints for generating, previewing, editing, exporting, and managing
court-ready legal drafts (Consumer Complaints, Legal Notices, RTI, Police Complaints).
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse, Response
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.case import LegalCase
from app.models.draft import LegalDraft
from app.models.evidence import EvidenceDocument
from app.models.user import User
from app.api.deps import get_current_user_optional
from app.services.legal_drafting_studio import LegalDraftingStudioService, NON_ADVOCACY_DISCLAIMER_TEXT
from app.services.document_export import DocumentExportService, STORAGE_DIR
from app.schemas.draft import (
    DraftGenerateRequest,
    DraftUpdateRequest,
    DraftResponse,
    DraftExportResponse,
    MissingInfoItem,
    VerifiedCitationItem,
    ExhibitItem,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/drafts", tags=["AI Legal Document Generation Studio"])
drafting_service = LegalDraftingStudioService()


@router.post("/generate", response_model=DraftResponse, status_code=status.HTTP_201_CREATED)
async def generate_legal_draft(
    request: DraftGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Generates a structured, evidence-linked legal draft.
    Validates statutory citations against the canonical index and detects missing factual information.
    """
    case_id = request.case_id or 1

    # Ensure LegalCase container exists
    case_stmt = select(LegalCase).where(LegalCase.id == case_id)
    case_res = await db.execute(case_stmt)
    case = case_res.scalar_one_or_none()

    if not case:
        user_id = current_user.id if current_user else 1
        # Check if user 1 exists, else create user container
        user_stmt = select(User).where(User.id == user_id)
        user_res = await db.execute(user_stmt)
        user = user_res.scalar_one_or_none()
        if not user:
            from app.core.security import get_password_hash
            user = User(
                id=user_id,
                email="citizen.drafting@example.in",
                hashed_password=get_password_hash("StrongPassword123!"),
                full_name="Citizen User",
                is_active=True,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

        case = LegalCase(
            id=case_id,
            user_id=user_id,
            title=f"Legal Matter #{case_id} - Drafting Workspace",
            raw_description=request.narrative or "Case created for document generation.",
            status="ACTIVE",
        )
        db.add(case)
        await db.commit()
        await db.refresh(case)

    # Fetch uploaded evidence documents for this case
    ev_stmt = select(EvidenceDocument).where(EvidenceDocument.case_id == case_id)
    ev_res = await db.execute(ev_stmt)
    evidence_records = ev_res.scalars().all()
    evidence_dicts = []
    for doc in evidence_records:
        doc_category = "OTHER_EVIDENCE"
        if doc.contradiction_warnings_json:
            try:
                c_data = json.loads(doc.contradiction_warnings_json)
                doc_category = c_data.get("category", "OTHER_EVIDENCE")
            except Exception:
                pass
        evidence_dicts.append({
            "id": doc.id,
            "document_id": doc.id,
            "filename": doc.filename,
            "category": doc_category,
        })

    # Generate draft using LegalDraftingStudioService
    try:
        draft_payload = drafting_service.generate_legal_draft(
            request=request,
            evidence_documents=evidence_dicts,
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))

    # Persist in LegalDraft database table
    metadata_json = json.dumps({
        "missing_information": [m.model_dump() for m in draft_payload["missing_information"]],
        "verified_citations": [c.model_dump() for c in draft_payload["verified_citations"]],
        "exhibits": [e.model_dump() for e in draft_payload["exhibits"]],
    })

    legal_draft = LegalDraft(
        case_id=case_id,
        draft_type=draft_payload["draft_type"],
        title=draft_payload["title"],
        content_markdown=draft_payload["content_markdown"],
        draft_metadata_json=metadata_json,
        disclaimer_accepted=True,
    )
    db.add(legal_draft)
    await db.commit()
    await db.refresh(legal_draft)

    # Pre-render initial PDF and DOCX exports
    try:
        _, _, pdf_path = DocumentExportService.generate_pdf(
            draft_id=legal_draft.id,
            title=legal_draft.title,
            content_markdown=legal_draft.content_markdown,
            draft_type=legal_draft.draft_type,
            save_to_disk=True,
        )
        _, _, docx_path = DocumentExportService.generate_docx(
            draft_id=legal_draft.id,
            title=legal_draft.title,
            content_markdown=legal_draft.content_markdown,
            draft_type=legal_draft.draft_type,
            save_to_disk=True,
        )
        legal_draft.pdf_path = pdf_path
        legal_draft.docx_path = docx_path
        await db.commit()
        await db.refresh(legal_draft)
    except Exception as e:
        logger.warning(f"Initial PDF/DOCX render notice: {e}")

    return DraftResponse(
        id=legal_draft.id,
        case_id=legal_draft.case_id,
        draft_type=legal_draft.draft_type,
        title=legal_draft.title,
        content_markdown=legal_draft.content_markdown,
        pdf_path=legal_draft.pdf_path,
        docx_path=legal_draft.docx_path,
        missing_information=draft_payload["missing_information"],
        verified_citations=draft_payload["verified_citations"],
        exhibits=draft_payload["exhibits"],
        disclaimer=NON_ADVOCACY_DISCLAIMER_TEXT,
        created_at=legal_draft.created_at,
        updated_at=legal_draft.updated_at,
    )


@router.get("/{draft_id}", response_model=DraftResponse)
async def get_legal_draft(
    draft_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Retrieves full legal draft with metadata, missing information, and verified citations."""
    stmt = select(LegalDraft).where(LegalDraft.id == draft_id)
    res = await db.execute(stmt)
    draft = res.scalar_one_or_none()

    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Legal draft with ID {draft_id} not found.",
        )

    meta = {}
    if draft.draft_metadata_json:
        try:
            meta = json.loads(draft.draft_metadata_json)
        except Exception:
            meta = {}

    missing_items = [MissingInfoItem(**m) for m in meta.get("missing_information", [])]
    citation_items = [VerifiedCitationItem(**c) for c in meta.get("verified_citations", [])]
    exhibit_items = [ExhibitItem(**e) for e in meta.get("exhibits", [])]

    return DraftResponse(
        id=draft.id,
        case_id=draft.case_id,
        draft_type=draft.draft_type,
        title=draft.title,
        content_markdown=draft.content_markdown,
        pdf_path=draft.pdf_path,
        docx_path=draft.docx_path,
        missing_information=missing_items,
        verified_citations=citation_items,
        exhibits=exhibit_items,
        disclaimer=NON_ADVOCACY_DISCLAIMER_TEXT,
        created_at=draft.created_at,
        updated_at=draft.updated_at,
    )


@router.get("/case/{case_id}", response_model=List[DraftResponse])
async def list_case_drafts(
    case_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Lists all legal drafts generated for a specific case."""
    stmt = select(LegalDraft).where(LegalDraft.case_id == case_id).order_by(LegalDraft.id.desc())
    res = await db.execute(stmt)
    drafts = res.scalars().all()

    response_list = []
    for d in drafts:
        meta = {}
        if d.draft_metadata_json:
            try:
                meta = json.loads(d.draft_metadata_json)
            except Exception:
                meta = {}
        response_list.append(
            DraftResponse(
                id=d.id,
                case_id=d.case_id,
                draft_type=d.draft_type,
                title=d.title,
                content_markdown=d.content_markdown,
                pdf_path=d.pdf_path,
                docx_path=d.docx_path,
                missing_information=[MissingInfoItem(**m) for m in meta.get("missing_information", [])],
                verified_citations=[VerifiedCitationItem(**c) for c in meta.get("verified_citations", [])],
                exhibits=[ExhibitItem(**e) for e in meta.get("exhibits", [])],
                disclaimer=NON_ADVOCACY_DISCLAIMER_TEXT,
                created_at=d.created_at,
                updated_at=d.updated_at,
            )
        )

    return response_list


@router.put("/{draft_id}", response_model=DraftResponse)
async def update_legal_draft(
    draft_id: int,
    request: DraftUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Updates the content markdown or title of a legal draft.
    Automatically regenerates and updates PDF and DOCX files.
    """
    stmt = select(LegalDraft).where(LegalDraft.id == draft_id)
    res = await db.execute(stmt)
    draft = res.scalar_one_or_none()

    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Legal draft with ID {draft_id} not found.",
        )

    draft.content_markdown = request.content_markdown
    if request.title:
        draft.title = request.title

    # Regenerate PDF & DOCX
    _, _, pdf_path = DocumentExportService.generate_pdf(
        draft_id=draft.id,
        title=draft.title,
        content_markdown=draft.content_markdown,
        draft_type=draft.draft_type,
        save_to_disk=True,
    )
    _, _, docx_path = DocumentExportService.generate_docx(
        draft_id=draft.id,
        title=draft.title,
        content_markdown=draft.content_markdown,
        draft_type=draft.draft_type,
        save_to_disk=True,
    )
    draft.pdf_path = pdf_path
    draft.docx_path = docx_path

    await db.commit()
    await db.refresh(draft)

    meta = {}
    if draft.draft_metadata_json:
        try:
            meta = json.loads(draft.draft_metadata_json)
        except Exception:
            meta = {}

    return DraftResponse(
        id=draft.id,
        case_id=draft.case_id,
        draft_type=draft.draft_type,
        title=draft.title,
        content_markdown=draft.content_markdown,
        pdf_path=draft.pdf_path,
        docx_path=draft.docx_path,
        missing_information=[MissingInfoItem(**m) for m in meta.get("missing_information", [])],
        verified_citations=[VerifiedCitationItem(**c) for c in meta.get("verified_citations", [])],
        exhibits=[ExhibitItem(**e) for e in meta.get("exhibits", [])],
        disclaimer=NON_ADVOCACY_DISCLAIMER_TEXT,
        created_at=draft.created_at,
        updated_at=draft.updated_at,
    )


@router.get("/{draft_id}/export/pdf")
async def export_draft_pdf(
    draft_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Exports and streams court-ready PDF file for download."""
    stmt = select(LegalDraft).where(LegalDraft.id == draft_id)
    res = await db.execute(stmt)
    draft = res.scalar_one_or_none()

    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Legal draft with ID {draft_id} not found.",
        )

    # Check if pre-rendered PDF exists, otherwise generate dynamically
    if draft.pdf_path and os.path.exists(draft.pdf_path):
        return FileResponse(
            draft.pdf_path,
            media_type="application/pdf",
            filename=os.path.basename(draft.pdf_path),
        )

    pdf_bytes, _, _ = DocumentExportService.generate_pdf(
        draft_id=draft.id,
        title=draft.title,
        content_markdown=draft.content_markdown,
        draft_type=draft.draft_type,
        save_to_disk=False,
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=draft_{draft_id}.pdf"},
    )


@router.get("/{draft_id}/export/docx")
async def export_draft_docx(
    draft_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Exports and streams court-ready DOCX document for download."""
    stmt = select(LegalDraft).where(LegalDraft.id == draft_id)
    res = await db.execute(stmt)
    draft = res.scalar_one_or_none()

    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Legal draft with ID {draft_id} not found.",
        )

    if draft.docx_path and os.path.exists(draft.docx_path):
        return FileResponse(
            draft.docx_path,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=os.path.basename(draft.docx_path),
        )

    docx_bytes, _, _ = DocumentExportService.generate_docx(
        draft_id=draft.id,
        title=draft.title,
        content_markdown=draft.content_markdown,
        draft_type=draft.draft_type,
        save_to_disk=False,
    )

    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename=draft_{draft_id}.docx"},
    )


@router.delete("/{draft_id}", status_code=status.HTTP_200_OK)
async def delete_legal_draft(
    draft_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Deletes a legal draft and any associated generated export files."""
    stmt = select(LegalDraft).where(LegalDraft.id == draft_id)
    res = await db.execute(stmt)
    draft = res.scalar_one_or_none()

    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Legal draft with ID {draft_id} not found.",
        )

    # Delete export files if on disk
    for path in (draft.pdf_path, draft.docx_path):
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except Exception as e:
                logger.warning(f"Could not remove export file {path}: {e}")

    await db.delete(draft)
    await db.commit()

    return {"message": f"Legal draft {draft_id} successfully deleted.", "draft_id": draft_id}

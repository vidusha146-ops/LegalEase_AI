"""
LegalEase AI - Evidence & Timeline API Router (Phase 5)
Endpoints for document upload, OCR extraction, entity extraction,
chronological timeline builder, consistency analysis, and statutory fact mapping.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.case import LegalCase
from app.models.evidence import EvidenceDocument
from app.models.timeline import TimelineEvent
from app.models.user import User
from app.api.deps import get_current_user_optional
from app.services.document_intelligence import (
    DocumentIntelligenceService,
    DocumentProcessingError,
    EncryptedDocumentError,
    CorruptedDocumentError,
    UnsupportedDocumentError,
)
from app.services.information_extraction import LegalInformationExtractor
from app.services.evidence_classifier import EvidenceClassifierService
from app.services.timeline_engine import ChronologicalTimelineEngine
from app.services.consistency_analyzer import EvidenceConsistencyAnalyzer
from app.services.evidence_mapper import EvidenceToLegalFactMapper
from app.schemas.evidence import (
    EvidenceUploadResponse,
    ReclassifyRequest,
    ReclassifyResponse,
    ManualTimelineEventRequest,
    TimelineEventResponse,
    CaseTimelineResponse,
    ConsistencyCheckRequest,
    ConsistencyCheckResponse,
    EvidenceToStatuteRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/evidence", tags=["Evidence & Document Intelligence"])
timeline_router = APIRouter(prefix="/timeline", tags=["Chronological Timeline"])


@router.post(
    "/upload",
    response_model=List[EvidenceUploadResponse],
    summary="Upload & Process Evidence Documents",
    description="Accepts multiple PDF, DOCX, or Image files, performs OCR/text extraction, entity extraction, and classification.",
)
async def upload_evidence(
    case_id: int = Form(...),
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> List[Dict[str, Any]]:
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files uploaded.",
        )

    # Verify or create case if not present (allows guest exploratory uploads)
    case_stmt = select(LegalCase).where(LegalCase.id == case_id)
    case_res = await db.execute(case_stmt)
    case = case_res.scalar_one_or_none()

    if not case:
        # Auto-create case container for standalone evidence analysis
        user_id = current_user.id if current_user else 1
        case = LegalCase(
            id=case_id,
            user_id=user_id,
            title=f"Legal Dispute Evidence Vault #{case_id}",
            raw_description="Case workspace initialized for evidence ingestion.",
            status="ACTIVE",
        )
        db.add(case)
        await db.commit()
        await db.refresh(case)

    # Ensure storage upload directory exists
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    processed_responses: List[Dict[str, Any]] = []

    for file in files:
        original_name = file.filename or "evidence_file"
        file_bytes = await file.read()

        try:
            # 1. Document Intelligence: Validation & Text Extraction
            extraction = DocumentIntelligenceService.extract_document_text(
                file_bytes=file_bytes,
                filename=original_name,
            )
        except EncryptedDocumentError as ede:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ede))
        except CorruptedDocumentError as cde:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(cde))
        except UnsupportedDocumentError as ude:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ude))
        except DocumentProcessingError as dpe:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(dpe))
        except Exception as e:
            logger.error(f"Unexpected document extraction failure on {original_name}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Processing failed: {e}")

        # 2. Information Extraction: Legal Entities & Dates
        entities = LegalInformationExtractor.extract_entities_from_pages(
            pages=extraction.get("pages", []),
            document_filename=original_name,
        )

        # 3. Evidence Classification
        classification = EvidenceClassifierService.classify_document(
            text=extraction.get("full_text", ""),
            filename=original_name,
        )

        # 4. Save file to local secure storage
        sanitized_name = DocumentIntelligenceService.sanitize_filename(original_name)
        storage_filename = f"case_{case_id}_{extraction['sha256_hash'][:12]}_{sanitized_name}"
        saved_file_path = upload_dir / storage_filename
        with open(saved_file_path, "wb") as f_out:
            f_out.write(file_bytes)

        # 5. Persist EvidenceDocument record in Database
        doc_record = EvidenceDocument(
            case_id=case_id,
            filename=original_name,
            file_path=str(saved_file_path),
            file_type=extraction.get("file_type", "UNKNOWN"),
            file_size_bytes=len(file_bytes),
            ocr_extracted_text=extraction.get("full_text", ""),
            extracted_entities_json=json.dumps(entities),
            contradiction_warnings_json=json.dumps(classification),
            is_processed=True,
        )
        db.add(doc_record)
        await db.commit()
        await db.refresh(doc_record)

        # 6. Auto-create Timeline Events from extracted procedural events
        for ev in entities.get("events", []):
            timeline_ev = TimelineEvent(
                case_id=case_id,
                evidence_id=doc_record.id,
                event_date=ev.get("date", "UNDATED"),
                event_title=ev.get("title", "Document Milestone"),
                event_description=f"Identified from {original_name} (Page {ev.get('page_number', 1)}): {ev.get('evidence_snippet', '')}",
                source_reference=f"{original_name} (p. {ev.get('page_number', 1)})",
                confidence_level=ev.get("confidence", "HIGH"),
            )
            db.add(timeline_ev)
        await db.commit()

        # Text snippet preview
        full_txt = extraction.get("full_text", "")
        preview = full_txt[:300] + ("..." if len(full_txt) > 300 else "")

        processed_responses.append({
            "document_id": doc_record.id,
            "case_id": case_id,
            "filename": original_name,
            "file_type": extraction.get("file_type", "UNKNOWN"),
            "file_size_bytes": len(file_bytes),
            "sha256_hash": extraction.get("sha256_hash", ""),
            "category": classification.get("category", "OTHER_EVIDENCE"),
            "category_title": classification.get("category_title", "Other Evidence"),
            "classification_confidence": classification.get("confidence", 0.5),
            "total_pages": extraction.get("total_pages", 1),
            "is_scanned": extraction.get("is_scanned", False),
            "ocr_performed": extraction.get("ocr_performed", False),
            "extracted_entities": entities,
            "extracted_text_preview": preview,
        })

    return processed_responses


@router.get(
    "/case/{case_id}",
    summary="List Evidence Documents for a Case",
    description="Returns all uploaded evidence documents and metadata for the specified case.",
)
async def list_case_evidence(
    case_id: int,
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    stmt = select(EvidenceDocument).where(EvidenceDocument.case_id == case_id)
    res = await db.execute(stmt)
    docs = res.scalars().all()

    output = []
    for d in docs:
        entities = json.loads(d.extracted_entities_json or "{}")
        classification = json.loads(d.contradiction_warnings_json or "{}")
        preview = (d.ocr_extracted_text or "")[:200]
        output.append({
            "document_id": d.id,
            "case_id": d.case_id,
            "filename": d.filename,
            "file_type": d.file_type,
            "file_size_bytes": d.file_size_bytes,
            "category": classification.get("category", "OTHER_EVIDENCE"),
            "category_title": classification.get("category_title", "Other Evidence"),
            "classification_confidence": classification.get("confidence", 0.5),
            "is_processed": d.is_processed,
            "extracted_entities": entities,
            "extracted_text_preview": preview,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        })
    return output


@router.get(
    "/{doc_id}",
    summary="Get Specific Evidence Document Details",
    description="Returns complete OCR extracted text and structured entities for a document.",
)
async def get_evidence_document(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    stmt = select(EvidenceDocument).where(EvidenceDocument.id == doc_id)
    res = await db.execute(stmt)
    doc = res.scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence document not found.")

    entities = json.loads(doc.extracted_entities_json or "{}")
    classification = json.loads(doc.contradiction_warnings_json or "{}")

    return {
        "document_id": doc.id,
        "case_id": doc.case_id,
        "filename": doc.filename,
        "file_type": doc.file_type,
        "file_size_bytes": doc.file_size_bytes,
        "category": classification.get("category", "OTHER_EVIDENCE"),
        "category_title": classification.get("category_title", "Other Evidence"),
        "confidence": classification.get("confidence", 0.5),
        "ocr_extracted_text": doc.ocr_extracted_text,
        "extracted_entities": entities,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
    }


@router.patch(
    "/{doc_id}/reclassify",
    response_model=ReclassifyResponse,
    summary="User Manual Reclassification",
    description="Allows citizen to manually override and correct the category of an evidence document.",
)
async def reclassify_document(
    doc_id: int,
    payload: ReclassifyRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    stmt = select(EvidenceDocument).where(EvidenceDocument.id == doc_id)
    res = await db.execute(stmt)
    doc = res.scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence document not found.")

    prev_data = json.loads(doc.contradiction_warnings_json or "{}")
    prev_cat = prev_data.get("category", "OTHER_EVIDENCE")

    reclassified = EvidenceClassifierService.reclassify(payload.new_category)
    doc.contradiction_warnings_json = json.dumps(reclassified)
    await db.commit()

    return {
        "document_id": doc.id,
        "previous_category": prev_cat,
        "updated_category": reclassified["category"],
        "category_title": reclassified["category_title"],
        "is_user_corrected": True,
    }


@router.delete(
    "/{doc_id}",
    summary="Delete Evidence Document",
    description="Permanently deletes an evidence document and associated file.",
)
async def delete_evidence_document(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    stmt = select(EvidenceDocument).where(EvidenceDocument.id == doc_id)
    res = await db.execute(stmt)
    doc = res.scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence document not found.")

    # Remove physical file if exists
    try:
        p = Path(doc.file_path)
        if p.exists():
            p.unlink()
    except Exception as e:
        logger.warning(f"Could not delete physical file {doc.file_path}: {e}")

    await db.delete(doc)
    await db.commit()

    return {"message": "Evidence document deleted successfully.", "document_id": doc_id}


# =============================================================================
# TIMELINE & CONSISTENCY ENDPOINTS
# =============================================================================

@timeline_router.get(
    "/case/{case_id}",
    response_model=CaseTimelineResponse,
    summary="Get Case Chronological Timeline",
    description="Builds sorted chronological incident timeline from extracted and manual events, detecting temporal gaps.",
)
async def get_case_timeline(
    case_id: int,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    stmt = select(TimelineEvent).where(TimelineEvent.case_id == case_id)
    res = await db.execute(stmt)
    events = res.scalars().all()

    doc_events = []
    manual_events = []

    for ev in events:
        ev_dict = {
            "id": ev.id,
            "case_id": ev.case_id,
            "evidence_id": ev.evidence_id,
            "event_date": ev.event_date,
            "event_title": ev.event_title,
            "event_description": ev.event_description,
            "source_reference": ev.source_reference,
            "confidence_level": ev.confidence_level,
        }
        if ev.evidence_id:
            doc_events.append(ev_dict)
        else:
            manual_events.append(ev_dict)

    timeline_res = ChronologicalTimelineEngine.build_timeline(
        document_events=doc_events,
        manual_events=manual_events,
    )
    timeline_res["case_id"] = case_id
    return timeline_res


@timeline_router.post(
    "/event",
    response_model=TimelineEventResponse,
    summary="Add Manual Timeline Event",
    description="Allows citizen to manually add a verified chronological incident to the case timeline.",
)
async def add_manual_timeline_event(
    payload: ManualTimelineEventRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    # Normalize date
    norm_date = payload.event_date.strip()
    if "/" in norm_date:
        parts = norm_date.split("/")
        if len(parts) == 3 and len(parts[2]) == 4:
            norm_date = f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"

    new_ev = TimelineEvent(
        case_id=payload.case_id,
        evidence_id=None,
        event_date=norm_date,
        event_title=payload.event_title,
        event_description=payload.event_description,
        source_reference=payload.source_reference or "Citizen Statement",
        confidence_level=payload.confidence_level or "HIGH",
    )
    db.add(new_ev)
    await db.commit()
    await db.refresh(new_ev)

    return {
        "id": new_ev.id,
        "case_id": new_ev.case_id,
        "evidence_id": None,
        "event_date": new_ev.event_date,
        "event_title": new_ev.event_title,
        "event_description": new_ev.event_description,
        "source_reference": new_ev.source_reference,
        "confidence_level": new_ev.confidence_level,
    }


@timeline_router.delete(
    "/event/{event_id}",
    summary="Delete Timeline Event",
    description="Deletes a timeline event.",
)
async def delete_timeline_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    stmt = select(TimelineEvent).where(TimelineEvent.id == event_id)
    res = await db.execute(stmt)
    ev = res.scalar_one_or_none()

    if not ev:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Timeline event not found.")

    await db.delete(ev)
    await db.commit()
    return {"message": "Timeline event deleted successfully.", "event_id": event_id}


@router.post(
    "/consistency-check",
    response_model=ConsistencyCheckResponse,
    summary="Evidence Consistency Analysis",
    description="Cross-examines uploaded documents and narrative to detect monetary variances and sequence anomalies.",
)
async def check_evidence_consistency(
    payload: ConsistencyCheckRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    stmt = select(EvidenceDocument).where(EvidenceDocument.case_id == payload.case_id)
    res = await db.execute(stmt)
    docs = res.scalars().all()

    docs_metadata = []
    for d in docs:
        entities = json.loads(d.extracted_entities_json or "{}")
        classification = json.loads(d.contradiction_warnings_json or "{}")
        docs_metadata.append({
            "filename": d.filename,
            "category": classification.get("category", "OTHER_EVIDENCE"),
            "dates": entities.get("dates", []),
            "monetary_amounts": entities.get("monetary_amounts", []),
        })

    analysis = EvidenceConsistencyAnalyzer.analyze_consistency(
        documents_metadata=docs_metadata,
        narrative=payload.narrative,
        predicted_domain=payload.predicted_domain,
        narrative_amount=payload.narrative_amount,
        narrative_date=payload.narrative_date,
    )
    analysis["case_id"] = payload.case_id
    return analysis


@router.post(
    "/map-to-statute",
    summary="Map Uploaded Evidence to Statutory Elements",
    description="Correlates authentic uploaded documents with statutory requirements under Explainable AI.",
)
async def map_evidence_to_statute_endpoint(
    payload: EvidenceToStatuteRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    docs_metadata = payload.uploaded_documents or []

    # If case_id provided, fetch documents from database
    if payload.case_id and not docs_metadata:
        stmt = select(EvidenceDocument).where(EvidenceDocument.case_id == payload.case_id)
        res = await db.execute(stmt)
        docs = res.scalars().all()
        for d in docs:
            cls_data = json.loads(d.contradiction_warnings_json or "{}")
            docs_metadata.append({
                "filename": d.filename,
                "category": cls_data.get("category", "OTHER_EVIDENCE"),
            })

    mapped = EvidenceToLegalFactMapper.map_evidence_to_statute(
        narrative=payload.narrative,
        act_code=payload.act_code,
        section_number=payload.section_number,
        uploaded_documents=docs_metadata,
    )
    return mapped

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.rag.citation_validator import LegalCitationValidator
from app.rag.crosswalk import BNSIPCCrosswalk
from app.rag.retriever import LegalKnowledgeRetriever

router = APIRouter(prefix="/statutes", tags=["Verified Legal Knowledge Base & RAG"])

retriever = LegalKnowledgeRetriever()
crosswalk = BNSIPCCrosswalk()
citation_validator = LegalCitationValidator()


class CitationVerifyRequest(BaseModel):
    text: str = Field(..., description="Legal complaint or text block containing statutory citations to verify")


class TemporalApplicabilityRequest(BaseModel):
    date_of_incident: str = Field(..., description="Date of incident in YYYY-MM-DD format")
    is_continuing: bool = Field(default=False, description="Whether the offence is continuing in nature")


@router.get("/search")
async def search_statutes(
    query: str = Query(..., min_length=3, description="Semantic search query describing the legal situation"),
    domain: Optional[str] = Query(None, description="Optional legal domain filter (e.g. CONSUMER_PROTECTION, CRIMINAL_LAW_BNS)"),
    act_code: Optional[str] = Query(None, description="Optional specific Act code filter (e.g. BNS_2023, IT_ACT_2000)"),
    top_k: int = Query(default=4, ge=1, le=10, description="Number of statutory provisions to retrieve"),
):
    """
    Performs semantic vector search across verified Indian Bare Acts in ChromaDB,
    optionally filtered by legal domain or Act code.
    """
    results = retriever.search_statutes(
        query=query,
        legal_domain=domain,
        act_code=act_code,
        top_k=top_k,
    )
    return {
        "query": query,
        "total_retrieved": len(results),
        "results": results,
    }


@router.get("/crosswalk/ipc/{ipc_section}")
async def lookup_ipc_to_bns(ipc_section: str):
    """
    Translates an IPC section to its corresponding BNS, 2023 equivalent,
    strictly distinguishing definition from punishment clauses.
    """
    mapping = crosswalk.lookup_by_ipc(ipc_section)
    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No verified BNS crosswalk mapping found for IPC Section '{ipc_section}'.",
        )
    return mapping


@router.get("/crosswalk/bns/{bns_section}")
async def lookup_bns_to_ipc(bns_section: str):
    """
    Translates a BNS section to its historical IPC equivalent,
    clarifying definition vs punishment roles.
    """
    mapping = crosswalk.lookup_by_bns(bns_section)
    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No verified IPC historical mapping found for BNS Section '{bns_section}'.",
        )
    return mapping


@router.post("/crosswalk/temporal-applicability")
async def evaluate_temporal_applicability(payload: TemporalApplicabilityRequest):
    """
    Evaluates applicable penal regime (IPC vs BNS) and criminal procedure (CrPC vs BNSS)
    based on Article 20(1) ex-post facto safeguards and Section 358 BNS / Section 531 BNSS savings clauses.
    """
    return crosswalk.evaluate_temporal_applicability(
        date_of_incident=payload.date_of_incident,
        is_continuing=payload.is_continuing,
    )


@router.post("/verify-citations")
async def verify_citations(payload: CitationVerifyRequest):
    """
    Scans a text narrative, extracts statutory citations via AST/regex,
    and cross-checks them against the Canonical Gazette Bare Act Index.
    """
    report = citation_validator.validate_text_citations(payload.text)
    return report

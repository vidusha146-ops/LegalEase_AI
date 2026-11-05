"""
LegalEase AI - Case Similarity Search Service (Phase 7 Module 1)
Production-grade multi-axial legal precedent similarity matching for Indian citizens.
Strictly decoupled scoring:
- Factual Alignment Index (Normalized Cosine Similarity strictly in [0.0, 100.0])
- Precedential Authority Tiering (Supreme Court Constitution Bench -> Single Bench)
- Jurisdictional Applicability (Article 141 Binding Constitutional vs Territorial/Persuasive)
- Overruled Landmark Alert & Quarantine for unverified entries
"""

import json
import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.judgment import CourtJudgment
from app.models.search_query import CaseSimilarityQuery
from app.rag.chroma_client import get_chroma_client
from app.schemas.judgment import (
    CaseSearchRequest,
    CaseSearchResponse,
    JudgmentMatchItem,
    JudgmentDetailResponse,
    PropositionTreatmentItem,
)

logger = logging.getLogger(__name__)

MANDATORY_ARTICLE_141_NOTICE = (
    "Under Article 141 of the Constitution of India, the law declared by the Supreme Court is binding "
    "on all courts within the territory of India. This case similarity analysis is an automated "
    "decision-support research tool provided strictly for informational purposes. In accordance with the "
    "Advocates Act, 1961 and Bar Council of India rules, this does not constitute legal representation, "
    "advocacy, or solicitation. Precedent interpretation must be verified with qualified legal counsel."
)

BENCHMARK_EVAL_NOTE = (
    "Evaluated against LegalEase AI Indian Court Judgment Precedent Benchmark "
    "(25 curated scenarios: 10 tuning, 15 held-out). Minimum precision target: >= 85%."
)


def compute_normalized_cosine_indicator(distance: float) -> float:
    """
    Computes Normalized Cosine Similarity Indicator strictly bound in [0.0, 100.0].
    Cosine distance d in Chroma is d = 1 - cos(u, v).
    cos(u, v) = 1.0 - d.
    If cos <= 0.0 -> 0.0.
    If cos > 0.0 -> round(cos * 100.0, 2).
    """
    if distance <= 0.0:
        return 100.0
    if distance >= 1.0:
        # Distance >= 1.0 implies orthogonal or negative cosine
        return 0.0
    cos_sim = max(0.0, 1.0 - distance)
    return round(cos_sim * 100.0, 2)


def determine_authority_tier(court: str, bench_size: int, bench_type: str) -> str:
    """Categorizes bench authority hierarchy under Indian constitutional law."""
    court_lower = court.lower()
    if "supreme court" in court_lower:
        if bench_size >= 5:
            return "TIER_1_SUPREME_COURT_CONSTITUTION_BENCH"
        return "TIER_2_SUPREME_COURT_DIVISION_BENCH"
    elif "high court" in court_lower:
        if bench_size >= 3:
            return "TIER_3_HIGH_COURT_FULL_BENCH"
        elif bench_size == 2:
            return "TIER_4_HIGH_COURT_DIVISION_BENCH"
        return "TIER_5_HIGH_COURT_SINGLE_BENCH"
    return "TIER_6_SPECIALIZED_TRIBUNAL"


def determine_jurisdictional_applicability(
    court: str,
    judgment_state: Optional[str],
    citizen_state: Optional[str],
    is_overruled: bool = False,
) -> str:
    """
    Computes jurisdictional applicability:
    - Supreme Court: BINDING_CONSTITUTIONAL (Article 141)
    - High Court (same state): BINDING_TERRITORIAL
    - High Court (different state): PERSUASIVE_TERRITORIAL
    - Tribunal: SPECIALIZED_TRIBUNAL_GUIDANCE
    """
    if is_overruled:
        return "OVERRULED_HISTORICAL_RECORD"

    court_lower = court.lower()
    if "supreme court" in court_lower:
        return "BINDING_CONSTITUTIONAL"

    if "high court" in court_lower:
        if not citizen_state or not judgment_state:
            return "BINDING_TERRITORIAL"
        if judgment_state.strip().lower() == citizen_state.strip().lower() or judgment_state == "All India":
            return "BINDING_TERRITORIAL"
        return "PERSUASIVE_TERRITORIAL"

    return "SPECIALIZED_TRIBUNAL_GUIDANCE"


def extract_factual_overlap(narrative: str, factual_summary: str, ratio: str) -> Tuple[List[str], List[str]]:
    """Generates structured overlap points and distinguishing factors."""
    overlap = []
    distinguishing = []

    words_narrative = set(re.findall(r"\b\w{4,}\b", narrative.lower()))
    words_facts = set(re.findall(r"\b\w{4,}\b", factual_summary.lower()))
    common = words_narrative.intersection(words_facts)

    # Key legal thematic tokens
    themes = {
        "theft": "Vehicle theft / stolen property insurance dispute",
        "delay": "Delayed delivery of possession / construction deficiency",
        "defect": "Manufacturing defect / sub-standard goods",
        "medical": "Medical negligence / duty of care by healthcare provider",
        "possession": "Real estate possession handover and interest compensation",
        "dishonour": "Negotiable instrument cheque dishonour under Section 138",
        "arbitration": "Arbitration clause invocation and Section 9/11 dispute",
        "maintenance": "Matrimonial maintenance and financial disclosure",
        "bail": "Arrest guidelines and non-custodial bail standards",
        "privacy": "Personal data protection and fundamental right to privacy",
        "rera": "Real Estate Regulatory Authority statutory consumer remedy",
        "repudiation": "Insurance claim repudiation on non-standard technical grounds",
    }

    matched_themes = [label for key, label in themes.items() if key in narrative.lower() and key in (factual_summary + ratio).lower()]
    if matched_themes:
        overlap.extend(matched_themes)
    elif common:
        overlap.append(f"Factual concordance identified on core elements: {', '.join(list(common)[:4])}")
    else:
        overlap.append("General statutory principles of consumer protection and contractual fairness apply.")

    # Distinguishing factors check
    if "commercial" in narrative.lower() and "personal" in factual_summary.lower():
        distinguishing.append("Dispute involves commercial purpose whereas precedent addresses personal/domestic use.")
    if "fir" in narrative.lower() and "fir" not in factual_summary.lower():
        distinguishing.append("Factual narrative references criminal FIR registration not present in underlying precedent.")
    if not distinguishing:
        distinguishing.append("Verify exact documentary terms (e.g. policy conditions, builder-buyer agreement clauses).")

    return overlap, distinguishing


class CaseSimilaritySearchService:
    """Service layer for searching, ranking, and analyzing landmark court precedents."""

    def __init__(self):
        self.chroma = get_chroma_client()

    async def search_similar_cases(
        self,
        request: CaseSearchRequest,
        session: AsyncSession,
        current_user_id: Optional[int] = None,
    ) -> CaseSearchResponse:
        """
        Executes vector search against ChromaDB public collection 'indian_court_judgments',
        enriches with relational database records, scores multi-axially, and logs query.
        """
        where_filter = {}
        if request.domain:
            where_filter["legal_domain"] = request.domain

        # Retrieve candidates from ChromaDB
        k = max(request.limit * 2, 8)
        raw_results = self.chroma.query_judgments(
            query_text=request.narrative,
            n_results=k,
            where_filter=where_filter if where_filter else None,
        )

        # Aggregate top chunks per judgment key
        judgment_scores: Dict[str, float] = {}
        for r in raw_results:
            meta = r.get("metadata", {})
            key = meta.get("judgment_key")
            if not key:
                continue
            dist = r.get("distance", 1.0)
            score = compute_normalized_cosine_indicator(dist)
            # Take highest score across chunks (ratio vs facts)
            if key not in judgment_scores or score > judgment_scores[key]:
                judgment_scores[key] = score

        if not judgment_scores:
            # Fallback: fetch default landmark judgments from database if vector matches empty
            stmt = select(CourtJudgment).limit(request.limit)
            if request.domain:
                stmt = select(CourtJudgment).where(CourtJudgment.legal_domain == request.domain).limit(request.limit)
            fallback_res = await session.execute(stmt)
            fallback_judgments = fallback_res.scalars().all()
            for fj in fallback_judgments:
                judgment_scores[fj.judgment_key] = 50.0

        # Query database for full metadata
        candidate_keys = list(judgment_scores.keys())
        stmt = select(CourtJudgment).where(CourtJudgment.judgment_key.in_(candidate_keys))
        db_res = await session.execute(stmt)
        judgments_map = {j.judgment_key: j for j in db_res.scalars().all()}

        matched_items: List[JudgmentMatchItem] = []

        for key, factual_score in sorted(judgment_scores.items(), key=lambda x: x[1], reverse=True):
            j = judgments_map.get(key)
            if not j:
                continue

            # Quarantine filter: exclude unverified unless specifically requested
            if not request.include_unverified and j.judgment_verification_status != "VERIFIED":
                continue

            is_overruled = (j.precedent_status == "OVERRULED")
            authority_tier = determine_authority_tier(j.court, j.bench_size, j.bench_type)
            jurisdictional_app = determine_jurisdictional_applicability(
                j.court, j.jurisdiction_state, request.jurisdiction_state, is_overruled
            )

            # Extract propositions
            propositions = []
            if j.subsequent_propositions_json:
                try:
                    props_raw = json.loads(j.subsequent_propositions_json)
                    for p in props_raw:
                        propositions.append(PropositionTreatmentItem(**p))
                except Exception as e:
                    logger.warning(f"Error parsing subsequent propositions for {key}: {e}")

            # Parse acts cited
            acts_cited = []
            if j.acts_cited_json:
                try:
                    acts_cited = json.loads(j.acts_cited_json)
                except Exception:
                    acts_cited = []

            overlap_points, dist_factors = extract_factual_overlap(
                request.narrative, j.factual_summary, j.ratio_decidendi
            )

            item = JudgmentMatchItem(
                judgment_key=j.judgment_key,
                case_title=j.case_title,
                canonical_citation=j.canonical_citation,
                court=j.court,
                bench_type=j.bench_type,
                bench_size=j.bench_size,
                coram=j.coram or "Bench of Supreme Court / High Court",
                judgment_date=j.judgment_date.isoformat() if j.judgment_date else "Unknown",
                legal_domain=j.legal_domain,
                jurisdiction_state=j.jurisdiction_state,
                factual_alignment_index=factual_score,
                precedential_authority=authority_tier,
                jurisdictional_applicability=jurisdictional_app,
                judgment_verification_status=j.judgment_verification_status,
                landmark_designation_status=j.landmark_designation_status,
                precedent_status=j.precedent_status,
                is_overruled=is_overruled,
                overruling_citation=j.overruling_citation,
                overruling_bench_size=j.overruling_bench_size,
                overruling_paragraph_pinpoint=j.overruling_paragraph_pinpoint,
                ratio_decidendi=j.ratio_decidendi,
                ratio_pinpoint=j.ratio_paragraph_pinpoint or "para 1",
                factual_summary=j.factual_summary,
                facts_pinpoint=j.facts_paragraph_pinpoint or "para 1",
                disposition_held=j.disposition_held,
                factual_overlap_points=overlap_points,
                shared_statutory_provisions=acts_cited,
                distinguishing_factors=dist_factors,
                propositions=propositions,
                source_url=j.source_url or "https://main.sci.gov.in",
            )
            matched_items.append(item)

            if len(matched_items) >= request.limit:
                break

        # Log query to database
        if current_user_id is not None:
            retrieved_keys = [m.judgment_key for m in matched_items]
            metrics = {
                "total_candidates": len(candidate_keys),
                "top_score": matched_items[0].factual_alignment_index if matched_items else 0.0,
                "domain_filter": request.domain,
            }
            query_log = CaseSimilarityQuery(
                user_id=current_user_id,
                case_id=request.case_id,
                query_text=request.narrative,
                legal_domain=request.domain,
                retrieved_judgment_ids_json=json.dumps(retrieved_keys),
                search_metrics_json=json.dumps(metrics),
            )
            session.add(query_log)
            await session.commit()

        return CaseSearchResponse(
            query_summary=request.narrative[:120] + ("..." if len(request.narrative) > 120 else ""),
            total_matches=len(matched_items),
            matches=matched_items,
            mandatory_precedent_notice=MANDATORY_ARTICLE_141_NOTICE,
            evaluation_benchmark_note=BENCHMARK_EVAL_NOTE,
        )

    async def get_judgment_by_key(
        self,
        judgment_key: str,
        session: AsyncSession,
    ) -> Optional[JudgmentDetailResponse]:
        """Fetches complete canonical judgment details by key."""
        stmt = select(CourtJudgment).where(CourtJudgment.judgment_key == judgment_key)
        res = await session.execute(stmt)
        j = res.scalar_one_or_none()
        if not j:
            return None

        propositions = []
        if j.subsequent_propositions_json:
            try:
                props_raw = json.loads(j.subsequent_propositions_json)
                for p in props_raw:
                    propositions.append(PropositionTreatmentItem(**p))
            except Exception as e:
                logger.warning(f"Error parsing subsequent propositions: {e}")

        acts_cited = []
        if j.acts_cited_json:
            try:
                acts_cited = json.loads(j.acts_cited_json)
            except Exception:
                acts_cited = []

        return JudgmentDetailResponse(
            judgment_key=j.judgment_key,
            case_title=j.case_title,
            canonical_citation=j.canonical_citation,
            court=j.court,
            bench_type=j.bench_type,
            bench_size=j.bench_size,
            coram=j.coram or "Bench of Supreme Court / High Court",
            judgment_date=j.judgment_date.isoformat() if j.judgment_date else "Unknown",
            legal_domain=j.legal_domain,
            jurisdiction_state=j.jurisdiction_state,
            authoritative_language=j.authoritative_language or "English",
            factual_summary=j.factual_summary,
            facts_paragraph_pinpoint=j.facts_paragraph_pinpoint or "para 1",
            ratio_decidendi=j.ratio_decidendi,
            ratio_paragraph_pinpoint=j.ratio_paragraph_pinpoint or "para 1",
            obiter_dicta=j.obiter_dicta,
            dicta_paragraph_pinpoint=j.dicta_paragraph_pinpoint,
            disposition_held=j.disposition_held,
            judgment_verification_status=j.judgment_verification_status,
            landmark_designation_status=j.landmark_designation_status,
            precedent_status=j.precedent_status,
            overruling_citation=j.overruling_citation,
            overruling_bench_size=j.overruling_bench_size,
            overruling_paragraph_pinpoint=j.overruling_paragraph_pinpoint,
            subsequent_propositions=propositions,
            acts_cited=acts_cited,
            source_url=j.source_url or "https://main.sci.gov.in",
            verified_at=j.verified_at,
            verified_by=j.verified_by,
        )

    async def list_judgments(
        self,
        session: AsyncSession,
        domain: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[JudgmentDetailResponse]:
        """Lists canonical landmark judgments with optional domain filtering."""
        stmt = select(CourtJudgment)
        if domain:
            stmt = stmt.where(CourtJudgment.legal_domain == domain)
        stmt = stmt.offset(offset).limit(limit)

        res = await session.execute(stmt)
        judgments = res.scalars().all()
        results = []
        for j in judgments:
            props = []
            if j.subsequent_propositions_json:
                try:
                    for p in json.loads(j.subsequent_propositions_json):
                        props.append(PropositionTreatmentItem(**p))
                except Exception:
                    pass
            acts = []
            if j.acts_cited_json:
                try:
                    acts = json.loads(j.acts_cited_json)
                except Exception:
                    pass

            results.append(
                JudgmentDetailResponse(
                    judgment_key=j.judgment_key,
                    case_title=j.case_title,
                    canonical_citation=j.canonical_citation,
                    court=j.court,
                    bench_type=j.bench_type,
                    bench_size=j.bench_size,
                    coram=j.coram or "Bench of Supreme Court / High Court",
                    judgment_date=j.judgment_date.isoformat() if j.judgment_date else "Unknown",
                    legal_domain=j.legal_domain,
                    jurisdiction_state=j.jurisdiction_state,
                    authoritative_language=j.authoritative_language or "English",
                    factual_summary=j.factual_summary,
                    facts_paragraph_pinpoint=j.facts_paragraph_pinpoint or "para 1",
                    ratio_decidendi=j.ratio_decidendi,
                    ratio_paragraph_pinpoint=j.ratio_paragraph_pinpoint or "para 1",
                    obiter_dicta=j.obiter_dicta,
                    dicta_paragraph_pinpoint=j.dicta_paragraph_pinpoint,
                    disposition_held=j.disposition_held,
                    judgment_verification_status=j.judgment_verification_status,
                    landmark_designation_status=j.landmark_designation_status,
                    precedent_status=j.precedent_status,
                    overruling_citation=j.overruling_citation,
                    overruling_bench_size=j.overruling_bench_size,
                    overruling_paragraph_pinpoint=j.overruling_paragraph_pinpoint,
                    subsequent_propositions=props,
                    acts_cited=acts,
                    source_url=j.source_url or "https://main.sci.gov.in",
                    verified_at=j.verified_at,
                    verified_by=j.verified_by,
                )
            )
        return results

"""
LegalEase AI - Landmark Court Judgments Ingestion Script
Phase 7: Case Similarity Search

Reads canonical_judgments.json, populates the CourtJudgment SQL table,
and indexes semantic chunks into ChromaDB collection 'indian_court_judgments'.
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal, init_db
from app.models.judgment import CourtJudgment
from app.rag.chroma_client import get_chroma_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("index_judgments")

DATA_FILE = Path(__file__).resolve().parent / "canonical_judgments.json"


async def ingest_judgments():
    if not DATA_FILE.exists():
        logger.error(f"Data file not found at {DATA_FILE}")
        return

    logger.info("Initializing database schema...")
    await init_db()

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        judgments_data: List[Dict[str, Any]] = json.load(f)

    logger.info(f"Loaded {len(judgments_data)} judgments from {DATA_FILE}")

    # 1. SQL Ingestion
    async with AsyncSessionLocal() as session:
        for item in judgments_data:
            key = item["judgment_key"]
            stmt = select(CourtJudgment).where(CourtJudgment.judgment_key == key)
            res = await session.execute(stmt)
            existing = res.scalar_one_or_none()

            j_date = None
            if item.get("judgment_date"):
                try:
                    j_date = datetime.strptime(item["judgment_date"], "%Y-%m-%d").date()
                except ValueError:
                    j_date = None

            v_date = None
            if item.get("verified_at"):
                try:
                    v_date = datetime.fromisoformat(item["verified_at"].replace("Z", "+00:00"))
                except ValueError:
                    v_date = None

            if existing:
                # Update fields
                existing.case_title = item["case_title"]
                existing.canonical_citation = item["canonical_citation"]
                existing.court = item["court"]
                existing.bench_type = item["bench_type"]
                existing.bench_size = item["bench_size"]
                existing.coram = item.get("coram")
                existing.judgment_date = j_date
                existing.legal_domain = item["legal_domain"]
                existing.jurisdiction_state = item.get("jurisdiction_state", "All India")
                existing.authoritative_language = item.get("authoritative_language", "English")
                existing.factual_summary = item["factual_summary"]
                existing.facts_paragraph_pinpoint = item.get("facts_paragraph_pinpoint")
                existing.ratio_decidendi = item["ratio_decidendi"]
                existing.ratio_paragraph_pinpoint = item.get("ratio_paragraph_pinpoint")
                existing.obiter_dicta = item.get("obiter_dicta")
                existing.dicta_paragraph_pinpoint = item.get("dicta_paragraph_pinpoint")
                existing.disposition_held = item["disposition_held"]
                existing.judgment_verification_status = item.get("judgment_verification_status", "VERIFIED")
                existing.landmark_designation_status = item.get("landmark_designation_status", "DESIGNATED_LANDMARK")
                existing.precedent_status = item.get("precedent_status", "AFFIRMED_LANDMARK")
                existing.overruling_citation = item.get("overruling_citation")
                existing.overruling_bench_size = item.get("overruling_bench_size")
                existing.overruling_paragraph_pinpoint = item.get("overruling_paragraph_pinpoint")
                existing.subsequent_propositions_json = json.dumps(item.get("subsequent_propositions", []))
                existing.acts_cited_json = json.dumps(item.get("acts_cited", []))
                existing.source_url = item.get("source_url")
                existing.verified_at = v_date
                existing.verified_by = item.get("verified_by")
            else:
                judgment = CourtJudgment(
                    judgment_key=key,
                    case_title=item["case_title"],
                    canonical_citation=item["canonical_citation"],
                    court=item["court"],
                    bench_type=item["bench_type"],
                    bench_size=item["bench_size"],
                    coram=item.get("coram"),
                    judgment_date=j_date,
                    legal_domain=item["legal_domain"],
                    jurisdiction_state=item.get("jurisdiction_state", "All India"),
                    authoritative_language=item.get("authoritative_language", "English"),
                    factual_summary=item["factual_summary"],
                    facts_paragraph_pinpoint=item.get("facts_paragraph_pinpoint"),
                    ratio_decidendi=item["ratio_decidendi"],
                    ratio_paragraph_pinpoint=item.get("ratio_paragraph_pinpoint"),
                    obiter_dicta=item.get("obiter_dicta"),
                    dicta_paragraph_pinpoint=item.get("dicta_paragraph_pinpoint"),
                    disposition_held=item["disposition_held"],
                    judgment_verification_status=item.get("judgment_verification_status", "VERIFIED"),
                    landmark_designation_status=item.get("landmark_designation_status", "DESIGNATED_LANDMARK"),
                    precedent_status=item.get("precedent_status", "AFFIRMED_LANDMARK"),
                    overruling_citation=item.get("overruling_citation"),
                    overruling_bench_size=item.get("overruling_bench_size"),
                    overruling_paragraph_pinpoint=item.get("overruling_paragraph_pinpoint"),
                    subsequent_propositions_json=json.dumps(item.get("subsequent_propositions", [])),
                    acts_cited_json=json.dumps(item.get("acts_cited", [])),
                    source_url=item.get("source_url"),
                    verified_at=v_date,
                    verified_by=item.get("verified_by"),
                )
                session.add(judgment)

        await session.commit()
        logger.info(f"Successfully synced {len(judgments_data)} judgments to database table 'court_judgments'.")

    # 2. ChromaDB Ingestion
    chroma = get_chroma_client()
    chunks = []
    for item in judgments_data:
        key = item["judgment_key"]
        acts_str = ", ".join(item.get("acts_cited", []))

        # Chunk 1: Ratio & Held (Primary legal principle)
        ratio_text = (
            f"Case: {item['case_title']} ({item['canonical_citation']})\n"
            f"Court: {item['court']} ({item['bench_size']}-Judge {item['bench_type']})\n"
            f"Legal Domain: {item['legal_domain']}\n"
            f"Ratio Decidendi: {item['ratio_decidendi']}\n"
            f"Holding: {item['disposition_held']}"
        )
        chunks.append({
            "chunk_id": f"{key}_ratio",
            "text": ratio_text,
            "metadata": {
                "judgment_key": key,
                "case_title": item["case_title"],
                "canonical_citation": item["canonical_citation"],
                "court": item["court"],
                "bench_size": item["bench_size"],
                "legal_domain": item["legal_domain"],
                "jurisdiction_state": item.get("jurisdiction_state", "All India"),
                "precedent_status": item.get("precedent_status", "AFFIRMED_LANDMARK"),
                "judgment_verification_status": item.get("judgment_verification_status", "VERIFIED"),
                "landmark_designation_status": item.get("landmark_designation_status", "DESIGNATED_LANDMARK"),
                "chunk_type": "ratio",
                "acts_cited": acts_str,
            }
        })

        # Chunk 2: Facts & Statutory Concordance
        facts_text = (
            f"Case: {item['case_title']} ({item['canonical_citation']})\n"
            f"Factual Summary: {item['factual_summary']}\n"
            f"Statutory Provisions: {acts_str}\n"
            f"Obiter Dicta: {item.get('obiter_dicta') or ''}"
        )
        chunks.append({
            "chunk_id": f"{key}_facts",
            "text": facts_text,
            "metadata": {
                "judgment_key": key,
                "case_title": item["case_title"],
                "canonical_citation": item["canonical_citation"],
                "court": item["court"],
                "bench_size": item["bench_size"],
                "legal_domain": item["legal_domain"],
                "jurisdiction_state": item.get("jurisdiction_state", "All India"),
                "precedent_status": item.get("precedent_status", "AFFIRMED_LANDMARK"),
                "judgment_verification_status": item.get("judgment_verification_status", "VERIFIED"),
                "landmark_designation_status": item.get("landmark_designation_status", "DESIGNATED_LANDMARK"),
                "chunk_type": "facts",
                "acts_cited": acts_str,
            }
        })

    logger.info(f"Upserting {len(chunks)} judgment chunks into ChromaDB collection '{chroma.judgments_collection.name}'...")
    indexed_count = chroma.add_judgment_chunks(chunks)
    total_in_chroma = chroma.count_judgments()
    logger.info(f"Indexing complete! Indexed chunks: {indexed_count}, Total in collection: {total_in_chroma}")


if __name__ == "__main__":
    asyncio.run(ingest_judgments())

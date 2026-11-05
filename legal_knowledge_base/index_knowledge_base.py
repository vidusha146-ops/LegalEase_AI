import json
import logging
import os
import sys
from pathlib import Path

# Add backend directory to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.core.config import settings
from app.rag.chunker import LegalDocumentChunker
from app.rag.chroma_client import ChromaDBClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("knowledge_base_indexer")

RAW_DIR = Path(__file__).resolve().parent / "raw_statutes"


def ingest_bare_acts_into_chromadb(persist_dir: str = None) -> int:
    """
    Ingests all official Bare Acts from raw_statutes into the persistent ChromaDB collection.
    """
    target_dir = persist_dir or settings.CHROMA_PERSIST_DIRECTORY
    logger.info(f"Initializing ChromaDB client at: {target_dir}")
    client = ChromaDBClient(persist_dir=target_dir)
    chunker = LegalDocumentChunker(max_chunk_chars=1200)

    statute_files = list(RAW_DIR.glob("*.json"))
    logger.info(f"Found {len(statute_files)} official Bare Act files.")

    all_chunks = []
    total_sections = 0

    for s_file in statute_files:
        with open(s_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        act_code = data["act_code"]
        act_title = data["act_title"]
        source_url = data["source_url"]
        legal_domain = data["legal_domain"]
        verification_date = data.get("verification_date", "2026-11-04")

        for sec in data["sections"]:
            total_sections += 1
            chunks = chunker.chunk_statute_section(
                act_code=act_code,
                act_title=act_title,
                section_number=sec["section_number"],
                section_title=sec["section_title"],
                chapter=sec.get("chapter", "General Provisions"),
                legal_domain=legal_domain,
                provision_type=sec["provision_type"],
                full_text=sec["full_text"],
                source_url=source_url,
                verification_date=verification_date,
                historical_counterpart=sec.get("historical_counterpart", ""),
            )
            all_chunks.extend(chunks)

    logger.info(f"Generated {len(all_chunks)} semantic statutory chunks from {total_sections} sections.")
    indexed_count = client.add_chunks(all_chunks)
    logger.info(f"Successfully ingested {indexed_count} chunks into ChromaDB. Total collection size: {client.count()}")
    return indexed_count


if __name__ == "__main__":
    ingest_bare_acts_into_chromadb()

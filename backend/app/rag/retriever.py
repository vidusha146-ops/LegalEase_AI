import logging
from typing import Dict, Any, List, Optional
from app.rag.chroma_client import ChromaDBClient, get_chroma_client

logger = logging.getLogger(__name__)


class LegalKnowledgeRetriever:
    """
    Hybrid statutory retriever combining semantic vector search
    with metadata filtering (Act, Domain, Provision Type) to retrieve
    verified Indian statutory provisions without hallucinations.
    """

    def __init__(self, chroma_client: Optional[ChromaDBClient] = None):
        self.chroma = chroma_client or get_chroma_client()

    def search_statutes(
        self,
        query: str,
        legal_domain: Optional[str] = None,
        act_code: Optional[str] = None,
        provision_type: Optional[str] = None,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves relevant statutory sections using semantic similarity,
        optionally constrained by domain or act filters.
        """
        filters: List[Dict[str, Any]] = []
        if legal_domain:
            filters.append({"legal_domain": legal_domain})
        if act_code:
            filters.append({"act_code": act_code})
        if provision_type:
            filters.append({"provision_type": provision_type})

        where_filter = None
        if len(filters) == 1:
            where_filter = filters[0]
        elif len(filters) > 1:
            where_filter = {"$and": filters}

        return self.chroma.query(
            query_text=query,
            n_results=top_k,
            where_filter=where_filter,
        )

    def get_exact_section(self, act_code: str, section_number: str) -> List[Dict[str, Any]]:
        """Direct deterministic lookup of an exact section from the persistent store."""
        return self.chroma.get_by_section_number(act_code=act_code, section_number=section_number)

    def build_grounded_context(
        self,
        query: str,
        legal_domain: Optional[str] = None,
        top_k: int = 4,
    ) -> Dict[str, Any]:
        """
        Retrieves top relevant sections and formats them into an authenticated
        grounding context block complete with official source URLs.
        """
        results = self.search_statutes(query=query, legal_domain=legal_domain, top_k=top_k)
        if not results:
            return {
                "grounded_context_str": "No matching statutory provisions found in verified index.",
                "retrieved_sections": [],
            }

        context_blocks = []
        retrieved_sections = []

        for idx, item in enumerate(results, start=1):
            meta = item["metadata"]
            doc = item["document"]
            retrieved_sections.append(
                {
                    "act_code": meta.get("act_code"),
                    "act_title": meta.get("act_title"),
                    "section_number": meta.get("section_number"),
                    "section_title": meta.get("section_title"),
                    "provision_type": meta.get("provision_type"),
                    "source_url": meta.get("source_url"),
                    "distance": item.get("distance", 0.0),
                }
            )
            block = (
                f"--- STATUTORY RECORD {idx} ---\n"
                f"Act: {meta.get('act_title')} ({meta.get('act_code')})\n"
                f"Section: {meta.get('section_number')} - {meta.get('section_title')}\n"
                f"Classification: {meta.get('provision_type')}\n"
                f"Official Gazette Source: {meta.get('source_url')}\n"
                f"Statutory Text:\n{doc}\n"
            )
            context_blocks.append(block)

        return {
            "grounded_context_str": "\n".join(context_blocks),
            "retrieved_sections": retrieved_sections,
        }

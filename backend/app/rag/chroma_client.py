import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.core.config import settings

logger = logging.getLogger(__name__)

STATUTES_COLLECTION_NAME = "indian_statutes"
JUDGMENTS_COLLECTION_NAME = "indian_court_judgments"


class ChromaDBClient:
    """
    Manages persistent ChromaDB vector storage for Indian Bare Acts
    and verified Indian Court Judgments.
    
    Collection separation:
    - 'indian_statutes': Bare Acts statutory chunks.
    - 'indian_court_judgments': Precedent judgments with factual summaries and ratio decidendi.
    """

    def __init__(self, persist_dir: Optional[str] = None):
        self.persist_dir = persist_dir or settings.CHROMA_PERSIST_DIRECTORY
        os.makedirs(self.persist_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name=STATUTES_COLLECTION_NAME,
            metadata={"description": "Verified Indian Bare Acts statutory chunks"},
        )
        self.judgments_collection = self.client.get_or_create_collection(
            name=JUDGMENTS_COLLECTION_NAME,
            metadata={"description": "Verified Indian Court Judgments with segmented ratio decidendi and obiter dicta"},
        )
        logger.info(
            f"ChromaDB persistent collections '{STATUTES_COLLECTION_NAME}' and '{JUDGMENTS_COLLECTION_NAME}' loaded from {self.persist_dir}"
        )

    def add_chunks(self, chunks: List[Dict[str, Any]]) -> int:
        """
        Ingests a list of semantic statutory chunks into the persistent collection.
        Uses chunk_id as the document ID and attaches statutory metadata.
        """
        if not chunks:
            return 0

        ids = []
        documents = []
        metadatas = []

        for chunk in chunks:
            ids.append(chunk["chunk_id"])
            documents.append(chunk["text"])
            # Ensure metadata values are strings, ints, floats, or bools for ChromaDB
            clean_meta = {}
            for k, v in chunk["metadata"].items():
                if v is None:
                    clean_meta[k] = ""
                elif isinstance(v, (str, int, float, bool)):
                    clean_meta[k] = v
                else:
                    clean_meta[k] = str(v)
            metadatas.append(clean_meta)

        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
        )
        logger.info(f"Indexed {len(ids)} statutory chunks into ChromaDB.")
        return len(ids)

    def query(
        self,
        query_text: str,
        n_results: int = 5,
        where_filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Performs semantic vector search over Indian statutes with optional metadata filtering.
        """
        query_kwargs: Dict[str, Any] = {
            "query_texts": [query_text],
            "n_results": n_results,
        }
        if where_filter:
            query_kwargs["where"] = where_filter

        results = self.collection.query(**query_kwargs)

        matched_items = []
        if results and results.get("ids") and len(results["ids"]) > 0:
            count = len(results["ids"][0])
            for i in range(count):
                matched_items.append(
                    {
                        "id": results["ids"][0][i],
                        "document": results["documents"][0][i] if results.get("documents") else "",
                        "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                        "distance": results["distances"][0][i] if results.get("distances") else 0.0,
                    }
                )
        return matched_items

    def count(self) -> int:
        return self.collection.count()

    def get_by_section_number(self, act_code: str, section_number: str) -> List[Dict[str, Any]]:
        """Fetches chunks matching an exact act_code and section_number."""
        results = self.collection.get(
            where={
                "$and": [
                    {"act_code": act_code},
                    {"section_number": section_number},
                ]
            }
        )
        items = []
        if results and results.get("ids"):
            for i in range(len(results["ids"])):
                items.append(
                    {
                        "id": results["ids"][i],
                        "document": results["documents"][i] if results.get("documents") else "",
                        "metadata": results["metadatas"][i] if results.get("metadatas") else {},
                    }
                )
        return items

    def add_judgment_chunks(self, chunks: List[Dict[str, Any]]) -> int:
        """
        Ingests judgment chunks into the public indian_court_judgments collection.
        Uses unique chunk IDs (e.g. SC_2008_NITIN_KHANDELWAL_ratio).
        """
        if not chunks:
            return 0

        ids = []
        documents = []
        metadatas = []

        for chunk in chunks:
            ids.append(chunk["chunk_id"])
            documents.append(chunk["text"])
            clean_meta = {}
            for k, v in chunk.get("metadata", {}).items():
                if v is None:
                    clean_meta[k] = ""
                elif isinstance(v, (str, int, float, bool)):
                    clean_meta[k] = v
                else:
                    clean_meta[k] = str(v)
            metadatas.append(clean_meta)

        self.judgments_collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
        )
        logger.info(f"Indexed {len(ids)} court judgment chunks into ChromaDB.")
        return len(ids)

    def query_judgments(
        self,
        query_text: str,
        n_results: int = 5,
        where_filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Performs semantic vector search over Indian court judgments with metadata filtering.
        Returns matched chunks with distance metrics.
        """
        query_kwargs: Dict[str, Any] = {
            "query_texts": [query_text],
            "n_results": n_results,
        }
        if where_filter:
            query_kwargs["where"] = where_filter

        results = self.judgments_collection.query(**query_kwargs)

        matched_items = []
        if results and results.get("ids") and len(results["ids"]) > 0:
            count = len(results["ids"][0])
            for i in range(count):
                matched_items.append(
                    {
                        "id": results["ids"][0][i],
                        "document": results["documents"][0][i] if results.get("documents") else "",
                        "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                        "distance": results["distances"][0][i] if results.get("distances") else 0.0,
                    }
                )
        return matched_items

    def count_judgments(self) -> int:
        """Returns the number of indexed judgment chunks."""
        return self.judgments_collection.count()

    def get_judgment_chunks_by_key(self, judgment_key: str) -> List[Dict[str, Any]]:
        """Fetches all indexed chunks for a given judgment key."""
        results = self.judgments_collection.get(
            where={"judgment_key": judgment_key}
        )
        items = []
        if results and results.get("ids"):
            for i in range(len(results["ids"])):
                items.append(
                    {
                        "id": results["ids"][i],
                        "document": results["documents"][i] if results.get("documents") else "",
                        "metadata": results["metadatas"][i] if results.get("metadatas") else {},
                    }
                )
        return items


# Singleton instance
_chroma_instance: Optional[ChromaDBClient] = None


def get_chroma_client() -> ChromaDBClient:
    global _chroma_instance
    if _chroma_instance is None:
        _chroma_instance = ChromaDBClient()
    return _chroma_instance

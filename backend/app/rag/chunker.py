from typing import Dict, Any, List
from app.rag.extractor import LegalTextExtractor


class LegalDocumentChunker:
    """
    Semantic statutory chunker that splits Bare Acts strictly along
    legal boundaries (sections, sub-sections, provisos, explanations),
    attaching statutory context headers to each chunk.
    """

    def __init__(self, max_chunk_chars: int = 1500, chunk_overlap_chars: int = 200):
        self.max_chunk_chars = max_chunk_chars
        self.chunk_overlap_chars = chunk_overlap_chars

    def chunk_statute_section(
        self,
        act_code: str,
        act_title: str,
        section_number: str,
        section_title: str,
        chapter: str,
        legal_domain: str,
        provision_type: str,
        full_text: str,
        source_url: str,
        verification_date: str = "2026-11-04",
        historical_counterpart: str = "",
    ) -> List[Dict[str, Any]]:
        """
        Creates semantic chunks for a single statutory section.
        Prepends an explicit legal header so embeddings retain full contextual grounding.
        """
        cleaned_text = LegalTextExtractor.clean_text(full_text)
        header = (
            f"[STATUTE]: {act_title} ({act_code})\n"
            f"[SECTION]: Section {section_number} - {section_title}\n"
            f"[CHAPTER]: {chapter}\n"
            f"[CLASSIFICATION]: {provision_type}\n"
        )
        if historical_counterpart:
            header += f"[HISTORICAL COUNTERPART]: {historical_counterpart}\n"
        header += "[STATUTORY TEXT]:\n"

        # If the complete section fits comfortably within the chunk size, keep it unified
        if len(cleaned_text) <= self.max_chunk_chars:
            chunk_id = f"{act_code}_SEC_{section_number.replace('(', '_').replace(')', '')}_0".upper()
            return [
                {
                    "chunk_id": chunk_id,
                    "text": f"{header}{cleaned_text}",
                    "metadata": {
                        "act_code": act_code,
                        "act_title": act_title,
                        "section_number": section_number,
                        "section_title": section_title,
                        "chapter": chapter,
                        "legal_domain": legal_domain,
                        "provision_type": provision_type,
                        "source_url": source_url,
                        "verification_date": verification_date,
                        "historical_counterpart": historical_counterpart or "None",
                    },
                }
            ]

        # For larger sections, split by sub-sections or explanations
        subsections = LegalTextExtractor.extract_subsections(cleaned_text)
        chunks = []
        current_text = ""
        part_idx = 0

        for sub in subsections:
            if len(current_text) + len(sub) > self.max_chunk_chars and current_text:
                chunk_id = f"{act_code}_SEC_{section_number.replace('(', '_').replace(')', '')}_{part_idx}".upper()
                chunks.append(
                    {
                        "chunk_id": chunk_id,
                        "text": f"{header}{current_text.strip()}",
                        "metadata": {
                            "act_code": act_code,
                            "act_title": act_title,
                            "section_number": section_number,
                            "section_title": section_title,
                            "chapter": chapter,
                            "legal_domain": legal_domain,
                            "provision_type": provision_type,
                            "source_url": source_url,
                            "verification_date": verification_date,
                            "historical_counterpart": historical_counterpart or "None",
                        },
                    }
                )
                part_idx += 1
                current_text = sub + " "
            else:
                current_text += sub + " "

        if current_text.strip():
            chunk_id = f"{act_code}_SEC_{section_number.replace('(', '_').replace(')', '')}_{part_idx}".upper()
            chunks.append(
                {
                    "chunk_id": chunk_id,
                    "text": f"{header}{current_text.strip()}",
                    "metadata": {
                        "act_code": act_code,
                        "act_title": act_title,
                        "section_number": section_number,
                        "section_title": section_title,
                        "chapter": chapter,
                        "legal_domain": legal_domain,
                        "provision_type": provision_type,
                        "source_url": source_url,
                        "verification_date": verification_date,
                        "historical_counterpart": historical_counterpart or "None",
                    },
                }
            )

        return chunks

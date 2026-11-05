import re
from typing import Dict, Any, List


class LegalTextExtractor:
    """
    Normalizes and cleans statutory legal texts extracted from
    official Gazette Bare Acts, preserving legal provisos, explanations,
    and marginal notes.
    """

    @staticmethod
    def clean_text(raw_text: str) -> str:
        """Removes duplicate whitespace, gazette line breaks, and page header noise."""
        if not raw_text:
            return ""
        # Remove multiple newlines and spaces
        cleaned = re.sub(r"\s+", " ", raw_text)
        # Standardize Indian legal typography
        cleaned = cleaned.replace("—", " - ").replace("–", " - ")
        cleaned = re.sub(r"\s+([.,;:?!])", r"\1", cleaned)
        return cleaned.strip()

    @staticmethod
    def extract_subsections(full_text: str) -> List[str]:
        """
        Splits a section into distinct numbered sub-sections
        e.g., (1), (2), (3) or Explanations while retaining context.
        """
        cleaned = LegalTextExtractor.clean_text(full_text)
        # Look for (1), (2) or Explanation patterns
        pattern = r"(\([0-9]+\)|Explanation\s+[0-9]*\.?|Provided\s+that)"
        parts = re.split(pattern, cleaned)
        
        if len(parts) <= 1:
            return [cleaned]

        subsections = []
        current = parts[0].strip()
        for i in range(1, len(parts), 2):
            delimiter = parts[i]
            content = parts[i + 1] if i + 1 < len(parts) else ""
            clause = f"{delimiter} {content}".strip()
            subsections.append(clause)
        
        return subsections if subsections else [cleaned]

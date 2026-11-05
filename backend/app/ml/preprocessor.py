"""
LegalEase AI - Legal Text Preprocessing Module
Specialized text cleaning for Indian legal disputes, preserving key statutory markers,
negations, and legal terminology while normalizing citizen colloquialisms.
"""

import re
import string
from typing import List


# Domain-critical negation & statutory markers that must NOT be stripped as stop words
PRESERVED_LEGAL_MARKERS = {
    "no", "not", "without", "against", "refused", "denied", "failed",
    "before", "after", "under", "between", "against"
}

# Common English stop words except preserved legal markers
BASE_STOP_WORDS = {
    "a", "about", "above", "after", "again", "all", "am", "an", "and", "any", "are",
    "as", "at", "be", "because", "been", "being", "below", "between", "both", "but",
    "by", "could", "did", "do", "does", "doing", "down", "during", "each", "few",
    "for", "from", "further", "had", "has", "have", "having", "he", "her", "here",
    "hers", "herself", "him", "himself", "his", "how", "i", "if", "in", "into", "is",
    "it", "its", "itself", "me", "more", "most", "my", "myself", "of", "off", "on",
    "once", "only", "or", "other", "our", "ours", "ourselves", "out", "over", "own",
    "same", "she", "should", "so", "some", "such", "than", "that", "the", "their",
    "theirs", "them", "themselves", "then", "there", "these", "they", "this", "those",
    "through", "to", "too", "under", "until", "up", "very", "was", "we", "were",
    "what", "when", "where", "which", "while", "who", "whom", "why", "with", "would",
    "you", "your", "yours", "yourself", "yourselves"
} - PRESERVED_LEGAL_MARKERS


class LegalTextPreprocessor:
    """
    Cleans and standardizes raw citizen legal text for TF-IDF feature extraction.
    """

    @staticmethod
    def clean(text: str) -> str:
        """
        Cleans text while preserving legal acronyms and numbers (e.g. 138, 420, 303).
        """
        if not text:
            return ""

        # Lowercase
        cleaned = text.lower()

        # Normalize currency expressions (Rs., INR, ₹)
        cleaned = re.sub(r"(?:rs\.?|inr|₹)\s*([0-9,]+)", lambda m: f"rupees_{m.group(1).replace(',', '')}", cleaned)

        # Standardize Indian legal terms
        cleaned = re.sub(r"\bf\.?i\.?r\.?\b", "fir_police_complaint", cleaned)
        cleaned = re.sub(r"\br\.?t\.?i\.?\b", "right_to_information_rti", cleaned)
        cleaned = re.sub(r"\bu\.?p\.?i\.?\b", "unified_payments_interface_upi", cleaned)
        cleaned = re.sub(r"\bm\.?a\.?c\.?t\.?\b", "motor_accident_claims_tribunal", cleaned)
        cleaned = re.sub(r"\be\.?p\.?f\.?o?\b", "provident_fund_epf", cleaned)

        # Remove URLs and emails
        cleaned = re.sub(r"https?://\S+|www\.\S+", " ", cleaned)
        cleaned = re.sub(r"\S+@\S+", " ", cleaned)

        # Replace hyphens and punctuation with spaces, keeping alphanumeric
        cleaned = re.sub(r"[^\w\s]", " ", cleaned)

        # Collapse whitespace
        tokens = cleaned.split()
        filtered_tokens = [
            t for t in tokens if len(t) > 1 and t not in BASE_STOP_WORDS
        ]

        return " ".join(filtered_tokens)

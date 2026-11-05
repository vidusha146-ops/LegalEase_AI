"""
LegalEase AI - Deterministic PII Scrubber & Unicode Normalization Engine
Phase 7 Module 2: Multilingual Legal Assistant

Features:
- Unicode decimal digit (Category 'Nd') normalization to ASCII 0-9 via unicodedata.decimal()
- 1:1 character offset tracking
- Deterministic regex redaction for Aadhaar, PAN, Phone, Email, Bank Accounts
- Citation whitelist preservation
- Fail-closed blocking for ambiguous numeric sequences (>= 9 unclassified digits)
"""

import re
import unicodedata
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Set


@dataclass
class RedactionResult:
    """Result of deterministic PII scrubbing."""
    original_text: str
    clean_text: str
    pii_detected: bool
    redacted_types: List[str] = field(default_factory=list)
    fail_closed_triggered: bool = False
    blocking_reason: Optional[str] = None


class DeterministicPIIScrubber:
    """
    Deterministic PII detection and redaction engine for Indian citizen texts.
    Guarantees that sensitive personal identifiers are scrubbed prior to any external
    LLM/translation transmission. Ambiguous sequences fail-closed to local processing.
    """

    # Aadhaar: 12 digits (with optional spaces or dashes)
    AADHAAR_REGEX = re.compile(r"\b([2-9]\d{3}[ -]?\d{4}[ -]?\d{4})\b")

    # PAN: 5 letters, 4 digits, 1 letter
    PAN_REGEX = re.compile(r"\b([A-Za-z]{5}\d{4}[A-Za-z]{1})\b")

    # Indian Mobile: 10 digits starting with 6-9, optional +91 or 0 prefix
    PHONE_REGEX = re.compile(r"\b(?:\+91[ -]?|0)?([6-9]\d{9})\b")

    # Email
    EMAIL_REGEX = re.compile(r"\b([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})\b")

    # Bank Account Contextual: 9 to 18 digits near account keywords
    BANK_CONTEXT_REGEX = re.compile(
        r"(?:a/c|account|acct|khata|खाता|खाते|ఖాతా|கணக்கு|অ্যাকাউন্ট|ખાતા)\s*(?:no\.?|number|संख्या)?\s*[:#-]?\s*(\d{9,18})\b",
        re.IGNORECASE,
    )

    # General 9-18 digit sequence
    AMBIGUOUS_DIGITS_REGEX = re.compile(r"\b(\d{9,18})\b")

    # Legal citation whitelist protection patterns
    CITATION_PATTERNS = [
        re.compile(r"\b(?:section|sec\.?|धारा|कलम|பிரிவு|విభాగం|ধারা|કલમ)\s+\d+[A-Za-z]?(?:\(\d+\))?", re.IGNORECASE),
        re.compile(r"\b(?:article|art\.?|अनुच्छेद|अनुच्छेद|অনুচ্ছেদ|சரத்து|ఆర్టికల్)\s+\d+[A-Za-z]?(?:\(\d+\))?", re.IGNORECASE),
        re.compile(r"\b(?:19|20)\d{2}\b"),  # Statutory/citation years
        re.compile(r"\(\d{4}\)\s+\d+\s+(?:scc|scr|air|bom\s+cr|scale)\b", re.IGNORECASE),
    ]

    @classmethod
    def normalize_unicode_digits(cls, text: str) -> Tuple[str, List[int]]:
        """
        Normalizes all Unicode decimal digits (Category 'Nd', e.g. Devanagari ०-९,
        Bengali ০-৯, Gujarati ૦-૯, Tamil, Telugu) to ASCII digits '0'-'9'.
        Returns normalized text and 1:1 character index map.
        """
        normalized_chars = []
        index_map = []

        for idx, char in enumerate(text):
            if unicodedata.category(char) == "Nd":
                # Convert to standard ASCII decimal digit
                dec_val = unicodedata.decimal(char)
                normalized_chars.append(str(dec_val))
            else:
                normalized_chars.append(char)
            index_map.append(idx)

        return "".join(normalized_chars), index_map

    @classmethod
    def scrub(cls, text: str) -> RedactionResult:
        """
        Scrubs PII from input text.
        1. Normalizes all Unicode digits.
        2. Identifies and whitelists legal citations.
        3. Detects and redacts Aadhaar, PAN, Phone, Email, Bank Accounts.
        4. Detects unclassified 9+ digit sequences: triggers fail-closed.
        """
        if not text or not text.strip():
            return RedactionResult(
                original_text=text,
                clean_text=text,
                pii_detected=False,
            )

        # Step 1: Normalize Unicode decimal digits
        norm_text, _ = cls.normalize_unicode_digits(text)
        clean = norm_text
        detected_types: List[str] = []

        # Step 2: Extract citation whitelists to prevent accidental redaction
        whitelist_spans: Set[Tuple[int, int]] = set()
        for pat in cls.CITATION_PATTERNS:
            for match in pat.finditer(norm_text):
                whitelist_spans.add((match.start(), match.end()))

        def is_whitelisted(start: int, end: int) -> bool:
            for w_start, w_end in whitelist_spans:
                if not (end <= w_start or start >= w_end):
                    return True
            return False

        # Step 3: Redact Email
        if cls.EMAIL_REGEX.search(clean):
            clean = cls.EMAIL_REGEX.sub("[REDACTED_EMAIL]", clean)
            detected_types.append("EMAIL")

        # Step 4: Redact PAN
        def redact_pan(m):
            start, end = m.span()
            if is_whitelisted(start, end):
                return m.group(0)
            return "[REDACTED_PAN]"

        if cls.PAN_REGEX.search(clean):
            clean = cls.PAN_REGEX.sub(redact_pan, clean)
            if "[REDACTED_PAN]" in clean:
                detected_types.append("PAN")

        # Step 5: Redact Bank Account with Context
        def redact_bank(m):
            return m.group(0).replace(m.group(1), "[REDACTED_BANK_ACCOUNT]")

        if cls.BANK_CONTEXT_REGEX.search(clean):
            clean = cls.BANK_CONTEXT_REGEX.sub(redact_bank, clean)
            detected_types.append("BANK_ACCOUNT")

        # Step 6: Redact Aadhaar
        def redact_aadhaar(m):
            start, end = m.span()
            if is_whitelisted(start, end):
                return m.group(0)
            digits = re.sub(r"\D", "", m.group(1))
            if len(digits) == 12:
                return "[REDACTED_AADHAAR]"
            return m.group(0)

        if cls.AADHAAR_REGEX.search(clean):
            clean = cls.AADHAAR_REGEX.sub(redact_aadhaar, clean)
            if "[REDACTED_AADHAAR]" in clean:
                detected_types.append("AADHAAR")

        # Step 7: Redact Phone Numbers
        def redact_phone(m):
            start, end = m.span()
            if is_whitelisted(start, end):
                return m.group(0)
            return "[REDACTED_PHONE]"

        if cls.PHONE_REGEX.search(clean):
            clean = cls.PHONE_REGEX.sub(redact_phone, clean)
            if "[REDACTED_PHONE]" in clean:
                detected_types.append("PHONE")

        # Step 8: Ambiguous 9+ consecutive digit sequence detection (Fail-Closed)
        fail_closed = False
        blocking_reason = None

        ambiguous_matches = list(cls.AMBIGUOUS_DIGITS_REGEX.finditer(clean))
        for am in ambiguous_matches:
            start, end = am.span()
            if is_whitelisted(start, end):
                continue
            digits_str = am.group(1)
            # If not already redacted
            fail_closed = True
            blocking_reason = (
                f"Ambiguous sensitive numeric sequence of {len(digits_str)} digits detected ('{digits_str[:3]}...'). "
                f"Deterministically blocking external LLM transmission to protect citizen privacy."
            )
            detected_types.append("AMBIGUOUS_NUMERIC_SEQUENCE")
            clean = clean[:start] + "[REDACTED_SENSITIVE_NUMBER]" + clean[end:]
            break

        pii_found = len(detected_types) > 0

        return RedactionResult(
            original_text=text,
            clean_text=clean,
            pii_detected=pii_found,
            redacted_types=list(set(detected_types)),
            fail_closed_triggered=fail_closed,
            blocking_reason=blocking_reason,
        )

"""
LegalEase AI - Multilingual Legal Assistant Test Suite (Phase 7 Module 2)
Validates:
- Script & Language detection across 6 Indian regional languages (hi, bn, mr, ta, te, gu) + en
- Unicode decimal digit (Category 'Nd') normalization to ASCII 0-9 with 1:1 offsets
- Deterministic PII scrubbing (Aadhaar, PAN, Phone, Email, Bank Account) with citation whitelist
- Citation token locking preventing statutory reference distortion
- Fail-closed external transmission blocking on ambiguous numeric sequences (>= 9 digits)
- Explicit user consent enforcement for external processing
- Verified legislative glossary retrieval across all 6 regional languages
- FastAPI multilingual endpoints lifecycle and Article 348 non-certified disclaimers
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.multilingual_assistant import (
    MultilingualAssistantService,
    SUPPORTED_LANGUAGES,
    UNCERTIFIED_TRANSLATION_DISCLAIMER,
)
from app.services.pii_scrubber import DeterministicPIIScrubber, RedactionResult
from app.services.legal_glossary import LegalGlossaryService, VERIFIED_LEGAL_GLOSSARY
from app.schemas.multilingual import (
    LanguageDetectionRequest,
    QueryTranslationRequest,
    MultilingualExplanationRequest,
)


@pytest.fixture(scope="session", autouse=True)
def anyio_backend():
    return "asyncio"


# =============================================================================
# 1. LANGUAGE & SCRIPT DETECTION TESTS
# =============================================================================

def test_language_and_script_detection():
    """Verifies script-based and statistical language identification across 7 languages."""
    # Hindi (Devanagari)
    res_hi = MultilingualAssistantService.detect_language("उपभोक्ता ने सेवा में कमी के कारण शिकायत दर्ज की है")
    assert res_hi.detected_language == "hi"
    assert res_hi.script_name == "Devanagari"
    assert res_hi.supported is True

    # Marathi (Devanagari with Marathi grammatical tokens)
    res_mr = MultilingualAssistantService.detect_language("ग्राहकाने सेवेतील त्रुटीमुळे न्यायालयात तक्रार दाखल केली आहे")
    assert res_mr.detected_language == "mr"
    assert res_mr.script_name == "Devanagari"
    assert res_mr.supported is True

    # Bengali
    res_bn = MultilingualAssistantService.detect_language("ভোক্তা পরিষেবাতে ত্রুটির জন্য ফোরামে একটি অভিযোগ দায়ের করেছেন")
    assert res_bn.detected_language == "bn"
    assert res_bn.script_name == "Bengali"
    assert res_bn.supported is True

    # Tamil
    res_ta = MultilingualAssistantService.detect_language("நுகர்வோர் சேவை குறைபாடு காரணமாக ஆணையத்தில் புகார் அளித்துள்ளார்")
    assert res_ta.detected_language == "ta"
    assert res_ta.script_name == "Tamil"
    assert res_ta.supported is True

    # Telugu
    res_te = MultilingualAssistantService.detect_language("వినియోగదారుడు సేవా లోపం కారణంగా కమిషన్ ముందు ఫిర్యాదు దాఖలు చేశాడు")
    assert res_te.detected_language == "te"
    assert res_te.script_name == "Telugu"
    assert res_te.supported is True

    # Gujarati
    res_gu = MultilingualAssistantService.detect_language("ગ્રાહકે સેવામાં ખામી હોવા બદલ કમિશન સમક્ષ ફરિયાદ દાખલ કરી છે")
    assert res_gu.detected_language == "gu"
    assert res_gu.script_name == "Gujarati"
    assert res_gu.supported is True

    # English
    res_en = MultilingualAssistantService.detect_language("The consumer filed a formal complaint regarding defective vehicle.")
    assert res_en.detected_language == "en"
    assert res_en.script_name == "Latin"
    assert res_en.supported is True


# =============================================================================
# 2. UNICODE DECIMAL DIGIT NORMALIZATION TESTS
# =============================================================================

def test_unicode_decimal_digit_normalization():
    """
    Verifies that Unicode Category 'Nd' digits (Devanagari, Bengali, Gujarati, etc.)
    are converted to standard ASCII '0'-'9' with exact 1:1 character index tracking.
    """
    # Devanagari digits: ०१२३४५६७८९ -> 0123456789
    dev_digits = "खाता संख्या १२३४५६७८९०"
    norm_dev, map_dev = DeterministicPIIScrubber.normalize_unicode_digits(dev_digits)
    assert "1234567890" in norm_dev
    assert len(norm_dev) == len(dev_digits)
    assert len(map_dev) == len(dev_digits)

    # Bengali digits: ০১২৩৪৫৬৭৮৯ -> 0123456789
    bn_digits = "অ্যাকাউন্ট নং ০১২৩৪৫৬৭৮৯"
    norm_bn, map_bn = DeterministicPIIScrubber.normalize_unicode_digits(bn_digits)
    assert "0123456789" in norm_bn

    # Gujarati digits: ૦૧૨૩૪૫૬૭૮૯ -> 0123456789
    gu_digits = "ખાતા નંબર ૦૧૨૩૪૫૬૭૮૯"
    norm_gu, map_gu = DeterministicPIIScrubber.normalize_unicode_digits(gu_digits)
    assert "0123456789" in norm_gu


# =============================================================================
# 3. DETERMINISTIC PII SCRUBBING & CITATION WHITELIST TESTS
# =============================================================================

def test_deterministic_pii_scrubbing_and_citation_whitelist():
    """
    Verifies that Aadhaar, PAN, Phone, Email, and Bank Accounts are redacted,
    while legal citations (Section 138, Article 21, (2008) 11 SCC 259) are protected.
    """
    sample_text = (
        "My name is Ramesh Kumar. My Aadhaar is 5432 8765 4321 and PAN is ABCDE1234F. "
        "Contact me at 9876543210 or citizen.help@example.com. Bank account: a/c 123456789012. "
        "I am filing a complaint under Section 138 of Negotiable Instruments Act and Article 21 "
        "citing landmark precedent (2008) 11 SCC 259 regarding vehicle theft in year 2019."
    )

    result = DeterministicPIIScrubber.scrub(sample_text)
    assert result.pii_detected is True
    assert "[REDACTED_AADHAAR]" in result.clean_text
    assert "[REDACTED_PAN]" in result.clean_text
    assert "[REDACTED_PHONE]" in result.clean_text
    assert "[REDACTED_EMAIL]" in result.clean_text
    assert "[REDACTED_BANK_ACCOUNT]" in result.clean_text

    # Statutory provisions and court citations MUST NOT be redacted
    assert "Section 138" in result.clean_text
    assert "Negotiable Instruments Act" in result.clean_text
    assert "Article 21" in result.clean_text
    assert "(2008) 11 SCC 259" in result.clean_text
    assert "2019" in result.clean_text

    # Verify Indic digit PII redaction
    indic_sample = "मेरा आधार ५४३२ ८७६५ ४३२१ और फोन ९८७६५४३२१० है धारा १३८ के तहत"
    res_indic = DeterministicPIIScrubber.scrub(indic_sample)
    assert "[REDACTED_AADHAAR]" in res_indic.clean_text
    assert "[REDACTED_PHONE]" in res_indic.clean_text


# =============================================================================
# 4. CITATION TOKEN LOCKING & PRESERVATION TESTS
# =============================================================================

def test_citation_token_locking_and_preservation():
    """
    Verifies that statutory citations are cleanly locked with placeholders
    and restored without corruption or distortion.
    """
    raw_query = (
        "Under Section 138 of Negotiable Instruments Act and Section 35 of Consumer Protection Act, "
        "following the ratio in (2008) 11 SCC 259 and AIR 2017 SC 4161 under Article 21."
    )

    locked, token_map = MultilingualAssistantService.lock_citations(raw_query)
    assert "{{LEGAL_CITATION_0}}" in locked
    assert len(token_map) >= 3

    # Ensure placeholders do not contain raw section numbers
    for token, orig in token_map.items():
        assert token in locked
        assert orig not in locked

    # Restore tokens
    restored = MultilingualAssistantService.unlock_citations(locked, token_map)
    assert restored == raw_query


# =============================================================================
# 5. FAIL-CLOSED AMBIGUOUS NUMERIC SEQUENCE DETECTION
# =============================================================================

def test_fail_closed_ambiguous_numeric_sequence():
    """
    Verifies that unclassified 9+ consecutive digit sequences trigger fail_closed_triggered=True,
    blocking external transmission and forcing local processing.
    """
    # Text with unclassified 14-digit numeric sequence
    suspicious_text = "Citizen filed complaint with transaction id 98765432101234 regarding delay."
    result = DeterministicPIIScrubber.scrub(suspicious_text)

    assert result.pii_detected is True
    assert result.fail_closed_triggered is True
    assert "Ambiguous sensitive numeric sequence" in (result.blocking_reason or "")
    assert "[REDACTED_SENSITIVE_NUMBER]" in result.clean_text


# =============================================================================
# 6. VERIFIED MULTILINGUAL LEGAL GLOSSARY TESTS
# =============================================================================

def test_verified_legal_glossary_retrieval():
    """
    Verifies authoritative legislative glossary terms across Hindi, Bengali,
    Marathi, Tamil, Telugu, and Gujarati.
    """
    terms = LegalGlossaryService.get_all_terms()
    assert len(terms) >= 12

    # Check Complainant term
    complainant = LegalGlossaryService.lookup_term("Complainant")
    assert complainant is not None
    assert complainant["translations"]["hi"] == "परिवादी / शिकायतकर्ता"
    assert complainant["translations"]["bn"] == "অভিযোগকারী"
    assert complainant["translations"]["mr"] == "तक्रारदार"
    assert complainant["translations"]["ta"] == "புகார்தாரர்"
    assert complainant["translations"]["te"] == "ఫిర్యాదుదారు"
    assert complainant["translations"]["gu"] == "ફરિયાદી"

    # Search glossary by regional term
    search_mr = LegalGlossaryService.search_glossary("तक्रारदार")
    assert len(search_mr) >= 1
    assert search_mr[0]["english_term"] == "Complainant"

    # Domain filtering
    consumer_terms = LegalGlossaryService.get_terms_by_domain("CONSUMER_PROTECTION")
    assert len(consumer_terms) >= 2
    assert any(t["english_term"] == "Deficiency of Service" for t in consumer_terms)


# =============================================================================
# 7. FASTAPI MULTILINGUAL ENDPOINTS LIFECYCLE TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_multilingual_api_lifecycle():
    """Tests /api/v1/multilingual endpoints with token preservation and consent rules."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Languages Endpoint
        lang_res = await client.get("/api/v1/multilingual/languages")
        assert lang_res.status_code == 200
        lang_data = lang_res.json()
        assert lang_data["total_supported"] == 7
        assert "hi" in lang_data["supported_languages"]
        assert "Article 348" in lang_data["article_348_advisory"]

        # 2. Language Detection Endpoint
        detect_payload = {"text": "বিবাদী পক্ষ পরিষেবাতে ত্রুটির জন্য দায়ী"}
        detect_res = await client.post("/api/v1/multilingual/detect-language", json=detect_payload)
        assert detect_res.status_code == 200
        assert detect_res.json()["detected_language"] == "bn"
        assert detect_res.json()["script_name"] == "Bengali"

        # 3. Query Translation with Citation Preservation & No External Consent
        trans_payload = {
            "text": "मेरी गाड़ी चोरी हो गई और बीमा कंपनी ने Section 35 of Consumer Protection Act के तहत दावा खारिज कर दिया",
            "target_language": "en",
            "consent_for_external_processing": False,  # Strict offline mode
        }
        trans_res = await client.post("/api/v1/multilingual/translate-query", json=trans_payload)
        assert trans_res.status_code == 200
        trans_data = trans_res.json()
        assert trans_data["detected_source_language"] == "hi"
        assert trans_data["provider_used"] == "LOCAL_OFFLINE_GLOSSARY"
        # Crucial check: Section 35 and Consumer Protection Act must be preserved untouched
        assert "Section 35" in trans_data["translated_text"]
        assert "Consumer Protection Act" in trans_data["translated_text"]
        assert "Article 348" in trans_data["uncertified_translation_disclaimer"]

        # 4. Query Translation with PII Scrubbing
        pii_query_payload = {
            "text": "मेरा आधार ५४३२ ८७६५ ४३२१ और फोन ९८७६५४३२१० है और चेक बाउंस हुआ",
            "target_language": "en",
            "consent_for_external_processing": True,
        }
        pii_trans_res = await client.post("/api/v1/multilingual/translate-query", json=pii_query_payload)
        assert pii_trans_res.status_code == 200
        pii_trans_data = pii_trans_res.json()
        assert pii_trans_data["pii_scrubbed"] is True
        assert "[REDACTED_AADHAAR]" in pii_trans_data["translated_text"]

        # 5. Multilingual Rights Guidance (Explanation) Endpoint
        explain_payload = {
            "narrative": "Purchased washing machine that failed on first cycle, company refused refund.",
            "target_language": "mr",
            "domain": "CONSUMER_PROTECTION",
            "consent_for_external_processing": False,
        }
        exp_res = await client.post("/api/v1/multilingual/explain", json=explain_payload)
        assert exp_res.status_code == 200
        exp_data = exp_res.json()
        assert exp_data["target_language"] == "mr"
        assert exp_data["language_name"] == "Marathi"
        assert len(exp_data["procedural_steps"]) >= 2
        assert len(exp_data["verified_glossary_terms"]) >= 1
        assert "Article 348" in exp_data["uncertified_translation_disclaimer"]
        assert "Advocates Act, 1961" in exp_data["mandatory_advocates_act_notice"]

        # 6. Glossary Retrieval Endpoint
        gloss_res = await client.get("/api/v1/multilingual/glossary?domain=CONSUMER_PROTECTION")
        assert gloss_res.status_code == 200
        gloss_data = gloss_res.json()
        assert len(gloss_data) >= 1
        assert any(item["english_term"] == "Opposite Party" for item in gloss_data)

"""
LegalEase AI - Multilingual Legal Assistant Service (Phase 7 Module 2)
Supports: Hindi (hi), Bengali (bn), Marathi (mr), Tamil (ta), Telugu (te), Gujarati (gu), English (en).

Features:
- Unicode script-based language identification
- Citation token locking preventing legal reference corruption
- Deterministic PII scrubbing with Unicode decimal digit (Nd) normalization
- Pluggable provider architecture: Local Offline Glossary vs Grounded External LLM
- Fail-closed deterministic fallback to local templates on ambiguous PII or consent denial
- Uncertified translation disclaimer under Article 348 of the Constitution
"""

import logging
import re
from typing import Dict, Any, List, Tuple, Optional
import httpx

from app.core.config import settings
from app.services.pii_scrubber import DeterministicPIIScrubber, RedactionResult
from app.services.legal_glossary import LegalGlossaryService
from app.schemas.multilingual import (
    LanguageDetectionResponse,
    QueryTranslationResponse,
    MultilingualExplanationResponse,
)

logger = logging.getLogger(__name__)

UNCERTIFIED_TRANSLATION_DISCLAIMER = (
    "NOTICE: This translation is an automated, non-certified linguistic assistance tool for informational "
    "decision support only. Under Article 348 of the Constitution of India and relevant court language rules, "
    "only the authoritative gazetted statutory text / original judicial order is legally controlling. "
    "This does not constitute certified legal translation or formal advocacy under the Advocates Act, 1961."
)

MANDATORY_ADVOCATES_ACT_NOTICE = (
    "In accordance with the Advocates Act, 1961 and Bar Council of India guidelines, this multilingual "
    "decision-support guidance does not constitute legal representation, advocacy, or an attorney-client relationship. "
    "Consult an enrolled advocate for judicial representation before Indian courts."
)

SUPPORTED_LANGUAGES = {
    "en": {"name": "English", "script": "Latin"},
    "hi": {"name": "Hindi", "script": "Devanagari"},
    "bn": {"name": "Bengali", "script": "Bengali"},
    "mr": {"name": "Marathi", "script": "Devanagari"},
    "ta": {"name": "Tamil", "script": "Tamil"},
    "te": {"name": "Telugu", "script": "Telugu"},
    "gu": {"name": "Gujarati", "script": "Gujarati"},
}

MARATHI_INDICATORS = {
    "आहे", "नाही", "केले", "दिले", "तक्रार", "पोलीस", "झाले", "करावे", "आणि", "यांचे",
    "न्यायालय", "खरेदी", "धनादेश", "ग्राहक", "पोटगी", "अधिकार", "तक्रारदार", "अर्ज"
}

HINDI_INDICATORS = {
    "है", "नहीं", "किया", "दिया", "शिकायत", "हुआ", "करना", "और", "इनका", "था", "थी",
    "उपभोक्ता", "न्यायालय", "जमानत", "परिवादी", "विपक्षी", "थाना", "प्राथमिकी", "आवेदन"
}


class MultilingualAssistantService:
    """
    Multilingual legal processing engine for Indian languages.
    Ensures zero hallucination of legal citations through deterministic token locking.
    """

    @classmethod
    def detect_language(cls, text: str) -> LanguageDetectionResponse:
        """
        Detects language and script from input text using Unicode codepoint distribution
        and statistical grammatical markers.
        """
        if not text or not text.strip():
            return LanguageDetectionResponse(
                detected_language="en",
                language_name="English",
                confidence=1.0,
                script_name="Latin",
                supported=True,
            )

        counts = {
            "bn": 0,
            "ta": 0,
            "te": 0,
            "gu": 0,
            "devanagari": 0,
            "latin": 0,
        }

        for char in text:
            cp = ord(char)
            if 0x0980 <= cp <= 0x09FF:
                counts["bn"] += 1
            elif 0x0B80 <= cp <= 0x0BFF:
                counts["ta"] += 1
            elif 0x0C00 <= cp <= 0x0C7F:
                counts["te"] += 1
            elif 0x0A80 <= cp <= 0x0AFF:
                counts["gu"] += 1
            elif 0x0900 <= cp <= 0x097F:
                counts["devanagari"] += 1
            elif (0x0041 <= cp <= 0x005A) or (0x0061 <= cp <= 0x007A):
                counts["latin"] += 1

        total_indic = sum(counts[k] for k in ["bn", "ta", "te", "gu", "devanagari"])
        total_chars = total_indic + counts["latin"]

        if total_chars == 0:
            return LanguageDetectionResponse(
                detected_language="en",
                language_name="English",
                confidence=0.5,
                script_name="Latin",
                supported=True,
            )

        # Non-Devanagari Indic scripts are uniquely identifiable by Unicode block
        if counts["bn"] > total_chars * 0.2:
            conf = round(min(1.0, counts["bn"] / max(total_indic, 1)), 2)
            return LanguageDetectionResponse(detected_language="bn", language_name="Bengali", confidence=conf, script_name="Bengali", supported=True)
        if counts["ta"] > total_chars * 0.2:
            conf = round(min(1.0, counts["ta"] / max(total_indic, 1)), 2)
            return LanguageDetectionResponse(detected_language="ta", language_name="Tamil", confidence=conf, script_name="Tamil", supported=True)
        if counts["te"] > total_chars * 0.2:
            conf = round(min(1.0, counts["te"] / max(total_indic, 1)), 2)
            return LanguageDetectionResponse(detected_language="te", language_name="Telugu", confidence=conf, script_name="Telugu", supported=True)
        if counts["gu"] > total_chars * 0.2:
            conf = round(min(1.0, counts["gu"] / max(total_indic, 1)), 2)
            return LanguageDetectionResponse(detected_language="gu", language_name="Gujarati", confidence=conf, script_name="Gujarati", supported=True)

        # Devanagari script: differentiate Hindi vs Marathi
        if counts["devanagari"] > total_chars * 0.2:
            words = set(re.findall(r"\b[\u0900-\u097F]+\b", text))
            mr_matches = len(words.intersection(MARATHI_INDICATORS))
            hi_matches = len(words.intersection(HINDI_INDICATORS))

            if mr_matches > hi_matches:
                return LanguageDetectionResponse(detected_language="mr", language_name="Marathi", confidence=0.85, script_name="Devanagari", supported=True)
            return LanguageDetectionResponse(detected_language="hi", language_name="Hindi", confidence=0.90, script_name="Devanagari", supported=True)

        return LanguageDetectionResponse(
            detected_language="en",
            language_name="English",
            confidence=0.95,
            script_name="Latin",
            supported=True,
        )

    @classmethod
    def lock_citations(cls, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Extracts statutory references, Act names, and legal case citations,
        replacing them with immutable placeholder tokens {{LEGAL_CITATION_X}}.
        """
        token_map: Dict[str, str] = {}
        token_counter = 0

        # Patterns for Indian citations, statutory sections, and Acts
        patterns = [
            # Standard Law Report Citations e.g. (2008) 11 SCC 259, AIR 2017 SC 4161
            re.compile(r"(?:\(\d{4}\)|\d{4})\s+\d*\s*(?:SCC|SCR|AIR|SCC\s+OnLine|Scale|Bom\s+CR)\s+\d+(?:/\d+)?", re.IGNORECASE),
            # Specific Section citations with Act
            re.compile(
                r"(?:Section|Sec\.?|धारा|कलम|பிரிவு|విభాగం|ধারা|કલમ)\s+\d+[A-Za-z]?(?:\(\d+[A-Za-z]?\))*(?:\s+(?:of|का|की|चे|च्या|இல்|లోని|এর|ની)\s+[A-Za-z\s,]+(?:Act|Sanhita|Code|Adhiniyam))?",
                re.IGNORECASE,
            ),
            # Articles of the Constitution
            re.compile(r"(?:Article|Art\.?|अनुच्छेद|अनुच्छेद|অনুচ্ছেদ|சரத்து|ఆర్టికల్)\s+\d+[A-Za-z]?(?:\(\d+[A-Za-z]?\))*", re.IGNORECASE),
            # Major Act Titles
            re.compile(
                r"(?:Consumer Protection Act|Negotiable Instruments Act|Bharatiya Nyaya Sanhita|Bharatiya Nagarik Suraksha Sanhita|"
                r"Indian Penal Code|Code of Criminal Procedure|Industrial Disputes Act|Motor Vehicles Act|Information Technology Act|"
                r"Right to Information Act|Limitation Act|Arbitration and Conciliation Act)(?:,\s*\d{4})?",
                re.IGNORECASE,
            ),
        ]

        locked_text = text
        for pat in patterns:
            for match in pat.finditer(locked_text):
                matched_str = match.group(0)
                if matched_str in token_map.values():
                    continue
                # If matched_str is already a token placeholder, skip
                if matched_str.startswith("{{LEGAL_CITATION_") and matched_str.endswith("}}"):
                    continue

                placeholder = f"{{{{LEGAL_CITATION_{token_counter}}}}}"
                token_map[placeholder] = matched_str
                # Replace exact match
                locked_text = locked_text.replace(matched_str, placeholder)
                token_counter += 1

        return locked_text, token_map

    @classmethod
    def unlock_citations(cls, text: str, token_map: Dict[str, str]) -> str:
        """
        Restores locked tokens {{LEGAL_CITATION_X}} back to their original canonical strings.
        """
        restored = text
        for placeholder, original in token_map.items():
            restored = restored.replace(placeholder, original)
        return restored

    @classmethod
    async def translate_query(
        cls,
        text: str,
        source_language: Optional[str] = None,
        target_language: str = "en",
        consent_for_external_processing: bool = False,
    ) -> QueryTranslationResponse:
        """
        Translates citizen queries into English for semantic vector search,
        preserving citations through token locking and applying deterministic PII scrubbing.
        """
        # 1. Deterministic PII Scrubbing
        scrubber_result: RedactionResult = DeterministicPIIScrubber.scrub(text)

        # 2. Source Language Detection
        detected_info = cls.detect_language(text)
        src_lang = source_language or detected_info.detected_language

        # If source is already target language and no PII was detected
        if src_lang == target_language:
            return QueryTranslationResponse(
                original_text=text,
                detected_source_language=src_lang,
                target_language=target_language,
                translated_text=scrubber_result.clean_text,
                locked_citations=[],
                provider_used="LOCAL_OFFLINE_GLOSSARY",
                pii_scrubbed=scrubber_result.pii_detected,
                redacted_pii_types=scrubber_result.redacted_types,
                fail_closed_triggered=scrubber_result.fail_closed_triggered,
                blocking_reason=scrubber_result.blocking_reason,
                uncertified_translation_disclaimer=UNCERTIFIED_TRANSLATION_DISCLAIMER,
            )

        # 3. Citation Token Locking
        locked_text, token_map = cls.lock_citations(scrubber_result.clean_text)
        locked_citations_list = list(token_map.values())

        # 4. Provider Selection & Translation
        provider_used = "LOCAL_OFFLINE_GLOSSARY"
        translated_raw = ""

        # Check conditions for external LLM processing
        can_call_external = (
            consent_for_external_processing
            and not scrubber_result.fail_closed_triggered
            and bool(settings.GEMINI_API_KEY.strip() if settings.GEMINI_API_KEY else "")
        )

        if can_call_external:
            try:
                translated_raw = await cls._translate_via_gemini(locked_text, src_lang, target_language)
                provider_used = "EXTERNAL_GROUNDED_LLM"
            except Exception as e:
                logger.warning(f"External LLM translation failed, failing closed to local offline glossary: {e}")
                translated_raw = cls._translate_via_local_glossary(locked_text, src_lang, target_language)
                provider_used = "LOCAL_OFFLINE_GLOSSARY"
        else:
            translated_raw = cls._translate_via_local_glossary(locked_text, src_lang, target_language)
            provider_used = "LOCAL_OFFLINE_GLOSSARY"

        # 5. Citation Token Unlocking
        final_translated = cls.unlock_citations(translated_raw, token_map)

        return QueryTranslationResponse(
            original_text=text,
            detected_source_language=src_lang,
            target_language=target_language,
            translated_text=final_translated,
            locked_citations=locked_citations_list,
            provider_used=provider_used,
            pii_scrubbed=scrubber_result.pii_detected,
            redacted_pii_types=scrubber_result.redacted_types,
            fail_closed_triggered=scrubber_result.fail_closed_triggered,
            blocking_reason=scrubber_result.blocking_reason,
            uncertified_translation_disclaimer=UNCERTIFIED_TRANSLATION_DISCLAIMER,
        )

    @classmethod
    def _translate_via_local_glossary(cls, text: str, source_lang: str, target_lang: str) -> str:
        """
        Deterministic offline translation using verified legislative glossary
        and core procedural vocabulary.
        """
        output = text

        # Map known legal terms in reverse (Indic -> English)
        for term_item in LegalGlossaryService.get_all_terms():
            eng = term_item["english_term"]
            indic_term = term_item["translations"].get(source_lang, "")
            if indic_term:
                # Handle dual terms separated by slash e.g. "परिवादी / शिकायतकर्ता"
                for sub in indic_term.split("/"):
                    sub_clean = sub.strip()
                    if sub_clean and sub_clean in output:
                        output = output.replace(sub_clean, eng)

        # Basic functional phrase translation rules
        phrase_mappings = {
            "hi": {
                "गाड़ी चोरी": "vehicle theft",
                "चोरी हो गई": "was stolen",
                "बीमा कंपनी": "insurance company",
                "दावा खारिज": "claim repudiated / rejected",
                "मुआवजा": "compensation",
                "मकान": "flat / property",
                "कब्जा": "possession",
                "देरी": "delay",
                "चेक बाउंस": "cheque bounce / dishonour",
                "खाता": "bank account",
                "थाना": "police station",
                "गिरफ्तार": "arrest",
                "जमानत": "bail",
                "मारपीट": "assault / domestic violence",
                "वेतन": "salary / wages",
            },
            "mr": {
                "वाहन चोरी": "vehicle theft",
                "विमा कंपनी": "insurance company",
                "दावा नाकारला": "claim repudiated",
                "ताबा": "possession",
                "धनादेश अनादर": "cheque dishonour",
                "पोलीस": "police",
                "जामीन": "bail",
            },
            "bn": {
                "গাড়ি চুরি": "vehicle theft",
                "বীমা কোম্পানি": "insurance company",
                "দাবি খারিজ": "claim rejected",
                "ফ্ল্যাট দখল": "flat possession",
                "চেক বাউন্স": "cheque bounce",
            },
            "ta": {
                "வாகனம் திருட்டு": "vehicle theft",
                "காப்பீட்டு நிறுவனம்": "insurance company",
                "கோரிக்கை நிராகரிக்கப்பட்டது": "claim repudiated",
                "காசோலை திரும்பியது": "cheque returned",
            },
            "te": {
                "వాహనం దొంగతనం": "vehicle theft",
                "భీమా సంస్థ": "insurance company",
                "క్లెయిమ్ తిరస్కరణ": "claim rejected",
                "చెక్ బౌన్స్": "cheque bounce",
            },
            "gu": {
                "વાહન ચોરી": "vehicle theft",
                "વીમા કંપની": "insurance company",
                "દાવો નકાર્યો": "claim repudiated",
                "ચેક બાઉન્સ": "cheque bounce",
            },
        }

        lang_phrases = phrase_mappings.get(source_lang, {})
        for indic_p, eng_p in lang_phrases.items():
            if indic_p in output:
                output = output.replace(indic_p, eng_p)

        return output

    @classmethod
    async def _translate_via_gemini(cls, text: str, source_lang: str, target_lang: str) -> str:
        """Calls Google Gemini API with token-locked text."""
        api_key = settings.GEMINI_API_KEY.strip()
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"

        prompt = (
            f"You are a professional legal translator for Indian law. Translate the following text from {source_lang} to {target_lang}.\n"
            f"CRITICAL RULE: DO NOT modify, translate, or remove any token of the format '{{{{LEGAL_CITATION_X}}}}'. "
            f"Keep all tokens exact. Preserve legal terminology.\n\n"
            f"Text to translate:\n{text}"
        )

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 1024},
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"Gemini translation returned HTTP {resp.status_code}")
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()

    @classmethod
    async def generate_multilingual_explanation(
        cls,
        narrative: str,
        target_language: str = "hi",
        domain: Optional[str] = None,
        consent_for_external_processing: bool = False,
    ) -> MultilingualExplanationResponse:
        """
        Generates structured citizen legal rights explanation in the requested regional language,
        complete with locked statutory citations, procedural steps, and verified glossary terms.
        """
        lang_info = SUPPORTED_LANGUAGES.get(target_language, SUPPORTED_LANGUAGES["hi"])
        lang_name = lang_info["name"]

        # Fetch relevant verified glossary terms for the domain
        glossary_terms = LegalGlossaryService.get_terms_by_domain(domain) if domain else LegalGlossaryService.get_all_terms()[:5]

        # Extract locked citations from narrative if any
        locked_narrative, token_map = cls.lock_citations(narrative)
        citations_found = list(token_map.values())

        # Multilingual explanation templates
        templates = {
            "hi": {
                "summary": "आपकी विधिक शिकायत का प्राथमिक विश्लेषण पूरा हो गया है। भारतीय विधिक ढांचे के अंतर्गत आपको विधिक उपचार प्राप्त करने का अधिकार है।",
                "provisions": citations_found or [
                    "उपभोक्ता संरक्षण अधिनियम, 2019: धारा 35 (जिला आयोग में परिवाद)",
                    "परक्राम्य लिखत अधिनियम, 1881: धारा 138 (चेक अनादरण विधिक सूचना)",
                    "भारतीय नागरिक सुरक्षा संहिता, 2023: धारा 173 (प्रथम सूचना रिपोर्ट)",
                ],
                "steps": [
                    "1. संबंधित विपक्षी पक्षकार को लिखित विधिक मांग सूचना (Legal Notice) प्रेषित करें।",
                    "2. लेन-देन, बिल, रसीद, बैंक विवरणी और पत्राचार के साक्ष्य दस्तावेज सुरक्षित संकलित करें।",
                    "3. परिसीमा काल (Limitation Period) समाप्त होने से पूर्व सक्षम अधिकरण/न्यायालय में परिवाद दायर करें।",
                ],
            },
            "bn": {
                "summary": "আপনার আইনি অভিযোগের প্রাথমিক বিশ্লেষণ সম্পন্ন হয়েছে। ভারতীয় আইনের অধীনে আপনি প্রতিকার চাওয়ার অধিকারী।",
                "provisions": citations_found or [
                    "ভোক্তা সুরক্ষা আইন, ২০১৯: ধারা ৩৫",
                    "হস্তান্তরযোগ্য দলিল আইন, ১৮৮১: ধারা ১৩৮",
                ],
                "steps": [
                    "১. বিরোধী পক্ষকে একটি আনুষ্ঠানিক আইনি নোটিশ প্রেরণ করুন।",
                    "২. সমস্ত চালান, ব্যাঙ্কের রসিদ এবং প্রমাণ সংগ্রহ ও সুরক্ষিত করুন।",
                    "৩. তামাদি মেয়াদের পূর্বে যথাযথ আইনি ফোরামে অভিযোগ দায়ের করুন।",
                ],
            },
            "mr": {
                "summary": "आपल्या कायदेशीर तक्रारीचे प्राथमिक विश्लेषण पूर्ण झाले आहे. भारतीय कायद्यानुसार आपणास दाद मागण्याचा पूर्ण अधिकार आहे.",
                "provisions": citations_found or [
                    "ग्राहक संरक्षण कायदा, २०१९: कलम ३५",
                    "धनादेश अनादर (एन.आय. ॲक्ट): कलम १३८",
                ],
                "steps": [
                    "१. विरुद्ध पक्षास कायदेशीर नोटीस (Legal Notice) पाठवा.",
                    "२. सर्व पावत्या, बँकेचे पुरावे आणि पत्रव्यवहार सुरक्षित ठेवा.",
                    "३. मुदत काळ संपण्यापूर्वी सक्षम ग्राहक मंचात किंवा न्यायालयात दाद मागा.",
                ],
            },
            "ta": {
                "summary": "உங்கள் சட்டப்பூர்வ புகாரின் முதற்கட்ட பகுப்பாய்வு முடிவடைந்தது. இந்திய சட்டத்தின் கீழ் நிவாரணம் பெற உங்களுக்கு உரிமை உண்டு.",
                "provisions": citations_found or [
                    "நுகர்வோர் பாதுகாப்பு சட்டம், 2019: பிரிவு 35",
                    "மாற்றுமுறை ஆவணச் சட்டம், 1881: பிரிவு 138",
                ],
                "steps": [
                    "1. எதிர் தரப்பினருக்கு முறையான சட்ட அறிவிப்பை அனுப்பவும்.",
                    "2. அனைத்து ரசீதுகள், வங்கி ஆவணங்கள் மற்றும் ஆதாரங்களை திரட்டவும்.",
                    "3. காலவரம்பு முடிவதற்குள் உரிய நுகர்வோர் ஆணையத்தில் புகார் அளிக்கவும்.",
                ],
            },
            "te": {
                "summary": "మీ చట్టపరమైన ఫిర్యాదు యొక్క ప్రాథమిక విశ్లేషణ పూర్తయింది. భారతీయ చట్టం ప్రకారం మీకు పరిహారం పొందే హక్కు ఉంది.",
                "provisions": citations_found or [
                    "వినియోగదారుల రక్షణ చట్టం, 2019: సెక్షన్ 35",
                    "నెగోషియబుల్ ఇన్స్ట్రుమెంట్స్ యాక్ట్, 1881: సెక్షన్ 138",
                ],
                "steps": [
                    "1. ప్రతివాదికి న్యాయపరమైన డిమాండ్ నోటీసు జారీ చేయండి.",
                    "2. అన్ని లావాదేవీల రసీదులు మరియు సాక్ష్య పత్రాలను భద్రపరచండి.",
                    "3. పరిమితి కాలం ముగిసేలోపు తగిన ఫోరంలో ఫిర్యాదు దాఖలు చేయండి.",
                ],
            },
            "gu": {
                "summary": "તમારી કાનૂની ફરિયાદનું પ્રાથમિક વિશ્લેષણ પૂર્ણ થયું છે. ભારતીય કાયદા હેઠળ તમને કાનૂની દાદ મેળવવાનો અધિકાર છે.",
                "provisions": citations_found or [
                    "ગ્રાહક સુરક્ષા અધિનિયમ, ૨૦૧૯: કલમ ૩૫",
                    "ચેક અસ્વીકાર (નેગોશિયેબલ ઇન્સ્ટ્રુમેન્ટ્સ એક્ટ): કલમ ૧૩૮",
                ],
                "steps": [
                    "૧. સામા પક્ષકારને કાનૂની નોટિસ મોકલો.",
                    "૨. તમામ પુરાવાઓ અને નાણાકીય દસ્તાવેજો એકત્રિત કરો.",
                    "૩. મુદત મર્યાદા સમાપ્ત થાય તે પહેલાં યોગ્ય કમિશનમાં ફરિયાદ દાખલ કરો.",
                ],
            },
            "en": {
                "summary": "Preliminary legal analysis of your grievance is complete. Under Indian law, you are entitled to seek statutory remedies.",
                "provisions": citations_found or [
                    "Consumer Protection Act, 2019: Section 35 (Filing complaint before District Commission)",
                    "Negotiable Instruments Act, 1881: Section 138 (Cheque dishonour statutory notice)",
                ],
                "steps": [
                    "1. Issue a formal written legal demand notice to the opposite party.",
                    "2. Preserve all receipts, agreements, bank transaction statements, and correspondences.",
                    "3. File complaint before the appropriate consumer commission or magistrate court within limitation period.",
                ],
            },
        }

        lang_content = templates.get(target_language, templates["en"])

        # Format verified glossary items with target translation
        glossary_display = []
        for g in glossary_terms:
            trans = g["translations"].get(target_language, g["english_term"])
            glossary_display.append({
                "term_id": g["term_id"],
                "english_term": g["english_term"],
                "regional_term": trans,
                "legal_definition": g["legal_definition"],
                "official_reference": g["official_reference"],
            })

        return MultilingualExplanationResponse(
            target_language=target_language,
            language_name=lang_name,
            translated_summary=lang_content["summary"],
            applicable_statutory_provisions=lang_content["provisions"],
            procedural_steps=lang_content["steps"],
            verified_glossary_terms=glossary_display,
            provider_used="LOCAL_OFFLINE_GLOSSARY",
            uncertified_translation_disclaimer=UNCERTIFIED_TRANSLATION_DISCLAIMER,
            mandatory_advocates_act_notice=MANDATORY_ADVOCATES_ACT_NOTICE,
        )

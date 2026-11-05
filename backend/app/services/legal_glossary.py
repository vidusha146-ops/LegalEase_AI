"""
LegalEase AI - Verified Multilingual Legal Glossary
Phase 7 Module 2: Multilingual Legal Assistant

Authoritative legislative legal terms translated across 6 Indian regional languages:
Hindi (hi), Bengali (bn), Marathi (mr), Tamil (ta), Telugu (te), Gujarati (gu).
Terminology verified against Official Languages (Legislative) Commission /
Vidhi Sahitya Prakashan (Ministry of Law and Justice, Govt of India) and State Official Language Acts.
"""

from typing import Dict, Any, List, Optional


VERIFIED_LEGAL_GLOSSARY: List[Dict[str, Any]] = [
    {
        "term_id": "TERM_COMPLAINANT",
        "english_term": "Complainant",
        "domain": "GENERAL_PROCEDURAL",
        "legal_definition": "A citizen or entity that makes a formal legal allegation or grievance before a court, tribunal, or authority.",
        "statutory_context": "Section 2(5) Consumer Protection Act, 2019 / Section 2(d) CrPC, 1973 (Section 2(h) BNSS, 2023)",
        "official_reference": "Vidhi Sahitya Prakashan, Ministry of Law and Justice",
        "translations": {
            "hi": "परिवादी / शिकायतकर्ता",
            "bn": "অভিযোগকারী",
            "mr": "तक्रारदार",
            "ta": "புகார்தாரர்",
            "te": "ఫిర్యాదుదారు",
            "gu": "ફરિયાદી",
        },
    },
    {
        "term_id": "TERM_OPPOSITE_PARTY",
        "english_term": "Opposite Party",
        "domain": "CONSUMER_PROTECTION",
        "legal_definition": "A person or corporate entity against whom a legal grievance, complaint, or claim is instituted.",
        "statutory_context": "Section 2(31) Consumer Protection Act, 2019",
        "official_reference": "Consumer Protection Rules & Vidhi Sahitya Prakashan",
        "translations": {
            "hi": "विपक्षी / प्रत्यर्थी",
            "bn": "বিবাদী পক্ষ",
            "mr": "विरुद्ध पक्ष",
            "ta": "எதிர் தரப்பினர்",
            "te": "ఎదురు పక్షం",
            "gu": "સામા પક્ષકાર",
        },
    },
    {
        "term_id": "TERM_DEFICIENCY_OF_SERVICE",
        "english_term": "Deficiency of Service",
        "domain": "CONSUMER_PROTECTION",
        "legal_definition": "Any fault, imperfection, shortcoming or inadequacy in the quality, nature and manner of performance of a service required to be maintained by law or contract.",
        "statutory_context": "Section 2(11) Consumer Protection Act, 2019",
        "official_reference": "Official Translation of Consumer Protection Act, 2019 (Govt. of India)",
        "translations": {
            "hi": "सेवा में न्यूनता / कमी",
            "bn": "পরিষেবায় ত্রুটি",
            "mr": "सेवेतील त्रुटी",
            "ta": "சேவை குறைபாடு",
            "te": "సేవా లోపం",
            "gu": "સેવામાં ખામી",
        },
    },
    {
        "term_id": "TERM_CHEQUE_DISHONOUR",
        "english_term": "Cheque Dishonour",
        "domain": "CHEQUE_BOUNCE_NI_ACT",
        "legal_definition": "The refusal of a drawee bank to pay the amount of a cheque due to insufficiency of funds or agreement violation.",
        "statutory_context": "Section 138 Negotiable Instruments Act, 1881",
        "official_reference": "Official Language Commission, Legislative Department",
        "translations": {
            "hi": "चेक अनादरण",
            "bn": "চেক প্রত্যাখ্যান",
            "mr": "धनादेश अनादर",
            "ta": "காசோலை திரும்புதல்",
            "te": "చెక్ తిరస్కరణ",
            "gu": "ચેક અસ્વીકાર / બાઉન્સ",
        },
    },
    {
        "term_id": "TERM_COGNIZABLE_OFFENCE",
        "english_term": "Cognizable Offence",
        "domain": "CRIMINAL_LAW_BNS",
        "legal_definition": "An offence for which a police officer may arrest without a warrant in accordance with the law.",
        "statutory_context": "Section 2(c) CrPC, 1973 / Section 2(g) BNSS, 2023",
        "official_reference": "Code of Criminal Procedure Official Translation (Vidhi Sahitya)",
        "translations": {
            "hi": "संज्ञेय अपराध",
            "bn": "আমলযোগ্য অপরাধ",
            "mr": "दखलपात्र गुन्हा",
            "ta": "கைதுக்குரிய குற்றம்",
            "te": "విచారణార్హ నేరం",
            "gu": "પોલીસ અધિકારનો ગુનો",
        },
    },
    {
        "term_id": "TERM_BAIL",
        "english_term": "Bail",
        "domain": "CRIMINAL_LAW_BNS",
        "legal_definition": "The conditional release of an accused person from custody upon furnishing security or personal bond to appear before court.",
        "statutory_context": "Chapter XXXIII CrPC, 1973 / Chapter XXXV BNSS, 2023",
        "official_reference": "Legal Glossary, Legislative Department, Ministry of Law and Justice",
        "translations": {
            "hi": "जमानत",
            "bn": "জামিন",
            "mr": "जामीन",
            "ta": "ஜாமீன் / பிணை",
            "te": "బెయిల్ / పూచీకత్తు",
            "gu": "જામીન",
        },
    },
    {
        "term_id": "TERM_RATIO_DECIDENDI",
        "english_term": "Ratio Decidendi",
        "domain": "JUDICIAL_PRECEDENT",
        "legal_definition": "The underlying legal principle or rationale upon which the judicial decision is founded, which forms binding precedent.",
        "statutory_context": "Article 141 Constitution of India",
        "official_reference": "Supreme Court Rules & Vidhi Sahitya Prakashan",
        "translations": {
            "hi": "निर्णय का मूल आधार / निश्चायक आधार",
            "bn": "সিদ্ধান্তের মূল নীতি",
            "mr": "निर्णयाचे मुख्य सूत्र",
            "ta": "தீர்ப்பின் மூலக் கொள்கை",
            "te": "తీర్పు నిర్ణయాత్మక సూత్రం",
            "gu": "ચુકાદાનો મુખ્ય આધાર",
        },
    },
    {
        "term_id": "TERM_OBITER_DICTA",
        "english_term": "Obiter Dicta",
        "domain": "JUDICIAL_PRECEDENT",
        "legal_definition": "Incidental remarks or judicial opinions expressed in a judgment that are not essential to the disposition and lack binding authority.",
        "statutory_context": "Indian Precedent Doctrine / Article 141 Constitution",
        "official_reference": "Legal Glossary, Ministry of Law and Justice",
        "translations": {
            "hi": "प्रासंगिक उक्ति / प्रसंगोक्त",
            "bn": "প্রাসঙ্গিক মন্তব্য",
            "mr": "प्रासंगिक विधान",
            "ta": "துணை கருத்துக்கள்",
            "te": "ప్రాసంగిక వ్యాఖ్య",
            "gu": "પ્રાસંગિક કથન",
        },
    },
    {
        "term_id": "TERM_INTERIM_MAINTENANCE",
        "english_term": "Interim Maintenance",
        "domain": "DOMESTIC_VIOLENCE_FAMILY",
        "legal_definition": "Temporary financial support awarded to a spouse or dependent during the pendency of matrimonial litigation.",
        "statutory_context": "Section 125 CrPC / Section 24 Hindu Marriage Act / Section 20 DV Act",
        "official_reference": "Family Courts Act Glossary (Vidhi Sahitya)",
        "translations": {
            "hi": "अंतरिम भरण-पोषण",
            "bn": "অন্তর্বর্তীকালীন ভরণপোষণ",
            "mr": "अंतरिम पोटगी",
            "ta": "இடைக்கால பராமரிப்பு",
            "te": "మధ్యంతర నిర్వహణ భత్యం",
            "gu": "વચગાળાનું ભરણપોષણ",
        },
    },
    {
        "term_id": "TERM_RETRENCHMENT",
        "english_term": "Retrenchment",
        "domain": "LABOUR_EMPLOYMENT",
        "legal_definition": "The termination by the employer of the service of a workman for any reason whatsoever, otherwise than as a punishment.",
        "statutory_context": "Section 2(oo) Industrial Disputes Act, 1947",
        "official_reference": "Industrial Disputes Act Official Hindi/Regional Text",
        "translations": {
            "hi": "छंटनी",
            "bn": "ছাঁটাই",
            "mr": "कामगार कपात",
            "ta": "ஆட்குறைப்பு",
            "te": "ఉద్యోగ తొలగింపు",
            "gu": "છટણી",
        },
    },
    {
        "term_id": "TERM_JURISDICTION",
        "english_term": "Jurisdiction",
        "domain": "GENERAL_PROCEDURAL",
        "legal_definition": "The practical authority granted to a legal body to administer justice within a defined field of responsibility or territory.",
        "statutory_context": "Code of Civil Procedure, 1908 / Consumer Protection Act, 2019",
        "official_reference": "Legal Glossary, Legislative Department, Ministry of Law and Justice",
        "translations": {
            "hi": "क्षेत्राधिकार / अधिकारिता",
            "bn": "এখতিয়ার",
            "mr": "अधिकारक्षेत्र",
            "ta": "அதிகார வரம்பு",
            "te": "అధికార పరిధి",
            "gu": "હકૂમત / ક્ષેત્રાધિકાર",
        },
    },
    {
        "term_id": "TERM_LIMITATION_PERIOD",
        "english_term": "Limitation Period",
        "domain": "GENERAL_PROCEDURAL",
        "legal_definition": "The legally prescribed time limit within which an aggrieved person must initiate a lawsuit or legal proceeding.",
        "statutory_context": "Limitation Act, 1963 / Section 69 Consumer Protection Act, 2019",
        "official_reference": "Limitation Act Official Translation (Govt. of India)",
        "translations": {
            "hi": "परिसीमा काल",
            "bn": "তামাদি মেয়াদ",
            "mr": "मुदत काळ",
            "ta": "காலவரம்பு காலம்",
            "te": "పరిమితి కాలం",
            "gu": "સમયમર્યાદા / મુદત",
        },
    },
    {
        "term_id": "TERM_FIR",
        "english_term": "First Information Report",
        "domain": "CRIMINAL_LAW_BNS",
        "legal_definition": "Information given to the police officer in charge regarding the commission of a cognizable offence, recorded under statutory procedure.",
        "statutory_context": "Section 154 CrPC, 1973 / Section 173 BNSS, 2023",
        "official_reference": "Police Manuals & Vidhi Sahitya Prakashan",
        "translations": {
            "hi": "प्रथम सूचना रिपोर्ट (एफआईआर)",
            "bn": "প্রথম তথ্য প্রতিবেদন (এফআইআর)",
            "mr": "प्रथम खबरी अहवाल (एफआयआर)",
            "ta": "முதல் தகவல் அறிக்கை (எஃப்.ஐ.ஆர்)",
            "te": "ప్రథమ సమాచార నివేదిక (ఎఫ్ఐఆర్)",
            "gu": "પ્રથમ માહિતી અહેવાલ (એફઆઈઆર)",
        },
    },
]


class LegalGlossaryService:
    """Provides verified legislative glossary retrieval and term mappings."""

    @classmethod
    def get_all_terms(cls) -> List[Dict[str, Any]]:
        return VERIFIED_LEGAL_GLOSSARY

    @classmethod
    def get_terms_by_domain(cls, domain: str) -> List[Dict[str, Any]]:
        return [t for t in VERIFIED_LEGAL_GLOSSARY if t.get("domain") == domain]

    @classmethod
    def lookup_term(cls, english_term: str) -> Optional[Dict[str, Any]]:
        target = english_term.strip().lower()
        for t in VERIFIED_LEGAL_GLOSSARY:
            if t["english_term"].lower() == target:
                return t
        return None

    @classmethod
    def translate_term(cls, english_term: str, target_lang: str) -> Optional[str]:
        item = cls.lookup_term(english_term)
        if item and target_lang in item["translations"]:
            return item["translations"][target_lang]
        return None

    @classmethod
    def search_glossary(cls, query: str, lang: str = "en") -> List[Dict[str, Any]]:
        q = query.strip().lower()
        results = []
        for t in VERIFIED_LEGAL_GLOSSARY:
            if q in t["english_term"].lower():
                results.append(t)
                continue
            if lang in t["translations"] and q in t["translations"][lang].lower():
                results.append(t)
                continue
            if any(q in trans.lower() for trans in t["translations"].values()):
                results.append(t)
        return results

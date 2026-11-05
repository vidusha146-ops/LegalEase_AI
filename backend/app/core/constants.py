"""
Legal Constants, Regulatory Disclaimers, and Statutory Taxonomies.
Adheres strictly to the Advocates Act, 1961 and Bar Council of India guidelines.
"""

# Mandatory Statutory Disclaimer for Indian Citizens
LEGAL_DISCLAIMER_EN = (
    "LegalEase AI is an academic and informational decision support system designed to assist "
    "Indian citizens in understanding statutory rights and procedural guidelines. It does NOT "
    "constitute formal legal counsel, advocacy, or solicitation under the Advocates Act, 1961. "
    "No lawyer-client relationship is created. For court representation or formal legal advice, "
    "users must consult an enrolled Advocate or visit their nearest District Legal Services Authority (DLSA)."
)

LEGAL_DISCLAIMER_HI = (
    "लीगलईज़ एआई (LegalEase AI) एक शैक्षणिक और सूचनात्मक निर्णय समर्थन प्रणाली है जो भारतीय नागरिकों "
    "को उनके कानूनी अधिकारों और प्रक्रियाओं को समझने में सहायता करती है। यह अधिवक्ता अधिनियम, 1961 "
    "के तहत औपचारिक कानूनी सलाह नहीं है। अदालत में प्रतिनिधित्व के लिए कृपया किसी पंजीकृत अधिवक्ता या "
    "निकटतम जिला विधिक सेवा प्राधिकरण (DLSA) से संपर्क करें।"
)

# Core Legal Domains in Indian Law
LEGAL_DOMAINS = [
    "CRIMINAL_LAW_BNS",              # Bharatiya Nyaya Sanhita, 2023 (replacing IPC)
    "CONSUMER_PROTECTION",           # Consumer Protection Act, 2019
    "CYBER_LAW_IT_ACT",              # Information Technology Act, 2000
    "LABOUR_EMPLOYMENT",             # Industrial Disputes, Payment of Wages, Gratuity Act
    "FAMILY_MATRIMONIAL",            # Hindu Marriage Act, Special Marriage Act, DV Act 2005
    "RTI_GOVERNANCE",                # Right to Information Act, 2005
    "CHEQUE_BOUNCE_NI_ACT",          # Negotiable Instruments Act, 1881 (Sec 138)
    "PROPERTY_TENANCY",              # Transfer of Property Act, Rent Control Acts
    "MOTOR_VEHICLE_ACCIDENT",        # Motor Vehicles Act, 1988 (Amended 2019)
    "CONSTITUTIONAL_CIVIL_RIGHTS",   # Fundamental Rights, Writ Petitions (Art 226/32)
]

# Emergency & Legal Aid Helplines in India
OFFICIAL_INDIAN_HELPLINES = {
    "NATIONAL_CONSUMER_HELPLINE": "1915",
    "NATIONAL_CYBER_CRIME_REPORTING": "1930",
    "NALSA_LEGAL_AID_HELPLINE": "15100",
    "WOMEN_IN_DISTRESS_HELPLINE": "1091",
    "NATIONAL_EMERGENCY_NUMBER": "112",
}

# Confidence Levels
CONFIDENCE_HIGH = "HIGH"         # > 80% grounded in exact bare act provisions
CONFIDENCE_MEDIUM = "MEDIUM"     # 50 - 80% - requires factual clarification from user
CONFIDENCE_LOW = "LOW"           # < 50% - incomplete facts or highly discretionary judicial matter

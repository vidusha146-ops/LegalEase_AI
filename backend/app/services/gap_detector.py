"""
LegalEase AI - Statutory Legal Gap Detection & Interactive Follow-up Engine
Detects missing factual ingredients required under Indian statutes
and generates domain-tailored interactive questions for citizens.
"""

import re
from typing import Dict, Any, List


# Domain-specific statutory ingredient checklists
DOMAIN_STATUTORY_INGREDIENTS: Dict[str, List[Dict[str, Any]]] = {
    "CRIMINAL_LAW_BNS": [
        {
            "id": "INCIDENT_DATE",
            "name": "Date & Time of Incident",
            "keywords": [r"\b(?:on|date|dated|day|yesterday|ago|january|february|march|april|may|june|july|august|september|october|november|december|202[0-9])\b", r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}"],
            "severity": "CRITICAL",
            "rationale": "Essential under Article 20(1) to determine whether the substantive charge falls under Bharatiya Nyaya Sanhita (BNS, post July 1, 2024) or the Indian Penal Code (IPC, pre July 1, 2024).",
            "question": "What is the approximate date and time when this incident occurred?"
        },
        {
            "id": "JURISDICTION_LOCATION",
            "name": "Specific Place of Occurrence / Police Station",
            "keywords": [r"\b(?:at|in|place|location|colony|sector|nagar|road|street|market|station|thana|police station|city|district)\b"],
            "severity": "CRITICAL",
            "rationale": "Required under Section 173 of BNSS, 2023 to establish local territorial jurisdiction for FIR registration or Zero-FIR.",
            "question": "Where did this incident occur (locality, landmark, city, and nearest police station)?"
        },
        {
            "id": "ACCUSED_IDENTITY",
            "name": "Identity or Description of Accused / Suspects",
            "keywords": [r"\b(?:name|accused|suspect|person|men|woman|driver|neighbor|known|unknown|gangster|thief|burglar)\b"],
            "severity": "RECOMMENDED",
            "rationale": "Necessary for naming in the formal complaint draft or requesting investigation into unknown persons under Section 175 BNSS.",
            "question": "Do you know the identity, names, or physical descriptions of the suspect(s) involved?"
        },
        {
            "id": "PROPERTY_VALUE",
            "name": "Estimated Monetary Value of Property",
            "keywords": [r"\b(?:rupees|rs|inr|lakh|crore|worth|value|amount|thousand|\d+000)\b"],
            "severity": "RECOMMENDED",
            "rationale": "Determines whether the statutory community service proviso under Section 303(2) BNS applies (for first-time theft < Rs. 5,000) and whether the offense is cognizable.",
            "question": "What is the estimated monetary value of the stolen, damaged, or misappropriated property?"
        },
        {
            "id": "POLICE_REPORTED",
            "name": "Prior Police Report / FIR Status",
            "keywords": [r"\b(?:fir|police complaint|reported|thana|chowki|gd entry|general diary|sp|sho)\b"],
            "severity": "RECOMMENDED",
            "rationale": "If police refuse to register an FIR under Section 173(1) BNSS, citizens have the statutory remedy to petition the Superintendent of Police under Section 173(4) or Magistrate under Section 175(3).",
            "question": "Have you already approached the police or attempted to lodge an FIR or General Diary (GD) entry?"
        }
    ],

    "CONSUMER_PROTECTION": [
        {
            "id": "PURCHASE_PROOF",
            "name": "Proof of Purchase (Invoice / Bill / Order ID)",
            "keywords": [r"\b(?:invoice|bill|receipt|order id|tax invoice|cash memo|booking id|ticket)\b"],
            "severity": "CRITICAL",
            "rationale": "Mandatory under Section 2(7) of the Consumer Protection Act, 2019 to establish consumer status and consideration paid.",
            "question": "Do you have the purchase invoice, payment receipt, or order ID number for this transaction?"
        },
        {
            "id": "DATE_OF_PURCHASE",
            "name": "Date of Purchase / Transaction",
            "keywords": [r"\b(?:date|bought|purchased|ordered|on|202[0-9]|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b"],
            "severity": "CRITICAL",
            "rationale": "Section 69 of the Consumer Protection Act prescribes a strict 2-year limitation period from the date the cause of action arose.",
            "question": "On what date did you purchase the product or book the service?"
        },
        {
            "id": "OPPOSITE_PARTY_DETAILS",
            "name": "Exact Name & Address of Seller / Service Provider",
            "keywords": [r"\b(?:company|seller|dealer|manufacturer|showroom|hospital|airline|platform|e-commerce|brand)\b"],
            "severity": "CRITICAL",
            "rationale": "Required for issuance of statutory notice and impleadment in District Consumer Commission complaints under Section 35.",
            "question": "What is the registered name, office address, and contact email of the seller or service provider?"
        },
        {
            "id": "PRIOR_NOTICE_SERVED",
            "name": "Prior Grievance / Written Notice Sent",
            "keywords": [r"\b(?:email|notice|complaint|ticket|called|customer care|service center|refused|replied)\b"],
            "severity": "RECOMMENDED",
            "rationale": "Serving a 15-day pre-litigation legal notice or grievance ticket demonstrates bonafide attempt to resolve before seeking forum relief under Section 39.",
            "question": "Have you sent a formal written complaint or email notice to the company giving them an opportunity to rectify the issue?"
        }
    ],

    "CYBER_LAW_IT_ACT": [
        {
            "id": "TRANSACTION_ID_UTR",
            "name": "Bank UTR / UPI Transaction Reference Number",
            "keywords": [r"\b(?:utr|transaction id|reference|ref no|upi id|debit|transferred|account)\b"],
            "severity": "CRITICAL",
            "rationale": "Crucial for police cyber cells and banks to trace and freeze fraudulent beneficiary accounts under Section 66D IT Act.",
            "question": "Do you have the bank transaction reference number (UTR / UPI Ref ID) for the fraudulent debit?"
        },
        {
            "id": "INCIDENT_TIMELINESS",
            "name": "Time Elapsed Since Unauthorized Transaction",
            "keywords": [r"\b(?:hours|today|yesterday|minutes|immediately|days|recently)\b"],
            "severity": "CRITICAL",
            "rationale": "The first 2 to 4 hours represent the 'Golden Window' to dial Cyber Helpline 1930 and reverse transactions before funds are withdrawn from ATM networks.",
            "question": "How many hours or days have passed since the unauthorized transaction occurred?"
        },
        {
            "id": "SUSPECT_IDENTIFIERS",
            "name": "Suspect Digital Footprint (Phone / URL / Handle / App)",
            "keywords": [r"\b(?:phone|number|link|sms|website|url|whatsapp|telegram|apk|app|profile|screen)\b"],
            "severity": "RECOMMENDED",
            "rationale": "Preserves digital evidence required for certificate of electronic records under Section 63 of Bharatiya Sakshya Adhiniyam, 2023.",
            "question": "What phone numbers, links, APK apps, or social media handles were used by the fraudster?"
        },
        {
            "id": "BANK_REPORTED",
            "name": "Written Notification to Bank",
            "keywords": [r"\b(?:bank|blocked|frozen|card blocked|branch|customer care|chargeback)\b"],
            "severity": "CRITICAL",
            "rationale": "Under RBI Circular DBR.No.Leg.BC.78/09.07.005/2017-18, reporting unauthorized transactions within 3 days ensures zero liability for the customer.",
            "question": "Have you formally notified your bank to freeze the account/card and lodged an unauthorized transaction dispute?"
        }
    ],

    "CHEQUE_BOUNCE_NI_ACT": [
        {
            "id": "RETURN_MEMO_DATE",
            "name": "Date of Bank Return Memo",
            "keywords": [r"\b(?:memo|return memo|dishonour date|dated|bank slip|slip)\b", r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}"],
            "severity": "CRITICAL",
            "rationale": "Section 138(b) of the Negotiable Instruments Act strictly requires sending a statutory demand notice within 30 days of receiving the bank memo.",
            "question": "What is the exact date stamped on the bank cheque return memo?"
        },
        {
            "id": "CHEQUE_NUMBER_AMOUNT",
            "name": "Cheque Number, Bank, & Amount",
            "keywords": [r"\b(?:cheque number|chq|amount|rupees|rs|lakh|thousand|\d{6})\b"],
            "severity": "CRITICAL",
            "rationale": "Must be specified with exactness in the legal demand notice and magistrate complaint.",
            "question": "What is the cheque number, issuing bank name, and exact amount?"
        },
        {
            "id": "STATUTORY_NOTICE_SERVED",
            "name": "Dispatch of 15-Day Statutory Legal Demand Notice",
            "keywords": [r"\b(?:legal notice|demand notice|registered post|speed post|tracking|served|dispatched)\b"],
            "severity": "CRITICAL",
            "rationale": "Cause of action under Section 138(c) arises only if the drawer fails to make payment within 15 days of receiving the registered demand notice.",
            "question": "Have you sent a formal legal demand notice via Registered Post / Speed Post giving 15 days to pay?"
        },
        {
            "id": "ENFORCEABLE_DEBT_PROOF",
            "name": "Proof of Legally Enforceable Debt or Liability",
            "keywords": [r"\b(?:invoice|agreement|promissory note|loan|supplied|bill|goods|debt|consideration)\b"],
            "severity": "RECOMMENDED",
            "rationale": "Required under Section 139 NI Act to substantiate the presumption of legally enforceable debt.",
            "question": "What documents (invoices, loan agreements, ledger balances) prove the legally enforceable debt?"
        }
    ],

    "LABOUR_EMPLOYMENT": [
        {
            "id": "EMPLOYMENT_PROOF",
            "name": "Proof of Employment (Appointment Letter / Salary Slips)",
            "keywords": [r"\b(?:appointment letter|contract|offer letter|salary slip|payslip|id card|pf)\b"],
            "severity": "CRITICAL",
            "rationale": "Establishes employer-employee relationship and contractual terms under the Industrial Disputes Act / Payment of Wages Act.",
            "question": "Do you have your appointment letter, recent salary slips, or official employee ID card?"
        },
        {
            "id": "TENURE_OF_SERVICE",
            "name": "Duration of Continuous Service",
            "keywords": [r"\b(?:years|months|service|tenure|joined|working since|continuous)\b"],
            "severity": "RECOMMENDED",
            "rationale": "5 years of continuous service is mandatory for claiming gratuity under Payment of Gratuity Act, 1972.",
            "question": "How many months or years of continuous service have you completed with this employer?"
        },
        {
            "id": "WRITTEN_TERMINATION_NOTICE",
            "name": "Written Termination Letter / Notice",
            "keywords": [r"\b(?:termination letter|relieving|email|verbal|notice period|severance)\b"],
            "severity": "RECOMMENDED",
            "rationale": "Determines whether termination violated statutory notice period or retrenchment compensation rules.",
            "question": "Did the company issue a written termination notice, or was it a verbal dismissal?"
        }
    ],

    "FAMILY_MATRIMONIAL": [
        {
            "id": "MARRIAGE_DETAILS",
            "name": "Date & Solemnization of Marriage",
            "keywords": [r"\b(?:married|wedding|marriage|solemnized|hindu marriage|registered|date)\b"],
            "severity": "CRITICAL",
            "rationale": "Establishes legal status of marriage under personal laws (Hindu Marriage Act, Special Marriage Act).",
            "question": "When and where was the marriage solemnized, and is it registered?"
        },
        {
            "id": "CHILD_DEPENDENTS",
            "name": "Minor Children / Dependents",
            "keywords": [r"\b(?:child|daughter|son|children|minor|custody|age|dependents)\b"],
            "severity": "RECOMMENDED",
            "rationale": "Crucial for calculating interim maintenance under Section 144 BNSS / Section 125 CrPC and determining guardianship.",
            "question": "Are there any minor children born from the wedlock, and with whom are they currently residing?"
        },
        {
            "id": "SPOUSE_INCOME_INDICATORS",
            "name": "Income and Assets of Spouse",
            "keywords": [r"\b(?:salary|earning|income|business|assets|car|property|bank|itr)\b"],
            "severity": "RECOMMENDED",
            "rationale": "Required for filing the mandatory Affidavit of Assets and Liabilities mandated by Supreme Court in Rajnesh v. Neha (2020).",
            "question": "What is the approximate monthly income, occupation, and lifestyle of the spouse?"
        }
    ],

    "RTI_GOVERNANCE": [
        {
            "id": "RTI_FILING_DATE",
            "name": "Filing Date of Original RTI Application",
            "keywords": [r"\b(?:filed on|dated|application date|submitted|receipt)\b", r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}"],
            "severity": "CRITICAL",
            "rationale": "Section 7(1) RTI Act gives 30 days for PIO response; first appeal limitation runs from expiry of this period.",
            "question": "On what date was the initial RTI application submitted?"
        },
        {
            "id": "PUBLIC_AUTHORITY_NAME",
            "name": "Name of Public Authority / Department",
            "keywords": [r"\b(?:department|ministry|corporation|panchayat|commission|board|officer|cpio|pio)\b"],
            "severity": "CRITICAL",
            "rationale": "Identifies the competent First Appellate Authority for filing statutory appeals under Section 19(1).",
            "question": "Which public department or authority was the RTI application addressed to?"
        }
    ],

    "PROPERTY_TENANCY": [
        {
            "id": "TENANCY_AGREEMENT",
            "name": "Written Lease / Tenancy Agreement",
            "keywords": [r"\b(?:lease|agreement|rent agreement|registered|tenancy deed|contract)\b"],
            "severity": "CRITICAL",
            "rationale": "Model Tenancy Act and Rent Control Acts require a written tenancy agreement to enforce rights and remedies.",
            "question": "Do you have a written or registered rent agreement with the landlord or tenant?"
        },
        {
            "id": "SECURITY_DEPOSIT_RECEIPT",
            "name": "Proof of Security Deposit Payment",
            "keywords": [r"\b(?:deposit|security|paid|transfer|bank transfer|receipt|advance)\b"],
            "severity": "RECOMMENDED",
            "rationale": "Essential documentary evidence for seeking refund through Rent Tribunal or Civil Court recovery suit.",
            "question": "What proof (bank transfer record, receipt) exists for the security deposit paid?"
        }
    ],

    "MOTOR_VEHICLE_ACCIDENT": [
        {
            "id": "VEHICLE_REGISTRATION_NUMBER",
            "name": "Offending Vehicle Registration Number",
            "keywords": [r"\b(?:vehicle number|car number|truck|bike|plate|dl\d|mh\d|ka\d|up\d|hr\d)\b"],
            "severity": "CRITICAL",
            "rationale": "Necessary for tracing owner and third-party insurance company in Motor Accident Claims Tribunal (MACT) petitions.",
            "question": "Did you note down the registration number of the offending vehicle?"
        },
        {
            "id": "POLICE_ACCIDENT_FIR",
            "name": "Accident FIR / Police Report",
            "keywords": [r"\b(?:fir|police report|accident report|dar|detailed accident report|gd entry)\b"],
            "severity": "CRITICAL",
            "rationale": "Detailed Accident Report (DAR) filed by police under Section 159 Motor Vehicles Act is treated as a claim petition before MACT.",
            "question": "Has an FIR or Detailed Accident Report (DAR) been registered at the local police station?"
        }
    ],

    "CONSTITUTIONAL_CIVIL_RIGHTS": [
        {
            "id": "STATE_AUTHORITY_NAMED",
            "name": "Public Officer / Department Acting Illegally",
            "keywords": [r"\b(?:police|officer|magistrate|collector|corporation|state|government|authority)\b"],
            "severity": "CRITICAL",
            "rationale": "Writs under Article 226 / 32 lie strictly against 'State' as defined under Article 12 of the Constitution.",
            "question": "Which specific public official, department, or state agency took the arbitrary action?"
        },
        {
            "id": "WRITTEN_SHOW_CAUSE_NOTICE",
            "name": "Show Cause Notice or Speaking Order Received",
            "keywords": [r"\b(?:notice|show cause|hearing|opportunity|speaking order|written reasons|natural justice)\b"],
            "severity": "RECOMMENDED",
            "rationale": "Failure to provide notice or hearing constitutes violation of Principles of Natural Justice (Audi Alteram Partem).",
            "question": "Did the authority issue any prior show-cause notice or provide an opportunity to present your side?"
        }
    ]
}


class LegalGapDetector:
    """
    Evaluates factual narratives against statutory ingredient checklists
    to identify missing legal elements and generate interactive follow-up questions.
    """

    @classmethod
    def detect_gaps(cls, text: str, domain: str) -> Dict[str, Any]:
        """
        Analyzes the user narrative for presence of required statutory ingredients.
        Returns provided ingredients, missing ingredients, completeness ratio,
        and prioritized interactive follow-up questions.
        """
        ingredients = DOMAIN_STATUTORY_INGREDIENTS.get(domain, [])
        if not ingredients:
            # Fallback for general or unlisted domains
            return {
                "domain": domain,
                "total_ingredients": 0,
                "provided_count": 0,
                "missing_count": 0,
                "completeness_ratio": 1.0,
                "provided_ingredients": [],
                "missing_ingredients": [],
                "follow_up_questions": [],
            }

        text_lower = text.lower()
        provided = []
        missing = []
        follow_ups = []

        for item in ingredients:
            is_present = False
            for pattern in item["keywords"]:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    is_present = True
                    break

            ingredient_info = {
                "id": item["id"],
                "name": item["name"],
                "severity": item["severity"],
                "rationale": item["rationale"],
            }

            if is_present:
                provided.append(ingredient_info)
            else:
                missing.append(ingredient_info)
                follow_ups.append(
                    {
                        "ingredient_id": item["id"],
                        "name": item["name"],
                        "severity": item["severity"],
                        "question": item["question"],
                        "rationale": item["rationale"],
                    }
                )

        total = len(ingredients)
        completeness_ratio = round(len(provided) / total, 4) if total > 0 else 1.0

        return {
            "domain": domain,
            "total_ingredients": total,
            "provided_count": len(provided),
            "missing_count": len(missing),
            "completeness_ratio": completeness_ratio,
            "provided_ingredients": provided,
            "missing_ingredients": missing,
            "follow_up_questions": follow_ups,
        }

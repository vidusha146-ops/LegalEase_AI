"""
LegalEase AI - Curated Legal Problem Classification Dataset Builder
Grounded in authentic Indian legal grievances across 10 statutory domains.
Each sample represents a realistic first-person citizen grievance in India.
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
CORPUS_FILE = DATA_DIR / "legal_problems_corpus.json"

DATASET = [
    # =========================================================================
    # 1. CRIMINAL_LAW_BNS (Bharatiya Nyaya Sanhita, 2023)
    # =========================================================================
    {
        "text": "My laptop and gold ring were stolen from my hostel room while I was attending lectures. The lock was picked and the room was ransacked.",
        "domain": "CRIMINAL_LAW_BNS",
        "sub_category": "THEFT",
        "key_ingredients": ["theft", "movable property", "dishonest taking", "without consent"]
    },
    {
        "text": "Two men on a motorcycle snatched my mother's gold chain while she was walking in the market yesterday evening and fled at high speed.",
        "domain": "CRIMINAL_LAW_BNS",
        "sub_category": "THEFT_SNATCHING",
        "key_ingredients": ["snatching", "force", "gold chain", "theft"]
    },
    {
        "text": "Burglars broke into our locked house at night while we were out of town for Diwali and took jewellery, cash, and electronic appliances worth Rs 3 lakhs.",
        "domain": "CRIMINAL_LAW_BNS",
        "sub_category": "HOUSEBREAKING_THEFT",
        "key_ingredients": ["dwelling house", "burglary", "theft", "breaking into locked premises"]
    },
    {
        "text": "A local gangster is calling my father daily threatening to shoot him and burn down our shop if we do not pay protection money of Rs 50,000 per month.",
        "domain": "CRIMINAL_LAW_BNS",
        "sub_category": "EXTORTION",
        "key_ingredients": ["extortion", "fear of injury", "threat to life", "dishonest inducement"]
    },
    {
        "text": "I entrusted my car and original registration papers to my mechanic for repairs, but he sold the vehicle to a third party and kept all the money.",
        "domain": "CRIMINAL_LAW_BNS",
        "sub_category": "CRIMINAL_BREACH_OF_TRUST",
        "key_ingredients": ["entrustment of property", "misappropriation", "dishonest conversion"]
    },
    {
        "text": "A builder promised me a 2BHK flat and took Rs 15 lakhs advance, but investigations revealed that he forged land sanction papers and has no title deed.",
        "domain": "CRIMINAL_LAW_BNS",
        "sub_category": "CHEATING_FORGERY",
        "key_ingredients": ["forged documents", "fraudulent inducement", "cheating", "delivery of property"]
    },
    {
        "text": "My neighbor attacked me with an iron rod following a parking altercation, fracturing my left arm and threatening to kill me if I report to police.",
        "domain": "CRIMINAL_LAW_BNS",
        "sub_category": "GRIEVOUS_HURT_INTIMIDATION",
        "key_ingredients": ["grievous hurt", "dangerous weapon", "fracture", "criminal intimidation"]
    },
    {
        "text": "Someone created a fake stamp and forged my signature on a property deed to sell our ancestral farmland behind our backs.",
        "domain": "CRIMINAL_LAW_BNS",
        "sub_category": "FORGERY",
        "key_ingredients": ["forged signature", "false document", "ancestral property", "intent to defraud"]
    },
    {
        "text": "Armed goons forcefully trespassed into our private agricultural godown, locked the guards inside a room, and looted 100 bags of wheat grain.",
        "domain": "CRIMINAL_LAW_BNS",
        "sub_category": "ROBBERY_TRESPASS",
        "key_ingredients": ["criminal trespass", "confinement", "looted property", "robbery"]
    },
    {
        "text": "A fraudulent travel agent collected passport copies and Rs 2 lakhs cash promising a Dubai work visa, but gave fake flight tickets and disappeared.",
        "domain": "CRIMINAL_LAW_BNS",
        "sub_category": "CHEATING",
        "key_ingredients": ["fake tickets", "dishonest inducement", "misrepresentation", "money paid"]
    },
    {
        "text": "The accused deliberately provoked a communal brawl in our neighborhood, pelted stones at houses, and physically assaulted passersby.",
        "domain": "CRIMINAL_LAW_BNS",
        "sub_category": "RIOTING_AFFRAY",
        "key_ingredients": ["unlawful assembly", "stone pelting", "public tranquility", "assault"]
    },
    {
        "text": "My business partner diverted corporate funds from our joint current account into his personal crypto wallet without my consent and fled the country.",
        "domain": "CRIMINAL_LAW_BNS",
        "sub_category": "CRIMINAL_BREACH_OF_TRUST",
        "key_ingredients": ["fiduciary duty", "unauthorized diversion", "misappropriation"]
    },
    {
        "text": "Someone stole my smartphone from my backpack while I was boarding a crowded metro train in New Delhi.",
        "domain": "CRIMINAL_LAW_BNS",
        "sub_category": "THEFT",
        "key_ingredients": ["theft", "movable property", "metro station", "without consent"]
    },
    {
        "text": "A man broke into my shop at night, broke open the cash register, and stole Rs 45,000 cash and inventory.",
        "domain": "CRIMINAL_LAW_BNS",
        "sub_category": "THEFT_HOUSEBREAKING",
        "key_ingredients": ["shop breaking", "cash stolen", "theft", "unlawful entry"]
    },
    {
        "text": "The local moneylender is threatening my family with physical violence and sending armed musclemen to our home to recover exorbitant 40% interest.",
        "domain": "CRIMINAL_LAW_BNS",
        "sub_category": "CRIMINAL_INTIMIDATION",
        "key_ingredients": ["criminal intimidation", "threat to cause injury", "extortionate conduct"]
    },

    # =========================================================================
    # 2. CONSUMER_PROTECTION (Consumer Protection Act, 2019)
    # =========================================================================
    {
        "text": "I purchased a smart LED TV from an electronics showroom with a 2-year manufacturer warranty. The display failed after 3 months, and the service center is refusing to repair or replace it.",
        "domain": "CONSUMER_PROTECTION",
        "sub_category": "DEFECTIVE_GOODS",
        "key_ingredients": ["warranty breach", "manufacturing defect", "refusal to service", "defective goods"]
    },
    {
        "text": "An e-commerce website delivered a counterfeit and used smartphone instead of the brand new model I ordered and paid for. They rejected my return request citing packaging policy.",
        "domain": "CONSUMER_PROTECTION",
        "sub_category": "UNFAIR_TRADE_PRACTICE",
        "key_ingredients": ["counterfeit goods", "deficiency in service", "return rejected", "e-commerce grievance"]
    },
    {
        "text": "I booked flight tickets to Mumbai, but the airline cancelled the flight without any prior notice and refused to provide a full refund or alternative accommodation.",
        "domain": "CONSUMER_PROTECTION",
        "sub_category": "DEFICIENCY_IN_SERVICE",
        "key_ingredients": ["flight cancellation", "deficiency of service", "refund denied", "compensation"]
    },
    {
        "text": "A private hospital charged Rs 2,50,000 for emergency treatment and billed me for medicines and oxygen cylinders that were never administered during the hospital stay.",
        "domain": "CONSUMER_PROTECTION",
        "sub_category": "MEDICAL_DEFICIENCY",
        "key_ingredients": ["excess billing", "service deficiency", "hospital overcharge", "unfair trade practice"]
    },
    {
        "text": "A real estate builder delayed possession of my flat by over 3 years beyond the agreed handover date in the builder-buyer agreement and is refusing to pay delay compensation.",
        "domain": "CONSUMER_PROTECTION",
        "sub_category": "BUILDER_DELAY",
        "key_ingredients": ["delayed possession", "builder buyer agreement", "deficiency of service", "interest claim"]
    },
    {
        "text": "I bought packaged baby milk powder from a supermarket that was past its expiry date, causing severe food poisoning and hospitalization for my infant child.",
        "domain": "CONSUMER_PROTECTION",
        "sub_category": "HAZARDOUS_GOODS",
        "key_ingredients": ["expired product", "product liability", "harm caused", "consumer compensation"]
    },
    {
        "text": "An insurance company rejected my health insurance cashless mediclaim for knee surgery citing a bogus non-disclosure clause despite all medical reports being submitted.",
        "domain": "CONSUMER_PROTECTION",
        "sub_category": "INSURANCE_DEFICIENCY",
        "key_ingredients": ["claim repudiation", "deficiency in insurance service", "arbitrary rejection"]
    },
    {
        "text": "The dry-cleaner lost my designer wedding sherwani worth Rs 45,000 and is offering only Rs 500 as compensation, citing terms printed in fine print on the receipt.",
        "domain": "CONSUMER_PROTECTION",
        "sub_category": "SERVICE_DEFICIENCY",
        "key_ingredients": ["loss of article", "deficiency in service", "inadequate compensation"]
    },
    {
        "text": "A coaching institute promised 100% placement guarantee in their brochure, charged Rs 1 lakh tuition fee, but shut down operations halfway through the academic course.",
        "domain": "CONSUMER_PROTECTION",
        "sub_category": "MISLEADING_ADVERTISEMENT",
        "key_ingredients": ["misleading advertisement", "unfair trade practice", "tuition fee refund"]
    },
    {
        "text": "The automobile dealer delivered a brand new car that had pre-existing engine transmission defects and stalled on the highway on the very first day of delivery.",
        "domain": "CONSUMER_PROTECTION",
        "sub_category": "MANUFACTURING_DEFECT",
        "key_ingredients": ["inherent defect", "defective goods", "replacement demand", "dealer liability"]
    },
    {
        "text": "I ordered groceries through a quick commerce delivery app, but several expensive items were missing from the package and customer support refused to issue a refund.",
        "domain": "CONSUMER_PROTECTION",
        "sub_category": "E_COMMERCE_DEFICIENCY",
        "key_ingredients": ["missing items", "delivery failure", "refund refused", "deficiency of service"]
    },
    {
        "text": "The telecom operator activated unauthorized paid value-added caller tune services on my postpaid mobile number and deducted charges for 8 consecutive months.",
        "domain": "CONSUMER_PROTECTION",
        "sub_category": "UNAUTHORIZED_BILLING",
        "key_ingredients": ["unauthorized deduction", "unfair trade practice", "telecom grievance"]
    },
    {
        "text": "The water purifier company took annual maintenance contract fees of Rs 6,000 but failed to send any technician for service for the entire year despite 12 complaints.",
        "domain": "CONSUMER_PROTECTION",
        "sub_category": "AMC_DEFICIENCY",
        "key_ingredients": ["service deficiency", "breach of contract", "annual maintenance", "consumer grievance"]
    },
    {
        "text": "A laptop manufacturer sold me a reconditioned second-hand laptop marketed and priced as a brand new premium ultrabook.",
        "domain": "CONSUMER_PROTECTION",
        "sub_category": "UNFAIR_TRADE_PRACTICE",
        "key_ingredients": ["misrepresentation", "used goods sold as new", "unfair trade practice"]
    },

    # =========================================================================
    # 3. CYBER_LAW_IT_ACT (Information Technology Act, 2000)
    # =========================================================================
    {
        "text": "I received an SMS claiming my electricity bill was unpaid with a link to update KYC. After clicking and entering details, Rs 95,000 was debited from my bank via unauthorized UPI transfers.",
        "domain": "CYBER_LAW_IT_ACT",
        "sub_category": "UPI_PHISHING_FRAUD",
        "key_ingredients": ["phishing link", "unauthorized debit", "UPI fraud", "identity theft"]
    },
    {
        "text": "A scammer created a fake WhatsApp profile using my photograph and name, contacting my relatives and colleagues requesting urgent emergency medical loans.",
        "domain": "CYBER_LAW_IT_ACT",
        "sub_category": "IMPERSONATION_IDENTITY_THEFT",
        "key_ingredients": ["identity theft", "cheating by personation", "computer source", "fake profile"]
    },
    {
        "text": "Someone hacked into my personal cloud storage and stole private intimate photographs, and is now blackmailing me via Telegram demanding Rs 2 lakhs to not leak them.",
        "domain": "CYBER_LAW_IT_ACT",
        "sub_category": "CYBER_EXTORTION_PRIVACY",
        "key_ingredients": ["unauthorized access", "privacy violation", "cyber extortion", "intimate images"]
    },
    {
        "text": "An unknown hacker infected my clinic computer with ransomware, encrypting all patient medical records and demanding Bitcoin payment to restore access.",
        "domain": "CYBER_LAW_IT_ACT",
        "sub_category": "RANSOMWARE_HACKING",
        "key_ingredients": ["ransomware", "unauthorized computer access", "data encryption", "damage to computer system"]
    },
    {
        "text": "I was duped by an online work-from-home Telegram scam promising high returns for rating Google Maps locations. I ended up losing Rs 4.5 lakhs in fictitious investment tasks.",
        "domain": "CYBER_LAW_IT_ACT",
        "sub_category": "ONLINE_INVESTMENT_FRAUD",
        "key_ingredients": ["cyber fraud", "online task scam", "cheating by personation", "electronic fund transfer"]
    },
    {
        "text": "Someone cloned my mobile SIM card through unauthorized KYC verification and intercepted banking OTPs to siphon off Rs 3 lakhs from my savings account.",
        "domain": "CYBER_LAW_IT_ACT",
        "sub_category": "SIM_SWAP_FRAUD",
        "key_ingredients": ["SIM swap", "OTP interception", "identity theft", "unauthorized fund access"]
    },
    {
        "text": "An anonymous Twitter handle is posting sexually explicit and morphed abusive images of my daughter along with her phone number and residential address.",
        "domain": "CYBER_LAW_IT_ACT",
        "sub_category": "CYBER_BULLYING_OBSCENITY",
        "key_ingredients": ["publishing obscene material", "doxxing", "harassment", "electronic form"]
    },
    {
        "text": "A disgruntled former employee stole our proprietary customer database containing confidential contact details and credit ratings before joining our competitor.",
        "domain": "CYBER_LAW_IT_ACT",
        "sub_category": "DATA_THEFT",
        "key_ingredients": ["data theft", "source code theft", "unauthorized downloading", "confidential breach"]
    },
    {
        "text": "I received a phone call from someone pretending to be a bank credit card manager who persuaded me to download AnyDesk screen sharing app, draining Rs 60,000.",
        "domain": "CYBER_LAW_IT_ACT",
        "sub_category": "REMOTE_ACCESS_FRAUD",
        "key_ingredients": ["remote access app", "social engineering", "cyber fraud", "cheating"]
    },
    {
        "text": "A fake matrimonial website collected Rs 25,000 membership fee and matched me with bot profiles that solicited money for customs clearance fees.",
        "domain": "CYBER_LAW_IT_ACT",
        "sub_category": "MATRIMONIAL_CYBER_SCAM",
        "key_ingredients": ["fake website", "cyber fraud", "cheating by personation", "customs scam"]
    },
    {
        "text": "My email account was hijacked and the hacker sent spoofed payment instruction emails to our overseas vendors requesting invoice payments to an offshore bank account.",
        "domain": "CYBER_LAW_IT_ACT",
        "sub_category": "BUSINESS_EMAIL_COMPROMISE",
        "key_ingredients": ["email spoofing", "unauthorized access", "wire fraud", "financial manipulation"]
    },
    {
        "text": "Someone installed covert spyware on my mobile phone to monitor my calls, read WhatsApp chats, and track my live GPS location without my knowledge.",
        "domain": "CYBER_LAW_IT_ACT",
        "sub_category": "SPYWARE_SURVEILLANCE",
        "key_ingredients": ["covert spyware", "unauthorized access", "privacy breach", "surveillance"]
    },
    {
        "text": "A fraudulent loan app harassed me by accessing my contact list and sending obscene abusive messages to my contacts threatening to defame me for a Rs 5,000 loan.",
        "domain": "CYBER_LAW_IT_ACT",
        "sub_category": "ILLEGAL_LOAN_APP_HARASSMENT",
        "key_ingredients": ["unauthorized data access", "contact list breach", "cyber harassment", "extortion"]
    },

    # =========================================================================
    # 4. LABOUR_EMPLOYMENT (Labour & Employment Laws)
    # =========================================================================
    {
        "text": "My software employer terminated my employment immediately without giving the mandatory 3 months notice period or paying severance salary stipulated in my contract.",
        "domain": "LABOUR_EMPLOYMENT",
        "sub_category": "WRONGFUL_TERMINATION",
        "key_ingredients": ["termination without notice", "severance pay", "employment contract", "unlawful dismissal"]
    },
    {
        "text": "The factory management has withheld salaries of 45 permanent workers for the last 5 months despite repeated formal representations and union meetings.",
        "domain": "LABOUR_EMPLOYMENT",
        "sub_category": "NON_PAYMENT_OF_WAGES",
        "key_ingredients": ["payment of wages", "delayed salary", "unlawful deduction", "labour dispute"]
    },
    {
        "text": "I worked continuously for 7 years in a manufacturing company, but upon resignation, the company is refusing to disburse my statutory gratuity and encashment of privileged leaves.",
        "domain": "LABOUR_EMPLOYMENT",
        "sub_category": "GRATUITY_DENIAL",
        "key_ingredients": ["payment of gratuity", "continuous service", "statutory benefit", "withholding"]
    },
    {
        "text": "My employer was deducting Provident Fund contributions from my monthly salary slip but failed to deposit the employee and employer share into my EPFO account for 2 years.",
        "domain": "LABOUR_EMPLOYMENT",
        "sub_category": "EPF_NON_DEPOSIT",
        "key_ingredients": ["provident fund", "EPFO default", "illegal deduction", "statutory non-compliance"]
    },
    {
        "text": "A private company denied maternity leave and statutory benefits to a female executive and terminated her services shortly after she notified her pregnancy.",
        "domain": "LABOUR_EMPLOYMENT",
        "sub_category": "MATERNITY_BENEFIT_DENIAL",
        "key_ingredients": ["maternity benefit act", "unlawful termination during pregnancy", "gender discrimination"]
    },
    {
        "text": "Workers at the construction site are made to work 14 hours every day without any overtime compensation or basic safety gear like helmets and safety harnesses.",
        "domain": "LABOUR_EMPLOYMENT",
        "sub_category": "FACTORIES_OVERTIME_VIOLATION",
        "key_ingredients": ["overtime wages", "occupational safety", "maximum working hours", "labour code"]
    },
    {
        "text": "The company refused to release my relieving letter, experience certificate, and final full and final settlement statement unless I sign an illegal blank bond.",
        "domain": "LABOUR_EMPLOYMENT",
        "sub_category": "WITHHOLDING_DOCUMENTS",
        "key_ingredients": ["relieving letter", "full and final settlement", "coercion", "employment bond"]
    },
    {
        "text": "My senior manager subjected me to unwelcome sexual advances and inappropriate remarks at work, and the Internal Complaints Committee (ICC) has failed to investigate for 4 months.",
        "domain": "LABOUR_EMPLOYMENT",
        "sub_category": "POSH_HARASSMENT",
        "key_ingredients": ["POSH act", "workplace sexual harassment", "internal complaints committee", "inaction"]
    },
    {
        "text": "The contract staffing agency has not paid minimum wages to security guards, paying only Rs 7,000 per month against the statutory notified rate of Rs 15,000.",
        "domain": "LABOUR_EMPLOYMENT",
        "sub_category": "MINIMUM_WAGES_VIOLATION",
        "key_ingredients": ["minimum wages act", "underpayment", "contract labour", "statutory violation"]
    },
    {
        "text": "The school management terminated a permanent teacher without holding any domestic inquiry or issuing a formal charge-sheet.",
        "domain": "LABOUR_EMPLOYMENT",
        "sub_category": "UNFAIR_LABOUR_PRACTICE",
        "key_ingredients": ["domestic inquiry", "principles of natural justice", "wrongful termination"]
    },
    {
        "text": "The IT firm arbitrarily changed my working hours to permanent night shifts without consent and slashed my base compensation by 30% citing company cost cutting.",
        "domain": "LABOUR_EMPLOYMENT",
        "sub_category": "UNILATERAL_CHANGE_OF_TERMS",
        "key_ingredients": ["unilateral salary reduction", "breach of contract", "terms of employment"]
    },

    # =========================================================================
    # 5. FAMILY_MATRIMONIAL (Family, Matrimonial & Domestic Law)
    # =========================================================================
    {
        "text": "My husband and mother-in-law are physically assaulting me and demanding a new SUV car and Rs 10 lakhs cash as additional dowry, locking me out of the matrimonial home.",
        "domain": "FAMILY_MATRIMONIAL",
        "sub_category": "DOWRY_CRUELTY",
        "key_ingredients": ["dowry demand", "cruelty by husband and in-laws", "matrimonial home", "physical abuse"]
    },
    {
        "text": "I am seeking monthly maintenance from my estranged husband who earns Rs 1.5 lakhs per month as a bank manager, but has abandoned me and our 5-year-old child without financial support.",
        "domain": "FAMILY_MATRIMONIAL",
        "sub_category": "MAINTENANCE_ALIMONY",
        "key_ingredients": ["maintenance", "neglect of wife and child", "interim maintenance", "abandonment"]
    },
    {
        "text": "My wife deserted me 3 years ago without any valid justification and took our minor daughter to another city, refusing to allow me any visitation or telephonic contact.",
        "domain": "FAMILY_MATRIMONIAL",
        "sub_category": "CHILD_CUSTODY_DESERTION",
        "key_ingredients": ["desertion", "child custody", "visitation rights", "guardianship"]
    },
    {
        "text": "I want to file for mutual consent divorce from my spouse as we have been living separately for over 2 years and mutually agreed on division of assets and child custody.",
        "domain": "FAMILY_MATRIMONIAL",
        "sub_category": "MUTUAL_DIVORCE",
        "key_ingredients": ["mutual consent divorce", "separation period", "settlement agreement", "family court"]
    },
    {
        "text": "My father passed away without leaving a will, and my two brothers are denying me my legal coparcenary share in the ancestral residential property and agricultural land.",
        "domain": "FAMILY_MATRIMONIAL",
        "sub_category": "HINDU_SUCCESSION_PARTITION",
        "key_ingredients": ["hindu succession act", "coparcener daughter rights", "intestate succession", "partition suit"]
    },
    {
        "text": "My husband has entered into a second marriage with another woman without legally obtaining a decree of divorce from me, our marriage being legally subsisting.",
        "domain": "FAMILY_MATRIMONIAL",
        "sub_category": "BIGAMY",
        "key_ingredients": ["bigamy", "subsisting marriage", "second marriage", "matrimonial offence"]
    },
    {
        "text": "I am filing an application under the Domestic Violence Act seeking immediate protection orders against verbal abuse, economic deprivation, and threats of eviction by my in-laws.",
        "domain": "FAMILY_MATRIMONIAL",
        "sub_category": "DOMESTIC_VIOLENCE_PROTECTION",
        "key_ingredients": ["protection of women from domestic violence act", "shared household", "monetary relief"]
    },
    {
        "text": "My maternal grandfather made a registered gift deed of his self-acquired property in my favor, but my uncles have filed a frivolous suit claiming he was of unsound mind.",
        "domain": "FAMILY_MATRIMONIAL",
        "sub_category": "PROPERTY_GIFT_DISPUTE",
        "key_ingredients": ["registered gift deed", "self-acquired property", "mental capacity", "family settlement"]
    },
    {
        "text": "My spouse constantly subjects me to extreme mental cruelty, making false accusations of adultery in front of family members and friends.",
        "domain": "FAMILY_MATRIMONIAL",
        "sub_category": "DIVORCE_CRUELTY",
        "key_ingredients": ["mental cruelty", "false allegations", "dissolution of marriage", "family court"]
    },
    {
        "text": "Elderly parents seeking maintenance from their wealthy son under the Senior Citizens Maintenance Act as he ousted them from their own house.",
        "domain": "FAMILY_MATRIMONIAL",
        "sub_category": "SENIOR_CITIZENS_MAINTENANCE",
        "key_ingredients": ["maintenance and welfare of parents and senior citizens act", "eviction", "elderly neglect"]
    },
    {
        "text": "Seeking restitution of conjugal rights as my husband withdrew from my society without any reasonable excuse after our wedding.",
        "domain": "FAMILY_MATRIMONIAL",
        "sub_category": "RESTITUTION_OF_CONJUGAL_RIGHTS",
        "key_ingredients": ["restitution of conjugal rights", "withdrawal from society", "hindu marriage act"]
    },

    # =========================================================================
    # 6. RTI_GOVERNANCE (Right to Information Act, 2005)
    # =========================================================================
    {
        "text": "I filed an RTI application with the Municipal Corporation regarding the tenders and expenditure on road repair in our ward, but have received no response even after 45 days.",
        "domain": "RTI_GOVERNANCE",
        "sub_category": "RTI_NON_RESPONSE",
        "key_ingredients": ["RTI application", "public information officer", "30 days statutory timeline", "deemed refusal"]
    },
    {
        "text": "The Central Public Information Officer (CPIO) arbitrarily rejected my RTI seeking civil works quality inspection reports citing Section 8 exemptions without giving any valid justification.",
        "domain": "RTI_GOVERNANCE",
        "sub_category": "RTI_ARBITRARY_REJECTION",
        "key_ingredients": ["CPIO rejection", "section 8 exemption misuse", "first appeal", "public interest"]
    },
    {
        "text": "I submitted a First Appeal to the Appellate Authority regarding denial of information by the education department, but 60 days have elapsed without any hearing or speaking order.",
        "domain": "RTI_GOVERNANCE",
        "sub_category": "RTI_FIRST_APPEAL_PENDING",
        "key_ingredients": ["first appeal", "first appellate authority", "second appeal to state information commission"]
    },
    {
        "text": "The public information officer demanded an exorbitant fee of Rs 25,000 for providing 100 pages of photocopy records, in direct violation of the standard RTI fee rules.",
        "domain": "RTI_GOVERNANCE",
        "sub_category": "EXORBITANT_FEE_DEMAND",
        "key_ingredients": ["RTI fee rules", "reasonable cost", "obstruction of information", "complaint under section 18"]
    },
    {
        "text": "Seeking information concerning life and liberty of an undertrial prisoner, which must be supplied within 48 hours under Section 7(1) of RTI Act, but jail authorities delayed for 10 days.",
        "domain": "RTI_GOVERNANCE",
        "sub_category": "RTI_LIFE_AND_LIBERTY",
        "key_ingredients": ["life or liberty", "48 hours timeline", "section 7 proviso", "statutory default"]
    },
    {
        "text": "The revenue department claimed in their RTI reply that land survey records from 2015 are missing and not traceable, attempting to cover up illegal encroachments on lake bed.",
        "domain": "RTI_GOVERNANCE",
        "sub_category": "RTI_MISSING_RECORDS",
        "key_ingredients": ["missing public records", "malafide denial", "penalty under section 20"]
    },
    {
        "text": "I want to file a Second Appeal before the Central Information Commission (CIC) against the Ministry of Railways for hiding internal accident probe findings.",
        "domain": "RTI_GOVERNANCE",
        "sub_category": "RTI_SECOND_APPEAL",
        "key_ingredients": ["second appeal", "central information commission", "statutory timeline", "disclosure of reports"]
    },
    {
        "text": "The PIO provided misleading and incomplete answers to my queries regarding teacher recruitment reservation quotas in government degree colleges.",
        "domain": "RTI_GOVERNANCE",
        "sub_category": "MISLEADING_INFORMATION",
        "key_ingredients": ["incomplete information", "false information", "section 20 penalty", "state information commission"]
    },
    {
        "text": "The development authority refused to provide environmental impact assessment reports for a newly sanctioned flyover claiming commercial confidence.",
        "domain": "RTI_GOVERNANCE",
        "sub_category": "COMMERCIAL_CONFIDENCE_CHALLENGE",
        "key_ingredients": ["public interest override", "environmental assessment", "section 8(1)(d)", "disclosure"]
    },
    {
        "text": "Filing complaint under Section 18 of RTI Act because the village panchayat office refused to accept my RTI application or give an acknowledgment receipt.",
        "domain": "RTI_GOVERNANCE",
        "sub_category": "REFUSAL_TO_RECEIVE_RTI",
        "key_ingredients": ["refusal to accept application", "section 18 complaint", "information commission"]
    },

    # =========================================================================
    # 7. CHEQUE_BOUNCE_NI_ACT (Negotiable Instruments Act, 1881)
    # =========================================================================
    {
        "text": "A client issued a cheque of Rs 3,50,000 for supply of steel rods which was dishonoured by the bank with the memo 'Funds Insufficient'. I want to send a statutory legal notice.",
        "domain": "CHEQUE_BOUNCE_NI_ACT",
        "sub_category": "CHEQUE_BOUNCE_INSUFFICIENT_FUNDS",
        "key_ingredients": ["cheque bounce", "funds insufficient", "section 138 notice", "30 days notice timeline"]
    },
    {
        "text": "A borrower issued three cheques of Rs 1,00,000 each towards repayment of a personal loan, but all cheques were returned unpaid with remarks 'Account Closed'.",
        "domain": "CHEQUE_BOUNCE_NI_ACT",
        "sub_category": "CHEQUE_BOUNCE_ACCOUNT_CLOSED",
        "key_ingredients": ["account closed", "dishonour of cheque", "discharge of debt", "section 138"]
    },
    {
        "text": "I served a formal legal notice under Section 138 of NI Act through registered post which was delivered 20 days ago, but the drawer has failed to make payment within 15 days.",
        "domain": "CHEQUE_BOUNCE_NI_ACT",
        "sub_category": "COMPLAINT_FILING_TIMELINE",
        "key_ingredients": ["statutory notice served", "15 days default period", "cause of action", "magistrate complaint"]
    },
    {
        "text": "The accused issued a cheque bearing forged signatures and then instructed their bank for 'Stop Payment' to avoid clearing legitimate supplier invoices.",
        "domain": "CHEQUE_BOUNCE_NI_ACT",
        "sub_category": "STOP_PAYMENT_DISHONOUR",
        "key_ingredients": ["stop payment instructions", "legally enforceable debt", "dishonour memo", "section 138"]
    },
    {
        "text": "A private limited company issued a business cheque of Rs 12 lakhs that bounced; I need to know whether the managing director and directors can be prosecuted under Section 141.",
        "domain": "CHEQUE_BOUNCE_NI_ACT",
        "sub_category": "COMPANY_VICARIOUS_LIABILITY",
        "key_ingredients": ["section 141 vicarious liability", "directors responsibility", "dishonoured company cheque"]
    },
    {
        "text": "In our cheque bounce complaint pending before Metropolitan Magistrate, we want to apply for 20% interim compensation under Section 143A of NI Act.",
        "domain": "CHEQUE_BOUNCE_NI_ACT",
        "sub_category": "INTERIM_COMPENSATION",
        "key_ingredients": ["section 143A", "interim compensation", "summary trial", "magistrate court"]
    },
    {
        "text": "The borrower claims the cheque was issued merely as security and not for an enforceable debt, attempting to evade trial in the Section 138 proceeding.",
        "domain": "CHEQUE_BOUNCE_NI_ACT",
        "sub_category": "SECURITY_CHEQUE_DEFENCE",
        "key_ingredients": ["security cheque", "presumption under section 139", "legally enforceable debt"]
    },
    {
        "text": "Bank return memo states 'Signature Differs from Specimen' on a cheque of Rs 75,000 given by my tenant towards 3 months rent arrears.",
        "domain": "CHEQUE_BOUNCE_NI_ACT",
        "sub_category": "SIGNATURE_MISMATCH_DISHONOUR",
        "key_ingredients": ["signature differs", "dishonour of cheque", "rent arrears", "legal notice"]
    },
    {
        "text": "Cheque dishonoured 5 days ago; need guidance on drafting legal demand notice within the mandatory 30 days limitation period.",
        "domain": "CHEQUE_BOUNCE_NI_ACT",
        "sub_category": "NOTICE_LIMITATION_PERIOD",
        "key_ingredients": ["30 days limitation", "demand notice", "return memo receipt", "section 138(b)"]
    },
    {
        "text": "The drawer paid only partial amount of Rs 20,000 out of Rs 1,00,000 cheque within the 15-day notice window, can I file the complaint for the balance?",
        "domain": "CHEQUE_BOUNCE_NI_ACT",
        "sub_category": "PARTIAL_PAYMENT_AFTER_NOTICE",
        "key_ingredients": ["partial payment", "failure to satisfy demand", "criminal complaint", "section 138"]
    },

    # =========================================================================
    # 8. PROPERTY_TENANCY (Property, Real Estate & Tenancy Disputes)
    # =========================================================================
    {
        "text": "The landlord has disconnected electricity and water connections to our rented apartment to forcefully evict us without any court order before the lease expired.",
        "domain": "PROPERTY_TENANCY",
        "sub_category": "ILLEGAL_DISPOSSESSION_UTILITIES",
        "key_ingredients": ["illegal eviction", "essential supplies disconnection", "rent control", "peaceful possession"]
    },
    {
        "text": "We vacated the rented flat after giving 1 month notice and handed over keys, but the landlord is refusing to refund our security deposit of Rs 1,20,000 citing bogus painting charges.",
        "domain": "PROPERTY_TENANCY",
        "sub_category": "SECURITY_DEPOSIT_WITHHOLDING",
        "key_ingredients": ["security deposit refund", "tenancy agreement", "unauthorized deduction", "civil recovery"]
    },
    {
        "text": "My neighbor has encroached upon 4 feet of my registered plot boundary while building his boundary wall, despite clear demarcations in my registered title deed.",
        "domain": "PROPERTY_TENANCY",
        "sub_category": "PLOT_BOUNDARY_ENCROACHMENT",
        "key_ingredients": ["boundary encroachment", "registered sale deed", "demarcation suit", "permanent injunction"]
    },
    {
        "text": "A tenant has not paid rent for the last 14 months and has refused to vacate the commercial shop premises even after expiry of the registered lease agreement.",
        "domain": "PROPERTY_TENANCY",
        "sub_category": "TENANT_EVICTION_ARREARS",
        "key_ingredients": ["eviction petition", "arrears of rent", "lease expiry", "rent tribunal"]
    },
    {
        "text": "Someone prepared a forged general power of attorney (GPA) and sold my vacant residential plot in suburban Bangalore to an unsuspecting third party.",
        "domain": "PROPERTY_TENANCY",
        "sub_category": "FRAUDULENT_LAND_SALE",
        "key_ingredients": ["forged power of attorney", "fraudulent conveyance", "declaration of title", "cancellation of sale deed"]
    },
    {
        "text": "I purchased an apartment from a builder who refuses to execute the registered sale deed and hand over the occupancy certificate (OC).",
        "domain": "PROPERTY_TENANCY",
        "sub_category": "OCCUPANCY_CERTIFICATE_CONVEYANCE",
        "key_ingredients": ["occupancy certificate", "conveyance deed", "RERA complaint", "specific performance"]
    },
    {
        "text": "Co-owner of our joint family property is attempting to sell the entire undivided ancestral property without obtaining consent of other legal heirs.",
        "domain": "PROPERTY_TENANCY",
        "sub_category": "UNDIVIDED_PROPERTY_SALE",
        "key_ingredients": ["undivided share", "partition suit", "temporary injunction", "ancestral estate"]
    },
    {
        "text": "The resident welfare association (RWA) is illegally preventing tenants from using the society clubhouse and swimming pool, imposing discriminatory charges.",
        "domain": "PROPERTY_TENANCY",
        "sub_category": "RWA_DISCRIMINATION",
        "key_ingredients": ["RWA bye-laws", "tenant rights", "discriminatory maintenance", "societies registration"]
    },
    {
        "text": "Landlord arbitrarily hiked monthly rent by 40% in one go, violating the statutory rent cap provisions of the Model Tenancy Act.",
        "domain": "PROPERTY_TENANCY",
        "sub_category": "EXORBITANT_RENT_HIKE",
        "key_ingredients": ["unlawful rent increase", "tenancy contract", "rent authority", "model tenancy act"]
    },
    {
        "text": "A builder constructed two extra unauthorized floors on top of our apartment complex in gross violation of the approved municipal sanctioned building plan.",
        "domain": "PROPERTY_TENANCY",
        "sub_category": "ILLEGAL_CONSTRUCTION",
        "key_ingredients": ["unauthorized construction", "sanctioned plan violation", "municipal corporation", "demolition notice"]
    },

    # =========================================================================
    # 9. MOTOR_VEHICLE_ACCIDENT (Motor Vehicles Act, 1988 / 2019)
    # =========================================================================
    {
        "text": "A speeding commercial truck ran a red light and hit my brother's motorcycle, causing severe head injuries, permanent disability, and ICU hospitalization.",
        "domain": "MOTOR_VEHICLE_ACCIDENT",
        "sub_category": "MACT_ACCIDENT_CLAIM",
        "key_ingredients": ["motor accident claims tribunal", "permanent disability", "rash and negligent driving", "third party insurance"]
    },
    {
        "text": "My father was killed in a hit-and-run road accident by an unidentified vehicle on the national highway. We need guidance on claiming compensation under the hit-and-run scheme.",
        "domain": "MOTOR_VEHICLE_ACCIDENT",
        "sub_category": "HIT_AND_RUN_COMPENSATION",
        "key_ingredients": ["hit and run", "fatal road accident", "solatium fund", "section 161 motor vehicles act"]
    },
    {
        "text": "The general insurance company repudiated our vehicle damage repair claim of Rs 1,80,000 alleging that the driver was not carrying a commercial badge endorsement.",
        "domain": "MOTOR_VEHICLE_ACCIDENT",
        "sub_category": "INSURANCE_CLAIM_REPUDIATION",
        "key_ingredients": ["insurance claim denial", "driving license endorsement", "own damage claim", "consumer forum"]
    },
    {
        "text": "An intoxicated driver crashed into our parked car outside our house at midnight, causing total vehicle loss and fleeing the spot without checking damage.",
        "domain": "MOTOR_VEHICLE_ACCIDENT",
        "sub_category": "DRUNK_DRIVING_PROPERTY_DAMAGE",
        "key_ingredients": ["drunken driving", "property damage", "FIR registration", "third party claim"]
    },
    {
        "text": "I was injured as a pillion rider when our cab driver collided with an electric pole due to reckless speeding on the expressway; how to claim compensation from cab aggregator insurance?",
        "domain": "MOTOR_VEHICLE_ACCIDENT",
        "sub_category": "CAB_PASSENGER_INJURY",
        "key_ingredients": ["passenger injury", "cab aggregator liability", "MACT claim", "medical expenses"]
    },
    {
        "text": "Police refused to register an accident FIR after a luxury SUV rammed my father's vegetable cart, citing political pressure from the car owner's family.",
        "domain": "MOTOR_VEHICLE_ACCIDENT",
        "sub_category": "FIR_NON_REGISTRATION_ACCIDENT",
        "key_ingredients": ["refusal to register FIR", "accident investigation", "section 173 BNSS", "superintendent of police"]
    },
    {
        "text": "Filing claim before MACT for loss of dependency and future prospects after the untimely death of our 32-year-old sole breadwinner in a bus accident.",
        "domain": "MOTOR_VEHICLE_ACCIDENT",
        "sub_category": "FATAL_ACCIDENT_DEPENDENCY",
        "key_ingredients": ["loss of dependency", "future prospects", "multiplier method", "fatal accident compensation"]
    },
    {
        "text": "The insurance company is delaying settlement of the MACT award granted by the tribunal 6 months ago, refusing to deposit the compensation amount in court.",
        "domain": "MOTOR_VEHICLE_ACCIDENT",
        "sub_category": "MACT_AWARD_EXECUTION",
        "key_ingredients": ["execution petition", "tribunal award", "interest on delayed compensation", "insurance company"]
    },
    {
        "text": "A municipal transport bus driver with an expired driving license caused a pile-up on the flyover damaging 5 private cars.",
        "domain": "MOTOR_VEHICLE_ACCIDENT",
        "sub_category": "UNLICENSED_DRIVER_LIABILITY",
        "key_ingredients": ["unlicensed driver", "owner liability", "third party claim", "motor vehicles act"]
    },
    {
        "text": "My brand new motorcycle was hit by an unregistered tractor carrying construction debris on a state highway.",
        "domain": "MOTOR_VEHICLE_ACCIDENT",
        "sub_category": "UNREGISTERED_VEHICLE_COLLISION",
        "key_ingredients": ["unregistered vehicle", "rash driving", "owner liability", "property damage"]
    },

    # =========================================================================
    # 10. CONSTITUTIONAL_CIVIL_RIGHTS (Constitutional & Civil Rights)
    # =========================================================================
    {
        "text": "Police arrested my brother without informing him of the grounds of arrest and kept him in unlawful custody for 48 hours without producing him before a judicial magistrate.",
        "domain": "CONSTITUTIONAL_CIVIL_RIGHTS",
        "sub_category": "HABEAS_CORPUS_ILLEGAL_DETENTION",
        "key_ingredients": ["illegal detention", "article 22 violation", "failure to produce before magistrate", "habeas corpus"]
    },
    {
        "text": "The district administration arbitrarily demolished our commercial shop without serving any prior show-cause notice or giving an opportunity for hearing.",
        "domain": "CONSTITUTIONAL_CIVIL_RIGHTS",
        "sub_category": "NATURAL_JUSTICE_DEMOLITION",
        "key_ingredients": ["violation of natural justice", "demolition without notice", "article 21", "writ petition"]
    },
    {
        "text": "State government authorities denied our peaceful student association permission to assemble and protest against fee hikes, invoking indiscriminate Section 144 orders.",
        "domain": "CONSTITUTIONAL_CIVIL_RIGHTS",
        "sub_category": "FREEDOM_OF_SPEECH_ASSEMBLY",
        "key_ingredients": ["freedom of speech and assembly", "article 19(1)(b)", "unreasonable restriction", "writ of mandamus"]
    },
    {
        "text": "A public university rejected a student's admission application despite qualifying in the entrance examination solely because of their transgender gender identity.",
        "domain": "CONSTITUTIONAL_CIVIL_RIGHTS",
        "sub_category": "EQUALITY_NON_DISCRIMINATION",
        "key_ingredients": ["article 14 and 15", "transgender persons protection of rights act", "discrimination in public education"]
    },
    {
        "text": "Local police subjected peaceful undertrial political prisoners to custodial beatings and torture inside the lockup to force a confession.",
        "domain": "CONSTITUTIONAL_CIVIL_RIGHTS",
        "sub_category": "CUSTODIAL_VIOLENCE",
        "key_ingredients": ["custodial torture", "article 21 violation", "human rights commission", "compensation claim"]
    },
    {
        "text": "The state public service commission cancelled the entire merit recruitment list arbitrarily without disclosing any inquiry report or assigning any objective rationale.",
        "domain": "CONSTITUTIONAL_CIVIL_RIGHTS",
        "sub_category": "ARBITRARY_STATE_ACTION",
        "key_ingredients": ["article 14 arbitrariness", "public employment", "writ of certiorari", "high court petition"]
    },
    {
        "text": "Internet services in our district have been continuously suspended for 30 consecutive days without any periodic review committee meetings or public review orders.",
        "domain": "CONSTITUTIONAL_CIVIL_RIGHTS",
        "sub_category": "INTERNET_SHUTDOWN_RIGHTS",
        "key_ingredients": ["telecom suspension rules", "anuradha bhasin judgment", "article 19(1)(a)", "proportionality"]
    },
    {
        "text": "A government hospital refused emergency delivery admission to an impoverished pregnant woman because she did not possess an Aadhaar card.",
        "domain": "CONSTITUTIONAL_CIVIL_RIGHTS",
        "sub_category": "RIGHT_TO_HEALTH_EMERGENCY",
        "key_ingredients": ["right to health", "article 21", "emergency medical treatment", "aadhaar denial"]
    },
    {
        "text": "Municipal corporation forcibly evicted street vendors possessing valid vending certificates without rehabilitating them under the Street Vendors Act.",
        "domain": "CONSTITUTIONAL_CIVIL_RIGHTS",
        "sub_category": "STREET_VENDORS_LIVELIHOOD",
        "key_ingredients": ["right to livelihood", "street vendors act", "article 21", "unlawful eviction"]
    },
    {
        "text": "Seeking a Writ of Quashing against a malicious political FIR filed to suppress investigative journalism exposing municipal corruption.",
        "domain": "CONSTITUTIONAL_CIVIL_RIGHTS",
        "sub_category": "MALICIOUS_PROSECUTION_WRIT",
        "key_ingredients": ["malicious prosecution", "freedom of press", "section 528 BNSS / 482 CrPC", "article 226"]
    }
]


def build_and_save_corpus():
    with open(CORPUS_FILE, "w", encoding="utf-8") as f:
        json.dump(DATASET, f, indent=2, ensure_ascii=False)
    
    print(f"Corpus successfully compiled and saved to: {CORPUS_FILE}")
    print(f"Total labeled citizen scenarios: {len(DATASET)}")
    
    # Class distribution check
    from collections import Counter
    counts = Counter(item["domain"] for item in DATASET)
    print("\nClass Distribution:")
    for domain, count in sorted(counts.items()):
        print(f"  - {domain:<30}: {count} samples")


if __name__ == "__main__":
    build_and_save_corpus()

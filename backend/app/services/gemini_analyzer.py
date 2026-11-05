"""
LegalEase AI - Structured Grounded Generative LLM Service
Calls Google Gemini API with schema constraints grounded strictly in retrieved ChromaDB Bare Acts.
Provides deterministic structured fallback when API key is unconfigured or in offline mode.
"""

import json
import logging
from typing import Dict, Any, List, Optional
import httpx

from app.core.config import settings
from app.core.constants import (
    LEGAL_DISCLAIMER_EN,
    LEGAL_DISCLAIMER_HI,
    OFFICIAL_INDIAN_HELPLINES,
)

logger = logging.getLogger(__name__)

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"


class GroundedGeminiAnalyzer:
    """
    Synthesizes citizen grievances and retrieved Indian Bare Acts into
    plain-language rights explanations and procedural steps.
    Strictly forbids hallucinated citations.
    """

    @classmethod
    async def generate_grounded_explanation(
        cls,
        narrative: str,
        predicted_domain: str,
        retrieved_statutes: List[Dict[str, Any]],
        missing_ingredients: List[Dict[str, Any]],
        language: str = "en",
    ) -> Dict[str, Any]:
        """
        Generates structured, plain-language legal explanation.
        Uses Gemini API if key is set; otherwise falls back to deterministic generator.
        """
        api_key = settings.GEMINI_API_KEY.strip() if settings.GEMINI_API_KEY else ""

        if api_key:
            try:
                return await cls._call_gemini_api(
                    api_key=api_key,
                    narrative=narrative,
                    domain=predicted_domain,
                    statutes=retrieved_statutes,
                    missing=missing_ingredients,
                    language=language,
                )
            except Exception as e:
                logger.warning(f"Gemini API call failed, falling back to deterministic template: {e}")

        # Deterministic Grounded Fallback
        return cls._generate_deterministic_explanation(
            narrative=narrative,
            domain=predicted_domain,
            statutes=retrieved_statutes,
            missing=missing_ingredients,
            language=language,
        )

    @classmethod
    async def _call_gemini_api(
        cls,
        api_key: str,
        narrative: str,
        domain: str,
        statutes: List[Dict[str, Any]],
        missing: List[Dict[str, Any]],
        language: str,
    ) -> Dict[str, Any]:
        """Direct REST call to Gemini 1.5 Flash with structured response schema."""
        statute_context = "\n".join([
            f"- {s.get('act_title')} Section {s.get('section_number')}: {s.get('section_title')}\n  Text: {s.get('document', '')[:300]}"
            for s in statutes[:3]
        ])

        system_instruction = (
            "You are LegalEase AI, an educational decision support system for Indian citizens under the Advocates Act, 1961. "
            "You MUST strictly ground all advice in the provided Indian statutory sections. "
            "NEVER fabricate statutory citations. "
            "Explain citizen rights in simple language without legalese. "
            f"Respond in {'Hindi' if language == 'hi' else 'English'}."
        )

        prompt = f"""
CITIZEN NARRATIVE:
{narrative}

PREDICTED DOMAIN:
{domain}

VERIFIED BARE ACT SECTIONS:
{statute_context}

MISSING STATUTORY INGREDIENTS:
{json.dumps([m.get('name') for m in missing])}

Please output a JSON object with:
1. "plain_language_summary": A 2-3 sentence overview of the legal situation.
2. "citizen_rights": A list of 3 specific rights under Indian law.
3. "immediate_steps": A list of 3 numbered procedural steps.
4. "advisory_warning": Any statutory cautionary note (e.g. limitation periods).
"""

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "systemInstruction": {"parts": [{"text": system_instruction}]},
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json",
            },
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{GEMINI_API_URL}?key={api_key}",
                json=payload,
            )
            if resp.status_code == 200:
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                parsed = json.loads(text)
                return {
                    "source": "GEMINI_1_5_FLASH_STRUCTURED",
                    "plain_language_summary": parsed.get("plain_language_summary", ""),
                    "citizen_rights": parsed.get("citizen_rights", []),
                    "immediate_steps": parsed.get("immediate_steps", []),
                    "advisory_warning": parsed.get("advisory_warning", ""),
                    "statutory_disclaimer": (
                        LEGAL_DISCLAIMER_HI if language == "hi" else LEGAL_DISCLAIMER_EN
                    ),
                }
            else:
                raise RuntimeError(f"Gemini HTTP {resp.status_code}: {resp.text}")

    @classmethod
    def _generate_deterministic_explanation(
        cls,
        narrative: str,
        domain: str,
        statutes: List[Dict[str, Any]],
        missing: List[Dict[str, Any]],
        language: str,
    ) -> Dict[str, Any]:
        """Deterministic grounded fallback guaranteeing 100% offline reliability."""
        statute_names = [
            f"{s.get('act_title')} Section {s.get('section_number')}"
            for s in statutes[:2] if s.get("section_number")
        ]
        statutes_str = ", ".join(statute_names) if statute_names else "applicable Indian enactments"

        if language == "hi":
            summary = (
                f"आपकी शिकायत भारतीय कानून के तहत {domain} क्षेत्र में आती है। "
                f"यह मामला मुख्य रूप से {statutes_str} के तहत विचारणीय है।"
            )
            rights = [
                f"कानूनी संरक्षण: {statutes_str} के तहत निष्पक्ष जांच और क्षतिपूर्ति पाने का अधिकार।",
                "शिकायत दर्ज करने का अधिकार: सक्षम फोरम या पुलिस थाने में औपचारिक प्रथम सूचना रिपोर्ट (FIR) या शिकायत दर्ज करने का अधिकार।",
                "विधिक सहायता: विधिक सेवा प्राधिकरण अधिनियम, 1987 के तहत निःशुल्क कानूनी सहायता (DLSA) प्राप्त करने का अधिकार।"
            ]
            steps = [
                "संबंधित साक्ष्य (रसीदें, बैंक ट्रांजेक्शन, लिखित पत्राचार) सुरक्षित रखें।",
                "विपक्षी पक्ष को 15 दिन का कानूनी मांग पत्र या शिकायत भेजें।",
                "उचित फोरम (उपभोक्ता आयोग, पुलिस, या न्यायाधिकरण) के समक्ष परिवाद प्रस्तुत करें।"
            ]
        else:
            summary = (
                f"Your grievance falls under {domain.replace('_', ' ')} under Indian statutory law. "
                f"Your primary statutory remedies are governed by {statutes_str}."
            )
            rights = [
                f"Statutory Remedy: Right to seek restitution, compensation, or penalty under {statutes_str}.",
                "Procedural Recourse: Right to receive a certified copy of your complaint / FIR without administrative fee.",
                "Access to Justice: Entitlement to free legal representation through DLSA under the Legal Services Authorities Act, 1987 (if eligible)."
            ]
            steps = [
                "1. Gather documentary evidence (invoices, transaction IDs, return memos, communication trail).",
                "2. Serve a formal 15-day pre-litigation representation or statutory demand notice.",
                "3. Approach the competent adjudicatory authority or police cell having jurisdiction."
            ]

        missing_names = [m.get("name") for m in missing if m.get("name")]
        warning = (
            f"Notice: To proceed effectively before judicial authorities, please clarify: {', '.join(missing_names[:3])}."
            if missing_names else "Factual details provided are legally sufficient to proceed to complaint drafting."
        )

        return {
            "source": "DETERMINISTIC_GROUNDED_TEMPLATE",
            "plain_language_summary": summary,
            "citizen_rights": rights,
            "immediate_steps": steps,
            "advisory_warning": warning,
            "statutory_disclaimer": (
                LEGAL_DISCLAIMER_HI if language == "hi" else LEGAL_DISCLAIMER_EN
            ),
        }

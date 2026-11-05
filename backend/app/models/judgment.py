"""
LegalEase AI - Court Judgment Model (Phase 7 Module 1)
Stores structured Indian court judgments with multi-dimensional precedential authority,
factual summaries, ratio decidendi, obiter dicta, and proposition-level subsequent treatment.
"""

from datetime import date, datetime, timezone
from typing import Optional, List
from sqlalchemy import Date, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models.base import TimestampMixin


class CourtJudgment(Base, TimestampMixin):
    """
    SQL Metadata model for verified Indian court judgments.
    Decouples factual summary from ratio decidendi and obiter dicta.
    Tracks proposition-level subsequent judicial treatment under the doctrine of precedent.
    """
    __tablename__ = "court_judgments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    judgment_key: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    case_title: Mapped[str] = mapped_column(String(255), nullable=False)
    canonical_citation: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    court: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    bench_type: Mapped[str] = mapped_column(String(50), nullable=False)
    bench_size: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    coram: Mapped[str] = mapped_column(String(255), nullable=False)
    judgment_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    legal_domain: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    jurisdiction_state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    authoritative_language: Mapped[str] = mapped_column(String(50), default="English", nullable=False)

    # Segmented Legal Layers with Pinpoint Paragraph Provenance
    factual_summary: Mapped[str] = mapped_column(Text, nullable=False)
    facts_paragraph_pinpoint: Mapped[str] = mapped_column(String(100), default="paras 1-5", nullable=False)
    ratio_decidendi: Mapped[str] = mapped_column(Text, nullable=False)
    ratio_paragraph_pinpoint: Mapped[str] = mapped_column(String(100), default="paras 10-12", nullable=False)
    obiter_dicta: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    dicta_paragraph_pinpoint: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    disposition_held: Mapped[str] = mapped_column(Text, nullable=False)

    # Three-Way Precedent Status Decoupling
    judgment_verification_status: Mapped[str] = mapped_column(
        String(50), default="UNVERIFIED_STATUS", nullable=False
    )  # IMPORTED | PROVISIONAL | VERIFIED
    landmark_designation_status: Mapped[str] = mapped_column(
        String(50), default="ORDINARY_PRECEDENT", nullable=False
    )  # ORDINARY_PRECEDENT | PROPOSED_LANDMARK | DESIGNATED_LANDMARK
    precedent_status: Mapped[str] = mapped_column(
        String(50), default="AFFIRMED_LANDMARK", nullable=False
    )  # AFFIRMED_LANDMARK | OVERRULED | NARROWED_MODIFIED | DISTINGUISHED | UNVERIFIED_STATUS

    # Overruling Provenance (Populated when legal proposition is overruled by larger bench)
    overruling_citation: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    overruling_bench_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    overruling_paragraph_pinpoint: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    subsequent_propositions_json: Mapped[str] = mapped_column(Text, default="[]")

    # Statutory Grounds & Official Source Provenance
    acts_cited_json: Mapped[str] = mapped_column(Text, default="[]")  # e.g. ["CONSUMER_PROTECTION_2019:35"]
    source_url: Mapped[str] = mapped_column(String(500), nullable=False)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    def __repr__(self) -> str:
        return f"<CourtJudgment(key='{self.judgment_key}', title='{self.case_title[:30]}', court='{self.court}')>"

from typing import Optional
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class TimelineEvent(Base, TimestampMixin):
    """
    Extracted chronological event for building the evidence timeline,
    identifying temporal gaps and inconsistencies in claims.
    """
    __tablename__ = "timeline_events"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("legal_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    evidence_id: Mapped[Optional[int]] = mapped_column(ForeignKey("evidence_documents.id", ondelete="SET NULL"), nullable=True)
    
    event_date: Mapped[str] = mapped_column(String(100), nullable=False)
    event_title: Mapped[str] = mapped_column(String(255), nullable=False)
    event_description: Mapped[str] = mapped_column(Text, nullable=False)
    source_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    confidence_level: Mapped[str] = mapped_column(String(20), default="HIGH", nullable=False)

    # Relationships
    case: Mapped["LegalCase"] = relationship("LegalCase", back_populates="timeline_events")
    evidence_document: Mapped[Optional["EvidenceDocument"]] = relationship(
        "EvidenceDocument", back_populates="timeline_events"
    )

    def __repr__(self) -> str:
        return f"<TimelineEvent(id={self.id}, date='{self.event_date}', title='{self.event_title[:30]}')>"

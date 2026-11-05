from typing import List, Optional
from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class LegalCase(Base, TimestampMixin):
    """
    Legal Case / Situation Model representing a citizen's inquiry,
    analyzed laws, procedural recommendations, and associated evidence.
    """
    __tablename__ = "legal_cases"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    raw_description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(50), default="NEW", nullable=False)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Serialized JSON representations of analysis
    applicable_laws_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    citizen_rights_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    missing_info_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    uncertainty_notes_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="cases")
    evidence_documents: Mapped[List["EvidenceDocument"]] = relationship(
        "EvidenceDocument", back_populates="case", cascade="all, delete-orphan"
    )
    timeline_events: Mapped[List["TimelineEvent"]] = relationship(
        "TimelineEvent", back_populates="case", cascade="all, delete-orphan"
    )
    drafts: Mapped[List["LegalDraft"]] = relationship(
        "LegalDraft", back_populates="case", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<LegalCase(id={self.id}, title='{self.title[:30]}', category='{self.category}')>"

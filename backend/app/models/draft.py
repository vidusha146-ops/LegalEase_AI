from typing import Optional
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class LegalDraft(Base, TimestampMixin):
    """
    Generated legal drafts: Police Complaint (FIR), Consumer Forum Grievance,
    RTI Application Form A, or Legal Notice for Dues/Breach.
    """
    __tablename__ = "legal_drafts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("legal_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    draft_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    pdf_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    docx_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    draft_metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    disclaimer_accepted: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Relationships
    case: Mapped["LegalCase"] = relationship("LegalCase", back_populates="drafts")

    def __repr__(self) -> str:
        return f"<LegalDraft(id={self.id}, type='{self.draft_type}', title='{self.title[:30]}')>"

from typing import List, Optional
from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class EvidenceDocument(Base, TimestampMixin):
    """
    Evidence and supporting document vault.
    Stores metadata, file paths, OCR extractions, and extracted entities.
    """
    __tablename__ = "evidence_documents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("legal_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    
    ocr_extracted_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extracted_entities_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    contradiction_warnings_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    case: Mapped["LegalCase"] = relationship("LegalCase", back_populates="evidence_documents")
    timeline_events: Mapped[List["TimelineEvent"]] = relationship(
        "TimelineEvent", back_populates="evidence_document"
    )

    def __repr__(self) -> str:
        return f"<EvidenceDocument(id={self.id}, filename='{self.filename}', is_processed={self.is_processed})>"

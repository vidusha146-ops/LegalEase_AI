"""
LegalEase AI - Case Similarity Search Query Model (Phase 7 Module 1)
Stores citizen search queries, retrieved judgment references, and evaluation metrics.
"""

from typing import Optional
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class CaseSimilarityQuery(Base, TimestampMixin):
    """
    Stores historical case similarity queries linked to citizen users.
    Enforces tenant isolation by foreign key user_id.
    """
    __tablename__ = "case_similarity_queries"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    case_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("legal_cases.id", ondelete="SET NULL"), nullable=True, index=True
    )
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    legal_domain: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    retrieved_judgment_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    search_metrics_json: Mapped[str] = mapped_column(Text, default="{}")

    # Relationships
    user: Mapped["User"] = relationship("User")
    case: Mapped[Optional["LegalCase"]] = relationship("LegalCase")

    def __repr__(self) -> str:
        return f"<CaseSimilarityQuery(id={self.id}, user_id={self.user_id}, domain='{self.legal_domain}')>"

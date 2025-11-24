"""
Request model for SQLAlchemy ORM.
"""
from sqlalchemy import String, Integer, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.source import Source
    from app.models.operator import Operator


class Request(Base):
    """
    Request model representing a user request that needs operator assignment.
    
    Attributes:
        id: Primary key
        user_id: Foreign key to users table
        source_id: Foreign key to sources table
        operator_id: Foreign key to operators table (nullable for unassigned)
        message: Request message content (non-empty string)
        status: Request status (pending, assigned, waiting, etc.)
        created_at: Timestamp of request creation
    """
    __tablename__ = "requests"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    source_id: Mapped[int] = mapped_column(Integer, ForeignKey("sources.id", ondelete="RESTRICT"), nullable=False, index=True)
    operator_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("operators.id", ondelete="RESTRICT"), nullable=True, index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="requests"
    )
    source: Mapped["Source"] = relationship(
        "Source",
        back_populates="requests",
        passive_deletes=True
    )
    operator: Mapped[Optional["Operator"]] = relationship(
        "Operator",
        back_populates="requests",
        foreign_keys=[operator_id],
        passive_deletes=True
    )
    
    def __repr__(self) -> str:
        return f"<Request(id={self.id}, user_id={self.user_id}, source_id={self.source_id}, operator_id={self.operator_id}, status='{self.status}')>"

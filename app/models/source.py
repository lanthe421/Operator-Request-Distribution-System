"""
Source model for SQLAlchemy ORM.
"""
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import List, TYPE_CHECKING

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.operator_source_weight import OperatorSourceWeight
    from app.models.request import Request


class Source(Base):
    """
    Source model representing a communication channel (bot, email, phone).
    
    Attributes:
        id: Primary key
        name: Source name (non-empty string)
        identifier: Unique source identifier (non-empty string)
        created_at: Timestamp of source creation
    """
    __tablename__ = "sources"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    identifier: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    
    # Relationships
    weights: Mapped[List["OperatorSourceWeight"]] = relationship(
        "OperatorSourceWeight",
        back_populates="source",
        cascade="all, delete-orphan"
    )
    requests: Mapped[List["Request"]] = relationship(
        "Request",
        back_populates="source",
        passive_deletes='all'
    )
    
    def __repr__(self) -> str:
        return f"<Source(id={self.id}, name='{self.name}', identifier='{self.identifier}')>"

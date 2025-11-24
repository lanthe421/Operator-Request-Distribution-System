"""
Operator model for SQLAlchemy ORM.
"""
from sqlalchemy import String, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import List, TYPE_CHECKING

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.operator_source_weight import OperatorSourceWeight
    from app.models.request import Request


class Operator(Base):
    """
    Operator model representing a CRM operator who handles user requests.
    
    Attributes:
        id: Primary key
        name: Operator's name (non-empty string)
        is_active: Whether operator is available for new assignments
        max_load_limit: Maximum number of concurrent requests
        current_load: Current number of assigned requests
        created_at: Timestamp of operator creation
    """
    __tablename__ = "operators"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    max_load_limit: Mapped[int] = mapped_column(Integer, nullable=False)
    current_load: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    
    # Relationships
    weights: Mapped[List["OperatorSourceWeight"]] = relationship(
        "OperatorSourceWeight",
        back_populates="operator",
        cascade="all, delete-orphan"
    )
    requests: Mapped[List["Request"]] = relationship(
        "Request",
        back_populates="operator",
        foreign_keys="Request.operator_id",
        passive_deletes='all'
    )
    
    def __repr__(self) -> str:
        return f"<Operator(id={self.id}, name='{self.name}', active={self.is_active}, load={self.current_load}/{self.max_load_limit})>"

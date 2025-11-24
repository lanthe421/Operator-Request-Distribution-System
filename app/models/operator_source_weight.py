"""
OperatorSourceWeight model for SQLAlchemy ORM.
"""
from sqlalchemy import Integer, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import TYPE_CHECKING

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.operator import Operator
    from app.models.source import Source


class OperatorSourceWeight(Base):
    """
    OperatorSourceWeight model representing weight configuration for operator-source pairs.
    
    Attributes:
        id: Primary key
        operator_id: Foreign key to operators table
        source_id: Foreign key to sources table
        weight: Weight value (1-100) for distribution probability
        created_at: Timestamp of weight configuration creation
    """
    __tablename__ = "operator_source_weights"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    operator_id: Mapped[int] = mapped_column(Integer, ForeignKey("operators.id"), nullable=False)
    source_id: Mapped[int] = mapped_column(Integer, ForeignKey("sources.id"), nullable=False, index=True)
    weight: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    
    # Relationships
    operator: Mapped["Operator"] = relationship(
        "Operator",
        back_populates="weights"
    )
    source: Mapped["Source"] = relationship(
        "Source",
        back_populates="weights"
    )
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('operator_id', 'source_id', name='uq_operator_source'),
        CheckConstraint('weight >= 1 AND weight <= 100', name='ck_weight_range'),
    )
    
    def __repr__(self) -> str:
        return f"<OperatorSourceWeight(operator_id={self.operator_id}, source_id={self.source_id}, weight={self.weight})>"

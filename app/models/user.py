"""
User model for SQLAlchemy ORM.
"""
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import List, TYPE_CHECKING

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.request import Request


class User(Base):
    """
    User model representing a user who submits requests.
    
    Attributes:
        id: Primary key
        identifier: Unique user identifier (email, phone, etc.)
        created_at: Timestamp of user creation
    """
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    identifier: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    
    # Relationships
    requests: Mapped[List["Request"]] = relationship(
        "Request",
        back_populates="user"
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, identifier='{self.identifier}')>"

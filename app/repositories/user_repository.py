"""
User repository for data access operations.
"""
from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User


class UserRepository:
    """Repository for User data access operations."""
    
    def __init__(self, session: Session):
        """
        Initialize repository with database session.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
    
    def get_by_identifier(self, identifier: str) -> Optional[User]:
        """
        Retrieve user by identifier.
        
        Args:
            identifier: User identifier (email, phone, etc.)
            
        Returns:
            User instance or None if not found
        """
        return self.session.query(User).filter(User.identifier == identifier).first()
    
    def create(self, identifier: str) -> User:
        """
        Create a new user.
        
        Args:
            identifier: User identifier
            
        Returns:
            Created user instance
        """
        user = User(identifier=identifier)
        self.session.add(user)
        self.session.flush()
        return user

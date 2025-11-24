"""
Source repository for data access operations.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.source import Source


class SourceRepository:
    """Repository for Source CRUD operations."""
    
    def __init__(self, session: Session):
        """
        Initialize repository with database session.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
    
    def create(self, name: str, identifier: str) -> Source:
        """
        Create a new source.
        
        Args:
            name: Source name
            identifier: Unique source identifier
            
        Returns:
            Created source instance
        """
        source = Source(name=name, identifier=identifier)
        self.session.add(source)
        self.session.flush()
        return source
    
    def get_all(self) -> List[Source]:
        """
        Retrieve all sources.
        
        Returns:
            List of all sources
        """
        return self.session.query(Source).all()
    
    def get_by_id(self, source_id: int) -> Optional[Source]:
        """
        Retrieve source by ID.
        
        Args:
            source_id: Source ID
            
        Returns:
            Source instance or None if not found
        """
        return self.session.query(Source).filter(Source.id == source_id).first()
    
    def get_by_identifier(self, identifier: str) -> Optional[Source]:
        """
        Retrieve source by identifier.
        
        Args:
            identifier: Source identifier
            
        Returns:
            Source instance or None if not found
        """
        return self.session.query(Source).filter(Source.identifier == identifier).first()

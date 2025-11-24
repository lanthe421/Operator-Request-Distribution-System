"""
Source service for business logic operations.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.source import Source
from app.models.operator_source_weight import OperatorSourceWeight
from app.repositories.source_repository import SourceRepository
from app.repositories.operator_repository import OperatorRepository


class SourceService:
    """Service for handling source business logic."""
    
    def __init__(self, session: Session):
        """
        Initialize source service with database session.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
        self.source_repository = SourceRepository(session)
        self.operator_repository = OperatorRepository(session)
    
    def create_source(self, name: str, identifier: str) -> Source:
        """
        Create a new source.
        
        Args:
            name: Source name (non-empty string)
            identifier: Unique source identifier (non-empty string)
            
        Returns:
            Created source instance
            
        Raises:
            ValueError: If name or identifier is empty/whitespace-only or identifier already exists
        """
        # Validate name is not empty or whitespace
        if not name or not name.strip():
            raise ValueError("Name must not be empty or whitespace-only")
        
        # Validate identifier is not empty or whitespace
        if not identifier or not identifier.strip():
            raise ValueError("Identifier must not be empty or whitespace-only")
        
        # Check if identifier already exists
        existing_source = self.source_repository.get_by_identifier(identifier)
        if existing_source:
            raise ValueError(f"Source with identifier '{identifier}' already exists")
        
        # Create source through repository
        try:
            source = self.source_repository.create(name=name, identifier=identifier)
            self.session.commit()
            return source
        except IntegrityError:
            self.session.rollback()
            raise ValueError(f"Source with identifier '{identifier}' already exists")
    
    def get_sources(self) -> List[Source]:
        """
        Retrieve all sources.
        
        Returns:
            List of all registered sources
        """
        return self.source_repository.get_all()
    
    def configure_weights(
        self, 
        source_id: int, 
        operator_weights: List[tuple[int, int]]
    ) -> None:
        """
        Configure operator weights for a specific source.
        
        Args:
            source_id: Source ID to configure weights for
            operator_weights: List of (operator_id, weight) tuples
            
        Raises:
            ValueError: If source not found, operator not found, or weight out of range
        """
        # Validate source exists
        source = self.source_repository.get_by_id(source_id)
        if not source:
            raise ValueError(f"Source with id {source_id} not found")
        
        # Process each operator weight configuration
        for operator_id, weight in operator_weights:
            # Validate weight range
            if weight < 1 or weight > 100:
                raise ValueError(f"Weight must be between 1 and 100, got {weight}")
            
            # Validate operator exists
            operator = self.operator_repository.get_by_id(operator_id)
            if not operator:
                raise ValueError(f"Operator with id {operator_id} not found")
            
            # Check if weight configuration already exists
            existing_weight = (
                self.session.query(OperatorSourceWeight)
                .filter(
                    OperatorSourceWeight.operator_id == operator_id,
                    OperatorSourceWeight.source_id == source_id
                )
                .first()
            )
            
            if existing_weight:
                # Update existing weight
                existing_weight.weight = weight
            else:
                # Create new weight configuration
                new_weight = OperatorSourceWeight(
                    operator_id=operator_id,
                    source_id=source_id,
                    weight=weight
                )
                self.session.add(new_weight)
        
        # Commit all changes
        try:
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise ValueError(f"Failed to configure weights: {str(e)}")
    
    def get_operator_weights(self, source_id: int) -> List[tuple[int, str, int]]:
        """
        Retrieve all operator weights for a specific source.
        
        Args:
            source_id: Source ID to retrieve weights for
            
        Returns:
            List of (operator_id, operator_name, weight) tuples
            
        Raises:
            ValueError: If source not found
        """
        # Validate source exists
        source = self.source_repository.get_by_id(source_id)
        if not source:
            raise ValueError(f"Source with id {source_id} not found")
        
        # Query operator weights with operator information
        weights = (
            self.session.query(
                OperatorSourceWeight.operator_id,
                OperatorSourceWeight.weight
            )
            .filter(OperatorSourceWeight.source_id == source_id)
            .all()
        )
        
        # Fetch operator names
        result = []
        for operator_id, weight in weights:
            operator = self.operator_repository.get_by_id(operator_id)
            if operator:
                result.append((operator_id, operator.name, weight))
        
        return result

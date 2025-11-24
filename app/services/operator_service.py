"""
Operator service for business logic operations.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.operator import Operator
from app.repositories.operator_repository import OperatorRepository


class OperatorService:
    """Service for handling operator business logic."""
    
    def __init__(self, session: Session):
        """
        Initialize operator service with database session.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
        self.repository = OperatorRepository(session)
    
    def create_operator(self, name: str, max_load_limit: int) -> Operator:
        """
        Create a new operator.
        
        Args:
            name: Operator name (non-empty string)
            max_load_limit: Maximum load capacity
            
        Returns:
            Created operator instance
            
        Raises:
            ValueError: If name is empty or whitespace-only
        """
        # Validate name is not empty or whitespace
        if not name or not name.strip():
            raise ValueError("Name must not be empty or whitespace-only")
        
        # Create operator through repository
        operator = self.repository.create(name=name, max_load_limit=max_load_limit)
        return operator
    
    def get_operators(self) -> List[Operator]:
        """
        Retrieve all operators.
        
        Returns:
            List of all operators with their current status and load information
        """
        return self.repository.get_all()
    
    def update_operator(self, operator_id: int, max_load_limit: int) -> Operator:
        """
        Update an operator's max_load_limit.
        
        Args:
            operator_id: Operator ID to update
            max_load_limit: New maximum load capacity
            
        Returns:
            Updated operator instance
            
        Raises:
            ValueError: If operator not found
        """
        # Get operator by ID
        operator = self.repository.get_by_id(operator_id)
        if not operator:
            raise ValueError(f"Operator with id {operator_id} not found")
        
        # Update max_load_limit
        operator.max_load_limit = max_load_limit
        
        # Save changes through repository
        return self.repository.update(operator)
    
    def toggle_active(self, operator_id: int) -> Operator:
        """
        Toggle an operator's active status.
        
        Changes is_active flag from True to False or False to True.
        When an operator is deactivated, they will not receive new request assignments.
        
        Args:
            operator_id: Operator ID to toggle
            
        Returns:
            Updated operator instance with toggled status
            
        Raises:
            ValueError: If operator not found
        """
        # Get operator by ID
        operator = self.repository.get_by_id(operator_id)
        if not operator:
            raise ValueError(f"Operator with id {operator_id} not found")
        
        # Toggle is_active flag
        operator.is_active = not operator.is_active
        
        # Save changes through repository
        return self.repository.update(operator)

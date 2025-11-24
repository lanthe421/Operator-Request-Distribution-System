"""
Operator repository for data access operations.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.operator import Operator


class OperatorRepository:
    """Repository for Operator CRUD operations and load management."""
    
    def __init__(self, session: Session):
        """
        Initialize repository with database session.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
    
    def create(self, name: str, max_load_limit: int) -> Operator:
        """
        Create a new operator.
        
        Args:
            name: Operator name
            max_load_limit: Maximum load capacity
            
        Returns:
            Created operator instance
        """
        operator = Operator(
            name=name,
            max_load_limit=max_load_limit,
            is_active=True,
            current_load=0
        )
        self.session.add(operator)
        self.session.flush()
        return operator
    
    def get_all(self) -> List[Operator]:
        """
        Retrieve all operators.
        
        Returns:
            List of all operators
        """
        return self.session.query(Operator).all()
    
    def get_by_id(self, operator_id: int) -> Optional[Operator]:
        """
        Retrieve operator by ID.
        
        Args:
            operator_id: Operator ID
            
        Returns:
            Operator instance or None if not found
        """
        return self.session.query(Operator).filter(Operator.id == operator_id).first()
    
    def update(self, operator: Operator) -> Operator:
        """
        Update an existing operator.
        
        Args:
            operator: Operator instance with updated values
            
        Returns:
            Updated operator instance
        """
        self.session.flush()
        return operator
    
    def increment_load(self, operator_id: int) -> None:
        """
        Increment operator's current load by 1.
        
        Args:
            operator_id: Operator ID
        """
        operator = self.get_by_id(operator_id)
        if operator:
            operator.current_load += 1
            self.session.flush()
    
    def decrement_load(self, operator_id: int) -> None:
        """
        Decrement operator's current load by 1.
        
        Args:
            operator_id: Operator ID
        """
        operator = self.get_by_id(operator_id)
        if operator:
            operator.current_load = max(0, operator.current_load - 1)
            self.session.flush()

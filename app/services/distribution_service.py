"""
Distribution service for operator assignment logic.
"""
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from app.models.operator import Operator
from app.models.operator_source_weight import OperatorSourceWeight
from app.models.request import Request
from app.utils.weighted_random import select_operator_by_weight


class DistributionService:
    """Service for handling request distribution to operators."""
    
    def __init__(self, session: Session):
        """
        Initialize distribution service with database session.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
    
    def get_available_operators(self, source_id: int) -> List[Tuple[Operator, int]]:
        """
        Get all available operators for a specific source.
        
        An operator is available if:
        - is_active equals True
        - current_load < max_load_limit
        - has a configured weight for the source
        
        Args:
            source_id: Source ID to get operators for
            
        Returns:
            List of (operator, weight) tuples for available operators
        """
        # Query operators with their weights for the given source
        # Filter by active status and load capacity
        available = (
            self.session.query(Operator, OperatorSourceWeight.weight)
            .join(OperatorSourceWeight, Operator.id == OperatorSourceWeight.operator_id)
            .filter(
                OperatorSourceWeight.source_id == source_id,
                Operator.is_active == True,
                Operator.current_load < Operator.max_load_limit
            )
            .all()
        )
        
        return available
    
    def assign_operator(self, request_id: int, operator_id: int) -> None:
        """
        Assign an operator to a request and increment operator's load.
        
        This operation is atomic within the session transaction.
        
        Args:
            request_id: Request ID to assign
            operator_id: Operator ID to assign to the request
        """
        # Get the request
        request = self.session.query(Request).filter(Request.id == request_id).first()
        if not request:
            raise ValueError(f"Request with id {request_id} not found")
        
        # Get the operator
        operator = self.session.query(Operator).filter(Operator.id == operator_id).first()
        if not operator:
            raise ValueError(f"Operator with id {operator_id} not found")
        
        # Assign operator to request
        request.operator_id = operator_id
        request.status = "assigned"
        
        # Increment operator's current load
        operator.current_load += 1
        
        # Flush changes to database
        self.session.flush()
    
    def handle_no_operators_available(self, request_id: int) -> None:
        """
        Handle the case when no operators are available for a request.
        
        Sets the request status to 'waiting' and leaves operator_id as NULL.
        
        Args:
            request_id: Request ID to mark as waiting
        """
        # Get the request
        request = self.session.query(Request).filter(Request.id == request_id).first()
        if not request:
            raise ValueError(f"Request with id {request_id} not found")
        
        # Set status to waiting with no operator assigned
        request.operator_id = None
        request.status = "waiting"
        
        # Flush changes to database
        self.session.flush()
    
    def distribute_request(self, request_id: int, source_id: int) -> Optional[int]:
        """
        Distribute a request to an available operator using weighted random selection.
        
        This is the main distribution method that orchestrates the entire process:
        1. Get available operators for the source
        2. If operators available, select one by weight and assign
        3. If no operators available, mark request as waiting
        
        Args:
            request_id: Request ID to distribute
            source_id: Source ID of the request
            
        Returns:
            Assigned operator ID or None if no operators available
        """
        # Get available operators with their weights
        available_operators = self.get_available_operators(source_id)
        
        if available_operators:
            # Select operator using weighted random selection
            selected_operator = select_operator_by_weight(available_operators)
            
            if selected_operator:
                # Assign the operator to the request
                self.assign_operator(request_id, selected_operator.id)
                return selected_operator.id
        
        # No operators available - mark as waiting
        self.handle_no_operators_available(request_id)
        return None

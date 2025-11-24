"""
Request repository for data access operations.
"""
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from app.models.request import Request


class RequestRepository:
    """Repository for Request CRUD and query operations."""
    
    def __init__(self, session: Session):
        """
        Initialize repository with database session.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
    
    def create(
        self,
        user_id: int,
        source_id: int,
        message: str,
        operator_id: Optional[int] = None,
        status: str = "pending"
    ) -> Request:
        """
        Create a new request.
        
        Args:
            user_id: User ID
            source_id: Source ID
            message: Request message
            operator_id: Operator ID (optional)
            status: Request status
            
        Returns:
            Created request instance
        """
        request = Request(
            user_id=user_id,
            source_id=source_id,
            operator_id=operator_id,
            message=message,
            status=status
        )
        self.session.add(request)
        self.session.flush()
        return request
    
    def get_all(self) -> List[Request]:
        """
        Retrieve all requests.
        
        Returns:
            List of all requests
        """
        return self.session.query(Request).all()
    
    def get_by_id(self, request_id: int) -> Optional[Request]:
        """
        Retrieve request by ID with relationships loaded.
        
        Args:
            request_id: Request ID
            
        Returns:
            Request instance with user, source, and operator loaded, or None if not found
        """
        return (
            self.session.query(Request)
            .options(
                joinedload(Request.user),
                joinedload(Request.source),
                joinedload(Request.operator)
            )
            .filter(Request.id == request_id)
            .first()
        )
    
    def update(self, request: Request) -> Request:
        """
        Update an existing request.
        
        Args:
            request: Request instance with updated values
            
        Returns:
            Updated request instance
        """
        self.session.flush()
        return request
    
    def get_by_operator(self, operator_id: int) -> List[Request]:
        """
        Retrieve all requests assigned to a specific operator.
        
        Args:
            operator_id: Operator ID
            
        Returns:
            List of requests assigned to the operator
        """
        return self.session.query(Request).filter(Request.operator_id == operator_id).all()
    
    def get_by_source(self, source_id: int) -> List[Request]:
        """
        Retrieve all requests from a specific source.
        
        Args:
            source_id: Source ID
            
        Returns:
            List of requests from the source
        """
        return self.session.query(Request).filter(Request.source_id == source_id).all()
    
    def get_unassigned(self) -> List[Request]:
        """
        Retrieve all unassigned requests (operator_id is NULL).
        
        Returns:
            List of unassigned requests
        """
        return self.session.query(Request).filter(Request.operator_id.is_(None)).all()

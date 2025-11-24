"""
Request service for handling request creation and retrieval.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.request import Request
from app.models.source import Source
from app.repositories.user_repository import UserRepository
from app.repositories.request_repository import RequestRepository
from app.services.distribution_service import DistributionService


class RequestService:
    """Service for handling request operations."""
    
    def __init__(self, session: Session):
        """
        Initialize request service with database session.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
        self.user_repository = UserRepository(session)
        self.request_repository = RequestRepository(session)
        self.distribution_service = DistributionService(session)
    
    def create_request(
        self,
        user_identifier: str,
        source_id: int,
        message: str
    ) -> Request:
        """
        Create a new request with automatic user creation and operator assignment.
        
        This method:
        1. Validates that source exists
        2. Checks if user exists, creates if not
        3. Creates the request
        4. Attempts to assign an operator using distribution service
        5. Records timestamp automatically
        
        Args:
            user_identifier: User identifier (email, phone, etc.)
            source_id: Source ID
            message: Request message
            
        Returns:
            Created request instance with operator assigned (if available)
            
        Raises:
            ValueError: If source does not exist
        """
        # Validate that source exists
        source = self.session.query(Source).filter(Source.id == source_id).first()
        if not source:
            raise ValueError(f"Source with id {source_id} not found")
        
        # Get or create user
        user = self.user_repository.get_by_identifier(user_identifier)
        if not user:
            user = self.user_repository.create(user_identifier)
        
        # Create request with pending status
        request = self.request_repository.create(
            user_id=user.id,
            source_id=source_id,
            message=message,
            status="pending"
        )
        
        # Attempt to distribute the request to an operator
        self.distribution_service.distribute_request(request.id, source_id)
        
        # Refresh to get updated status and operator_id
        self.session.refresh(request)
        
        return request
    
    def get_requests(self) -> List[Request]:
        """
        Retrieve all requests.
        
        Returns:
            List of all requests with their current status and assignment information
        """
        return self.request_repository.get_all()
    
    def get_request_by_id(self, request_id: int) -> Optional[Request]:
        """
        Retrieve a specific request by ID with all relationships loaded.
        
        This method loads the request with:
        - User information
        - Source information
        - Operator information (if assigned)
        - Creation timestamp
        
        Args:
            request_id: Request ID
            
        Returns:
            Request instance with relationships loaded, or None if not found
        """
        return self.request_repository.get_by_id(request_id)

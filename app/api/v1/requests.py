"""
API endpoints for request management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.request import (
    RequestCreate,
    RequestResponse,
    RequestDetailResponse
)
from app.services.request_service import RequestService


router = APIRouter(prefix="/requests", tags=["requests"])


@router.post(
    "/",
    response_model=RequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new request",
    description="Create a new request with automatic user creation and operator assignment. "
                "If the user_identifier doesn't exist, a new user will be created. "
                "The system will attempt to assign an available operator based on configured weights."
)
def create_request(
    request_data: RequestCreate,
    db: Session = Depends(get_db)
) -> RequestResponse:
    """
    Create a new request with distribution.
    
    Args:
        request_data: Request creation data (user_identifier, source_id, message)
        db: Database session dependency
        
    Returns:
        Created request with operator assignment (if available)
        
    Raises:
        HTTPException 400: If validation fails (empty message, invalid source_id)
        HTTPException 404: If source not found
    """
    try:
        service = RequestService(db)
        request = service.create_request(
            user_identifier=request_data.user_identifier,
            source_id=request_data.source_id,
            message=request_data.message
        )
        db.commit()
        db.refresh(request)
        return RequestResponse.model_validate(request)
    except ValueError as e:
        db.rollback()
        # Check if it's a "not found" error
        if "not found" in str(e).lower() or "does not exist" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create request: {str(e)}"
        )


@router.get(
    "/",
    response_model=List[RequestResponse],
    summary="List all requests",
    description="Retrieve all requests with their current status and assignment information."
)
def list_requests(
    db: Session = Depends(get_db)
) -> List[RequestResponse]:
    """
    Get all requests.
    
    Args:
        db: Database session dependency
        
    Returns:
        List of all requests with complete information
    """
    try:
        service = RequestService(db)
        requests = service.get_requests()
        return [RequestResponse.model_validate(req) for req in requests]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve requests: {str(e)}"
        )


@router.get(
    "/{request_id}",
    response_model=RequestDetailResponse,
    summary="Get request details",
    description="Retrieve detailed information about a specific request including "
                "user, source, and operator information."
)
def get_request_details(
    request_id: int,
    db: Session = Depends(get_db)
) -> RequestDetailResponse:
    """
    Get detailed request information.
    
    Args:
        request_id: ID of the request to retrieve
        db: Database session dependency
        
    Returns:
        Request with user, source, and operator details
        
    Raises:
        HTTPException 404: If request not found
    """
    try:
        service = RequestService(db)
        request = service.get_request_by_id(request_id)
        
        if not request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Request with id {request_id} not found"
            )
        
        # Build detailed response with relationships
        return RequestDetailResponse(
            id=request.id,
            user_id=request.user_id,
            user_identifier=request.user.identifier,
            source_id=request.source_id,
            source_name=request.source.name,
            operator_id=request.operator_id,
            operator_name=request.operator.name if request.operator else None,
            message=request.message,
            status=request.status,
            created_at=request.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve request details: {str(e)}"
        )

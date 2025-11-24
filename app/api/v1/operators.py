"""
API endpoints for operator management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.operator import (
    OperatorCreate,
    OperatorUpdate,
    OperatorResponse,
    OperatorToggleResponse
)
from app.services.operator_service import OperatorService


router = APIRouter(prefix="/operators", tags=["operators"])


@router.post(
    "/",
    response_model=OperatorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new operator",
    description="Create a new operator with name and max_load_limit. "
                "Operator is created with is_active=True and current_load=0."
)
def create_operator(
    operator_data: OperatorCreate,
    db: Session = Depends(get_db)
) -> OperatorResponse:
    """
    Create a new operator.
    
    Args:
        operator_data: Operator creation data (name, max_load_limit)
        db: Database session dependency
        
    Returns:
        Created operator with all fields
        
    Raises:
        HTTPException 400: If validation fails (empty name, invalid max_load_limit)
    """
    try:
        service = OperatorService(db)
        operator = service.create_operator(
            name=operator_data.name,
            max_load_limit=operator_data.max_load_limit
        )
        db.commit()
        db.refresh(operator)
        return OperatorResponse.model_validate(operator)
    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create operator: {str(e)}"
        )


@router.get(
    "/",
    response_model=List[OperatorResponse],
    summary="List all operators",
    description="Retrieve all operators with their current status and load information."
)
def list_operators(
    db: Session = Depends(get_db)
) -> List[OperatorResponse]:
    """
    Get all operators.
    
    Args:
        db: Database session dependency
        
    Returns:
        List of all operators with complete information
    """
    try:
        service = OperatorService(db)
        operators = service.get_operators()
        return [OperatorResponse.model_validate(op) for op in operators]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve operators: {str(e)}"
        )


@router.put(
    "/{operator_id}",
    response_model=OperatorResponse,
    summary="Update operator",
    description="Update an operator's max_load_limit."
)
def update_operator(
    operator_id: int,
    operator_data: OperatorUpdate,
    db: Session = Depends(get_db)
) -> OperatorResponse:
    """
    Update an operator's max_load_limit.
    
    Args:
        operator_id: ID of the operator to update
        operator_data: Update data (max_load_limit)
        db: Database session dependency
        
    Returns:
        Updated operator with all fields
        
    Raises:
        HTTPException 404: If operator not found
        HTTPException 400: If validation fails
    """
    try:
        service = OperatorService(db)
        operator = service.update_operator(
            operator_id=operator_id,
            max_load_limit=operator_data.max_load_limit
        )
        db.commit()
        db.refresh(operator)
        return OperatorResponse.model_validate(operator)
    except ValueError as e:
        db.rollback()
        # Check if it's a "not found" error
        if "not found" in str(e).lower():
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
            detail=f"Failed to update operator: {str(e)}"
        )


@router.put(
    "/{operator_id}/toggle-active",
    response_model=OperatorToggleResponse,
    summary="Toggle operator active status",
    description="Toggle an operator's active status. "
                "When deactivated, the operator will not receive new request assignments."
)
def toggle_operator_active(
    operator_id: int,
    db: Session = Depends(get_db)
) -> OperatorToggleResponse:
    """
    Toggle an operator's active status.
    
    Args:
        operator_id: ID of the operator to toggle
        db: Database session dependency
        
    Returns:
        Operator with updated active status
        
    Raises:
        HTTPException 404: If operator not found
    """
    try:
        service = OperatorService(db)
        operator = service.toggle_active(operator_id=operator_id)
        db.commit()
        db.refresh(operator)
        return OperatorToggleResponse.model_validate(operator)
    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to toggle operator status: {str(e)}"
        )

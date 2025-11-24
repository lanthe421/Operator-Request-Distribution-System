"""
API endpoints for source management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.source import (
    SourceCreate,
    SourceResponse,
    OperatorWeightConfigList,
    OperatorWeightResponse
)
from app.services.source_service import SourceService


router = APIRouter(prefix="/sources", tags=["sources"])


@router.post(
    "/",
    response_model=SourceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new source",
    description="Create a new source with name and unique identifier. "
                "Sources represent communication channels (bot, email, phone, etc.)."
)
def create_source(
    source_data: SourceCreate,
    db: Session = Depends(get_db)
) -> SourceResponse:
    """
    Create a new source.
    
    Args:
        source_data: Source creation data (name, identifier)
        db: Database session dependency
        
    Returns:
        Created source with all fields
        
    Raises:
        HTTPException 400: If validation fails (empty name/identifier, duplicate identifier)
    """
    try:
        service = SourceService(db)
        source = service.create_source(
            name=source_data.name,
            identifier=source_data.identifier
        )
        db.refresh(source)
        return SourceResponse.model_validate(source)
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
            detail=f"Failed to create source: {str(e)}"
        )


@router.get(
    "/",
    response_model=List[SourceResponse],
    summary="List all sources",
    description="Retrieve all registered sources with their information."
)
def list_sources(
    db: Session = Depends(get_db)
) -> List[SourceResponse]:
    """
    Get all sources.
    
    Args:
        db: Database session dependency
        
    Returns:
        List of all sources with complete information
    """
    try:
        service = SourceService(db)
        sources = service.get_sources()
        return [SourceResponse.model_validate(source) for source in sources]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve sources: {str(e)}"
        )


@router.post(
    "/{source_id}/operators",
    response_model=List[OperatorWeightResponse],
    summary="Configure operator weights for source",
    description="Configure or update operator weights for a specific source. "
                "Weights must be between 1 and 100 and determine the probability "
                "of operator assignment for requests from this source."
)
def configure_operator_weights(
    source_id: int,
    weight_config: OperatorWeightConfigList,
    db: Session = Depends(get_db)
) -> List[OperatorWeightResponse]:
    """
    Configure operator weights for a source.
    
    Args:
        source_id: ID of the source to configure weights for
        weight_config: List of operator weight configurations
        db: Database session dependency
        
    Returns:
        List of all configured operator weights for the source
        
    Raises:
        HTTPException 404: If source or operator not found
        HTTPException 400: If validation fails (weight out of range)
    """
    try:
        service = SourceService(db)
        
        # Convert schema to list of tuples for service
        operator_weights = [
            (config.operator_id, config.weight)
            for config in weight_config.weights
        ]
        
        # Configure weights
        service.configure_weights(
            source_id=source_id,
            operator_weights=operator_weights
        )
        
        # Retrieve and return all configured weights for this source
        weights = service.get_operator_weights(source_id)
        
        return [
            OperatorWeightResponse(
                operator_id=operator_id,
                operator_name=operator_name,
                weight=weight
            )
            for operator_id, operator_name, weight in weights
        ]
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
            detail=f"Failed to configure operator weights: {str(e)}"
        )

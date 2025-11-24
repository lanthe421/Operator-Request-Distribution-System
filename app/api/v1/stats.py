"""
API endpoints for statistics and analytics.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.stats import OperatorLoadStats, DistributionStats
from app.services.stats_service import StatsService


router = APIRouter(prefix="/stats", tags=["statistics"])


@router.get(
    "/operators-load",
    response_model=List[OperatorLoadStats],
    summary="Get operator load statistics",
    description="Retrieve load statistics for all operators including current load, "
                "max load limit, and load percentage. Includes both active and inactive operators."
)
def get_operators_load(
    db: Session = Depends(get_db)
) -> List[OperatorLoadStats]:
    """
    Get operator load statistics.
    
    Returns statistics for all operators including:
    - Current load and max load limit
    - Load percentage calculation
    - Active status
    
    Args:
        db: Database session dependency
        
    Returns:
        List of operator load statistics
        
    Raises:
        HTTPException 500: If statistics retrieval fails
    """
    try:
        service = StatsService(db)
        stats = service.get_operator_load_stats()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve operator load statistics: {str(e)}"
        )


@router.get(
    "/requests-distribution",
    response_model=DistributionStats,
    summary="Get request distribution statistics",
    description="Retrieve request distribution statistics grouped by operator and source. "
                "Includes counts of total requests, unassigned requests, and breakdowns by operator and source."
)
def get_requests_distribution(
    db: Session = Depends(get_db)
) -> DistributionStats:
    """
    Get request distribution statistics.
    
    Returns comprehensive distribution statistics including:
    - Request counts grouped by operator
    - Request counts grouped by source
    - Total request count
    - Unassigned request count
    
    Args:
        db: Database session dependency
        
    Returns:
        Distribution statistics with operator and source breakdowns
        
    Raises:
        HTTPException 500: If statistics retrieval fails
    """
    try:
        service = StatsService(db)
        stats = service.get_request_distribution_stats()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve request distribution statistics: {str(e)}"
        )

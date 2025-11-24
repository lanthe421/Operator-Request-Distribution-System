"""
Statistics service for operator load and request distribution analytics.
"""
from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.operator import Operator
from app.models.request import Request
from app.models.source import Source
from app.schemas.stats import (
    OperatorLoadStats,
    OperatorDistributionStats,
    SourceDistributionStats,
    DistributionStats
)


class StatsService:
    """Service for calculating statistics and analytics."""
    
    def __init__(self, session: Session):
        """
        Initialize service with database session.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
    
    def get_operator_load_stats(self) -> List[OperatorLoadStats]:
        """
        Get load statistics for all operators.
        
        Returns:
            List of operator load statistics with percentage calculation
        """
        operators = self.session.query(Operator).all()
        
        stats = []
        for operator in operators:
            load_percentage = 0.0
            if operator.max_load_limit > 0:
                load_percentage = (operator.current_load / operator.max_load_limit) * 100
            
            stats.append(OperatorLoadStats(
                operator_id=operator.id,
                operator_name=operator.name,
                is_active=operator.is_active,
                current_load=operator.current_load,
                max_load_limit=operator.max_load_limit,
                load_percentage=load_percentage
            ))
        
        return stats
    
    def get_request_distribution_stats(self) -> DistributionStats:
        """
        Get request distribution statistics grouped by operator and source.
        
        Returns:
            Distribution statistics including by operator, by source, and unassigned counts
        """
        # Get distribution by operator
        by_operator = self._get_distribution_by_operator()
        
        # Get distribution by source
        by_source = self._get_distribution_by_source()
        
        # Get total and unassigned counts
        total_requests = self.session.query(func.count(Request.id)).scalar() or 0
        unassigned_requests = (
            self.session.query(func.count(Request.id))
            .filter(Request.operator_id.is_(None))
            .scalar() or 0
        )
        
        return DistributionStats(
            by_operator=by_operator,
            by_source=by_source,
            total_requests=total_requests,
            unassigned_requests=unassigned_requests
        )
    
    def _get_distribution_by_operator(self) -> List[OperatorDistributionStats]:
        """
        Get request distribution grouped by operator.
        
        Returns:
            List of operator distribution statistics
        """
        # Query for assigned requests grouped by operator
        assigned_stats = (
            self.session.query(
                Request.operator_id,
                Operator.name,
                func.count(Request.id).label('request_count')
            )
            .join(Operator, Request.operator_id == Operator.id)
            .group_by(Request.operator_id, Operator.name)
            .all()
        )
        
        # Query for unassigned requests
        unassigned_count = (
            self.session.query(func.count(Request.id))
            .filter(Request.operator_id.is_(None))
            .scalar() or 0
        )
        
        # Build result list
        result = []
        for operator_id, operator_name, request_count in assigned_stats:
            result.append(OperatorDistributionStats(
                operator_id=operator_id,
                operator_name=operator_name,
                request_count=request_count
            ))
        
        # Add unassigned requests if any exist
        if unassigned_count > 0:
            result.append(OperatorDistributionStats(
                operator_id=None,
                operator_name=None,
                request_count=unassigned_count
            ))
        
        return result
    
    def _get_distribution_by_source(self) -> List[SourceDistributionStats]:
        """
        Get request distribution grouped by source.
        
        Returns:
            List of source distribution statistics
        """
        stats = (
            self.session.query(
                Request.source_id,
                Source.name,
                func.count(Request.id).label('request_count')
            )
            .join(Source, Request.source_id == Source.id)
            .group_by(Request.source_id, Source.name)
            .all()
        )
        
        result = []
        for source_id, source_name, request_count in stats:
            result.append(SourceDistributionStats(
                source_id=source_id,
                source_name=source_name,
                request_count=request_count
            ))
        
        return result

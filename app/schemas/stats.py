"""
Pydantic schemas for Statistics API response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional


class OperatorLoadStats(BaseModel):
    """Schema for operator load statistics."""
    operator_id: int
    operator_name: str
    is_active: bool
    current_load: int
    max_load_limit: int
    load_percentage: float = Field(..., description="Load percentage (current_load / max_load_limit * 100)")
    
    class Config:
        from_attributes = True


class OperatorDistributionStats(BaseModel):
    """Schema for request distribution by operator."""
    operator_id: Optional[int]
    operator_name: Optional[str]
    request_count: int
    
    class Config:
        from_attributes = True


class SourceDistributionStats(BaseModel):
    """Schema for request distribution by source."""
    source_id: int
    source_name: str
    request_count: int
    
    class Config:
        from_attributes = True


class DistributionStats(BaseModel):
    """Schema for overall distribution statistics."""
    by_operator: list[OperatorDistributionStats]
    by_source: list[SourceDistributionStats]
    total_requests: int
    unassigned_requests: int
    
    class Config:
        from_attributes = True

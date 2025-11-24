"""
Pydantic schemas for Source API request/response validation.
"""
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import List


class SourceCreate(BaseModel):
    """Schema for creating a new source."""
    name: str = Field(..., min_length=1, description="Source name (non-empty string)")
    identifier: str = Field(..., min_length=1, description="Unique source identifier (non-empty string)")
    
    @field_validator('name', 'identifier')
    @classmethod
    def validate_not_whitespace(cls, v: str) -> str:
        """Validate that field is not empty or whitespace-only."""
        if not v or not v.strip():
            raise ValueError('Field must not be empty or whitespace-only')
        return v


class SourceResponse(BaseModel):
    """Schema for source response."""
    id: int
    name: str
    identifier: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class OperatorWeightConfig(BaseModel):
    """Schema for configuring operator weight for a source."""
    operator_id: int = Field(..., description="Operator ID")
    weight: int = Field(..., ge=1, le=100, description="Weight value between 1 and 100")
    
    @field_validator('weight')
    @classmethod
    def validate_weight_range(cls, v: int) -> int:
        """Validate that weight is within valid range 1-100."""
        if v < 1 or v > 100:
            raise ValueError('Weight must be between 1 and 100')
        return v


class OperatorWeightConfigList(BaseModel):
    """Schema for configuring multiple operator weights for a source."""
    weights: List[OperatorWeightConfig] = Field(..., description="List of operator weight configurations")


class OperatorWeightResponse(BaseModel):
    """Schema for operator weight response."""
    operator_id: int
    operator_name: str
    weight: int
    
    class Config:
        from_attributes = True

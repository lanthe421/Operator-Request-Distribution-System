"""
Pydantic schemas for Operator API request/response validation.
"""
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional


class OperatorCreate(BaseModel):
    """Schema for creating a new operator."""
    name: str = Field(..., min_length=1, description="Operator name (non-empty string)")
    max_load_limit: int = Field(..., gt=0, description="Maximum number of concurrent requests")
    
    @field_validator('name')
    @classmethod
    def validate_name_not_whitespace(cls, v: str) -> str:
        """Validate that name is not empty or whitespace-only."""
        if not v or not v.strip():
            raise ValueError('Name must not be empty or whitespace-only')
        return v


class OperatorUpdate(BaseModel):
    """Schema for updating an operator."""
    max_load_limit: int = Field(..., gt=0, description="Maximum number of concurrent requests")


class OperatorResponse(BaseModel):
    """Schema for operator response."""
    id: int
    name: str
    is_active: bool
    max_load_limit: int
    current_load: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class OperatorToggleResponse(BaseModel):
    """Schema for operator toggle active status response."""
    id: int
    name: str
    is_active: bool
    
    class Config:
        from_attributes = True

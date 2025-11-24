"""
Pydantic schemas for Request API request/response validation.
"""
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional


class RequestCreate(BaseModel):
    """Schema for creating a new request."""
    user_identifier: str = Field(..., min_length=1, description="User identifier (email, phone, etc.)")
    source_id: int = Field(..., description="Source ID")
    message: str = Field(..., min_length=1, description="Request message (non-empty string)")
    
    @field_validator('user_identifier', 'message')
    @classmethod
    def validate_not_whitespace(cls, v: str) -> str:
        """Validate that field is not empty or whitespace-only."""
        if not v or not v.strip():
            raise ValueError('Field must not be empty or whitespace-only')
        return v


class RequestResponse(BaseModel):
    """Schema for request response."""
    id: int
    user_id: int
    source_id: int
    operator_id: Optional[int]
    message: str
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class RequestDetailResponse(BaseModel):
    """Schema for detailed request response with relationships."""
    id: int
    user_id: int
    user_identifier: str
    source_id: int
    source_name: str
    operator_id: Optional[int]
    operator_name: Optional[str]
    message: str
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

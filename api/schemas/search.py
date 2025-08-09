"""
Pydantic schemas for search API
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class SearchBase(BaseModel):
    """Base search schema with common fields"""
    search_term: str = Field(..., min_length=1, max_length=200, description="Search term to track")
    website: str = Field(..., min_length=1, max_length=100, description="Website to search (e.g., 'ebay', 'reverb')")
    is_active: bool = Field(default=True, description="Whether this search should be active")

class SearchCreate(SearchBase):
    """Schema for creating a new search"""
    pass

class SearchUpdate(BaseModel):
    """Schema for updating a search"""
    search_term: Optional[str] = Field(None, min_length=1, max_length=200)
    website: Optional[str] = Field(None, min_length=1, max_length=100)
    is_active: Optional[bool] = None

class SearchResponse(SearchBase):
    """Schema for search response"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SearchListResponse(BaseModel):
    """Schema for list of searches response"""
    searches: list[SearchResponse]
    total: int
    active_count: int 
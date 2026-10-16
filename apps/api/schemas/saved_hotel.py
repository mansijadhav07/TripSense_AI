"""
TripSense AI - Saved Hotel Schemas

Pydantic schemas for bookmarked / saved hotels.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime


class SaveHotelRequest(BaseModel):
    """Request schema for saving a hotel."""
    hotel_id: str = Field(..., description="ID of hotel to save")


class SavedHotelItem(BaseModel):
    """Schema for a saved hotel item."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    hotel_id: str
    saved_at: datetime
    hotel_details: Optional[Dict[str, Any]] = None


class SavedHotelsResponse(BaseModel):
    """Response schema for listing saved hotels."""
    success: bool = True
    data: List[Dict[str, Any]]
    total: int
    message: str = "Saved hotels retrieved"

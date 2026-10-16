"""
TripSense AI - User Preference Schemas

Pydantic schemas for user recommendation preferences request/response validation.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime


class UserPreferenceBase(BaseModel):
    """Base schema for user preferences."""
    destination: Optional[str] = Field(default=None, max_length=200, description="Preferred destination")
    min_rating: Optional[float] = Field(default=3.0, ge=1.0, le=5.0, description="Minimum acceptable rating")
    cleanliness_weight: float = Field(default=1.0, ge=0.0, le=3.0, description="Cleanliness aspect weight")
    location_weight: float = Field(default=1.0, ge=0.0, le=3.0, description="Location aspect weight")
    rooms_weight: float = Field(default=1.0, ge=0.0, le=3.0, description="Rooms aspect weight")
    service_weight: float = Field(default=1.0, ge=0.0, le=3.0, description="Service aspect weight")
    value_weight: float = Field(default=1.0, ge=0.0, le=3.0, description="Value aspect weight")
    sleep_quality_weight: float = Field(default=1.0, ge=0.0, le=3.0, description="Sleep quality weight")
    travel_style: Optional[str] = Field(default="leisure", max_length=50, description="Travel style: leisure, family, business, luxury")


class UserPreferenceUpdate(UserPreferenceBase):
    """Request schema for updating preferences."""
    pass


class UserPreferenceResponse(BaseModel):
    """Response schema for user preferences."""
    model_config = ConfigDict(from_attributes=True)

    success: bool = True
    data: Optional[Dict[str, Any]] = None
    message: str = "User preferences retrieved"

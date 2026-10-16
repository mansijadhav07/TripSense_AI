"""
TripSense AI - Hotel Schemas

Pydantic schemas for hotel search and detail API endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class HotelAspects(BaseModel):
    """Aspect-level ratings for a hotel."""
    cleanliness: Optional[float] = Field(default=None, ge=0, le=5)
    service: Optional[float] = Field(default=None, ge=0, le=5)
    location: Optional[float] = Field(default=None, ge=0, le=5)
    rooms: Optional[float] = Field(default=None, ge=0, le=5)
    value: Optional[float] = Field(default=None, ge=0, le=5)
    sleep_quality: Optional[float] = Field(default=None, ge=0, le=5)


class HotelBase(BaseModel):
    """Base hotel information."""
    hotel_id: str
    name: Optional[str] = None
    location: Optional[str] = None
    avg_rating: Optional[float] = Field(default=None, ge=0, le=5)
    review_count: Optional[int] = Field(default=None, ge=0)
    aspects: Optional[HotelAspects] = None
    sentiment_score: Optional[float] = Field(default=None, ge=-1, le=1)
    is_trending: bool = False


class HotelDetail(HotelBase):
    """Detailed hotel information for the detail page."""
    bayesian_rating: Optional[float] = None
    rating_distribution: Optional[Dict[str, int]] = None
    positive_keywords: Optional[List[str]] = None
    negative_keywords: Optional[List[str]] = None
    review_text_sample: Optional[str] = None
    similar_hotel_ids: Optional[List[str]] = None


class HotelSearchFilters(BaseModel):
    """Filters for hotel search."""
    destination: Optional[str] = Field(default=None, max_length=200)
    min_rating: Optional[float] = Field(default=None, ge=1.0, le=5.0)
    max_rating: Optional[float] = Field(default=None, ge=1.0, le=5.0)
    min_reviews: Optional[int] = Field(default=None, ge=0)
    sort_by: Optional[str] = Field(
        default="rating",
        description="Sort by: rating, reviews, sentiment, name"
    )
    sort_order: Optional[str] = Field(default="desc", description="asc or desc")
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class HotelSearchResponse(BaseModel):
    """Paginated hotel search results."""
    success: bool = True
    data: Dict[str, Any]
    message: str = "Hotels retrieved successfully"


class HotelDetailResponse(BaseModel):
    """Hotel detail response."""
    success: bool = True
    data: Dict[str, Any]
    message: str = "Hotel details retrieved successfully"

"""
TripSense AI - Recommendation Schemas

Pydantic schemas for recommendation API request/response validation.
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Optional, Dict, Any


class AspectWeights(BaseModel):
    """User preferences for hotel aspects."""
    cleanliness: float = Field(default=1.0, ge=0.0, le=3.0, description="Weight for cleanliness (0-3)")
    service: float = Field(default=1.0, ge=0.0, le=3.0, description="Weight for service quality")
    location: float = Field(default=1.0, ge=0.0, le=3.0, description="Weight for location")
    rooms: float = Field(default=1.0, ge=0.0, le=3.0, description="Weight for room quality")
    value: float = Field(default=1.0, ge=0.0, le=3.0, description="Weight for value for money")


class RecommendationFilters(BaseModel):
    """Filters to apply to recommendations."""
    min_rating: Optional[float] = Field(default=None, ge=1.0, le=5.0, description="Minimum average rating")
    max_rating: Optional[float] = Field(default=None, ge=1.0, le=5.0, description="Maximum average rating")
    min_reviews: Optional[int] = Field(default=None, ge=0, description="Minimum review count")
    destination: Optional[str] = Field(default=None, max_length=200, description="Destination/location filter")


class RecommendationRequest(BaseModel):
    """Request schema for generating recommendations."""
    model_config = ConfigDict(protected_namespaces=())

    top_n: int = Field(default=10, ge=1, le=50, description="Number of recommendations to return")
    filters: Optional[RecommendationFilters] = Field(default=None, description="Recommendation filters")
    aspect_weights: Optional[AspectWeights] = Field(default=None, description="Aspect importance weights")
    model_type: Optional[str] = Field(
        default="hybrid",
        description="Model to use: hybrid, popularity, content, collaborative"
    )
    travel_styles: Optional[List[str]] = Field(
        default=None,
        description="Preferred travel styles: family, business, romantic, budget, luxury, adventure"
    )
    dataset_user_id: Optional[str] = Field(
        default=None,
        description="Demo persona: score as an existing dataset user (e.g. user_00012) using their trained factors and history"
    )
    user_context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional context (e.g., travel dates, group size)"
    )

    @field_validator("model_type")
    @classmethod
    def validate_model_type(cls, v):
        allowed = ["hybrid", "popularity", "content", "collaborative", "sentiment"]
        if v and v not in allowed:
            raise ValueError(f"model_type must be one of: {allowed}")
        return v


class RecommendationExplanation(BaseModel):
    """Explanation for why a hotel was recommended."""
    model_config = ConfigDict(protected_namespaces=())

    primary_reason: str = Field(description="Main reason for recommendation")
    contributing_factors: List[str] = Field(description="Contributing factors")
    model_contribution: Optional[Dict[str, float]] = Field(
        default=None,
        description="Score contribution from each model"
    )


class AspectScores(BaseModel):
    """Aspect-level scores for a hotel."""
    cleanliness: Optional[float] = None
    service: Optional[float] = None
    location: Optional[float] = None
    rooms: Optional[float] = None
    value: Optional[float] = None
    sleep_quality: Optional[float] = None


class HotelRecommendation(BaseModel):
    """A single hotel recommendation with metadata."""
    hotel_id: str
    name: Optional[str] = None
    rank: int = Field(description="Rank in recommendation list (1-based)")
    score: float = Field(description="Recommendation score (0-1)")
    avg_rating: Optional[float] = None
    review_count: Optional[int] = None
    location: Optional[str] = None
    aspect_scores: Optional[AspectScores] = None
    sentiment_score: Optional[float] = None
    explanation: Optional[RecommendationExplanation] = None
    is_trending: bool = Field(default=False)
    match_percentage: Optional[int] = Field(
        default=None,
        description="Percentage match with user preferences (0-100)"
    )


class RecommendationResponse(BaseModel):
    """Response schema for recommendation endpoints."""
    success: bool = True
    data: Dict[str, Any]
    message: str = "Recommendations generated successfully"


class ExplanationRequest(BaseModel):
    """Request to explain a specific hotel recommendation."""
    hotel_id: str
    user_preferences: Optional[Dict[str, Any]] = None


class ExplanationResponse(BaseModel):
    """Detailed explanation for a hotel recommendation."""
    hotel_id: str
    hotel_name: Optional[str] = None
    overall_score: float
    aspect_breakdown: Dict[str, float]
    strengths: List[str]
    weaknesses: List[str]
    sentiment_summary: Optional[str] = None
    similar_hotels: Optional[List[str]] = None

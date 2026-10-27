"""TripSense AI - Review / sentiment schemas."""
from typing import Dict, Optional

from pydantic import BaseModel, Field


class SentimentRequest(BaseModel):
    text: str = Field(min_length=3, max_length=5000)


class ReviewCreate(BaseModel):
    hotel_id: str = Field(min_length=1, max_length=255)
    text: str = Field(min_length=3, max_length=5000)
    rating: Optional[int] = Field(default=None, ge=1, le=5)


class SentimentResult(BaseModel):
    label: str
    score: float = Field(description="P(positive) - P(negative), in [-1, 1]")
    confidence: float
    probabilities: Dict[str, float]

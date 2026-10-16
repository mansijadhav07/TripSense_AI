"""
TripSense AI - Recommendations Router

API endpoints for generating and explaining hotel recommendations.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from dependencies.auth import get_current_user, get_optional_user
from models.user import User
from schemas.recommendation import (
    RecommendationRequest,
    RecommendationResponse,
    ExplanationResponse,
)
from services.recommendation_service import RecommendationService

router = APIRouter()

# Module-level service instance (initialized once)
_recommendation_service: Optional[RecommendationService] = None


def get_recommendation_service() -> RecommendationService:
    """Get or create the recommendation service singleton."""
    global _recommendation_service
    if _recommendation_service is None:
        _recommendation_service = RecommendationService()
    return _recommendation_service


@router.post(
    "/generate",
    response_model=RecommendationResponse,
    summary="Generate hotel recommendations",
    description="Generate personalized hotel recommendations based on preferences and filters."
)
async def generate_recommendations(
    request: RecommendationRequest,
    current_user: Optional[User] = Depends(get_optional_user),
    service: RecommendationService = Depends(get_recommendation_service),
):
    """
    Generate top-N hotel recommendations.
    
    - **top_n**: Number of recommendations (1-50, default 10)
    - **model_type**: Algorithm to use (hybrid, popularity, content, collaborative)
    - **filters**: Optional destination, rating, and review count filters
    - **aspect_weights**: Custom weights for hotel aspects (cleanliness, service, etc.)
    """
    try:
        user_id = str(current_user.id) if current_user else None

        # Extract filters
        destination = None
        min_rating = None
        max_rating = None
        if request.filters:
            destination = request.filters.destination
            min_rating = request.filters.min_rating
            max_rating = request.filters.max_rating

        # Extract aspect weights
        aspect_weights = None
        if request.aspect_weights:
            aspect_weights = request.aspect_weights.model_dump()

        # Log the incoming request for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Recommendation request: top_n={request.top_n}, model={request.model_type}, "
                   f"destination={destination}, min_rating={min_rating}, weights={aspect_weights}")

        result = service.generate_recommendations(
            top_n=request.top_n,
            user_id=user_id,
            destination=destination,
            min_rating=min_rating,
            max_rating=max_rating,
            aspect_weights=aspect_weights,
            model_type=request.model_type or "hybrid",
        )

        return RecommendationResponse(
            success=True,
            data=result,
            message=f"Generated {len(result.get('recommendations', []))} recommendations"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Recommendation service error: {str(e)}"
        )


@router.get(
    "/explain/{hotel_id}",
    response_model=ExplanationResponse,
    summary="Explain hotel recommendation",
    description="Get a detailed explanation for why a hotel was recommended."
)
async def explain_recommendation(
    hotel_id: str,
    service: RecommendationService = Depends(get_recommendation_service),
):
    """
    Get detailed explanation for a hotel recommendation.
    
    Returns aspect breakdown, strengths, weaknesses, and similar hotels.
    """
    try:
        explanation = service.explain_hotel(hotel_id)
        if not explanation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Hotel '{hotel_id}' not found"
            )

        return ExplanationResponse(**explanation)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Explanation service error: {str(e)}"
        )


@router.get(
    "/popular",
    response_model=RecommendationResponse,
    summary="Get popular hotels",
    description="Get top hotels by popularity (no authentication required)."
)
async def get_popular_hotels(
    top_n: int = Query(default=10, ge=1, le=50),
    destination: Optional[str] = Query(default=None),
    min_rating: Optional[float] = Query(default=None, ge=1.0, le=5.0),
    service: RecommendationService = Depends(get_recommendation_service),
):
    """
    Get popular hotels by review count and rating.
    
    Does not require authentication. Good for landing page / cold start.
    """
    try:
        result = service.generate_recommendations(
            top_n=top_n,
            destination=destination,
            min_rating=min_rating,
            model_type="popularity",
        )

        return RecommendationResponse(
            success=True,
            data=result,
            message=f"Retrieved {len(result.get('recommendations', []))} popular hotels"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )

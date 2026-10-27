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
from models.preference import UserPreference
from models.review import Review
from models.saved_hotel import SavedHotel
from services.ml_model_loader import ModelUnavailable
from services.recommendation_service import RecommendationService, SAVED_IMPLICIT_RATING

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
    db: Session = Depends(get_db),
):
    """
    Generate top-N hotel recommendations.
    
    - **top_n**: Number of recommendations (1-50, default 10)
    - **model_type**: Algorithm to use (hybrid, popularity, content, collaborative)
    - **filters**: Optional destination, rating, and review count filters
    - **aspect_weights**: Custom weights for hotel aspects (cleanliness, service, etc.)
    """
    try:
        destination = min_rating = max_rating = None
        if request.filters:
            destination = request.filters.destination
            min_rating = request.filters.min_rating
            max_rating = request.filters.max_rating
        aspect_weights = request.aspect_weights.model_dump() if request.aspect_weights else None

        history, exclude = {}, set()
        travel_styles = list(request.travel_styles or [])
        if current_user:
            ratings = {}
            for r in db.query(Review).filter(Review.user_id == current_user.id).all():
                exclude.add(r.hotel_id)
                if r.rating:
                    ratings.setdefault(r.hotel_id, []).append(float(r.rating))
            history = {h: sum(v) / len(v) for h, v in ratings.items()}
            for sv in db.query(SavedHotel).filter(SavedHotel.user_id == current_user.id).all():
                history.setdefault(sv.hotel_id, SAVED_IMPLICIT_RATING)
            pref = db.query(UserPreference).filter(UserPreference.user_id == current_user.id).first()
            if pref and pref.travel_style and not travel_styles:
                travel_styles = [pref.travel_style]

        result = service.generate_recommendations(
            top_n=request.top_n,
            user_id=request.dataset_user_id,
            history=history,
            exclude_ids=exclude,
            destination=destination,
            min_rating=min_rating,
            max_rating=max_rating,
            aspect_weights=aspect_weights,
            travel_styles=travel_styles,
            model_type=request.model_type or "hybrid",
        )
        return RecommendationResponse(
            success=True,
            data=result,
            message=f"Generated {len(result.get('recommendations', []))} recommendations"
        )
    except ModelUnavailable as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Recommendation service error: {str(e)}"
        )


@router.get("/personas", summary="Demo personas (real dataset users)")
async def personas(service: RecommendationService = Depends(get_recommendation_service)):
    try:
        return {"success": True, "data": service.list_personas(), "message": "Dataset users usable as dataset_user_id"}
    except ModelUnavailable as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))


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

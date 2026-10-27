"""
TripSense AI - Reviews & Sentiment Router
Submit a review (scored by the trained sentiment model) or analyse arbitrary text.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from dependencies.auth import get_current_user, get_optional_user
from models.review import Review
from models.user import User
from routers.recommendations import get_recommendation_service
from schemas.review import ReviewCreate, SentimentRequest
from services.hotel_service import get_hotel_store
from services.ml_model_loader import ModelUnavailable
from services.recommendation_service import RecommendationService

router = APIRouter()


def _analyze(service: RecommendationService, text: str):
    try:
        return service.analyze_review(text)
    except ModelUnavailable as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))


@router.post("/analyze", summary="Analyse the sentiment of a piece of text (not stored)")
async def analyze_sentiment(
    payload: SentimentRequest,
    service: RecommendationService = Depends(get_recommendation_service),
):
    return {"success": True, "data": _analyze(service, payload.text), "message": "Sentiment analysed"}


@router.post("", status_code=status.HTTP_201_CREATED, summary="Submit a hotel review")
async def submit_review(
    payload: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    service: RecommendationService = Depends(get_recommendation_service),
):
    """Store the review and return the sentiment model's verdict. Rated reviews also feed
    the user's personalisation history for later recommendations."""
    if not get_hotel_store().get_by_id(payload.hotel_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Hotel '{payload.hotel_id}' not found")
    sentiment = _analyze(service, payload.text)
    review = Review(user_id=current_user.id, hotel_id=payload.hotel_id, rating=payload.rating, text=payload.text,
                    sentiment_label=sentiment["label"], sentiment_score=sentiment["score"])
    db.add(review)
    db.commit()
    db.refresh(review)
    return {"success": True, "data": {"id": review.id, "hotel_id": review.hotel_id, "rating": review.rating,
                                      "text": review.text, "sentiment": sentiment,
                                      "created_at": review.created_at.isoformat() if review.created_at else None},
            "message": "Review submitted"}


@router.get("/hotel/{hotel_id}", summary="Reviews submitted through the app for a hotel")
async def hotel_reviews(hotel_id: str, db: Session = Depends(get_db)):
    rows = db.query(Review).filter(Review.hotel_id == hotel_id).order_by(Review.created_at.desc()).limit(50).all()
    return {"success": True, "data": [
        {"id": r.id, "rating": r.rating, "text": r.text, "sentiment_label": r.sentiment_label,
         "sentiment_score": r.sentiment_score, "created_at": r.created_at.isoformat() if r.created_at else None}
        for r in rows], "message": f"{len(rows)} reviews"}

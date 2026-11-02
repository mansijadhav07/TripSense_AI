"""
TripSense AI - Reviews & Sentiment Router
List and submit hotel reviews, or analyse arbitrary text.
"""
import logging
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from dependencies.auth import get_current_user, get_optional_user
from models.review import Review
from models.user import User
from routers.recommendations import get_recommendation_service
from schemas.review import ReviewCreate, SentimentRequest
from services.hotel_service import get_hotel_store
from services.ml_model_loader import ModelUnavailable, REPO_ROOT
from services.recommendation_service import RecommendationService

router = APIRouter()
logger = logging.getLogger(__name__)


def _catalog_reviews_path() -> Path:
    configured_path = Path(settings.processed_data_path)
    if configured_path.is_absolute():
        return configured_path / "synthetic_reviews.parquet"

    candidates = [
        Path.cwd() / configured_path / "synthetic_reviews.parquet",
        REPO_ROOT / configured_path / "synthetic_reviews.parquet",
    ]
    return next((path for path in candidates if path.is_file()), candidates[0])


@lru_cache(maxsize=1)
def _load_catalog_reviews():
    import pandas as pd

    path = _catalog_reviews_path()
    if not path.is_file():
        logger.error("Catalog review data file is missing: %s", path)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Hotel catalog review data is unavailable.",
        )
    return pd.read_parquet(
        path,
        columns=["review_id", "hotel_id", "overall", "review_text", "post_date", "is_synthetic"],
    )


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


@router.get("/hotel/{hotel_id}", summary="Catalog and TripSense reviews for a hotel")
def hotel_reviews(
    hotel_id: str,
    db: Session = Depends(get_db),
    service: RecommendationService = Depends(get_recommendation_service),
):
    try:
        catalog = _load_catalog_reviews()
        catalog = catalog[catalog["hotel_id"].astype(str) == hotel_id]
        catalog_reviews = []
        if not catalog.empty:
            sentiments = [service.analyze_review(text) for text in catalog["review_text"].astype(str)]
            for (_, row), sentiment in zip(catalog.iterrows(), sentiments):
                created_at = row["post_date"]
                catalog_reviews.append({
                    "id": str(row["review_id"]),
                    "rating": int(row["overall"]),
                    "text": str(row["review_text"]),
                    "sentiment_label": sentiment["label"],
                    "sentiment_score": sentiment["score"],
                    "created_at": created_at.isoformat() if hasattr(created_at, "isoformat") else str(created_at),
                    "source": "catalog",
                    "is_synthetic": bool(row["is_synthetic"]),
                })
    except ModelUnavailable as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    submitted = db.query(Review).filter(Review.hotel_id == hotel_id).order_by(Review.created_at.desc()).limit(50).all()
    submitted_reviews = [{
        "id": review.id,
        "rating": review.rating,
        "text": review.text,
        "sentiment_label": review.sentiment_label,
        "sentiment_score": review.sentiment_score,
        "created_at": review.created_at.isoformat() if review.created_at else None,
        "source": "user",
        "is_synthetic": False,
    } for review in submitted]

    reviews = catalog_reviews + submitted_reviews
    reviews.sort(key=lambda review: review["created_at"] or "", reverse=True)
    return {"success": True, "data": reviews, "message": f"{len(reviews)} reviews"}

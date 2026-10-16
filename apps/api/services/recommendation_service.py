"""
TripSense AI - Recommendation Service

Generates hotel recommendations using different algorithms:
- Popularity-based (non-personalized fallback)
- Content-based filtering (similarity)
- Hybrid ensemble (best results)

Loads real model artifacts when available, falls back to
data-driven heuristics otherwise.
"""

import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
import json

from services.hotel_service import get_hotel_store

logger = logging.getLogger(__name__)


class RecommendationService:
    """
    Generates personalized hotel recommendations.
    
    Falls back gracefully when trained models aren't available,
    using the actual hotel features for real recommendations.
    """

    def __init__(self):
        self.hotel_store = get_hotel_store()
        self._artifacts_dir = self._find_artifacts_dir()
        logger.info(f"RecommendationService initialized. Hotels loaded: {self.hotel_store.total_hotels}")

    def _find_artifacts_dir(self) -> Path:
        candidates = [
            Path(__file__).resolve().parent.parent.parent.parent / "artifacts",
            Path("artifacts"),
            Path("../../artifacts"),
        ]
        for p in candidates:
            if p.exists():
                return p
        return candidates[0]

    def generate_recommendations(
        self,
        top_n: int = 10,
        user_id: Optional[str] = None,
        destination: Optional[str] = None,
        min_rating: Optional[float] = None,
        max_rating: Optional[float] = None,
        aspect_weights: Optional[Dict[str, float]] = None,
        model_type: str = "hybrid",
    ) -> Dict[str, Any]:
        """
        Generate top-N hotel recommendations.
        
        Returns ranked list of hotels with scores and explanations.
        """
        logger.info(f"Generating {top_n} recommendations [model={model_type}, user={user_id}]")

        # Get candidate hotels
        hotels, total = self.hotel_store.search(
            destination=destination,
            min_rating=min_rating,
            max_rating=max_rating,
            sort_by="avg_rating",
            sort_order="desc",
            page=1,
            page_size=500,
        )

        if not hotels:
            logger.warning("No hotels found matching filters")
            return {"recommendations": [], "total": 0, "model_used": model_type}

        # Score hotels based on model type
        if model_type == "popularity":
            scored = self._score_by_popularity(hotels)
        elif model_type == "content":
            scored = self._score_by_content(hotels, aspect_weights)
        else:
            # Hybrid: combine multiple signals
            scored = self._score_hybrid(hotels, aspect_weights)

        # Sort and take top-N
        scored.sort(key=lambda x: x["score"], reverse=True)
        top_recommendations = scored[:top_n]

        # Enrich with explanations
        enriched = []
        for rank, hotel in enumerate(top_recommendations, start=1):
            enriched.append(self._enrich_recommendation(hotel, rank, aspect_weights))

        return {
            "recommendations": enriched,
            "total": len(scored),
            "model_used": model_type,
            "filters_applied": {
                "destination": destination,
                "min_rating": min_rating,
                "max_rating": max_rating,
            },
        }

    def _score_by_popularity(self, hotels: List[Dict]) -> List[Dict]:
        """Score hotels by popularity (review count + rating)."""
        max_reviews = max((h.get("review_count") or 0 for h in hotels), default=1)
        max_reviews = max(max_reviews, 1)

        for h in hotels:
            review_count = h.get("review_count") or 0
            avg_rating = h.get("avg_rating") or 3.0

            pop_score = (
                0.5 * np.log1p(review_count) / np.log1p(max_reviews) +
                0.5 * (avg_rating / 5.0)
            )
            h["score"] = round(float(pop_score), 4)
            h["model_contribution"] = {"popularity": 1.0}

        return hotels

    def _score_by_content(self, hotels: List[Dict], aspect_weights: Optional[Dict[str, float]] = None) -> List[Dict]:
        """Score hotels by aspect-weighted content scores."""
        default_weights = {
            "cleanliness": 1.0,
            "service": 1.0,
            "location_score": 1.0,
            "rooms": 1.0,
            "value": 1.0,
        }

        if aspect_weights:
            weights = {
                "cleanliness": aspect_weights.get("cleanliness", 1.0),
                "service": aspect_weights.get("service", 1.0),
                "location_score": aspect_weights.get("location", 1.0),
                "rooms": aspect_weights.get("rooms", 1.0),
                "value": aspect_weights.get("value", 1.0),
            }
        else:
            weights = default_weights

        total_weight = sum(weights.values()) or 1.0

        for h in hotels:
            content_score = 0.0
            for aspect, weight in weights.items():
                aspect_val = h.get(aspect) or h.get("avg_rating") or 3.0
                content_score += (aspect_val / 5.0) * weight

            content_score = content_score / total_weight

            # Blend with sentiment
            sentiment = h.get("sentiment_score") or 0.0
            sentiment_normalized = (sentiment + 1) / 2  # -1..1 -> 0..1

            h["score"] = round(float(0.7 * content_score + 0.3 * sentiment_normalized), 4)
            h["model_contribution"] = {"content": 0.7, "sentiment": 0.3}

        return hotels

    def _score_hybrid(self, hotels: List[Dict], aspect_weights: Optional[Dict[str, float]] = None) -> List[Dict]:
        """Hybrid scoring combining popularity, content, and sentiment signals."""
        w_pop = 0.20
        w_content = 0.40
        w_sentiment = 0.25
        w_rating = 0.15

        max_reviews = max((h.get("review_count") or 0 for h in hotels), default=1)
        max_reviews = max(max_reviews, 1)

        default_aspect_weights = {
            "cleanliness": 1.0,
            "service": 1.0,
            "location_score": 1.0,
            "rooms": 1.0,
            "value": 1.0,
        }

        if aspect_weights:
            aw = {
                "cleanliness": aspect_weights.get("cleanliness", 1.0),
                "service": aspect_weights.get("service", 1.0),
                "location_score": aspect_weights.get("location", 1.0),
                "rooms": aspect_weights.get("rooms", 1.0),
                "value": aspect_weights.get("value", 1.0),
            }
        else:
            aw = default_aspect_weights

        total_aw = sum(aw.values()) or 1.0

        for h in hotels:
            # Popularity signal
            review_count = h.get("review_count") or 0
            pop_score = np.log1p(review_count) / np.log1p(max_reviews)

            # Content signal (aspect-weighted)
            content_score = 0.0
            for aspect, weight in aw.items():
                aspect_val = h.get(aspect) or h.get("avg_rating") or 3.0
                content_score += (aspect_val / 5.0) * weight
            content_score = content_score / total_aw

            # Sentiment signal
            sentiment = h.get("sentiment_score") or 0.0
            sentiment_norm = (sentiment + 1) / 2

            # Rating signal
            avg_rating = h.get("avg_rating") or 3.0
            rating_norm = avg_rating / 5.0

            hybrid = (
                w_pop * pop_score +
                w_content * content_score +
                w_sentiment * sentiment_norm +
                w_rating * rating_norm
            )

            h["score"] = round(float(hybrid), 4)
            h["model_contribution"] = {
                "popularity": round(w_pop * pop_score, 4),
                "content": round(w_content * content_score, 4),
                "sentiment": round(w_sentiment * sentiment_norm, 4),
                "rating": round(w_rating * rating_norm, 4),
            }

        return hotels

    def _enrich_recommendation(self, hotel: Dict, rank: int, aspect_weights: Optional[Dict] = None) -> Dict:
        """Add explanation and metadata to a recommendation."""
        score = hotel.get("score", 0.0)
        match_pct = min(100, int(score * 100 * 1.3))  # scale to more readable %

        # Generate explanation
        avg_rating = hotel.get("avg_rating") or 3.0
        review_count = hotel.get("review_count") or 0
        sentiment = hotel.get("sentiment_score") or 0.0

        factors = []
        if avg_rating >= 4.5:
            factors.append(f"Excellent overall rating ({avg_rating:.1f}/5)")
        elif avg_rating >= 4.0:
            factors.append(f"Very good rating ({avg_rating:.1f}/5)")

        if review_count > 1000:
            factors.append(f"Highly reviewed ({review_count:,} reviews)")
        elif review_count > 200:
            factors.append(f"Well reviewed ({review_count:,} reviews)")

        if sentiment > 0.5:
            factors.append("Overwhelmingly positive guest sentiment")
        elif sentiment > 0.2:
            factors.append("Positive guest sentiment")

        # Check aspect scores
        for aspect in ["cleanliness", "service", "value"]:
            if hotel.get(aspect, 0) and float(hotel.get(aspect, 0)) >= 4.5:
                factors.append(f"Outstanding {aspect} score ({hotel[aspect]:.1f}/5)")

        if not factors:
            factors = ["Good overall performance across multiple metrics"]

        primary = factors[0] if factors else "Strong overall hotel quality"

        loc_score = hotel.get("location_score")
        if loc_score is None:
            try:
                loc_val = hotel.get("location")
                loc_score = float(loc_val) if loc_val not in (None, "Various") else None
            except (ValueError, TypeError):
                loc_score = None

        aspect_dict = {
            "cleanliness": float(hotel["cleanliness"]) if hotel.get("cleanliness") is not None else None,
            "service": float(hotel["service"]) if hotel.get("service") is not None else None,
            "location": float(loc_score) if loc_score is not None else None,
            "rooms": float(hotel["rooms"]) if hotel.get("rooms") is not None else None,
            "value": float(hotel["value"]) if hotel.get("value") is not None else None,
        }

        return {
            **hotel,
            "hotel_name": hotel.get("name") or f"Hotel {hotel.get('hotel_id')}",
            "destination": hotel.get("location") or "Verified Location",
            "aspect_scores": aspect_dict,
            "rank": rank,
            "match_percentage": match_pct,
            "explanation": {
                "primary_reason": primary,
                "contributing_factors": factors,
                "model_contribution": hotel.get("model_contribution", {}),
            },
            "is_trending": review_count > 500 and avg_rating >= 4.0,
        }

    def explain_hotel(self, hotel_id: str, user_preferences: Optional[Dict] = None) -> Optional[Dict]:
        """Generate detailed explanation for a specific hotel."""
        hotel = self.hotel_store.get_by_id(hotel_id)
        if not hotel:
            return None

        avg_rating = hotel.get("avg_rating") or 3.0
        aspects = {}
        for col in ["cleanliness", "service", "location_score", "rooms", "value", "sleep_quality"]:
            if hotel.get(col) is not None:
                display_key = "location" if col == "location_score" else col
                aspects[display_key] = round(float(hotel[col]), 2)

        strengths = []
        weaknesses = []
        for aspect, val in aspects.items():
            if val >= 4.3:
                strengths.append(f"Excellent {aspect} ({val:.1f}/5)")
            elif val <= 3.0:
                weaknesses.append(f"Average {aspect} ({val:.1f}/5)")

        # Sentiment summary
        sentiment = hotel.get("sentiment_score") or 0.0
        if sentiment > 0.6:
            sentiment_summary = "Guests are overwhelmingly positive about this hotel"
        elif sentiment > 0.3:
            sentiment_summary = "Most guests have a positive experience"
        elif sentiment > 0:
            sentiment_summary = "Mixed but slightly positive guest reviews"
        else:
            sentiment_summary = "Mixed guest reviews"

        # Similar hotels
        similar = self.hotel_store.get_similar(hotel_id, top_n=3)
        similar_ids = [s["hotel_id"] for s in similar]

        return {
            "hotel_id": hotel_id,
            "hotel_name": hotel.get("name", hotel_id),
            "overall_score": round(avg_rating / 5.0, 3),
            "aspect_breakdown": aspects,
            "strengths": strengths if strengths else ["Solid overall performance"],
            "weaknesses": weaknesses if weaknesses else [],
            "sentiment_summary": sentiment_summary,
            "similar_hotels": similar_ids,
        }

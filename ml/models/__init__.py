"""
TripSense AI Recommendation Models

This package contains all recommendation algorithms:
- PopularityRecommender: Baseline popularity-based recommendations
- CollaborativeFilteringRecommender: ALS matrix factorization
- ContentBasedRecommender: Feature similarity matching
- NLPSentimentRecommender: Sentiment and text-based recommendations
- HybridEnsembleRecommender: Weighted ensemble of all models
"""

from .popularity_model import PopularityRecommender
from .collaborative_filtering import CollaborativeFilteringRecommender
from .content_based import ContentBasedRecommender
from .nlp_sentiment import NLPSentimentRecommender
from .hybrid_ensemble import HybridEnsembleRecommender

__all__ = [
    "PopularityRecommender",
    "CollaborativeFilteringRecommender",
    "ContentBasedRecommender",
    "NLPSentimentRecommender",
    "HybridEnsembleRecommender",
]

__version__ = "1.0.0"

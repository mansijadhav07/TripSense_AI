"""
TripSense AI - Analytics Schemas

Pydantic schemas for analytics/dashboard API endpoints.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any


class DatasetStats(BaseModel):
    """Dataset statistics for the analytics dashboard."""
    total_reviews: int
    total_hotels: int
    total_users: int
    avg_rating: float
    rating_std: float
    sparsity_percent: float
    date_range: Optional[Dict[str, str]] = None


class RatingBucket(BaseModel):
    """Single rating bucket for distribution chart."""
    rating: str
    count: int
    percentage: float


class ModelMetrics(BaseModel):
    """Metrics for a single recommendation model."""
    model_config = ConfigDict(protected_namespaces=())

    model_name: str
    model_type: str
    precision_at_10: float
    recall_at_10: float
    ndcg_at_10: float
    map_score: float
    coverage: float
    hit_rate: float
    description: str


class SparkBenchmark(BaseModel):
    """Spark vs Pandas benchmark result."""
    dataset_size: int
    operation: str
    spark_seconds: float
    pandas_seconds: float
    speedup: float


class DatasetStatsResponse(BaseModel):
    """Response for dataset statistics endpoint."""
    success: bool = True
    data: Dict[str, Any]
    message: str = "Dataset statistics retrieved"


class ModelPerformanceResponse(BaseModel):
    """Response for model performance endpoint."""
    success: bool = True
    data: Dict[str, Any]
    message: str = "Model performance data retrieved"

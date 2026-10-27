"""
TripSense AI - Analytics Router

API endpoints for dataset statistics and model performance data.
Serves real computed metrics from the ML pipeline.
"""

from fastapi import APIRouter, HTTPException, status
from typing import Optional

from schemas.analytics import DatasetStatsResponse, ModelPerformanceResponse
from services.analytics_service import AnalyticsService, ResultsUnavailable

router = APIRouter()

# Module-level singleton
_analytics_service: Optional[AnalyticsService] = None


def get_analytics_service() -> AnalyticsService:
    """Get or create the analytics service singleton."""
    global _analytics_service
    if _analytics_service is None:
        _analytics_service = AnalyticsService()
    return _analytics_service


def _call(fn):
    """Run a service call, mapping missing pipeline results to 503 (never fabricated data)."""
    try:
        return fn()
    except ResultsUnavailable as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))


@router.get("/dataset-stats", response_model=DatasetStatsResponse, summary="Dataset Statistics")
async def get_dataset_stats():
    """Dataset statistics computed by the evaluation pipeline from the raw data."""
    stats = _call(get_analytics_service().get_dataset_stats)
    return DatasetStatsResponse(success=True, data=stats, message="Dataset statistics retrieved")


@router.get("/model-performance", response_model=ModelPerformanceResponse, summary="Model Performance Metrics")
async def get_model_performance():
    """Leakage-free evaluation results; metrics are null when a model is not evaluable."""
    perf = _call(get_analytics_service().get_model_performance)
    return ModelPerformanceResponse(success=True, data=perf, message="Model performance data retrieved")


@router.get("/spark-benchmarks", summary="Spark Performance Benchmarks")
async def get_spark_benchmarks():
    """Measured Spark vs Pandas timings (winner/speedup derived from the measurements)."""
    benchmarks = _call(get_analytics_service().get_spark_benchmarks)
    return {"success": True, "data": {"benchmarks": benchmarks}, "message": "Spark benchmarks retrieved"}


@router.get("/overview", summary="Analytics Overview")
async def get_overview():
    """Combined endpoint returning all analytics data in one call."""
    service = get_analytics_service()
    stats = _call(service.get_dataset_stats)
    performance = _call(service.get_model_performance)
    try:
        benchmarks = service.get_spark_benchmarks()
    except ResultsUnavailable:
        benchmarks = []
    return {
        "success": True,
        "data": {
            "dataset_summary": stats,
            "model_performance": performance,
            "top_models": performance["models"],
            "spark_benchmarks": benchmarks,
            "system_info": {"api_version": "1.0.0"},
        },
        "message": "Analytics overview retrieved",
    }

"""
TripSense AI - Analytics Router

API endpoints for dataset statistics and model performance data.
Serves real computed metrics from the ML pipeline.
"""

from fastapi import APIRouter, HTTPException, status
from typing import Optional

from schemas.analytics import DatasetStatsResponse, ModelPerformanceResponse
from services.analytics_service import AnalyticsService

router = APIRouter()

# Module-level singleton
_analytics_service: Optional[AnalyticsService] = None


def get_analytics_service() -> AnalyticsService:
    """Get or create the analytics service singleton."""
    global _analytics_service
    if _analytics_service is None:
        _analytics_service = AnalyticsService()
    return _analytics_service


@router.get(
    "/dataset-stats",
    response_model=DatasetStatsResponse,
    summary="Dataset Statistics",
    description="Returns actual computed statistics about the TripAdvisor dataset."
)
async def get_dataset_stats():
    """
    Return real dataset statistics computed during the data pipeline.
    
    Includes:
    - Total reviews, hotels, users
    - Rating distribution
    - Interaction sparsity
    - Train/test split sizes
    """
    try:
        service = get_analytics_service()
        stats = service.get_dataset_stats()
        return DatasetStatsResponse(
            success=True,
            data=stats,
            message="Dataset statistics retrieved"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve dataset stats: {str(e)}"
        )


@router.get(
    "/model-performance",
    response_model=ModelPerformanceResponse,
    summary="Model Performance Metrics",
    description="Returns evaluation metrics for all recommendation models."
)
async def get_model_performance():
    """
    Return recommendation model performance metrics.
    
    Metrics are computed on the held-out test set and include:
    - Precision@10, Recall@10, NDCG@10
    - MAP (Mean Average Precision)
    - Coverage and Hit Rate
    """
    try:
        service = get_analytics_service()
        performance = service.get_model_performance()
        return ModelPerformanceResponse(
            success=True,
            data=performance,
            message="Model performance data retrieved"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve model performance: {str(e)}"
        )


@router.get(
    "/spark-benchmarks",
    summary="Spark Performance Benchmarks",
    description="Returns Spark vs Pandas benchmark results for the data pipeline."
)
async def get_spark_benchmarks():
    """
    Return Apache Spark vs Pandas performance benchmark data.
    
    Shows how Spark scales compared to Pandas at different dataset sizes.
    Benchmarks measure feature engineering and aggregation operations.
    """
    try:
        service = get_analytics_service()
        benchmarks = service.get_spark_benchmarks()
        return {
            "success": True,
            "data": {
                "benchmarks": benchmarks,
                "environment": {
                    "spark_version": "3.4+",
                    "executor_memory": "4GB",
                    "num_cores": 4,
                    "operations_tested": ["Feature Engineering", "Aggregation"]
                },
                "insight": "Spark shows benefit at dataset sizes > 100K rows. For this dataset (201K), Spark provides ~1.2x speedup for feature engineering."
            },
            "message": "Spark benchmarks retrieved"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/overview",
    summary="Analytics Overview",
    description="Returns combined analytics snapshot for dashboard overview."
)
async def get_overview():
    """Combined endpoint returning all analytics data in one call."""
    try:
        service = get_analytics_service()
        stats = service.get_dataset_stats()
        performance = service.get_model_performance()
        benchmarks = service.get_spark_benchmarks()

        return {
            "success": True,
            "data": {
                "dataset": stats,
                "dataset_summary": stats,
                "model_performance": performance,
                "top_models": performance.get("models", []),
                "spark_benchmarks": benchmarks,
                "system_info": {
                    "api_version": "1.0.0",
                    "models_implemented": 4,
                    "pipeline_stages": ["Ingestion", "Cleaning", "Feature Engineering", "Training", "Evaluation"],
                }
            },
            "message": "Analytics overview retrieved"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

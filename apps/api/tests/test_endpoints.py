"""
TripSense AI - Endpoints Test Suite

Tests all core API endpoints for recommendations, hotels, and analytics.
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Ensure api directory is on sys.path
api_dir = Path(__file__).resolve().parent.parent
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))

from main import app

client = TestClient(app)


def _reset_catalog(monkeypatch, allow_synthetic: bool):
    """Rebuild the hotel-store/recommendation singletons under an explicit data policy."""
    import services.hotel_service as hs
    from config import settings
    from routers import recommendations as rec_router
    monkeypatch.setattr(settings, "allow_synthetic_data", allow_synthetic)
    monkeypatch.setattr(hs.HotelDataStore, "_find_data_dir", lambda self: Path("/nonexistent-tripsense-data"))
    monkeypatch.setattr(hs, "_hotel_store", None)
    monkeypatch.setattr(rec_router, "_recommendation_service", None)


@pytest.fixture
def no_catalog(monkeypatch):
    _reset_catalog(monkeypatch, False)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert "endpoints" in data


def test_popular_recommendations():
    response = client.get("/api/v1/recommendations/popular?top_n=5")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["data_source"] == "pipeline"
    assert len(data["recommendations"]) == 5
    assert data["model_used"] == "popularity"


def test_generate_recommendations_hybrid():
    payload = {
        "top_n": 5,
        "model_type": "hybrid",
        "travel_styles": ["family"],
        "aspect_weights": {"cleanliness": 1.5, "service": 1.2, "location": 1.0, "rooms": 1.0, "value": 1.0},
    }
    response = client.post("/api/v1/recommendations/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    recs = data["data"]["recommendations"]
    assert len(recs) == 5
    first_item = recs[0]
    assert first_item["hotel_id"].startswith("hotel_")
    assert 0 <= first_item["match_percentage"] <= 100
    assert first_item["explanation"]["primary_reason"]
    assert set(first_item["explanation"]["model_contribution"]) == {"cf", "content", "sentiment"}
    assert data["data"]["personalization"]["mode"] == "preferences"


def test_hotel_search():
    response = client.get("/api/v1/hotels/search?page=1&page_size=5")
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data["hotels"]) == 5
    assert data["pagination"]["total_hotels"] == 500
    h = data["hotels"][0]
    assert h["name"] and h["location"] and h["styles"]


def test_catalog_unavailable_returns_503_not_fake_data(no_catalog):
    assert client.get("/api/v1/hotels/search").status_code == 503
    assert client.get("/api/v1/recommendations/popular").status_code == 503


def test_recommendations_are_deterministic():
    body = {"top_n": 5, "model_type": "content", "travel_styles": ["luxury"]}
    a = client.post("/api/v1/recommendations/generate", json=body).json()["data"]["recommendations"]
    b = client.post("/api/v1/recommendations/generate", json=body).json()["data"]["recommendations"]
    assert [r["hotel_id"] for r in a] == [r["hotel_id"] for r in b]


def test_analytics_serves_pipeline_results_only(tmp_path, monkeypatch):
    from routers import analytics as ar
    from services.analytics_service import AnalyticsService
    monkeypatch.setattr(ar, "_analytics_service", AnalyticsService(evaluation_dir=tmp_path))
    for path in ("model-performance", "spark-benchmarks", "overview"):
        assert client.get(f"/api/v1/analytics/{path}").status_code == 503


def test_analytics_endpoints_match_pipeline_output():
    import json
    root = Path(__file__).resolve().parents[3]
    stats = client.get("/api/v1/analytics/dataset-stats").json()["data"]
    on_disk = json.loads((root / "data/processed/dataset_stats.json").read_text())
    assert stats["total_reviews"] == on_disk["total_reviews"] and stats["avg_rating"] == on_disk["avg_rating"]
    assert stats["hotel_id_is_unique_per_row"] is False

    perf = client.get("/api/v1/analytics/model-performance").json()["data"]
    report = json.loads((root / "ml/evaluation/results/synthetic_evaluation.json").read_text())
    models = {m["model_name"]: m for m in perf["models"]}
    assert set(models) >= {"Collaborative Filtering (SVD)", "Content-Based", "Sentiment Analysis", "Hybrid Ensemble"}
    assert models["Hybrid Ensemble"]["ndcg_at_10"] == report["models"]["hybrid_ensemble"]["ndcg_at_k"]
    assert models["Sentiment Analysis"]["text_metrics"]["accuracy"] == report["models"]["sentiment_analysis"]["accuracy"]
    sent = models["Sentiment Analysis"]
    sr = report["models"]["sentiment_analysis"]["ranking_by_hotel_sentiment"]
    assert sent["ndcg_at_10"] == sr["ndcg_at_k"] and sent["hit_rate"] == sr["hit_rate_at_k"]  # not n/a
    assert all(models[n][f] is not None for n in models for f in ("ndcg_at_10", "recall_at_10", "precision_at_10", "hit_rate"))
    assert all(v == 0 for v in perf["leakage_checks"].values())
    assert client.get("/api/v1/analytics/overview").status_code == 200


def test_saved_hotels_list_roundtrip():
    """Regression: listing saved hotels used a non-existent store method (HTTP 500)."""
    r = client.post("/api/v1/auth/register", json={"email": "saved@example.com", "password": "SavedPass123!"})
    token = r.json()["data"]["token"]["access_token"] if r.status_code < 300 else client.post(
        "/api/v1/auth/login", json={"email": "saved@example.com", "password": "SavedPass123!"}
    ).json()["data"]["token"]["access_token"]
    h = {"Authorization": f"Bearer {token}"}
    hotel_id = client.get("/api/v1/hotels/search?page_size=1").json()["data"]["hotels"][0]["hotel_id"]
    assert client.post("/api/v1/users/me/saved-hotels", json={"hotel_id": hotel_id}, headers=h).status_code == 201
    listed = client.get("/api/v1/users/me/saved-hotels", headers=h)
    assert listed.status_code == 200
    item = listed.json()["data"][0]
    assert item["hotel_id"] == hotel_id and item["hotel"]["avg_rating"] is not None
    assert client.get("/api/v1/users/me/saved-hotels").status_code == 401
    client.delete(f"/api/v1/users/me/saved-hotels/{hotel_id}", headers=h)

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
    response = client.get("/api/v1/recommendations/popular?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) > 0


def test_generate_recommendations_hybrid():
    payload = {
        "top_n": 5,
        "model_type": "hybrid",
        "aspect_weights": {
            "cleanliness": 1.5,
            "service": 1.2,
            "location": 1.0,
            "rooms": 1.0,
            "value": 1.0
        }
    }
    response = client.post("/api/v1/recommendations/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    recs = data["data"].get("recommendations", [])
    assert len(recs) > 0
    first_item = recs[0]
    assert "hotel_id" in first_item
    assert "match_percentage" in first_item
    assert "explanation" in first_item


def test_hotel_search():
    response = client.get("/api/v1/hotels/search?page=1&page_size=5")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) > 0


def test_analytics_endpoints():
    r1 = client.get("/api/v1/analytics/dataset-stats")
    assert r1.status_code == 200
    assert r1.json()["success"] is True

    r2 = client.get("/api/v1/analytics/model-performance")
    assert r2.status_code == 200
    assert r2.json()["success"] is True

    r3 = client.get("/api/v1/analytics/overview")
    assert r3.status_code == 200
    assert r3.json()["success"] is True

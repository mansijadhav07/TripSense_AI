"""
Health Check Endpoint Tests
"""
import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
def test_health_endpoint(client: TestClient):
    """Test basic health check endpoint"""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data


@pytest.mark.unit
def test_ready_endpoint(client: TestClient):
    """Test readiness check endpoint"""
    response = client.get("/ready")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "ready"
    assert "checks" in data
    assert "database" in data["checks"]


@pytest.mark.unit
def test_info_endpoint(client: TestClient):
    """Test service info endpoint"""
    response = client.get("/info")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "name" in data
    assert "version" in data
    assert "environment" in data
    assert data["name"] == "TripSense AI"


@pytest.mark.unit
def test_ready_returns_503_when_database_down(client: TestClient, db_session, monkeypatch):
    """A failing DB must produce a real HTTP 503, not a 200 with a tuple body."""
    def boom(*a, **k):
        raise RuntimeError("db down")
    monkeypatch.setattr(db_session, "execute", boom)
    response = client.get("/ready")
    assert response.status_code == 503
    assert response.json()["ready"] is False

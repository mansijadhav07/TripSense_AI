"""
Quick test to verify API can start without database.
"""

import sys
from fastapi.testclient import TestClient

# Mock database for testing
class MockEngine:
    pass

class MockBase:
    metadata = type('obj', (object,), {'create_all': lambda bind: None})()

# Patch database before importing main
sys.modules['database'].engine = MockEngine()
sys.modules['database'].Base = MockBase

from main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "TripSense AI"
    assert data["status"] == "running"
    print("✅ Root endpoint works")

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    print("✅ Health endpoint works")

if __name__ == "__main__":
    print("Testing API endpoints...")
    test_root()
    test_health()
    print("\n✅ All tests passed!")

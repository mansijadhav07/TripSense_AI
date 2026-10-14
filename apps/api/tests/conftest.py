"""
Pytest Configuration and Fixtures
"""
import os
import pytest
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app
from config import get_settings


# Test database URL (in-memory SQLite)
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine"""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_engine) -> Generator[Session, None, None]:
    """Create a new database session for each test"""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
    )
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Create test client with database override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_settings():
    """Override settings for testing"""
    settings = get_settings()
    settings.ENVIRONMENT = "testing"
    settings.JWT_SECRET_KEY = "test-secret-key-for-testing-only"
    return settings


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "email": "test@example.com",
        "password": "TestPassword123!"
    }


@pytest.fixture
def sample_preference_data():
    """Sample preference data for testing"""
    return {
        "destination": "New York",
        "min_budget": 100,
        "max_budget": 500,
        "min_rating": 4.0,
        "cleanliness_weight": 0.2,
        "location_weight": 0.25,
        "rooms_weight": 0.15,
        "service_weight": 0.15,
        "value_weight": 0.15,
        "sleep_quality_weight": 0.1,
        "travel_style": "business"
    }


@pytest.fixture
def authenticated_client(client: TestClient, sample_user_data: dict) -> TestClient:
    """Create authenticated test client"""
    # Register user
    response = client.post("/api/v1/auth/register", json=sample_user_data)
    assert response.status_code == 201
    
    # Login
    response = client.post("/api/v1/auth/login", json=sample_user_data)
    assert response.status_code == 200
    
    token = response.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    
    return client

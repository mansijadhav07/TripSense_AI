"""
Authentication Tests
"""
import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
def test_user_registration(client: TestClient, sample_user_data: dict):
    """Test user registration endpoint"""
    response = client.post("/api/v1/auth/register", json=sample_user_data)
    
    assert response.status_code == 201
    data = response.json()
    
    assert "user" in data
    assert data["user"]["email"] == sample_user_data["email"]
    assert "id" in data["user"]
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"


@pytest.mark.integration
def test_duplicate_registration(client: TestClient, sample_user_data: dict):
    """Test that duplicate email registration fails"""
    # First registration
    response = client.post("/api/v1/auth/register", json=sample_user_data)
    assert response.status_code == 201
    
    # Duplicate registration
    response = client.post("/api/v1/auth/register", json=sample_user_data)
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


@pytest.mark.integration
def test_user_login(client: TestClient, sample_user_data: dict):
    """Test user login endpoint"""
    # Register first
    client.post("/api/v1/auth/register", json=sample_user_data)
    
    # Login
    response = client.post("/api/v1/auth/login", json=sample_user_data)
    
    assert response.status_code == 200
    data = response.json()
    
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"


@pytest.mark.integration
def test_login_invalid_credentials(client: TestClient, sample_user_data: dict):
    """Test login with invalid credentials"""
    # Register first
    client.post("/api/v1/auth/register", json=sample_user_data)
    
    # Wrong password
    wrong_data = sample_user_data.copy()
    wrong_data["password"] = "WrongPassword123!"
    
    response = client.post("/api/v1/auth/login", json=wrong_data)
    assert response.status_code == 401


@pytest.mark.integration
def test_get_current_user(authenticated_client: TestClient, sample_user_data: dict):
    """Test getting current user info"""
    response = authenticated_client.get("/api/v1/auth/me")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["email"] == sample_user_data["email"]
    assert "id" in data
    assert "created_at" in data


@pytest.mark.integration
def test_get_current_user_unauthorized(client: TestClient):
    """Test that unauthorized requests fail"""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.integration
def test_logout(authenticated_client: TestClient):
    """Test logout endpoint"""
    response = authenticated_client.post("/api/v1/auth/logout")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["message"] == "Successfully logged out"

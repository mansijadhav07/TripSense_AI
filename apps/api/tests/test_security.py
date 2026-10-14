"""
Security Utility Tests
"""
import pytest
from datetime import datetime, timedelta
from utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token
)


@pytest.mark.unit
def test_password_hashing():
    """Test password hashing"""
    password = "TestPassword123!"
    hashed = hash_password(password)
    
    assert hashed != password
    assert len(hashed) > 0
    assert hashed.startswith("$2b$")  # bcrypt prefix


@pytest.mark.unit
def test_password_verification():
    """Test password verification"""
    password = "TestPassword123!"
    hashed = hash_password(password)
    
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


@pytest.mark.unit
def test_create_access_token(test_settings):
    """Test JWT token creation"""
    user_id = "123e4567-e89b-12d3-a456-426614174000"
    token = create_access_token(user_id)
    
    assert token is not None
    assert len(token) > 0
    assert isinstance(token, str)


@pytest.mark.unit
def test_decode_access_token(test_settings):
    """Test JWT token decoding"""
    user_id = "123e4567-e89b-12d3-a456-426614174000"
    token = create_access_token(user_id)
    
    decoded_user_id = decode_access_token(token)
    
    assert decoded_user_id == user_id


@pytest.mark.unit
def test_decode_invalid_token():
    """Test decoding invalid token"""
    invalid_token = "invalid.token.here"
    
    decoded = decode_access_token(invalid_token)
    
    assert decoded is None


@pytest.mark.unit
def test_token_expiration(test_settings):
    """Test that expired tokens are rejected"""
    user_id = "123e4567-e89b-12d3-a456-426614174000"
    
    # Create token with negative expiration (already expired)
    expires_delta = timedelta(minutes=-10)
    token = create_access_token(user_id, expires_delta)
    
    decoded = decode_access_token(token)
    
    assert decoded is None

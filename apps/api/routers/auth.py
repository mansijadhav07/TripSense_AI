"""
TripSense AI - Authentication Router

API endpoints for user registration and login.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from schemas.auth import UserRegister, UserLogin, Token, UserResponse, AuthResponse
from services.auth_service import register_user, authenticate_user, create_user_token
from dependencies.auth import get_current_user
from models.user import User

router = APIRouter()


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user.
    
    Creates a new user account with email and password.
    Password must be at least 8 characters.
    
    Returns user information and JWT access token.
    """
    # Create user
    user = register_user(db, user_data)
    
    # Generate token
    token = create_user_token(user)
    
    user_dict = {
        "id": str(user.id),
        "email": user.email,
        "created_at": user.created_at.isoformat()
    }
    token_dict = {
        "access_token": token.access_token,
        "token_type": token.token_type,
        "expires_in": token.expires_in
    }
    
    return AuthResponse(
        success=True,
        data={
            "user": user_dict,
            "token": token_dict
        },
        user=user_dict,
        token=token_dict,
        access_token=token.access_token,
        token_type=token.token_type,
        message="User registered successfully"
    )


@router.post("/login", response_model=AuthResponse)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user and return access token.
    
    Validates email and password, then returns JWT token
    for accessing protected endpoints.
    """
    # Authenticate user
    user = authenticate_user(db, credentials.email, credentials.password)
    
    # Generate token
    token = create_user_token(user)
    
    user_dict = {
        "id": str(user.id),
        "email": user.email
    }
    token_dict = {
        "access_token": token.access_token,
        "token_type": token.token_type,
        "expires_in": token.expires_in
    }
    
    return AuthResponse(
        success=True,
        data={
            "user": user_dict,
            "token": token_dict
        },
        user=user_dict,
        token=token_dict,
        access_token=token.access_token,
        token_type=token.token_type,
        message="Login successful"
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information.
    
    Requires valid JWT token in Authorization header.
    """
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        created_at=current_user.created_at
    )


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """
    Logout current user.
    
    Since JWT tokens are stateless, this endpoint mainly serves
    to validate the token. Client should discard the token.
    """
    return {
        "success": True,
        "message": "Successfully logged out"
    }

"""
TripSense AI - Users & Preferences Router

API endpoints for managing user profile and recommendation preferences.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from models.user import User
from models.preference import UserPreference
from dependencies.auth import get_current_user
from schemas.user_preference import UserPreferenceUpdate, UserPreferenceResponse

router = APIRouter()


@router.get("/me/preferences", response_model=UserPreferenceResponse)
async def get_my_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the current authenticated user's recommendation preferences."""
    pref = db.query(UserPreference).filter(UserPreference.user_id == current_user.id).first()
    
    if not pref:
        # Return default preferences if not yet explicitly saved
        return UserPreferenceResponse(
            success=True,
            data={
                "destination": None,
                "min_rating": 3.0,
                "cleanliness_weight": 1.0,
                "location_weight": 1.0,
                "rooms_weight": 1.0,
                "service_weight": 1.0,
                "value_weight": 1.0,
                "sleep_quality_weight": 1.0,
                "travel_style": "leisure"
            },
            message="Default preferences returned"
        )
    
    return UserPreferenceResponse(
        success=True,
        data={
            "destination": pref.destination,
            "min_rating": float(pref.min_rating) if pref.min_rating else 3.0,
            "cleanliness_weight": float(pref.cleanliness_weight) if pref.cleanliness_weight else 1.0,
            "location_weight": float(pref.location_weight) if pref.location_weight else 1.0,
            "rooms_weight": float(pref.rooms_weight) if pref.rooms_weight else 1.0,
            "service_weight": float(pref.service_weight) if pref.service_weight else 1.0,
            "value_weight": float(pref.value_weight) if pref.value_weight else 1.0,
            "sleep_quality_weight": float(pref.sleep_quality_weight) if pref.sleep_quality_weight else 1.0,
            "travel_style": pref.travel_style or "leisure"
        },
        message="User preferences retrieved"
    )


@router.put("/me/preferences", response_model=UserPreferenceResponse)
async def update_my_preferences(
    payload: UserPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update or create the current authenticated user's recommendation preferences."""
    pref = db.query(UserPreference).filter(UserPreference.user_id == current_user.id).first()
    
    if not pref:
        pref = UserPreference(
            user_id=current_user.id,
            destination=payload.destination,
            min_rating=payload.min_rating,
            cleanliness_weight=payload.cleanliness_weight,
            location_weight=payload.location_weight,
            rooms_weight=payload.rooms_weight,
            service_weight=payload.service_weight,
            value_weight=payload.value_weight,
            sleep_quality_weight=payload.sleep_quality_weight,
            travel_style=payload.travel_style,
        )
        db.add(pref)
    else:
        if payload.destination is not None:
            pref.destination = payload.destination
        if payload.min_rating is not None:
            pref.min_rating = payload.min_rating
        pref.cleanliness_weight = payload.cleanliness_weight
        pref.location_weight = payload.location_weight
        pref.rooms_weight = payload.rooms_weight
        pref.service_weight = payload.service_weight
        pref.value_weight = payload.value_weight
        pref.sleep_quality_weight = payload.sleep_quality_weight
        pref.travel_style = payload.travel_style
    
    db.commit()
    db.refresh(pref)
    
    return UserPreferenceResponse(
        success=True,
        data={
            "destination": pref.destination,
            "min_rating": float(pref.min_rating),
            "cleanliness_weight": float(pref.cleanliness_weight),
            "location_weight": float(pref.location_weight),
            "rooms_weight": float(pref.rooms_weight),
            "service_weight": float(pref.service_weight),
            "value_weight": float(pref.value_weight),
            "sleep_quality_weight": float(pref.sleep_quality_weight),
            "travel_style": pref.travel_style
        },
        message="Preferences updated successfully"
    )

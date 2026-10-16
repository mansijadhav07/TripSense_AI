"""
TripSense AI - Saved Hotels Router

API endpoints for bookmarking and managing saved hotels.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models.user import User
from models.saved_hotel import SavedHotel
from dependencies.auth import get_current_user
from schemas.saved_hotel import SaveHotelRequest, SavedHotelsResponse
from services.hotel_service import get_hotel_store

router = APIRouter()


@router.get("", response_model=SavedHotelsResponse)
async def list_saved_hotels(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve all hotels saved by the current user."""
    saved = db.query(SavedHotel).filter(SavedHotel.user_id == current_user.id).order_by(SavedHotel.saved_at.desc()).all()
    hotel_store = get_hotel_store()
    
    items = []
    for s in saved:
        hotel_data = hotel_store.get_hotel_by_id(s.hotel_id)
        items.append({
            "id": str(s.id),
            "hotel_id": s.hotel_id,
            "saved_at": s.saved_at.isoformat() if s.saved_at else None,
            "hotel": hotel_data or {
                "hotel_id": s.hotel_id,
                "name": f"Hotel {s.hotel_id}",
                "avg_rating": 4.0,
                "review_count": 50,
                "location": "Saved"
            }
        })
    
    return SavedHotelsResponse(
        success=True,
        data=items,
        total=len(items),
        message=f"Retrieved {len(items)} saved hotels"
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def save_hotel(
    payload: SaveHotelRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Save a hotel to user's favorites list."""
    existing = db.query(SavedHotel).filter(
        SavedHotel.user_id == current_user.id,
        SavedHotel.hotel_id == payload.hotel_id
    ).first()
    
    if existing:
        return {"success": True, "message": "Hotel is already saved"}
    
    new_save = SavedHotel(
        user_id=current_user.id,
        hotel_id=payload.hotel_id
    )
    db.add(new_save)
    db.commit()
    
    return {"success": True, "message": "Hotel saved successfully"}


@router.delete("/{hotel_id}")
async def remove_saved_hotel(
    hotel_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a hotel from user's favorites list."""
    saved = db.query(SavedHotel).filter(
        SavedHotel.user_id == current_user.id,
        SavedHotel.hotel_id == hotel_id
    ).first()
    
    if not saved:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hotel {hotel_id} not found in saved list"
        )
    
    db.delete(saved)
    db.commit()
    
    return {"success": True, "message": "Hotel removed from saved list"}

"""
TripSense AI - Hotels Router

API endpoints for hotel search and detail retrieval.
"""

from fastapi import APIRouter, HTTPException, status, Query, Depends
from typing import Optional

from schemas.hotel import HotelSearchResponse, HotelDetailResponse
from services.hotel_service import get_hotel_store

router = APIRouter()


@router.get(
    "/search",
    response_model=HotelSearchResponse,
    summary="Search hotels",
    description="Search hotels with filters for destination, rating, and reviews."
)
async def search_hotels(
    destination: Optional[str] = Query(default=None, description="City or location name"),
    min_rating: Optional[float] = Query(default=None, ge=1.0, le=5.0),
    max_rating: Optional[float] = Query(default=None, ge=1.0, le=5.0),
    min_reviews: Optional[int] = Query(default=None, ge=0),
    sort_by: str = Query(default="avg_rating", description="Sort field: avg_rating, review_count, name"),
    sort_order: str = Query(default="desc", description="Sort order: asc or desc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    """
    Search hotels with optional filters.
    
    Returns paginated results sorted by the specified field.
    """
    try:
        store = get_hotel_store()
        hotels, total = store.search(
            destination=destination,
            min_rating=min_rating,
            max_rating=max_rating,
            min_reviews=min_reviews,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            page_size=page_size,
        )

        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        return HotelSearchResponse(
            success=True,
            data={
                "hotels": hotels,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_hotels": total,
                    "total_pages": total_pages,
                    "has_next": page < total_pages,
                    "has_prev": page > 1,
                },
                "filters_applied": {
                    "destination": destination,
                    "min_rating": min_rating,
                    "max_rating": max_rating,
                    "min_reviews": min_reviews,
                }
            },
            message=f"Found {total} hotels"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Hotel search error: {str(e)}"
        )


@router.get(
    "/{hotel_id}",
    response_model=HotelDetailResponse,
    summary="Get hotel details",
    description="Get full details for a specific hotel including aspect scores and similar hotels."
)
async def get_hotel_detail(hotel_id: str):
    """
    Get comprehensive hotel details.
    
    Includes aspect-level scores, sentiment analysis results, and similar hotels.
    """
    store = get_hotel_store()
    hotel = store.get_by_id(hotel_id)

    if not hotel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hotel '{hotel_id}' not found"
        )

    # Get similar hotels
    similar_hotels = store.get_similar(hotel_id, top_n=6)
    hotel["similar_hotels"] = similar_hotels

    # Build aspect breakdown
    aspect_keys = {
        "cleanliness": "cleanliness",
        "service": "service",
        "location_score": "location",
        "rooms": "rooms",
        "value": "value",
        "sleep_quality": "sleep_quality",
    }
    aspect_scores = {}
    for data_key, display_key in aspect_keys.items():
        val = hotel.get(data_key)
        if val is not None:
            try:
                aspect_scores[display_key] = round(float(val), 2)
            except (TypeError, ValueError):
                pass

    hotel["aspect_scores"] = aspect_scores

    return HotelDetailResponse(
        success=True,
        data=hotel,
        message="Hotel details retrieved"
    )


@router.get(
    "/{hotel_id}/similar",
    response_model=HotelSearchResponse,
    summary="Get similar hotels",
    description="Find hotels similar to the specified hotel."
)
async def get_similar_hotels(
    hotel_id: str,
    top_n: int = Query(default=6, ge=1, le=20),
):
    """Get hotels similar to a given hotel based on feature similarity."""
    store = get_hotel_store()

    # Verify hotel exists
    hotel = store.get_by_id(hotel_id)
    if not hotel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hotel '{hotel_id}' not found"
        )

    similar = store.get_similar(hotel_id, top_n=top_n)

    return HotelSearchResponse(
        success=True,
        data={
            "hotels": similar,
            "reference_hotel": {"hotel_id": hotel_id, "name": hotel.get("name")},
            "pagination": {"total_hotels": len(similar)},
        },
        message=f"Found {len(similar)} similar hotels"
    )

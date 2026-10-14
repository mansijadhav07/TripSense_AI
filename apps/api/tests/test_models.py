"""
Database Model Tests
"""
import pytest
from sqlalchemy.orm import Session
from models.user import User
from models.preference import UserPreference
from models.saved_hotel import SavedHotel
from utils.security import hash_password


@pytest.mark.unit
@pytest.mark.db
def test_create_user(db_session: Session):
    """Test creating a user"""
    user = User(
        email="test@example.com",
        hashed_password=hash_password("TestPassword123!")
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.created_at is not None
    assert user.updated_at is not None


@pytest.mark.unit
@pytest.mark.db
def test_user_preference_relationship(db_session: Session):
    """Test user-preference relationship"""
    user = User(
        email="test@example.com",
        hashed_password=hash_password("TestPassword123!")
    )
    db_session.add(user)
    db_session.commit()
    
    preference = UserPreference(
        user_id=user.id,
        destination="Paris",
        min_budget=200,
        max_budget=800,
        min_rating=4.5,
        travel_style="leisure"
    )
    db_session.add(preference)
    db_session.commit()
    db_session.refresh(user)
    
    assert user.preference is not None
    assert user.preference.destination == "Paris"
    assert user.preference.min_budget == 200


@pytest.mark.unit
@pytest.mark.db
def test_saved_hotel(db_session: Session):
    """Test saved hotel model"""
    user = User(
        email="test@example.com",
        hashed_password=hash_password("TestPassword123!")
    )
    db_session.add(user)
    db_session.commit()
    
    saved_hotel = SavedHotel(
        user_id=user.id,
        hotel_id="hotel_12345"
    )
    db_session.add(saved_hotel)
    db_session.commit()
    db_session.refresh(user)
    
    assert len(user.saved_hotels) == 1
    assert user.saved_hotels[0].hotel_id == "hotel_12345"
    assert user.saved_hotels[0].saved_at is not None


@pytest.mark.unit
@pytest.mark.db
def test_unique_email_constraint(db_session: Session):
    """Test that email must be unique"""
    user1 = User(
        email="test@example.com",
        hashed_password=hash_password("TestPassword123!")
    )
    db_session.add(user1)
    db_session.commit()
    
    user2 = User(
        email="test@example.com",
        hashed_password=hash_password("AnotherPassword123!")
    )
    db_session.add(user2)
    
    with pytest.raises(Exception):  # SQLAlchemy will raise an integrity error
        db_session.commit()

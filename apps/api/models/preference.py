"""
TripSense AI - User Preference Model

User preferences for personalized recommendations.
"""

from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from database import Base


class UserPreference(Base):
    """User preference model for recommendation personalization."""
    
    __tablename__ = "user_preferences"
    
    # Primary key - SQLite compatible String UUID
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False
    )
    
    # Foreign key
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )
    
    # Destination preferences
    destination = Column(String(255), nullable=True)
    
    # Budget preferences
    min_budget = Column(Numeric(10, 2), nullable=True)
    max_budget = Column(Numeric(10, 2), nullable=True)
    
    # Rating threshold
    min_rating = Column(Numeric(2, 1), default=3.0, nullable=False)
    
    # Aspect weights (for aspect-based recommendation)
    cleanliness_weight = Column(Numeric(3, 2), default=1.0, nullable=False)
    location_weight = Column(Numeric(3, 2), default=1.0, nullable=False)
    rooms_weight = Column(Numeric(3, 2), default=1.0, nullable=False)
    service_weight = Column(Numeric(3, 2), default=1.0, nullable=False)
    value_weight = Column(Numeric(3, 2), default=1.0, nullable=False)
    sleep_quality_weight = Column(Numeric(3, 2), default=1.0, nullable=False)
    
    # Travel style
    travel_style = Column(String(50), nullable=True)  # e.g., "family", "business", "leisure"
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="preference")
    
    def __repr__(self):
        return f"<UserPreference(user_id={self.user_id}, destination={self.destination})>"
    
    @property
    def aspect_weights(self):
        """Return aspect weights as dictionary."""
        return {
            "cleanliness": float(self.cleanliness_weight),
            "location": float(self.location_weight),
            "rooms": float(self.rooms_weight),
            "service": float(self.service_weight),
            "value": float(self.value_weight),
            "sleep_quality": float(self.sleep_quality_weight)
        }


"""
TripSense AI - Saved Hotel Model

User's saved/bookmarked hotels for later reference.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from database import Base


class SavedHotel(Base):
    """Saved hotel model for user bookmarks."""
    
    __tablename__ = "saved_hotels"
    
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
        nullable=False,
        index=True
    )
    
    # Hotel reference (matches hotel_id from dataset)
    hotel_id = Column(String(255), nullable=False, index=True)
    
    # Timestamp
    saved_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="saved_hotels")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'hotel_id', name='unique_user_hotel'),
    )
    
    def __repr__(self):
        return f"<SavedHotel(user_id={self.user_id}, hotel_id={self.hotel_id})>"


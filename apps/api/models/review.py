"""
TripSense AI - Review Model
User-submitted hotel reviews, scored by the trained sentiment model.
"""
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
import uuid
from database import Base


class Review(Base):
    """A review submitted through the app (kept separate from the synthetic training data)."""
    __tablename__ = "reviews"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    hotel_id = Column(String(255), nullable=False, index=True)
    rating = Column(Integer, nullable=True)              # optional 1-5 stars given by the user
    text = Column(Text, nullable=False)
    sentiment_label = Column(String(16), nullable=False)
    sentiment_score = Column(Float, nullable=False)      # P(positive) - P(negative), in [-1, 1]
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<Review(user_id={self.user_id}, hotel_id={self.hotel_id}, label={self.sentiment_label})>"

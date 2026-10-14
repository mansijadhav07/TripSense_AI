"""
TripSense AI - Model Experiment Model

Track ML model training experiments and evaluation results.
"""

from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from database import Base


class ModelExperiment(Base):
    """Model experiment tracking for ML pipeline."""
    
    __tablename__ = "model_experiments"
    
    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )
    
    # Experiment identification
    experiment_name = Column(String(255), nullable=False)
    model_type = Column(String(50), nullable=False)  # "popularity", "collaborative", "content", "hybrid"
    
    # Configuration
    parameters = Column(JSON, nullable=True)  # Model hyperparameters
    
    # Results
    metrics = Column(JSON, nullable=True)  # Evaluation metrics (precision, recall, NDCG, etc.)
    
    # Metadata
    dataset_version = Column(String(50), nullable=True)
    training_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    status = Column(String(50), default="running", nullable=False)  # running, completed, failed
    
    # Optional notes
    notes = Column(String(1000), nullable=True)
    
    def __repr__(self):
        return f"<ModelExperiment(name={self.experiment_name}, type={self.model_type}, status={self.status})>"

"""
TripSense AI - Model Experiment Tracking

Track ML model experiments, parameters, and metrics.
"""

from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.sql import func
import uuid

from database import Base


class ModelExperiment(Base):
    """Model experiment tracking for ML pipeline."""
    
    __tablename__ = "model_experiments"
    
    # Primary key - SQLite compatible String UUID
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False
    )
    
    # Experiment details
    experiment_name = Column(String(255), nullable=False)
    model_type = Column(String(50), nullable=False)  # e.g., "collaborative", "content", "hybrid"
    
    # Configuration
    parameters = Column(JSON, nullable=True)  # Hyperparameters used
    metrics = Column(JSON, nullable=True)  # Evaluation metrics (precision, recall, etc.)
    
    # Metadata
    dataset_version = Column(String(50), nullable=True)
    training_date = Column(DateTime, server_default=func.now(), nullable=False)
    status = Column(String(50), nullable=False)  # e.g., "training", "completed", "failed"
    notes = Column(String(1000), nullable=True)
    
    def __repr__(self):
        return f"<ModelExperiment(name={self.experiment_name}, type={self.model_type}, status={self.status})>"

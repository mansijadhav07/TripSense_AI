"""
TripSense AI - Application Configuration

Loads and validates environment variables for the FastAPI application.
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pathlib import Path

# Find project root (.env location)
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
env_file = project_root / ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "TripSense AI"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "info"
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"
    
    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:3001"]
    
    # Database
    database_url: str
    db_echo: bool = False
    
    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    
    # Data Paths
    raw_data_path: str = "./data/raw/tripadvisor_reviews.csv"
    processed_data_path: str = "./data/processed"
    model_artifacts_path: str = "./artifacts"
    reports_path: str = "./data/reports"
    
    # ML Model Configuration
    als_rank: int = 10
    als_reg_param: float = 0.1
    als_max_iter: int = 10
    
    # Hybrid Model Weights
    weight_collaborative: float = 0.35
    weight_content: float = 0.30
    weight_aspect: float = 0.20
    weight_sentiment: float = 0.10
    weight_popularity: float = 0.05
    
    # Recommendation Settings
    default_top_n: int = 10
    min_reviews_for_popularity: int = 10
    
    # Feature Engineering
    tfidf_max_features: int = 500
    min_rating: float = 1.0
    max_rating: float = 5.0
    
    # Evaluation
    test_size: float = 0.2
    random_seed: int = 42
    precision_k: int = 10
    recall_k: int = 10
    ndcg_k: int = 10
    
    # Environment
    environment: str = "development"
    
    model_config = SettingsConfigDict(
        env_file=str(env_file),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        protected_namespaces=('settings_',)
    )
    
    def validate_weights(self) -> None:
        """Validate that hybrid model weights sum to approximately 1.0"""
        total = (
            self.weight_collaborative +
            self.weight_content +
            self.weight_aspect +
            self.weight_sentiment +
            self.weight_popularity
        )
        if not 0.95 <= total <= 1.05:
            raise ValueError(f"Hybrid model weights must sum to ~1.0, got {total}")
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Uses lru_cache to ensure settings are loaded only once.
    """
    settings = Settings()
    settings.validate_weights()
    return settings


# Export settings instance
settings = get_settings()

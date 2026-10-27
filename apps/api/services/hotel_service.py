"""
TripSense AI - Hotel Service

Loads hotel data from processed parquet files and provides
search, detail, and similarity functionality.
"""

import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from functools import lru_cache

from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

CATALOG_COLUMNS = ["hotel_id", "name", "location", "avg_rating", "review_count"]


class HotelDataStore:
    """In-memory hotel data store loaded from processed Parquet files."""

    _instance: Optional["HotelDataStore"] = None
    _loaded: bool = False

    def __init__(self, data_dir: str = None):
        self.data_dir = Path(data_dir) if data_dir else self._find_data_dir()
        self.hotels_df: Optional[pd.DataFrame] = None
        self.hotel_index: Dict[str, Dict] = {}
        self.data_source = "unavailable"
        self._load_hotels()

    def _find_data_dir(self) -> Path:
        """Find the processed data directory."""
        candidates = [
            Path(__file__).resolve().parent.parent.parent.parent / "data" / "processed",
            Path("data/processed"),
            Path("../../data/processed"),
        ]
        for path in candidates:
            if path.exists():
                return path
        return candidates[0]

    @staticmethod
    def _looks_like_ids(df: pd.DataFrame) -> bool:
        """True only if hotel_id values look like identifiers (short, no spaces, repeated across reviews)."""
        ids = df["hotel_id"].astype(str)
        sample = ids.head(200)
        return not (sample.str.len().gt(50).any() or sample.str.contains(" ").any() or sample.str.startswith(("-", '"')).any())

    def _use_fallback(self, reason: str) -> None:
        from config import settings
        if settings.allow_synthetic_data:
            logger.warning(f"{reason} ALLOW_SYNTHETIC_DATA=true -> serving SYNTHETIC demo hotels.")
            self.hotels_df = self._generate_synthetic_hotels()
            self.data_source = "synthetic-demo"
        else:
            logger.error(f"{reason} No hotel catalogue is available; catalogue endpoints will return 503.")
            self.hotels_df = pd.DataFrame(columns=CATALOG_COLUMNS)
            self.data_source = "unavailable"
        self._build_hotel_index()
        self._loaded = self.data_source != "unavailable"

    def _load_hotels(self) -> None:
        """Load the hotel catalogue; never silently substitute synthetic data."""
        try:
            for name in ("features/hotel_features_complete.parquet", "features/hotel_features.parquet"):
                path = self.data_dir / name
                if not path.exists():
                    continue
                df = pd.read_parquet(path)
                if df.empty or "hotel_id" not in df.columns or not self._looks_like_ids(df):
                    return self._use_fallback(f"{path} does not contain valid hotel identifiers.")
                self.hotels_df = self._normalize_hotel_df(df)
                self.data_source = "pipeline"
                self._build_hotel_index()
                self._loaded = True
                return
            self._use_fallback("No hotel feature files found.")
        except Exception as e:
            self._use_fallback(f"Failed to load hotel data ({e}).")

    def _normalize_hotel_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize column names and types."""
        # Map common column name variations
        col_map = {
            "offering_id": "hotel_id",
            "hotelId": "hotel_id",
            "hotel_name": "name",
            "hotel_avg_rating": "avg_rating",
            "avg_rating": "avg_rating",
            "rating": "avg_rating",
            "hotel_review_count": "review_count",
            "num_reviews": "review_count",
            "total_reviews": "review_count",
            "hotel_avg_cleanliness": "cleanliness",
            "hotel_avg_service": "service",
            "hotel_avg_location": "location_score",
            "hotel_avg_rooms": "rooms",
            "hotel_avg_value": "value",
            "hotel_avg_sentiment": "sentiment_score",
        }

        # Rename matching columns
        df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns and v not in df.columns})

        # Ensure hotel_id exists
        if "hotel_id" not in df.columns:
            df["hotel_id"] = [f"hotel_{i}" for i in range(len(df))]

        df["hotel_id"] = df["hotel_id"].astype(str)

        # Ensure avg_rating
        if "avg_rating" not in df.columns:
            if "cleanliness" in df.columns:
                aspect_cols = [c for c in ["cleanliness", "service", "location", "rooms", "value"] if c in df.columns]
                df["avg_rating"] = df[aspect_cols].mean(axis=1).round(2)
            else:
                df["avg_rating"] = 3.5

        df["avg_rating"] = pd.to_numeric(df["avg_rating"], errors="coerce").fillna(3.5).clip(1, 5)

        if "review_count" not in df.columns:
            df["review_count"] = 10

        df["review_count"] = pd.to_numeric(df["review_count"], errors="coerce").fillna(10).astype(int)

        # Use catalogue names; only synthesise one if the source has no usable name column
        if "name" not in df.columns or df["name"].isna().all() or df["name"].astype(str).str.len().gt(80).any():
            df["name"] = df["hotel_id"].apply(lambda x: f"Hotel {x.replace('hotel_', '').replace('_', ' ').title()}")

        # Add location if missing
        if "location" not in df.columns:
            df["location"] = "Various"

        return df

    def _generate_synthetic_hotels(self) -> pd.DataFrame:
        """Generate synthetic hotel data for testing."""
        import random
        random.seed(42)
        np.random.seed(42)

        destinations = ["Paris", "London", "New York", "Tokyo", "Rome", "Barcelona", "Sydney", "Dubai"]
        hotel_names = ["Grand Palace", "Royal Inn", "Harbor View", "City Center", "The Landmark",
                       "Ocean Breeze", "Mountain Retreat", "Boutique Stay", "Luxury Suites", "Comfort Lodge"]

        n = 200
        hotels = []
        for i in range(n):
            dest = random.choice(destinations)
            name = random.choice(hotel_names)
            hotels.append({
                "hotel_id": f"hotel_{i}",
                "name": f"{name} {dest}",
                "location": dest,
                "avg_rating": round(random.uniform(2.5, 5.0), 1),
                "review_count": random.randint(20, 5000),
                "cleanliness": round(random.uniform(2.5, 5.0), 1),
                "service": round(random.uniform(2.5, 5.0), 1),
                "location_score": round(random.uniform(2.5, 5.0), 1),
                "rooms": round(random.uniform(2.5, 5.0), 1),
                "value": round(random.uniform(2.5, 5.0), 1),
                "sentiment_score": round(random.uniform(-0.5, 1.0), 3),
            })

        return pd.DataFrame(hotels)

    def _build_hotel_index(self) -> None:
        """Build an in-memory index for O(1) hotel lookups."""
        if self.hotels_df is None:
            return

        for _, row in self.hotels_df.iterrows():
            hotel_dict = {}
            for col in self.hotels_df.columns:
                val = row[col]
                if pd.isna(val) if not isinstance(val, (list, dict)) else False:
                    hotel_dict[col] = None
                elif hasattr(val, "item"):
                    hotel_dict[col] = val.item()
                else:
                    hotel_dict[col] = val
            self.hotel_index[str(row["hotel_id"])] = hotel_dict

        logger.info(f"✅ Hotel index built: {len(self.hotel_index)} hotels")

    def search(
        self,
        destination: Optional[str] = None,
        min_rating: Optional[float] = None,
        max_rating: Optional[float] = None,
        min_reviews: Optional[int] = None,
        sort_by: str = "avg_rating",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Dict], int]:
        """Search hotels with filters and pagination."""
        if self.hotels_df is None:
            return [], 0

        df = self.hotels_df.copy()

        # Apply filters
        if destination:
            dest_lower = destination.lower()
            if "location" in df.columns:
                df = df[df["location"].astype(str).str.lower().str.contains(dest_lower, na=False)]
            if "name" in df.columns and len(df) == 0:
                df = self.hotels_df[self.hotels_df["name"].astype(str).str.lower().str.contains(dest_lower, na=False)]

        if min_rating is not None:
            df = df[df["avg_rating"] >= min_rating]

        if max_rating is not None:
            df = df[df["avg_rating"] <= max_rating]

        if min_reviews is not None:
            df = df[df["review_count"] >= min_reviews]

        total = len(df)

        # Sort
        sort_col = sort_by if sort_by in df.columns else "avg_rating"
        ascending = sort_order == "asc"
        try:
            df = df.sort_values(sort_col, ascending=ascending)
        except Exception:
            pass

        # Paginate
        start = (page - 1) * page_size
        end = start + page_size
        page_df = df.iloc[start:end]

        hotels = []
        for _, row in page_df.iterrows():
            hotels.append(self._row_to_dict(row))

        return hotels, total

    def get_by_id(self, hotel_id: str) -> Optional[Dict]:
        """Get hotel details by ID."""
        return self.hotel_index.get(hotel_id)

    def get_similar(self, hotel_id: str, top_n: int = 5) -> List[Dict]:
        """Hotels closest in the content model's feature space (review text, destination, style, aspects)."""
        if hotel_id not in self.hotel_index:
            return []
        try:
            from services.ml_model_loader import get_model_store
            cm = get_model_store().require().content
        except Exception:
            return []
        if hotel_id not in cm.hotel_idx:
            return []
        sims = cm.Vn @ cm.Vn[cm.hotel_idx[hotel_id]]
        out = []
        for j in np.argsort(-sims):
            other = cm.hotel_ids[j]
            if other != hotel_id and other in self.hotel_index:
                out.append({**self.hotel_index[other], "similarity": round(float(sims[j]), 4)})
                if len(out) >= top_n:
                    break
        return out

    def get_popular(self, top_n: int = 10) -> List[Dict]:
        """Get most popular hotels."""
        if self.hotels_df is None:
            return []

        df = self.hotels_df.copy()
        if "review_count" in df.columns and "avg_rating" in df.columns:
            df["pop_score"] = (
                0.5 * np.log1p(df["review_count"].fillna(0)) +
                0.5 * df["avg_rating"].fillna(0)
            )
            df = df.sort_values("pop_score", ascending=False)
        
        return [self._row_to_dict(row) for _, row in df.head(top_n).iterrows()]

    def _row_to_dict(self, row) -> Dict:
        """Convert DataFrame row to dict, handling NaN."""
        result = {}
        for col in row.index:
            val = row[col]
            if pd.isna(val) if not isinstance(val, (list, dict, str)) else False:
                result[col] = None
            elif hasattr(val, "item"):
                result[col] = val.item()
            else:
                result[col] = val
        return result

    @property
    def total_hotels(self) -> int:
        return len(self.hotels_df) if self.hotels_df is not None else 0

    @property
    def is_loaded(self) -> bool:
        return self._loaded


# Module-level singleton
_hotel_store: Optional[HotelDataStore] = None


def require_catalog() -> None:
    """FastAPI dependency: 503 when no valid hotel catalogue is loaded."""
    store = get_hotel_store()
    if not store.is_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Hotel catalogue unavailable: the processed data has no valid hotel identifiers. "
                   "Run the pipeline on a dataset with real hotel IDs (see README), or set "
                   "ALLOW_SYNTHETIC_DATA=true for a clearly-labelled demo.",
        )


def get_hotel_store() -> HotelDataStore:
    """Get or create the hotel data store singleton."""
    global _hotel_store
    if _hotel_store is None:
        _hotel_store = HotelDataStore()
    return _hotel_store

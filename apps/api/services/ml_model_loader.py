"""
TripSense AI - ML Model Loader
==============================
Loads the fitted recommender bundle (artifacts/models/recommender.pkl) written by
ml/scripts/train_and_evaluate.py. The model classes live in ml/recsys/core.py and
are shared with training/evaluation, so serving uses exactly what was evaluated.

There are no heuristic fallbacks: if the artifact is missing the models report
unavailable and the API returns 503 with instructions.
"""
import logging
import pickle
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:          # makes `ml.recsys` importable (needed to unpickle)
    sys.path.insert(0, str(REPO_ROOT))

ARTIFACT_PATH = REPO_ROOT / "artifacts" / "models" / "recommender.pkl"


class ModelUnavailable(RuntimeError):
    """Raised when the trained model artifact cannot be loaded."""


class ModelStore:
    def __init__(self, path: Path = ARTIFACT_PATH):
        self.path = path
        self.recommender = None
        self.error: Optional[str] = None
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            self.error = (f"Model artifact not found at {self.path}. Run "
                          "`python ml/scripts/generate_synthetic_dataset.py` then "
                          "`python ml/scripts/train_and_evaluate.py`.")
            logger.error(self.error)
            return
        try:
            with open(self.path, "rb") as f:
                self.recommender = pickle.load(f)
            logger.info("Loaded recommender (CF-SVD, content, sentiment, hybrid) from %s", self.path)
        except Exception as e:                      # noqa: BLE001 - surfaced via .error / 503
            self.error = f"Could not load {self.path}: {e}"
            logger.error(self.error)

    @property
    def available(self) -> bool:
        return self.recommender is not None

    # Kept for health/startup logging; all four models come from the one bundle.
    cf_available = content_available = sentiment_available = available

    def require(self):
        if not self.available:
            raise ModelUnavailable(self.error or "Models not loaded")
        return self.recommender


_model_store: Optional[ModelStore] = None


def get_model_store() -> ModelStore:
    global _model_store
    if _model_store is None:
        _model_store = ModelStore()
    return _model_store

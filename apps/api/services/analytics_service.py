"""
TripSense AI - Analytics Service
================================
Serves dataset statistics and held-out model metrics. Nothing is hardcoded:
  * ml/evaluation/results/synthetic_evaluation.json  <- ml/scripts/train_and_evaluate.py
  * data/processed/dataset_stats.json                <- ml/scripts/generate_synthetic_dataset.py
  * ml/evaluation/results/spark_benchmark.json       <- ml/evaluation/benchmark_spark.py
If a file is missing the endpoint answers 503 telling the operator which script to run.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

MODEL_DISPLAY = [
    ("popularity", "Popularity Baseline", "non_personalized",
     "Non-personalised baseline: Bayesian-average rating."),
    ("collaborative_filtering_svd", "Collaborative Filtering (SVD)", "personalized",
     "Matrix factorisation: scikit-surprise SVD for rating prediction + truncated SVD of the interaction matrix for ranking."),
    ("content_based", "Content-Based", "personalized",
     "Cosine similarity between a user profile and hotel vectors (review-text TF-IDF, destination, style, amenities, aspect quality)."),
    ("sentiment_analysis", "Sentiment Analysis", "text",
     "TF-IDF + logistic regression classifying review text as negative / neutral / positive; for ranking, hotels are ordered by mean (shrunk, out-of-fold) review sentiment."),
    ("hybrid_ensemble", "Hybrid Ensemble", "ensemble",
     "Validation-tuned blend of CF, content and sentiment scores."),
    ("random_baseline", "Random Baseline", "non_personalized",
     "Seeded random ranking, the floor every model must beat."),
]


class ResultsUnavailable(RuntimeError):
    """Raised when the pipeline has not produced the requested results file."""


class AnalyticsService:
    """Serves analytics data from ML evaluation results."""

    def __init__(self, evaluation_dir: Optional[Path] = None):
        self.project_root = self._find_project_root()
        env_dir = os.environ.get("TRIPSENSE_EVALUATION_DIR")
        self.evaluation_dir = Path(
            evaluation_dir or env_dir or (self.project_root / "ml" / "evaluation" / "results")
        )

    @staticmethod
    def _find_project_root() -> Path:
        here = Path(__file__).resolve()
        for p in here.parents:
            if (p / "ml").exists() and (p / "apps").exists():
                return p
        return Path.cwd()

    def _load(self, name: str) -> Dict[str, Any]:
        path = self.evaluation_dir / name
        if not path.exists():
            raise ResultsUnavailable(
                f"{name} not found at {path}. "
                "Run `python ml/scripts/train_and_evaluate.py` first."
            )
        with open(path) as f:
            return json.load(f)

    def get_dataset_stats(self) -> Dict[str, Any]:
        stats_path = self.project_root / "data" / "processed" / "dataset_stats.json"
        if not stats_path.exists():
            raise ResultsUnavailable(f"{stats_path} not found. Run `python ml/scripts/generate_synthetic_dataset.py`.")
        stats = json.loads(stats_path.read_text())
        stats.update({
            "data_source": "Synthetic (reproducible, seed=%s)" % stats.get("seed", 42),
            "hotel_id_is_unique_per_row": False,
            "dataset_note": "Synthetic dataset with learnable user/hotel structure; see ml/scripts/generate_synthetic_dataset.py.",
        })
        return stats

    def get_model_performance(self) -> Dict[str, Any]:
        data = self._load("synthetic_evaluation.json")
        raw = data["models"]
        info = data["dataset_info"]
        k = info["k"]
        models: List[Dict[str, Any]] = []
        for key, name, mtype, desc in MODEL_DISPLAY:
            m = raw.get(key)
            if m is None:
                continue
            e: Dict[str, Any] = {"model_name": name, "model_type": mtype, "description": desc,
                                 "status": "evaluated", "reason": None, "k": k}
            if mtype == "text":
                # Ranking metrics come from ranking hotels by their mean review sentiment
                # (same protocol as every other model); classification metrics are kept alongside.
                r = m.get("ranking_by_hotel_sentiment") or {}
                e.update(precision_at_10=r.get("precision_at_k"), recall_at_10=r.get("recall_at_k"),
                         ndcg_at_10=r.get("ndcg_at_k"), hit_rate=r.get("hit_rate_at_k"),
                         coverage=r.get("catalog_coverage"), evaluated_users=r.get("evaluated_users"),
                         text_metrics={f: m.get(f) for f in (
                             "accuracy", "macro_f1", "majority_class_accuracy", "majority_class_macro_f1",
                             "auc_positive_vs_rest", "n_test_reviews")})
            else:
                e.update(precision_at_10=m["precision_at_k"], recall_at_10=m["recall_at_k"], ndcg_at_10=m["ndcg_at_k"],
                         hit_rate=m["hit_rate_at_k"], coverage=m.get("catalog_coverage"),
                         evaluated_users=m.get("evaluated_users"))
                if "rmse" in m:
                    e["rating_metrics"] = {f: m.get(f) for f in ("rmse", "mae", "baseline_global_mean_rmse",
                                                                   "baseline_global_mean_mae")}
                if m.get("weights"):
                    e["weights"] = m["weights"]
            models.append(e)
        return {
            "models": models,
            "evaluation_timestamp": data.get("evaluated_at"),
            "dataset_info": info,
            "leakage_checks": data.get("leakage_checks"),
            "tuning": data.get("tuning"),
            "note": (f"All metrics are computed on held-out test reviews ({info['split']}). {info['evaluation_protocol']}"),
        }

    def get_spark_benchmarks(self) -> List[Dict[str, Any]]:
        """Return Spark vs Pandas performance benchmarks."""
        data = self._load("spark_benchmark.json")
        benchmarks = data["benchmarks"] if isinstance(data, dict) else data
        out = []
        for b in benchmarks:
            b = dict(b)
            b["speedup"] = round(b["pandas_seconds"] / b["spark_seconds"], 3) if b.get("spark_seconds") else None
            b["winner"] = "Spark" if (b.get("spark_seconds") or 999) < (b.get("pandas_seconds") or 0) else "Pandas"
            out.append(b)
        return out

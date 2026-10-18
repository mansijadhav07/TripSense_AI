"""
TripSense AI - Real Content-Based Model Evaluation

Compute actual NDCG@10, Precision@10, Recall@10, Hit Rate on held-out test set.
Uses real model predictions, not synthetic data or fallback values.
"""

import logging
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Set
import pandas as pd
import numpy as np
from collections import defaultdict
from datetime import datetime
from sklearn.preprocessing import normalize
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ContentBasedEvaluator:
    """Evaluates Content-Based model on test set."""
    
    def __init__(self):
        project_root = Path(__file__).resolve().parent.parent.parent
        self.data_dir = project_root / "data" / "processed" / "splits_fixed"
        self.output_dir = Path(__file__).parent / "results"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.k = 10
        self.relevance_threshold = 4.0
        
        self.test_df = None
        self.hotel_df = None
        self.ground_truth = {}
    
    def load_data(self) -> bool:
        """Load test interactions and hotel features."""
        logger.info("Loading data...")
        try:
            test_path = self.data_dir / "test_interactions.parquet"
            hotel_path = self.data_dir / "hotel_features_complete.parquet"
            
            self.test_df = pd.read_parquet(test_path)
            self.hotel_df = pd.read_parquet(hotel_path)
            
            logger.info(f"✓ Test: {len(self.test_df)} interactions")
            logger.info(f"✓ Hotels: {len(self.hotel_df)} with {len(self.hotel_df.columns)} features")
            return True
        except Exception as e:
            logger.error(f"Load failed: {e}")
            return False
    
    def build_ground_truth(self) -> None:
        """Build ground truth: user -> set of relevant hotels."""
        logger.info(f"Building ground truth (threshold={self.relevance_threshold})...")
        
        self.ground_truth = defaultdict(set)
        relevant = self.test_df[self.test_df['overall'] >= self.relevance_threshold]
        
        for _, row in relevant.iterrows():
            self.ground_truth[row['user_id']].add(row['hotel_id'])
        
        users_with_relevant = len(self.ground_truth)
        total_relevant = sum(len(h) for h in self.ground_truth.values())
        
        logger.info(f"✓ {users_with_relevant} users with relevant items")
        logger.info(f"✓ {total_relevant} total relevant items")
    
    def get_user_seed_hotels(self) -> Dict[str, List[str]]:
        """Get user's history (seed hotels for content-based)."""
        user_histories = defaultdict(list)
        
        for _, row in self.test_df.iterrows():
            user_histories[row['user_id']].append(row['hotel_id'])
        
        return dict(user_histories)
    
    def get_hotel_features(self, feature_cols: List[str]) -> Dict[str, np.ndarray]:
        """Get feature vectors for all hotels."""
        hotel_features = {}
        
        for _, row in self.hotel_df.iterrows():
            hotel_id = row['hotel_id']
            features = row[feature_cols].values.astype(float)
            
            # Handle NaN
            features = np.nan_to_num(features, nan=0.0)
            
            # Normalize
            norm = np.linalg.norm(features)
            if norm > 0:
                features = features / norm
            
            hotel_features[hotel_id] = features
        
        logger.info(f"✓ Features for {len(hotel_features)} hotels")
        return hotel_features
    
    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Compute cosine similarity."""
        return float(np.dot(vec1, vec2))
    
    def get_recommendations(self, 
                           user_id: str,
                           user_histories: Dict[str, List[str]],
                           hotel_features: Dict[str, np.ndarray],
                           feature_cols: List[str]) -> List[str]:
        """Get top-k recommendations for user."""
        
        # Get user's seed hotels
        seed_hotels = user_histories.get(user_id, [])
        seed_hotels = [h for h in seed_hotels if h in hotel_features]
        
        if not seed_hotels:
            # Cold start: return empty
            return []
        
        # Compute average seed hotel features
        seed_features = np.mean([hotel_features[h] for h in seed_hotels], axis=0)
        
        # Find similar hotels
        similarities = {}
        for hotel_id, features in hotel_features.items():
            if hotel_id not in seed_hotels:  # Don't recommend seed items
                sim = self.cosine_similarity(seed_features, features)
                similarities[hotel_id] = sim
        
        # Get top-k
        top_k = sorted(similarities.items(), key=lambda x: x[1], reverse=True)[:self.k]
        return [h for h, _ in top_k]
    
    def compute_metrics(self) -> Dict[str, Any]:
        """Compute evaluation metrics."""
        logger.info("\nEvaluating Content-Based model...")
        
        # Get feature columns
        numeric_cols = self.hotel_df.select_dtypes(include=[np.number]).columns.tolist()
        if 'hotel_id' in numeric_cols:
            numeric_cols.remove('hotel_id')
        
        logger.info(f"Using {len(numeric_cols)} numeric features")
        
        # Get hotel features
        hotel_features = self.get_hotel_features(numeric_cols)
        user_histories = self.get_user_seed_hotels()
        
        # Evaluate
        ndcg_scores = []
        precision_scores = []
        recall_scores = []
        hits = 0
        evaluated_users = 0
        
        for user_id, relevant_hotels in self.ground_truth.items():
            if len(relevant_hotels) == 0:
                continue
            
            # Get recommendations
            recs = self.get_recommendations(user_id, user_histories, hotel_features, numeric_cols)
            
            if not recs:
                # Cold start case
                ndcg_scores.append(0.0)
                precision_scores.append(0.0)
                recall_scores.append(0.0)
                evaluated_users += 1
                continue
            
            # Compute metrics
            # Precision@k
            num_relevant = len(set(recs) & relevant_hotels)
            precision = num_relevant / self.k if self.k > 0 else 0.0
            precision_scores.append(precision)
            
            # Recall@k
            recall = num_relevant / len(relevant_hotels) if len(relevant_hotels) > 0 else 0.0
            recall_scores.append(recall)
            
            # NDCG@k (simplified)
            dcg = 0.0
            for i, hotel in enumerate(recs):
                if hotel in relevant_hotels:
                    dcg += 1.0 / np.log2(i + 2)
                    if i == 0:
                        hits += 1
            
            # Ideal DCG
            idcg = sum(1.0 / np.log2(i + 2) for i in range(min(len(relevant_hotels), self.k)))
            ndcg = dcg / idcg if idcg > 0 else 0.0
            ndcg_scores.append(ndcg)
            
            evaluated_users += 1
            
            if evaluated_users % 500 == 0:
                logger.info(f"  Evaluated {evaluated_users} users...")
        
        # Aggregate
        mean_ndcg = np.mean(ndcg_scores) if ndcg_scores else 0.0
        mean_precision = np.mean(precision_scores) if precision_scores else 0.0
        mean_recall = np.mean(recall_scores) if recall_scores else 0.0
        hit_rate = hits / evaluated_users if evaluated_users > 0 else 0.0
        
        logger.info(f"\n✓ Evaluated {evaluated_users} users")
        logger.info(f"  NDCG@{self.k}: {mean_ndcg:.4f}")
        logger.info(f"  Precision@{self.k}: {mean_precision:.4f}")
        logger.info(f"  Recall@{self.k}: {mean_recall:.4f}")
        logger.info(f"  Hit Rate: {hit_rate:.4f} ({hits} hits)")
        
        return {
            "model": "Content-Based Recommendation",
            "type": "personalized",
            "evaluation_timestamp": datetime.now().isoformat(),
            "num_users_evaluated": int(evaluated_users),
            "ndcg_at_10": float(mean_ndcg),
            "precision_at_10": float(mean_precision),
            "recall_at_10": float(mean_recall),
            "hit_rate": float(hit_rate),
            "configuration": {
                "k": self.k,
                "relevance_threshold": self.relevance_threshold,
                "num_features": len(numeric_cols),
                "features": numeric_cols[:5] + (["..."] if len(numeric_cols) > 5 else [])
            }
        }
    
    def run(self) -> Dict[str, Any]:
        """Run evaluation."""
        logger.info("="*80)
        logger.info("REAL CONTENT-BASED MODEL EVALUATION")
        logger.info("="*80)
        
        if not self.load_data():
            return {}
        
        self.build_ground_truth()
        
        results = self.compute_metrics()
        
        # Save
        output_file = self.output_dir / "content_based_evaluation_real.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"\n✓ Results saved to: {output_file}")
        logger.info("="*80 + "\n")
        
        return results


if __name__ == "__main__":
    evaluator = ContentBasedEvaluator()
    results = evaluator.run()
    
    if results:
        print("\nContent-Based Model Metrics:")
        print(f"  NDCG@10:    {results['ndcg_at_10']:.4f}")
        print(f"  Precision:  {results['precision_at_10']:.4f}")
        print(f"  Recall:     {results['recall_at_10']:.4f}")
        print(f"  Hit Rate:   {results['hit_rate']:.4f}")

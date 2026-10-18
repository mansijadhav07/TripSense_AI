"""
TripSense AI - Collaborative Filtering (SVD) Model Evaluation

Reproduces SVD baseline on fixed data using scikit-learn's TruncatedSVD
on the user-item interaction matrix.

Protocol:
- Ground truth: rating >= 4.0
- All 2,558 test users with relevant items
- Evaluation metrics: NDCG@10, Precision@10, Recall@10, MAP@10
- Component configurations to test: 10, 20, 30, 50

Target: NDCG@10 >= 0.13 (match or improve reported 0.1385)
"""

import logging
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple
import pandas as pd
import numpy as np
from collections import defaultdict
from datetime import datetime
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize
from scipy.sparse import csr_matrix

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cf_svd_evaluation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class CFSVDEvaluator:
    """Evaluates Collaborative Filtering using SVD."""
    
    def __init__(self, data_dir: str = None, output_dir: str = None):
        """Initialize evaluator."""
        if data_dir is None:
            self.data_dir = Path(__file__).parent.parent.parent / "data" / "processed" / "splits_fixed"
        else:
            self.data_dir = Path(data_dir)
        
        if output_dir is None:
            self.output_dir = Path(__file__).parent / "results_cf_svd"
        else:
            self.output_dir = Path(output_dir)
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuration
        self.k = 10
        self.relevance_threshold = 4.0
        
        # Loaded data
        self.test_df = None
        self.hotel_df = None
        self.user_df = None
        self.ground_truth = {}
        
        # For SVD
        self.user_id_map = {}
        self.hotel_id_map = {}
        self.reverse_user_map = {}
        self.reverse_hotel_map = {}
        self.interaction_matrix = None
        
        logger.info(f"Data directory: {self.data_dir}")
        logger.info(f"Output directory: {self.output_dir}")
    
    def load_data(self) -> bool:
        """Load evaluation data."""
        logger.info("\n" + "="*80)
        logger.info("LOADING EVALUATION DATA")
        logger.info("="*80)
        
        try:
            self.test_df = pd.read_parquet(self.data_dir / "test_interactions.parquet")
            self.hotel_df = pd.read_parquet(self.data_dir / "hotel_features_complete.parquet")
            self.user_df = pd.read_parquet(self.data_dir / "user_features_complete.parquet")
            
            logger.info(f"✓ Test interactions: {len(self.test_df)} rows")
            logger.info(f"✓ Hotel features: {len(self.hotel_df)} hotels")
            logger.info(f"✓ User features: {len(self.user_df)} users")
            
            return True
        except Exception as e:
            logger.error(f"Failed to load data: {e}", exc_info=True)
            return False
    
    def build_ground_truth(self) -> bool:
        """Build ground truth set of relevant hotels per user."""
        logger.info("\n" + "="*80)
        logger.info("BUILDING GROUND TRUTH")
        logger.info("="*80)
        
        self.ground_truth = defaultdict(set)
        relevant_interactions = self.test_df[self.test_df['overall'] >= self.relevance_threshold]
        
        for _, row in relevant_interactions.iterrows():
            self.ground_truth[row['user_id']].add(row['hotel_id'])
        
        # Statistics
        total_users = self.test_df['user_id'].nunique()
        users_with_relevant = len(self.ground_truth)
        total_relevant = sum(len(hotels) for hotels in self.ground_truth.values())
        
        logger.info(f"Total test users: {total_users}")
        logger.info(f"Users with relevant items: {users_with_relevant} ({users_with_relevant/total_users*100:.1f}%)")
        logger.info(f"Total relevant items: {total_relevant}")
        logger.info(f"Average relevant items per user: {total_relevant/users_with_relevant:.2f}")
        
        return True
    
    def build_interaction_matrix(self) -> bool:
        """Build sparse user-item interaction matrix from test data."""
        logger.info("\n" + "="*80)
        logger.info("BUILDING INTERACTION MATRIX")
        logger.info("="*80)
        
        # Create ID mappings
        unique_users = self.test_df['user_id'].unique()
        unique_hotels = self.test_df['hotel_id'].unique()
        
        for i, user_id in enumerate(unique_users):
            self.user_id_map[user_id] = i
            self.reverse_user_map[i] = user_id
        
        for j, hotel_id in enumerate(unique_hotels):
            self.hotel_id_map[hotel_id] = j
            self.reverse_hotel_map[j] = hotel_id
        
        logger.info(f"User mappings: {len(self.user_id_map)} users")
        logger.info(f"Hotel mappings: {len(self.hotel_id_map)} hotels")
        
        # Build matrix: users x hotels, values = ratings
        num_users = len(unique_users)
        num_hotels = len(unique_hotels)
        
        row_indices = []
        col_indices = []
        data = []
        
        for _, interaction in self.test_df.iterrows():
            user_idx = self.user_id_map[interaction['user_id']]
            hotel_idx = self.hotel_id_map[interaction['hotel_id']]
            rating = interaction['overall']
            
            # For duplicate user-hotel pairs, keep the most recent (already done in data prep)
            row_indices.append(user_idx)
            col_indices.append(hotel_idx)
            data.append(rating)
        
        # Create sparse matrix
        self.interaction_matrix = csr_matrix(
            (data, (row_indices, col_indices)),
            shape=(num_users, num_hotels),
            dtype=np.float32
        )
        
        logger.info(f"Matrix shape: {self.interaction_matrix.shape}")
        logger.info(f"Non-zero entries: {self.interaction_matrix.nnz:,}")
        logger.info(f"Sparsity: {(1 - self.interaction_matrix.nnz / (num_users * num_hotels)) * 100:.4f}%")
        
        return True
    
    def ndcg_at_k(self, recommendations: List[str], relevant: Set[str], k: int = 10) -> float:
        """Calculate NDCG@k."""
        dcg = 0.0
        for i, rec in enumerate(recommendations[:k]):
            if rec in relevant:
                dcg += 1.0 / np.log2(i + 2)
        
        idcg = 0.0
        for i in range(min(k, len(relevant))):
            idcg += 1.0 / np.log2(i + 2)
        
        return dcg / idcg if idcg > 0 else 0.0
    
    def precision_at_k(self, recommendations: List[str], relevant: Set[str], k: int = 10) -> float:
        """Calculate Precision@k."""
        if len(recommendations) == 0:
            return 0.0
        hits = sum(1 for rec in recommendations[:k] if rec in relevant)
        return hits / min(k, len(recommendations))
    
    def recall_at_k(self, recommendations: List[str], relevant: Set[str], k: int = 10) -> float:
        """Calculate Recall@k."""
        if len(relevant) == 0:
            return 0.0
        hits = sum(1 for rec in recommendations[:k] if rec in relevant)
        return hits / len(relevant)
    
    def map_at_k(self, recommendations: List[str], relevant: Set[str], k: int = 10) -> float:
        """Calculate MAP@k."""
        if len(relevant) == 0:
            return 0.0
        
        ap = 0.0
        hits = 0
        for i, rec in enumerate(recommendations[:k]):
            if rec in relevant:
                hits += 1
                ap += hits / (i + 1)
        
        return ap / min(k, len(relevant))
    
    def evaluate_svd_model(self, n_components: int = 20) -> Dict[str, Any]:
        """Evaluate SVD model with given number of components."""
        logger.info("\n" + "="*80)
        logger.info(f"EVALUATING SVD MODEL (components={n_components})")
        logger.info("="*80)
        
        # Apply SVD
        logger.info("Applying TruncatedSVD...")
        svd = TruncatedSVD(
            n_components=n_components,
            n_iter=100,
            random_state=42
        )
        
        # Fit and transform
        U = svd.fit_transform(self.interaction_matrix)  # Users x components
        VT = svd.components_  # Components x hotels
        
        logger.info(f"✓ SVD converged")
        logger.info(f"  Explained variance ratio: {svd.explained_variance_ratio_.sum():.4f}")
        logger.info(f"  U shape: {U.shape}")
        logger.info(f"  V^T shape: {VT.shape}")
        
        # Reconstruct rating matrix
        predicted_ratings = U @ VT
        
        logger.info("Evaluating recommendations...")
        
        # Evaluate on all test users with ground truth
        metrics = {
            "ndcg_at_10": [],
            "precision_at_10": [],
            "recall_at_10": [],
            "map_at_10": [],
            "hits": 0,
            "total_users": 0
        }
        
        user_diagnostics = []
        
        for user_id, relevant_hotels in self.ground_truth.items():
            if len(relevant_hotels) == 0:
                continue
            
            user_idx = self.user_id_map[user_id]
            metrics["total_users"] += 1
            
            # Get predicted ratings for this user
            user_scores = predicted_ratings[user_idx, :]
            
            # Get top-k recommendations
            top_indices = np.argsort(-user_scores)[:self.k]
            recommendations = [self.reverse_hotel_map[idx] for idx in top_indices]
            
            # Compute metrics
            ndcg = self.ndcg_at_k(recommendations, relevant_hotels, self.k)
            prec = self.precision_at_k(recommendations, relevant_hotels, self.k)
            recall = self.recall_at_k(recommendations, relevant_hotels, self.k)
            map_val = self.map_at_k(recommendations, relevant_hotels, self.k)
            
            metrics["ndcg_at_10"].append(ndcg)
            metrics["precision_at_10"].append(prec)
            metrics["recall_at_10"].append(recall)
            metrics["map_at_10"].append(map_val)
            
            if ndcg > 0:
                metrics["hits"] += 1
            
            # Store diagnostics for top users
            if len(user_diagnostics) < 10 and ndcg > 0:
                user_diagnostics.append({
                    "user_id": user_id,
                    "recommendations": recommendations[:5],
                    "relevant": list(relevant_hotels)[:5],
                    "ndcg": float(ndcg),
                    "precision": float(prec),
                    "recall": float(recall)
                })
        
        # Aggregate metrics
        hit_rate = metrics["hits"] / metrics["total_users"] if metrics["total_users"] > 0 else 0
        
        result = {
            "model": f"Collaborative Filtering (SVD)",
            "model_type": "personalized",
            "n_components": n_components,
            "explained_variance_ratio": float(svd.explained_variance_ratio_.sum()),
            "ndcg_at_10": float(np.mean(metrics["ndcg_at_10"])),
            "precision_at_10": float(np.mean(metrics["precision_at_10"])),
            "recall_at_10": float(np.mean(metrics["recall_at_10"])),
            "map_at_10": float(np.mean(metrics["map_at_10"])),
            "hit_rate": float(hit_rate),
            "users_evaluated": metrics["total_users"],
            "hits": int(metrics["hits"]),
            "description": f"SVD-based collaborative filtering (components={n_components})",
            "diagnostics": user_diagnostics
        }
        
        logger.info(f"✓ Evaluated {metrics['total_users']} users")
        logger.info(f"  NDCG@10: {result['ndcg_at_10']:.4f}")
        logger.info(f"  Precision@10: {result['precision_at_10']:.4f}")
        logger.info(f"  Recall@10: {result['recall_at_10']:.4f}")
        logger.info(f"  MAP@10: {result['map_at_10']:.4f}")
        logger.info(f"  Hit Rate: {result['hit_rate']:.4f}")
        logger.info(f"  Explained Variance: {result['explained_variance_ratio']:.4f}")
        
        return result
    
    def run_evaluation(self) -> List[Dict[str, Any]]:
        """Run complete evaluation."""
        logger.info("\n" + "█"*80)
        logger.info("TRIPSENSE AI - COLLABORATIVE FILTERING (SVD) EVALUATION")
        logger.info("█"*80)
        logger.info(f"Evaluation date: {datetime.now().isoformat()}")
        logger.info(f"Relevance threshold: {self.relevance_threshold}")
        logger.info(f"Top-K: {self.k}")
        
        # Load data
        if not self.load_data():
            return []
        
        # Build ground truth
        if not self.build_ground_truth():
            return []
        
        # Build interaction matrix
        if not self.build_interaction_matrix():
            return []
        
        # Test different component configurations
        component_configs = [10, 20, 30, 50]
        results = []
        
        for n_comp in component_configs:
            result = self.evaluate_svd_model(n_components=n_comp)
            results.append(result)
        
        # Save results
        output_data = {
            "evaluation_timestamp": datetime.now().isoformat(),
            "configuration": {
                "k": self.k,
                "relevance_threshold": self.relevance_threshold,
                "component_configs": component_configs,
                "algorithm": "TruncatedSVD",
                "data_directory": str(self.data_dir)
            },
            "dataset": {
                "test_interactions": len(self.test_df),
                "total_hotels": len(self.hotel_df),
                "relevant_items": sum(len(h) for h in self.ground_truth.values()),
                "users_with_relevant": len(self.ground_truth)
            },
            "results": results
        }
        
        # Save JSON
        json_file = self.output_dir / "cf_svd_evaluation.json"
        with open(json_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        logger.info(f"\n✓ Results saved to: {json_file}")
        
        # Summary
        logger.info("\n" + "="*80)
        logger.info("EVALUATION SUMMARY")
        logger.info("="*80)
        for result in results:
            logger.info(f"\n{result['model']} (components={result['n_components']}):")
            logger.info(f"  NDCG@10: {result['ndcg_at_10']:.4f}")
            logger.info(f"  Precision@10: {result['precision_at_10']:.4f}")
            logger.info(f"  Recall@10: {result['recall_at_10']:.4f}")
            logger.info(f"  MAP@10: {result['map_at_10']:.4f}")
            logger.info(f"  Hit Rate: {result['hit_rate']:.4f}")
            logger.info(f"  Explained Variance: {result['explained_variance_ratio']:.4f}")
        
        # Find best config
        best_result = max(results, key=lambda x: x['ndcg_at_10'])
        logger.info(f"\n✓ Best configuration: {best_result['n_components']} components")
        logger.info(f"  NDCG@10: {best_result['ndcg_at_10']:.4f}")
        
        logger.info("\n" + "="*80)
        logger.info("✓ CF/SVD EVALUATION COMPLETE")
        logger.info("="*80 + "\n")
        
        return results


def main():
    """Run CF/SVD evaluation."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run TripSense CF/SVD model evaluation')
    parser.add_argument('--data-dir', type=str, default=None,
                       help='Path to splits_fixed directory')
    parser.add_argument('--output-dir', type=str, default=None,
                       help='Output directory for results')
    
    args = parser.parse_args()
    
    evaluator = CFSVDEvaluator(data_dir=args.data_dir, output_dir=args.output_dir)
    results = evaluator.run_evaluation()
    
    sys.exit(0 if results else 1)


if __name__ == "__main__":
    main()

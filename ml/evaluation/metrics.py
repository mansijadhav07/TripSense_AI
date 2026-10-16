"""
TripSense AI - Recommendation Evaluation Metrics

Implements standard recommendation system evaluation metrics:
- Precision@K
- Recall@K
- NDCG@K
- MAP (Mean Average Precision)
- Coverage
- Diversity

All metrics handle edge cases (empty lists, missing ground truth).
"""

import numpy as np
from typing import List, Dict, Optional, Set, Any
import logging

logger = logging.getLogger(__name__)


class RecommendationMetrics:
    """
    Collection of evaluation metrics for recommendation systems.
    
    All methods are static and work with item IDs (strings or ints).
    """

    @staticmethod
    def precision_at_k(recommended: List, relevant: Set, k: int) -> float:
        """
        Precision@K: Fraction of top-K recommendations that are relevant.
        
        Args:
            recommended: Ordered list of recommended items (top-K considered)
            relevant: Set of ground truth relevant items
            k: Cutoff rank
            
        Returns:
            Precision@K score in [0, 1]
        """
        if not recommended or not relevant or k <= 0:
            return 0.0
        
        top_k = recommended[:k]
        hits = sum(1 for item in top_k if item in relevant)
        return hits / min(k, len(top_k))

    @staticmethod
    def recall_at_k(recommended: List, relevant: Set, k: int) -> float:
        """
        Recall@K: Fraction of relevant items found in top-K.
        
        Args:
            recommended: Ordered list of recommended items
            relevant: Set of ground truth relevant items
            k: Cutoff rank
            
        Returns:
            Recall@K score in [0, 1]
        """
        if not recommended or not relevant or k <= 0:
            return 0.0
        
        top_k = recommended[:k]
        hits = sum(1 for item in top_k if item in relevant)
        return hits / len(relevant)

    @staticmethod
    def ndcg_at_k(recommended: List, relevant: Set, k: int) -> float:
        """
        NDCG@K: Normalized Discounted Cumulative Gain at rank K.
        
        Considers position of relevant items - earlier positions score higher.
        
        Args:
            recommended: Ordered list of recommended items
            relevant: Set of ground truth relevant items
            k: Cutoff rank
            
        Returns:
            NDCG@K score in [0, 1]
        """
        if not recommended or not relevant or k <= 0:
            return 0.0
        
        top_k = recommended[:k]
        
        # DCG: actual ranking
        dcg = 0.0
        for i, item in enumerate(top_k):
            if item in relevant:
                # +2 because position is 1-indexed
                dcg += 1.0 / np.log2(i + 2)
        
        # IDCG: ideal ranking (all relevant items at top)
        ideal_hits = min(len(relevant), k)
        idcg = sum(1.0 / np.log2(i + 2) for i in range(ideal_hits))
        
        if idcg == 0:
            return 0.0
        
        return dcg / idcg

    @staticmethod
    def average_precision(recommended: List, relevant: Set) -> float:
        """
        Average Precision: Mean of precision at each relevant item position.
        
        Args:
            recommended: Ordered list of recommended items
            relevant: Set of ground truth relevant items
            
        Returns:
            AP score in [0, 1]
        """
        if not recommended or not relevant:
            return 0.0
        
        hits = 0
        sum_precision = 0.0
        
        for i, item in enumerate(recommended):
            if item in relevant:
                hits += 1
                sum_precision += hits / (i + 1)
        
        return sum_precision / len(relevant)

    @staticmethod
    def mean_average_precision(
        all_recommended: List[List],
        all_relevant: List[Set]
    ) -> float:
        """
        MAP: Mean Average Precision across all users.
        
        Args:
            all_recommended: List of recommended item lists (one per user)
            all_relevant: List of relevant item sets (one per user)
            
        Returns:
            MAP score in [0, 1]
        """
        if not all_recommended or not all_relevant:
            return 0.0
        
        ap_scores = []
        for recommended, relevant in zip(all_recommended, all_relevant):
            if relevant:
                ap = RecommendationMetrics.average_precision(recommended, relevant)
                ap_scores.append(ap)
        
        return np.mean(ap_scores) if ap_scores else 0.0

    @staticmethod
    def map_score(recommended: Any, relevant: Any) -> float:
        """Alias for average_precision or mean_average_precision."""
        if isinstance(relevant, set):
            return RecommendationMetrics.average_precision(recommended, relevant)
        return RecommendationMetrics.mean_average_precision(recommended, relevant)

    @staticmethod
    def catalog_coverage(
        all_recommended: List[List],
        total_items: int
    ) -> float:
        """
        Coverage: Fraction of catalog covered by recommendations.
        
        Args:
            all_recommended: All recommendations given to all users
            total_items: Total number of items in catalog
            
        Returns:
            Coverage score in [0, 1]
        """
        if not all_recommended or total_items <= 0:
            return 0.0
        
        recommended_items: Set = set()
        for rec_list in all_recommended:
            recommended_items.update(rec_list)
        
        return len(recommended_items) / total_items

    @staticmethod
    def intra_list_diversity(recommended: List, similarity_matrix: Dict) -> float:
        """
        Intra-List Diversity: Average dissimilarity within recommendation list.
        
        Higher = more diverse recommendations.
        
        Args:
            recommended: List of recommended items
            similarity_matrix: Dict of {(item_a, item_b): similarity_score}
            
        Returns:
            Diversity score in [0, 1]
        """
        if len(recommended) < 2:
            return 0.0
        
        total_dissimilarity = 0.0
        pairs = 0
        
        for i in range(len(recommended)):
            for j in range(i + 1, len(recommended)):
                pair = (recommended[i], recommended[j])
                sim = similarity_matrix.get(pair, similarity_matrix.get((pair[1], pair[0]), 0.0))
                total_dissimilarity += (1.0 - sim)
                pairs += 1
        
        return total_dissimilarity / pairs if pairs > 0 else 0.0

    @staticmethod
    def evaluate_model(
        recommended_lists: List[List],
        relevant_sets: List[Set],
        k: int = 10
    ) -> Dict[str, float]:
        """
        Comprehensive evaluation of a model across all users.
        
        Args:
            recommended_lists: List of recommendation lists, one per user
            relevant_sets: List of ground truth item sets, one per user
            k: Cutoff rank for metrics
            
        Returns:
            Dictionary of metric name -> score
        """
        if not recommended_lists or not relevant_sets:
            logger.warning("Empty inputs to evaluate_model")
            return {
                "precision_at_k": 0.0,
                "recall_at_k": 0.0,
                "ndcg_at_k": 0.0,
                "map": 0.0,
                "num_users": 0
            }
        
        precision_scores = []
        recall_scores = []
        ndcg_scores = []
        ap_scores = []
        
        for recommended, relevant in zip(recommended_lists, relevant_sets):
            if not relevant:
                continue
            
            precision_scores.append(
                RecommendationMetrics.precision_at_k(recommended, relevant, k)
            )
            recall_scores.append(
                RecommendationMetrics.recall_at_k(recommended, relevant, k)
            )
            ndcg_scores.append(
                RecommendationMetrics.ndcg_at_k(recommended, relevant, k)
            )
            ap_scores.append(
                RecommendationMetrics.average_precision(recommended, relevant)
            )
        
        n_users = len(precision_scores)
        
        return {
            f"precision_at_{k}": float(np.mean(precision_scores)) if precision_scores else 0.0,
            f"recall_at_{k}": float(np.mean(recall_scores)) if recall_scores else 0.0,
            f"ndcg_at_{k}": float(np.mean(ndcg_scores)) if ndcg_scores else 0.0,
            "map": float(np.mean(ap_scores)) if ap_scores else 0.0,
            "num_users_evaluated": n_users
        }

    @staticmethod
    def hit_rate_at_k(recommended_lists: List[List], relevant_sets: List[Set], k: int = 10) -> float:
        """
        Hit Rate@K: Fraction of users who got at least one relevant item in top-K.
        
        Args:
            recommended_lists: All recommendation lists
            relevant_sets: All ground truth sets
            k: Cutoff rank
            
        Returns:
            Hit rate in [0, 1]
        """
        if not recommended_lists:
            return 0.0
        
        hits = 0
        for recommended, relevant in zip(recommended_lists, relevant_sets):
            top_k = set(recommended[:k])
            if top_k & relevant:
                hits += 1
        
        return hits / len(recommended_lists)

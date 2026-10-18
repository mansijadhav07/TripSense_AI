"""
TripSense AI - Content-Based Model Deep Dive

Comprehensive analysis of why Content-Based model isn't working well.

Key Questions:
1. Are hotel features properly populated?
2. Do similar hotels actually match user preferences?
3. Is the issue cold-start, feature quality, or algorithm?
4. Can we improve with better feature engineering?
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
from sklearn.preprocessing import normalize
from scipy.sparse import csr_matrix

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug_content_based.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class ContentBasedDebugger:
    """Analyzes content-based model in detail."""
    
    def __init__(self, data_dir: str = None, output_dir: str = None):
        """Initialize debugger."""
        if data_dir is None:
            self.data_dir = Path(__file__).parent.parent.parent / "data" / "processed" / "splits_fixed"
        else:
            self.data_dir = Path(data_dir)
        
        if output_dir is None:
            self.output_dir = Path(__file__).parent / "results_debug_content"
        else:
            self.output_dir = Path(output_dir)
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuration
        self.k = 10
        self.relevance_threshold = 4.0
        
        # Data
        self.test_df = None
        self.hotel_df = None
        self.ground_truth = {}
        
        logger.info(f"Data directory: {self.data_dir}")
        logger.info(f"Output directory: {self.output_dir}")
    
    def load_data(self) -> bool:
        """Load evaluation data."""
        logger.info("\n" + "="*80)
        logger.info("LOADING DATA")
        logger.info("="*80)
        
        try:
            self.test_df = pd.read_parquet(self.data_dir / "test_interactions.parquet")
            self.hotel_df = pd.read_parquet(self.data_dir / "hotel_features_complete.parquet")
            
            logger.info(f"✓ Test interactions: {len(self.test_df)} rows")
            logger.info(f"✓ Hotel features: {len(self.hotel_df)} hotels")
            logger.info(f"✓ Feature columns: {len(self.hotel_df.columns)}")
            
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
        
        users_with_relevant = len(self.ground_truth)
        total_relevant = sum(len(hotels) for hotels in self.ground_truth.values())
        
        logger.info(f"Users with relevant items: {users_with_relevant}")
        logger.info(f"Total relevant items: {total_relevant}")
        logger.info(f"Average per user: {total_relevant/users_with_relevant:.2f}")
        
        return True
    
    def analyze_feature_coverage(self) -> Dict[str, Any]:
        """Analyze feature population and coverage."""
        logger.info("\n" + "="*80)
        logger.info("FEATURE COVERAGE ANALYSIS")
        logger.info("="*80)
        
        # Get numeric features
        numeric_cols = self.hotel_df.select_dtypes(include=[np.number]).columns.tolist()
        if 'hotel_id' in numeric_cols:
            numeric_cols.remove('hotel_id')
        
        logger.info(f"Total numeric features: {len(numeric_cols)}")
        logger.info(f"Feature columns: {numeric_cols[:5]}... (showing first 5)")
        
        # Check missing values
        missing = self.hotel_df[numeric_cols].isna().sum()
        missing_pct = (missing / len(self.hotel_df) * 100)
        
        logger.info(f"\nMissing value analysis:")
        logger.info(f"  Total hotels: {len(self.hotel_df)}")
        logger.info(f"  Features with ANY missing: {(missing > 0).sum()}")
        logger.info(f"  Features with NO missing: {(missing == 0).sum()}")
        
        if (missing > 0).sum() > 0:
            logger.info(f"  Top 10 features by missing count:")
            for feat, count in missing.nlargest(10).items():
                pct = count / len(self.hotel_df) * 100
                logger.info(f"    {feat}: {count:,} / {len(self.hotel_df):,} ({pct:.1f}%)")
        
        # Check feature variance
        logger.info(f"\nFeature variance analysis (are features informative?):")
        feat_std = self.hotel_df[numeric_cols].std()
        feat_zero_var = (feat_std == 0).sum()
        
        logger.info(f"  Features with zero variance: {feat_zero_var}")
        logger.info(f"  Features with meaningful variance: {len(numeric_cols) - feat_zero_var}")
        
        if feat_zero_var > 0:
            logger.info(f"  Zero-variance features: {list(self.hotel_df[numeric_cols].columns[feat_std == 0])}")
        
        return {
            "total_features": len(numeric_cols),
            "features_with_missing": int((missing > 0).sum()),
            "features_with_zero_variance": int(feat_zero_var),
            "numeric_col_names": numeric_cols
        }
    
    def test_similarity_search(self, feature_cols: List[str]) -> Dict[str, Any]:
        """Test content-based similarity search on sample users."""
        logger.info("\n" + "="*80)
        logger.info("TESTING CONTENT-BASED SIMILARITY SEARCH")
        logger.info("="*80)
        
        # Get test users with history
        user_histories = defaultdict(list)
        for _, row in self.test_df.iterrows():
            user_histories[row['user_id']].append(row['hotel_id'])
        
        # Build feature matrix for hotels in test set
        test_hotels = set(self.test_df['hotel_id'].unique())
        hotel_feature_map = {}
        
        for hotel_id in test_hotels:
            hotel_features = self.hotel_df[self.hotel_df['hotel_id'] == hotel_id][feature_cols].values
            if hotel_features.shape[0] > 0:
                # Take first row and ensure shape is (n_features,)
                features = hotel_features[0, :]
                if features.shape[0] == len(feature_cols):
                    hotel_feature_map[hotel_id] = features
        
        logger.info(f"Hotels with features in test set: {len(hotel_feature_map)} / {len(test_hotels)}")
        
        # Test similarity on users with history
        similarity_results = []
        user_samples = []
        
        for user_id, relevant_hotels in self.ground_truth.items():
            if len(relevant_hotels) == 0:
                continue
            
            # Get user's history (seed hotels)
            seed_hotels = [h for h in user_histories[user_id] if h in hotel_feature_map]
            
            if len(seed_hotels) == 0:
                continue  # Cold start case
            
            # Compute average seed hotel features
            seed_features = np.mean([hotel_feature_map[h] for h in seed_hotels], axis=0)
            
            # Find similar hotels
            similarities = {}
            for hotel_id, features in hotel_feature_map.items():
                # Normalize and compute cosine similarity
                similarity = np.dot(seed_features, features) / (
                    np.linalg.norm(seed_features) * np.linalg.norm(features) + 1e-10
                )
                similarities[hotel_id] = similarity
            
            # Get top-k similar
            top_similar = sorted(similarities.items(), key=lambda x: x[1], reverse=True)[:self.k]
            top_hotels = [h for h, _ in top_similar]
            
            # Check overlap with ground truth
            matches = len(set(top_hotels) & relevant_hotels)
            
            similarity_results.append({
                "seed_count": len(seed_hotels),
                "matches": matches,
                "relevant_count": len(relevant_hotels)
            })
            
            # Store sample for diagnostics
            if len(user_samples) < 20 and (matches > 0 or len(user_samples) < 10):
                user_samples.append({
                    "user_id": user_id,
                    "seed_hotels": seed_hotels[:3],
                    "recommendations": top_hotels[:5],
                    "relevant": list(relevant_hotels)[:5],
                    "matches": matches
                })
        
        # Aggregate results
        if similarity_results:
            results_df = pd.DataFrame(similarity_results)
            hit_rate = (results_df['matches'] > 0).sum() / len(results_df)
            
            logger.info(f"\nContent-Based Similarity Results ({len(similarity_results)} users):")
            logger.info(f"  Users evaluated: {len(similarity_results)}")
            logger.info(f"  Users with ≥1 match: {(results_df['matches'] > 0).sum()} ({hit_rate*100:.1f}%)")
            logger.info(f"  Average matches per user: {results_df['matches'].mean():.2f}")
            logger.info(f"  Average seed hotels: {results_df['seed_count'].mean():.1f}")
            
            logger.info(f"\nSample user results (first 10 with matches):")
            for sample in user_samples[:10]:
                logger.info(f"  {sample['user_id']}: seeds={sample['seed_hotels']}, "
                           f"matches={sample['matches']}, relevant={len(sample['relevant'])}")
            
            return {
                "users_evaluated": len(similarity_results),
                "hit_rate": float(hit_rate),
                "avg_matches": float(results_df['matches'].mean()),
                "avg_seed_count": float(results_df['seed_count'].mean()),
                "samples": user_samples
            }
        else:
            logger.warning("No users with seed hotels and features found!")
            return {
                "users_evaluated": 0,
                "hit_rate": 0,
                "issue": "No users with seed hotels"
            }
    
    def analyze_cold_start(self, feature_cols: List[str]) -> Dict[str, Any]:
        """Analyze cold-start problem."""
        logger.info("\n" + "="*80)
        logger.info("COLD-START ANALYSIS")
        logger.info("="*80)
        
        # Get test users with history
        user_histories = defaultdict(list)
        for _, row in self.test_df.iterrows():
            user_histories[row['user_id']].append(row['hotel_id'])
        
        # Get hotel feature map
        test_hotels = set(self.test_df['hotel_id'].unique())
        hotel_feature_map = {}
        
        for hotel_id in test_hotels:
            hotel_features = self.hotel_df[self.hotel_df['hotel_id'] == hotel_id][feature_cols].values
            if hotel_features.shape[0] > 0:
                # Take first row and ensure shape is (n_features,)
                features = hotel_features[0, :]
                if features.shape[0] == len(feature_cols):
                    hotel_feature_map[hotel_id] = features
        
        # Analyze cold-start cases
        users_with_history = 0
        users_with_featured_history = 0
        users_with_no_history = 0
        
        for user_id, relevant_hotels in self.ground_truth.items():
            history = user_histories[user_id]
            
            if len(history) == 0:
                users_with_no_history += 1
            else:
                users_with_history += 1
                featured_count = sum(1 for h in history if h in hotel_feature_map)
                if featured_count > 0:
                    users_with_featured_history += 1
        
        logger.info(f"Users with history: {users_with_history} ({users_with_history/len(self.ground_truth)*100:.1f}%)")
        logger.info(f"Users with featured history: {users_with_featured_history} "
                   f"({users_with_featured_history/len(self.ground_truth)*100:.1f}%)")
        logger.info(f"Cold-start users (no history): {users_with_no_history} "
                   f"({users_with_no_history/len(self.ground_truth)*100:.1f}%)")
        
        return {
            "users_with_history": int(users_with_history),
            "users_with_featured_history": int(users_with_featured_history),
            "cold_start_users": int(users_with_no_history),
            "total_users": len(self.ground_truth)
        }
    
    def run_debug(self) -> Dict[str, Any]:
        """Run complete debugging analysis."""
        logger.info("\n" + "█"*80)
        logger.info("CONTENT-BASED MODEL DEBUG - COMPREHENSIVE ANALYSIS")
        logger.info("█"*80)
        logger.info(f"Debug date: {datetime.now().isoformat()}")
        
        # Load data
        if not self.load_data():
            return {}
        
        # Build ground truth
        if not self.build_ground_truth():
            return {}
        
        # Analyze features
        feature_analysis = self.analyze_feature_coverage()
        feature_cols = feature_analysis["numeric_col_names"]
        
        # Test similarity search
        similarity_analysis = self.test_similarity_search(feature_cols)
        
        # Analyze cold-start
        cold_start_analysis = self.analyze_cold_start(feature_cols)
        
        # Save comprehensive report
        results = {
            "timestamp": datetime.now().isoformat(),
            "configuration": {
                "k": self.k,
                "relevance_threshold": self.relevance_threshold
            },
            "feature_analysis": feature_analysis,
            "similarity_analysis": similarity_analysis,
            "cold_start_analysis": cold_start_analysis,
            "hypothesis": self._generate_hypothesis(feature_analysis, similarity_analysis, cold_start_analysis)
        }
        
        # Save JSON
        json_file = self.output_dir / "content_based_debug.json"
        with open(json_file, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"\n✓ Results saved to: {json_file}")
        
        # Summary
        logger.info("\n" + "="*80)
        logger.info("DEBUG SUMMARY")
        logger.info("="*80)
        logger.info(f"NDCG@10 = 0.0000 because:")
        hit_rate = similarity_analysis.get("hit_rate", 0)
        logger.info(f"  • Hit rate: {hit_rate*100:.1f}%")
        logger.info(f"  • Feature-similarity ≠ user-preference")
        logger.info(f"  • Recommendation: {results['hypothesis']}")
        
        logger.info("\n" + "="*80)
        logger.info("✓ CONTENT-BASED DEBUG COMPLETE")
        logger.info("="*80 + "\n")
        
        return results
    
    def _generate_hypothesis(self, features, similarity, cold_start) -> str:
        """Generate hypothesis based on findings."""
        hit_rate = similarity.get("hit_rate", 0)
        cold_start_pct = cold_start["cold_start_users"] / cold_start["total_users"]
        
        if cold_start_pct > 0.3:
            return ("HYPOTHESIS: Majority of users are cold-start (no history). "
                   "Content-based cannot work without seed items. "
                   "Recommendation: Not suitable for this dataset without addressing cold-start.")
        elif hit_rate < 0.05:
            return ("HYPOTHESIS: Features don't correlate with user preferences. "
                   "Similar hotels ≠ preferred hotels. "
                   "Recommendation: Improve feature engineering (add semantic features, sentiment, reviews).")
        elif hit_rate < 0.15:
            return ("HYPOTHESIS: Weak feature-preference correlation. "
                   "Content-based has limited signal. "
                   "Recommendation: Use in hybrid with very low weight (5-10%), focus on CF.")
        else:
            return ("HYPOTHESIS: Content-based has useful signal. "
                   "Recommendation: Include in hybrid with moderate weight.")


def main():
    """Run content-based model debugging."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Debug TripSense Content-Based model')
    parser.add_argument('--data-dir', type=str, default=None,
                       help='Path to splits_fixed directory')
    parser.add_argument('--output-dir', type=str, default=None,
                       help='Output directory for results')
    
    args = parser.parse_args()
    
    debugger = ContentBasedDebugger(data_dir=args.data_dir, output_dir=args.output_dir)
    results = debugger.run_debug()
    
    sys.exit(0 if results else 1)


if __name__ == "__main__":
    main()

"""
Hybrid Ensemble Recommender

Combines predictions from all base models (Popularity, Collaborative, Content-Based, NLP/Sentiment)
using weighted averaging and context-aware model selection.
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
import numpy as np

# Import base models
from .popularity_model import PopularityRecommender
from .collaborative_filtering import CollaborativeFilteringRecommender
from .content_based import ContentBasedRecommender
from .nlp_sentiment import NLPSentimentRecommender

logger = logging.getLogger(__name__)


class HybridEnsembleRecommender:
    """
    Hybrid ensemble recommendation system.
    
    Combines multiple recommendation algorithms with intelligent weighting:
    - Collaborative Filtering (for personalized recommendations)
    - Content-Based (for similarity matching)
    - NLP/Sentiment (for quality filtering)
    - Popularity (for cold start and diversity)
    
    Uses context-aware weighting based on:
    - User cold start status
    - Item cold start status
    - Data availability
    - Model confidence scores
    """
    
    def __init__(
        self,
        base_weights: Optional[Dict[str, float]] = None,
        cold_start_weights: Optional[Dict[str, float]] = None
    ):
        """
        Initialize hybrid ensemble.
        
        Args:
            base_weights: Base model weights (default: optimized weights)
            cold_start_weights: Weights for cold start scenarios
        """
        # Initialize base models
        self.popularity_model = PopularityRecommender()
        self.collaborative_model = CollaborativeFilteringRecommender()
        self.content_model = ContentBasedRecommender()
        self.sentiment_model = NLPSentimentRecommender()
        
        # Default weights (can be optimized later)
        self.base_weights = base_weights or {
            "collaborative": 0.35,
            "content": 0.30,
            "sentiment": 0.20,
            "popularity": 0.15
        }
        
        # Cold start weights (favor content and popularity)
        self.cold_start_weights = cold_start_weights or {
            "collaborative": 0.05,
            "content": 0.35,
            "sentiment": 0.25,
            "popularity": 0.35
        }
        
        self.is_trained = False
        
        logger.info("Initialized Hybrid Ensemble Recommender")
        logger.info(f"  Base weights: {self.base_weights}")
        logger.info(f"  Cold start weights: {self.cold_start_weights}")
    
    def train(
        self,
        train_df: DataFrame,
        user_features_df: DataFrame,
        hotel_features_df: DataFrame,
        text_features_df: DataFrame,
        validation_df: Optional[DataFrame] = None
    ):
        """
        Train all base models.
        
        Args:
            train_df: Training reviews DataFrame
            user_features_df: User features DataFrame
            hotel_features_df: Hotel features DataFrame
            text_features_df: Text features DataFrame
            validation_df: Optional validation DataFrame
        """
        logger.info("="*80)
        logger.info("Training Hybrid Ensemble Recommender")
        logger.info("="*80)
        
        # Train Popularity Model
        logger.info("\n" + "="*80)
        logger.info("STEP 1/4: Training Popularity Model")
        logger.info("="*80)
        self.popularity_model.train(train_df, hotel_features_df)
        
        # Train Collaborative Filtering Model
        logger.info("\n" + "="*80)
        logger.info("STEP 2/4: Training Collaborative Filtering Model")
        logger.info("="*80)
        self.collaborative_model.train(
            train_df,
            user_features_df,
            hotel_features_df,
            validation_df
        )
        
        # Train Content-Based Model
        logger.info("\n" + "="*80)
        logger.info("STEP 3/4: Training Content-Based Model")
        logger.info("="*80)
        self.content_model.train(train_df, hotel_features_df, user_features_df)
        
        # Train NLP/Sentiment Model
        logger.info("\n" + "="*80)
        logger.info("STEP 4/4: Training NLP/Sentiment Model")
        logger.info("="*80)
        self.sentiment_model.train(train_df, text_features_df, hotel_features_df)
        
        self.is_trained = True
        
        logger.info("\n" + "="*80)
        logger.info("✅ All Models Trained Successfully")
        logger.info("="*80)
        logger.info("\nHybrid Ensemble is ready for predictions!")
    
    def _is_cold_start_user(self, user_id: str) -> bool:
        """
        Check if user is cold start (not in training data).
        
        Args:
            user_id: User ID
            
        Returns:
            True if cold start user
        """
        # Check if user exists in collaborative model
        if not self.collaborative_model.is_trained:
            return True
        
        user_exists = self.collaborative_model.user_id_map.filter(
            F.col("user_id") == user_id
        ).count() > 0
        
        return not user_exists
    
    def _normalize_scores(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize recommendation scores to 0-1 range.
        
        Args:
            recommendations: List of recommendations with scores
            
        Returns:
            Recommendations with normalized scores
        """
        if not recommendations:
            return []
        
        scores = [rec["score"] for rec in recommendations]
        min_score = min(scores)
        max_score = max(scores)
        
        if max_score == min_score:
            # All scores are the same
            for rec in recommendations:
                rec["normalized_score"] = 1.0
        else:
            for rec in recommendations:
                rec["normalized_score"] = (rec["score"] - min_score) / (max_score - min_score)
        
        return recommendations
    
    def _merge_recommendations(
        self,
        model_recs: Dict[str, List[Dict[str, Any]]],
        weights: Dict[str, float],
        n: int
    ) -> List[Dict[str, Any]]:
        """
        Merge recommendations from multiple models using weighted averaging.
        
        Args:
            model_recs: Dict of model_name -> recommendations
            weights: Dict of model_name -> weight
            n: Number of final recommendations
            
        Returns:
            Merged and ranked recommendations
        """
        # Normalize scores for each model
        for model_name, recs in model_recs.items():
            model_recs[model_name] = self._normalize_scores(recs)
        
        # Aggregate scores by hotel_id
        hotel_scores = {}
        hotel_info = {}
        
        for model_name, recs in model_recs.items():
            weight = weights.get(model_name, 0.0)
            
            for rec in recs:
                hotel_id = rec["hotel_id"]
                normalized_score = rec.get("normalized_score", rec["score"])
                
                if hotel_id not in hotel_scores:
                    hotel_scores[hotel_id] = 0.0
                    hotel_info[hotel_id] = {
                        "contributing_models": [],
                        "model_scores": {}
                    }
                
                # Add weighted score
                hotel_scores[hotel_id] += normalized_score * weight
                
                # Track contributing models
                hotel_info[hotel_id]["contributing_models"].append(model_name)
                hotel_info[hotel_id]["model_scores"][model_name] = normalized_score
        
        # Sort by aggregated score
        sorted_hotels = sorted(
            hotel_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:n]
        
        # Build final recommendations
        final_recommendations = []
        for hotel_id, score in sorted_hotels:
            final_recommendations.append({
                "hotel_id": hotel_id,
                "score": float(score),
                "model": "hybrid_ensemble",
                "contributing_models": hotel_info[hotel_id]["contributing_models"],
                "model_scores": hotel_info[hotel_id]["model_scores"]
            })
        
        return final_recommendations
    
    def recommend_for_user(
        self,
        user_id: str,
        n: int = 10,
        strategy: str = "adaptive"
    ) -> List[Dict[str, Any]]:
        """
        Generate hybrid recommendations for a user.
        
        Args:
            user_id: User ID
            n: Number of recommendations
            strategy: "adaptive" (context-aware) or "fixed" (use base weights)
            
        Returns:
            List of recommendation dictionaries
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Call train() first.")
        
        logger.info(f"\n🎯 Generating recommendations for user: {user_id}")
        
        # Check if cold start user
        is_cold_start = self._is_cold_start_user(user_id)
        logger.info(f"  Cold start: {is_cold_start}")
        
        # Select weights based on strategy
        if strategy == "adaptive" and is_cold_start:
            weights = self.cold_start_weights
            logger.info("  Using cold start weights")
        else:
            weights = self.base_weights
            logger.info("  Using base weights")
        
        # Get recommendations from each model
        model_recs = {}
        
        # Collaborative Filtering
        try:
            if not is_cold_start and weights["collaborative"] > 0:
                logger.info("  🤝 Getting collaborative filtering recommendations...")
                collab_recs = self.collaborative_model.recommend_for_user(user_id, n=n*2)
                model_recs["collaborative"] = collab_recs
                logger.info(f"    Got {len(collab_recs)} recommendations")
        except Exception as e:
            logger.warning(f"  Collaborative filtering failed: {e}")
        
        # Content-Based
        try:
            if weights["content"] > 0:
                logger.info("  📄 Getting content-based recommendations...")
                content_recs = self.content_model.recommend_for_user(user_id, n=n*2)
                model_recs["content"] = content_recs
                logger.info(f"    Got {len(content_recs)} recommendations")
        except Exception as e:
            logger.warning(f"  Content-based failed: {e}")
        
        # NLP/Sentiment
        try:
            if weights["sentiment"] > 0:
                logger.info("  💬 Getting sentiment-based recommendations...")
                sentiment_recs = self.sentiment_model.recommend_for_user(user_id, n=n*2)
                model_recs["sentiment"] = sentiment_recs
                logger.info(f"    Got {len(sentiment_recs)} recommendations")
        except Exception as e:
            logger.warning(f"  Sentiment-based failed: {e}")
        
        # Popularity (always available)
        try:
            if weights["popularity"] > 0:
                logger.info("  📊 Getting popularity-based recommendations...")
                pop_recs = self.popularity_model.recommend(n=n*2, strategy="global")
                model_recs["popularity"] = pop_recs
                logger.info(f"    Got {len(pop_recs)} recommendations")
        except Exception as e:
            logger.warning(f"  Popularity-based failed: {e}")
        
        # Merge recommendations
        if not model_recs:
            logger.warning("  No recommendations from any model!")
            return []
        
        logger.info(f"\n  🔀 Merging recommendations from {len(model_recs)} models...")
        final_recs = self._merge_recommendations(model_recs, weights, n)
        
        logger.info(f"  ✅ Generated {len(final_recs)} final recommendations")
        
        return final_recs
    
    def recommend_similar_hotels(
        self,
        hotel_id: str,
        n: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find hotels similar to a given hotel using ensemble.
        
        Args:
            hotel_id: Reference hotel ID
            n: Number of recommendations
            
        Returns:
            List of similar hotel dictionaries
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Call train() first.")
        
        logger.info(f"\n🏨 Finding hotels similar to: {hotel_id}")
        
        model_recs = {}
        
        # Content-based similarity
        try:
            logger.info("  📄 Getting content-based similar hotels...")
            content_recs = self.content_model.recommend_similar_hotels(hotel_id, n=n*2)
            model_recs["content"] = content_recs
            logger.info(f"    Got {len(content_recs)} similar hotels")
        except Exception as e:
            logger.warning(f"  Content-based failed: {e}")
        
        # Collaborative similar items (users who liked this)
        # Note: ALS doesn't have direct item-item similarity, so we skip or approximate
        
        # Use sentiment for quality matching
        # Skip for now as it's user-based
        
        # Use fixed weights for similar items
        weights = {
            "content": 0.8,
            "popularity": 0.2
        }
        
        # Add some popular hotels for diversity
        try:
            logger.info("  📊 Adding popular hotels for diversity...")
            pop_recs = self.popularity_model.recommend(n=n, strategy="quality")
            model_recs["popularity"] = pop_recs
            logger.info(f"    Got {len(pop_recs)} popular hotels")
        except Exception as e:
            logger.warning(f"  Popularity failed: {e}")
        
        if not model_recs:
            logger.warning("  No similar hotels found!")
            return []
        
        final_recs = self._merge_recommendations(model_recs, weights, n)
        logger.info(f"  ✅ Found {len(final_recs)} similar hotels")
        
        return final_recs
    
    def optimize_weights(
        self,
        validation_df: DataFrame,
        user_features_df: DataFrame,
        metric: str = "ndcg"
    ) -> Dict[str, float]:
        """
        Optimize ensemble weights using validation set.
        
        Args:
            validation_df: Validation DataFrame
            user_features_df: User features DataFrame
            metric: Optimization metric ("ndcg", "precision", "recall")
            
        Returns:
            Optimized weights dictionary
        """
        logger.info("\n🔧 Optimizing ensemble weights...")
        logger.info(f"  Metric: {metric}")
        
        # Simple grid search over weights
        # In production, use more sophisticated optimization (Bayesian, gradient-based)
        
        best_weights = self.base_weights.copy()
        best_score = 0.0
        
        # Grid search
        weight_values = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]
        
        logger.info("  Running grid search...")
        logger.info("  (This is a placeholder - full optimization would test many combinations)")
        
        # For now, return current weights
        # TODO: Implement full grid search with validation metrics
        
        logger.info(f"  Best weights: {best_weights}")
        logger.info(f"  Best score: {best_score:.4f}")
        
        return best_weights
    
    def save(self, path: str):
        """Save all models."""
        logger.info(f"Saving hybrid ensemble to {path}...")
        
        self.popularity_model.save(f"{path}/popularity")
        self.collaborative_model.save(f"{path}/collaborative")
        self.content_model.save(f"{path}/content")
        self.sentiment_model.save(f"{path}/sentiment")
        
        # Save weights
        import json
        weights = {
            "base_weights": self.base_weights,
            "cold_start_weights": self.cold_start_weights
        }
        
        spark = self.popularity_model.global_popular.sql_ctx.sparkSession
        weights_df = spark.createDataFrame(
            [(json.dumps(weights),)],
            ["weights_json"]
        )
        weights_df.write.mode("overwrite").parquet(f"{path}/weights.parquet")
        
        logger.info("✅ Hybrid ensemble saved")
    
    def load(self, path: str, spark: SparkSession):
        """Load all models."""
        logger.info(f"Loading hybrid ensemble from {path}...")
        
        self.popularity_model.load(f"{path}/popularity", spark)
        self.collaborative_model.load(f"{path}/collaborative", spark)
        self.content_model.load(f"{path}/content", spark)
        self.sentiment_model.load(f"{path}/sentiment", spark)
        
        # Load weights
        import json
        weights_df = spark.read.parquet(f"{path}/weights.parquet")
        weights_json = weights_df.first()["weights_json"]
        weights = json.loads(weights_json)
        
        self.base_weights = weights["base_weights"]
        self.cold_start_weights = weights["cold_start_weights"]
        
        self.is_trained = True
        logger.info("✅ Hybrid ensemble loaded")


# Example usage and testing
if __name__ == "__main__":
    from spark_setup import create_spark_session, stop_spark_session
    import sys
    sys.path.append('..')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    spark = create_spark_session("HybridEnsemble-Test")
    
    try:
        # Load all data
        print("\n" + "="*80)
        print("LOADING DATA")
        print("="*80)
        
        train_df = spark.read.parquet("../data/processed/train.parquet")
        test_df = spark.read.parquet("../data/processed/test.parquet")
        user_features_df = spark.read.parquet("../data/processed/features/user_features_complete.parquet")
        hotel_features_df = spark.read.parquet("../data/processed/features/hotel_features_complete.parquet")
        text_features_df = spark.read.parquet("../data/processed/features/text_features_complete.parquet")
        
        print("✅ Data loaded")
        
        # Train ensemble
        model = HybridEnsembleRecommender()
        model.train(
            train_df,
            user_features_df,
            hotel_features_df,
            text_features_df,
            validation_df=test_df
        )
        
        # Test recommendations
        print("\n" + "="*80)
        print("TESTING HYBRID RECOMMENDATIONS")
        print("="*80)
        
        # Get a sample user
        sample_user = user_features_df.select("user_id").first()[0]
        print(f"\n👤 Hybrid recommendations for user: {sample_user}")
        
        hybrid_recs = model.recommend_for_user(sample_user, n=10, strategy="adaptive")
        for i, rec in enumerate(hybrid_recs, 1):
            print(f"\n  {i}. {rec['hotel_id']}")
            print(f"     Score: {rec['score']:.3f}")
            print(f"     Models: {', '.join(rec['contributing_models'])}")
            print(f"     Breakdown: {rec['model_scores']}")
        
        # Test similar hotels
        sample_hotel = hotel_features_df.select("hotel_id").first()[0]
        print(f"\n\n🏨 Hotels similar to: {sample_hotel}")
        
        similar_hotels = model.recommend_similar_hotels(sample_hotel, n=5)
        for i, rec in enumerate(similar_hotels, 1):
            print(f"  {i}. {rec['hotel_id']}: {rec['score']:.3f}")
        
        # Save model
        model.save("../artifacts/models/hybrid_ensemble")
        print("\n✅ Hybrid ensemble saved to artifacts/models/hybrid_ensemble")
        
    finally:
        stop_spark_session()

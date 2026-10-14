"""
Popularity-Based Recommender

Recommends hotels based on global and local popularity metrics.
Serves as baseline and cold-start fallback.
"""
import logging
from typing import List, Dict, Any
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.window import Window

logger = logging.getLogger(__name__)


class PopularityRecommender:
    """
    Popularity-based recommendation model.
    
    Strategies:
    1. Global popularity (most reviewed + highest rated)
    2. Trending (recent popularity increase)
    3. Quality-adjusted popularity (rating-weighted)
    """
    
    def __init__(self):
        self.global_popular = None
        self.trending_popular = None
        self.quality_popular = None
        self.is_trained = False
    
    def train(self, reviews_df: DataFrame, hotel_features_df: DataFrame):
        """
        Train popularity model by computing popularity scores.
        
        Args:
            reviews_df: Reviews DataFrame
            hotel_features_df: Hotel features DataFrame
        """
        logger.info("="*80)
        logger.info("Training Popularity-Based Recommender")
        logger.info("="*80)
        
        # 1. Global Popularity Score
        logger.info("\n📊 Computing global popularity scores...")
        self.global_popular = hotel_features_df.select(
            "hotel_id",
            "hotel_review_count",
            "hotel_avg_rating",
            "hotel_unique_reviewers"
        ).withColumn(
            "popularity_score",
            # Weighted combination: 50% review count, 30% rating, 20% unique reviewers
            (F.log1p(F.col("hotel_review_count")) * 0.5 +
             F.col("hotel_avg_rating") * 0.3 +
             F.log1p(F.col("hotel_unique_reviewers")) * 0.2)
        ).orderBy(F.desc("popularity_score"))
        
        logger.info(f"✅ Global popularity computed for {self.global_popular.count():,} hotels")
        
        # 2. Trending Popularity (recent vs historical)
        logger.info("\n📈 Computing trending scores...")
        self.trending_popular = hotel_features_df.select(
            "hotel_id",
            "hotel_review_count",
            "hotel_avg_rating",
            "review_trend"  # From hotel features
        ).withColumn(
            "trending_score",
            F.col("review_trend") * F.log1p(F.col("hotel_review_count"))
        ).orderBy(F.desc("trending_score"))
        
        logger.info(f"✅ Trending scores computed")
        
        # 3. Quality-Adjusted Popularity
        logger.info("\n⭐ Computing quality-adjusted popularity...")
        self.quality_popular = hotel_features_df.select(
            "hotel_id",
            "hotel_review_count",
            "hotel_avg_rating",
            "pct_5star",
            "rating_consistency"
        ).withColumn(
            "quality_score",
            # Favor high ratings + many reviews + consistency
            (F.col("hotel_avg_rating") / 5.0) * 0.4 +
            (F.log1p(F.col("hotel_review_count")) / 10.0) * 0.3 +
            F.col("pct_5star") * 0.2 +
            F.col("rating_consistency") * 0.1
        ).orderBy(F.desc("quality_score"))
        
        logger.info(f"✅ Quality scores computed")
        
        self.is_trained = True
        
        # Show top hotels in each category
        logger.info("\n🏆 Top 5 Globally Popular Hotels:")
        self.global_popular.select(
            "hotel_id", "hotel_review_count", "hotel_avg_rating", "popularity_score"
        ).show(5, truncate=False)
        
        logger.info("\n🔥 Top 5 Trending Hotels:")
        self.trending_popular.select(
            "hotel_id", "review_trend", "trending_score"
        ).show(5, truncate=False)
        
        logger.info("\n⭐ Top 5 Quality Hotels:")
        self.quality_popular.select(
            "hotel_id", "hotel_avg_rating", "pct_5star", "quality_score"
        ).show(5, truncate=False)
        
        logger.info("\n" + "="*80)
        logger.info("Popularity Model Training Complete")
        logger.info("="*80)
    
    def recommend_global(self, n: int = 10, min_reviews: int = 10) -> List[str]:
        """
        Get top-N globally popular hotels.
        
        Args:
            n: Number of recommendations
            min_reviews: Minimum review count threshold
            
        Returns:
            List of hotel IDs
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Call train() first.")
        
        recommendations = self.global_popular \
            .filter(F.col("hotel_review_count") >= min_reviews) \
            .limit(n) \
            .select("hotel_id") \
            .rdd.flatMap(lambda x: x).collect()
        
        return recommendations
    
    def recommend_trending(self, n: int = 10, min_reviews: int = 5) -> List[str]:
        """
        Get top-N trending hotels.
        
        Args:
            n: Number of recommendations
            min_reviews: Minimum review count threshold
            
        Returns:
            List of hotel IDs
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Call train() first.")
        
        # Join with global to get review counts
        recommendations = self.trending_popular \
            .join(
                self.global_popular.select("hotel_id", "hotel_review_count"),
                "hotel_id"
            ) \
            .filter(F.col("hotel_review_count") >= min_reviews) \
            .limit(n) \
            .select("hotel_id") \
            .rdd.flatMap(lambda x: x).collect()
        
        return recommendations
    
    def recommend_quality(self, n: int = 10, min_reviews: int = 20) -> List[str]:
        """
        Get top-N quality hotels (high ratings + reviews).
        
        Args:
            n: Number of recommendations
            min_reviews: Minimum review count threshold
            
        Returns:
            List of hotel IDs
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Call train() first.")
        
        # Join with global to get review counts
        recommendations = self.quality_popular \
            .join(
                self.global_popular.select("hotel_id", "hotel_review_count"),
                "hotel_id"
            ) \
            .filter(F.col("hotel_review_count") >= min_reviews) \
            .limit(n) \
            .select("hotel_id") \
            .rdd.flatMap(lambda x: x).collect()
        
        return recommendations
    
    def recommend(
        self,
        user_id: str = None,
        n: int = 10,
        strategy: str = "global"
    ) -> List[Dict[str, Any]]:
        """
        Generate recommendations using popularity.
        
        Args:
            user_id: User ID (ignored for popularity model)
            n: Number of recommendations
            strategy: "global", "trending", or "quality"
            
        Returns:
            List of recommendation dictionaries
        """
        if strategy == "trending":
            hotel_ids = self.recommend_trending(n)
            scores_df = self.trending_popular
            score_col = "trending_score"
        elif strategy == "quality":
            hotel_ids = self.recommend_quality(n)
            scores_df = self.quality_popular
            score_col = "quality_score"
        else:  # global
            hotel_ids = self.recommend_global(n)
            scores_df = self.global_popular
            score_col = "popularity_score"
        
        # Get scores for recommended hotels
        recommendations = []
        for hotel_id in hotel_ids:
            score_row = scores_df.filter(F.col("hotel_id") == hotel_id).first()
            if score_row:
                recommendations.append({
                    "hotel_id": hotel_id,
                    "score": float(score_row[score_col]),
                    "model": "popularity",
                    "strategy": strategy
                })
        
        return recommendations
    
    def save(self, path: str):
        """Save model artifacts."""
        logger.info(f"Saving popularity model to {path}...")
        
        self.global_popular.write.mode("overwrite").parquet(f"{path}/global_popular.parquet")
        self.trending_popular.write.mode("overwrite").parquet(f"{path}/trending_popular.parquet")
        self.quality_popular.write.mode("overwrite").parquet(f"{path}/quality_popular.parquet")
        
        logger.info("✅ Model saved")
    
    def load(self, path: str, spark):
        """Load model artifacts."""
        logger.info(f"Loading popularity model from {path}...")
        
        self.global_popular = spark.read.parquet(f"{path}/global_popular.parquet")
        self.trending_popular = spark.read.parquet(f"{path}/trending_popular.parquet")
        self.quality_popular = spark.read.parquet(f"{path}/quality_popular.parquet")
        self.is_trained = True
        
        logger.info("✅ Model loaded")


# Example usage and testing
if __name__ == "__main__":
    from spark_setup import create_spark_session, stop_spark_session
    import sys
    sys.path.append('..')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    spark = create_spark_session("PopularityModel-Test")
    
    try:
        # Load data
        reviews_df = spark.read.parquet("../data/processed/tripadvisor_cleaned.parquet")
        hotel_features_df = spark.read.parquet("../data/processed/features/hotel_features_complete.parquet")
        
        # Train model
        model = PopularityRecommender()
        model.train(reviews_df, hotel_features_df)
        
        # Test recommendations
        print("\n" + "="*80)
        print("TESTING RECOMMENDATIONS")
        print("="*80)
        
        print("\n📊 Top 10 Global Popular:")
        global_recs = model.recommend(n=10, strategy="global")
        for i, rec in enumerate(global_recs, 1):
            print(f"  {i}. {rec['hotel_id']}: {rec['score']:.3f}")
        
        print("\n🔥 Top 10 Trending:")
        trending_recs = model.recommend(n=10, strategy="trending")
        for i, rec in enumerate(trending_recs, 1):
            print(f"  {i}. {rec['hotel_id']}: {rec['score']:.3f}")
        
        print("\n⭐ Top 10 Quality:")
        quality_recs = model.recommend(n=10, strategy="quality")
        for i, rec in enumerate(quality_recs, 1):
            print(f"  {i}. {rec['hotel_id']}: {rec['score']:.3f}")
        
        # Save model
        model.save("../artifacts/models/popularity")
        print("\n✅ Model saved to artifacts/models/popularity")
        
    finally:
        stop_spark_session()

"""
NLP and Sentiment-Based Recommender

Recommends hotels based on sentiment analysis and text features from reviews.
Uses sentiment scores, keywords, and text similarity for recommendations.
"""
import logging
from typing import List, Dict, Any, Optional
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window

logger = logging.getLogger(__name__)


class NLPSentimentRecommender:
    """
    NLP and sentiment-based recommendation model.
    
    Strategies:
    1. Sentiment-weighted recommendations
    2. Aspect-level sentiment matching
    3. Positive keyword matching
    4. Review quality filtering
    """
    
    def __init__(self):
        self.hotel_sentiment = None
        self.user_sentiment_prefs = None
        self.aspect_sentiments = None
        self.is_trained = False
    
    def _aggregate_hotel_sentiment(
        self,
        reviews_df: DataFrame,
        text_features_df: DataFrame
    ) -> DataFrame:
        """
        Aggregate sentiment scores for each hotel.
        
        Args:
            reviews_df: Reviews DataFrame
            text_features_df: Text features DataFrame
            
        Returns:
            DataFrame with hotel sentiment aggregations
        """
        logger.info("\n📊 Aggregating hotel sentiment scores...")
        
        # Join reviews with text features
        review_sentiment = reviews_df.select(
            "review_id", "hotel_id", "rating"
        ).join(
            text_features_df.select(
                "review_id",
                "sentiment_score",
                "sentiment_magnitude",
                "word_count",
                "positive_word_count",
                "negative_word_count"
            ),
            "review_id"
        )
        
        # Aggregate by hotel
        hotel_sentiment = review_sentiment.groupBy("hotel_id").agg(
            # Sentiment metrics
            F.avg("sentiment_score").alias("avg_sentiment"),
            F.stddev("sentiment_score").alias("sentiment_std"),
            F.avg("sentiment_magnitude").alias("avg_magnitude"),
            
            # Positive/negative word ratios
            F.sum("positive_word_count").alias("total_positive_words"),
            F.sum("negative_word_count").alias("total_negative_words"),
            
            # Review characteristics
            F.avg("word_count").alias("avg_review_length"),
            F.count("review_id").alias("review_count"),
            
            # Rating alignment with sentiment
            F.corr("rating", "sentiment_score").alias("rating_sentiment_correlation")
        )
        
        # Calculate positive/negative word ratio
        hotel_sentiment = hotel_sentiment.withColumn(
            "positive_negative_ratio",
            F.when(
                F.col("total_negative_words") > 0,
                F.col("total_positive_words") / F.col("total_negative_words")
            ).otherwise(F.col("total_positive_words"))
        )
        
        # Calculate sentiment consistency
        hotel_sentiment = hotel_sentiment.withColumn(
            "sentiment_consistency",
            1.0 - F.least(F.col("sentiment_std") / 2.0, F.lit(1.0))  # Normalize to 0-1
        )
        
        # Calculate overall sentiment score
        hotel_sentiment = hotel_sentiment.withColumn(
            "overall_sentiment_score",
            (F.col("avg_sentiment") * 0.4 +
             F.col("positive_negative_ratio") * 0.3 +
             F.col("sentiment_consistency") * 0.2 +
             F.col("rating_sentiment_correlation") * 0.1)
        )
        
        logger.info(f"✅ Aggregated sentiment for {hotel_sentiment.count():,} hotels")
        
        return hotel_sentiment
    
    def _aggregate_aspect_sentiment(
        self,
        reviews_df: DataFrame,
        text_features_df: DataFrame
    ) -> DataFrame:
        """
        Aggregate aspect-level sentiment for hotels.
        
        Args:
            reviews_df: Reviews DataFrame
            text_features_df: Text features DataFrame
            
        Returns:
            DataFrame with aspect-level sentiment
        """
        logger.info("\n🎯 Aggregating aspect-level sentiment...")
        
        # Join reviews with text features (assuming aspect columns exist)
        review_aspects = reviews_df.select(
            "review_id", "hotel_id"
        ).join(
            text_features_df.select(
                "review_id",
                "has_cleanliness_mention",
                "has_service_mention",
                "has_location_mention",
                "has_room_mention",
                "has_value_mention",
                "sentiment_score"
            ),
            "review_id"
        )
        
        # Aggregate aspect mentions by hotel
        aspect_sentiment = review_aspects.groupBy("hotel_id").agg(
            # Count mentions
            F.sum(F.when(F.col("has_cleanliness_mention") == 1, 1).otherwise(0)).alias("cleanliness_mentions"),
            F.sum(F.when(F.col("has_service_mention") == 1, 1).otherwise(0)).alias("service_mentions"),
            F.sum(F.when(F.col("has_location_mention") == 1, 1).otherwise(0)).alias("location_mentions"),
            F.sum(F.when(F.col("has_room_mention") == 1, 1).otherwise(0)).alias("room_mentions"),
            F.sum(F.when(F.col("has_value_mention") == 1, 1).otherwise(0)).alias("value_mentions"),
            
            # Average sentiment when aspect is mentioned
            F.avg(F.when(F.col("has_cleanliness_mention") == 1, F.col("sentiment_score"))).alias("cleanliness_sentiment"),
            F.avg(F.when(F.col("has_service_mention") == 1, F.col("sentiment_score"))).alias("service_sentiment"),
            F.avg(F.when(F.col("has_location_mention") == 1, F.col("sentiment_score"))).alias("location_sentiment"),
            F.avg(F.when(F.col("has_room_mention") == 1, F.col("sentiment_score"))).alias("room_sentiment"),
            F.avg(F.when(F.col("has_value_mention") == 1, F.col("sentiment_score"))).alias("value_sentiment"),
            
            F.count("review_id").alias("total_reviews")
        )
        
        # Calculate aspect mention ratios
        for aspect in ["cleanliness", "service", "location", "room", "value"]:
            aspect_sentiment = aspect_sentiment.withColumn(
                f"{aspect}_mention_ratio",
                F.col(f"{aspect}_mentions") / F.col("total_reviews")
            )
        
        logger.info(f"✅ Aggregated aspect sentiment for {aspect_sentiment.count():,} hotels")
        
        return aspect_sentiment
    
    def _build_user_sentiment_preferences(
        self,
        reviews_df: DataFrame,
        text_features_df: DataFrame
    ) -> DataFrame:
        """
        Build user sentiment preference profiles.
        
        Args:
            reviews_df: Reviews DataFrame
            text_features_df: Text features DataFrame
            
        Returns:
            DataFrame with user sentiment preferences
        """
        logger.info("\n👤 Building user sentiment preferences...")
        
        # Join reviews with text features
        user_reviews = reviews_df.select(
            "review_id", "user_id", "rating"
        ).join(
            text_features_df.select(
                "review_id",
                "sentiment_score",
                "word_count",
                "positive_word_count",
                "negative_word_count"
            ),
            "review_id"
        )
        
        # Aggregate by user
        user_prefs = user_reviews.groupBy("user_id").agg(
            # Sentiment preferences
            F.avg("sentiment_score").alias("avg_sentiment_preference"),
            F.stddev("sentiment_score").alias("sentiment_variance"),
            
            # Review characteristics
            F.avg("word_count").alias("avg_review_length"),
            F.avg("positive_word_count").alias("avg_positive_words"),
            F.avg("negative_word_count").alias("avg_negative_words"),
            
            # User activity
            F.count("review_id").alias("review_count")
        )
        
        # Calculate user sentiment profile
        user_prefs = user_prefs.withColumn(
            "positive_negative_ratio",
            F.when(
                F.col("avg_negative_words") > 0,
                F.col("avg_positive_words") / F.col("avg_negative_words")
            ).otherwise(F.col("avg_positive_words"))
        )
        
        logger.info(f"✅ Built sentiment preferences for {user_prefs.count():,} users")
        
        return user_prefs
    
    def train(
        self,
        reviews_df: DataFrame,
        text_features_df: DataFrame,
        hotel_features_df: Optional[DataFrame] = None
    ):
        """
        Train NLP/Sentiment model.
        
        Args:
            reviews_df: Reviews DataFrame
            text_features_df: Text features DataFrame
            hotel_features_df: Optional hotel features DataFrame
        """
        logger.info("="*80)
        logger.info("Training NLP/Sentiment Recommender")
        logger.info("="*80)
        
        # Aggregate hotel sentiment
        self.hotel_sentiment = self._aggregate_hotel_sentiment(
            reviews_df,
            text_features_df
        )
        
        # Aggregate aspect-level sentiment
        self.aspect_sentiments = self._aggregate_aspect_sentiment(
            reviews_df,
            text_features_df
        )
        
        # Build user sentiment preferences
        self.user_sentiment_prefs = self._build_user_sentiment_preferences(
            reviews_df,
            text_features_df
        )
        
        # Cache for faster access
        self.hotel_sentiment.cache()
        self.aspect_sentiments.cache()
        self.user_sentiment_prefs.cache()
        
        # Show statistics
        logger.info("\n📊 Model Statistics:")
        logger.info(f"  Hotels with sentiment: {self.hotel_sentiment.count():,}")
        logger.info(f"  Hotels with aspect sentiment: {self.aspect_sentiments.count():,}")
        logger.info(f"  Users with preferences: {self.user_sentiment_prefs.count():,}")
        
        # Show top sentiment hotels
        logger.info("\n😊 Top 5 Hotels by Sentiment:")
        self.hotel_sentiment.orderBy(F.desc("overall_sentiment_score")).select(
            "hotel_id",
            "avg_sentiment",
            "positive_negative_ratio",
            "overall_sentiment_score"
        ).show(5)
        
        self.is_trained = True
        
        logger.info("\n" + "="*80)
        logger.info("NLP/Sentiment Model Training Complete")
        logger.info("="*80)
    
    def recommend_by_sentiment(
        self,
        n: int = 10,
        min_reviews: int = 10,
        min_sentiment: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Recommend hotels with best sentiment scores.
        
        Args:
            n: Number of recommendations
            min_reviews: Minimum review count
            min_sentiment: Minimum sentiment score
            
        Returns:
            List of recommendation dictionaries
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Call train() first.")
        
        # Filter and rank by sentiment
        top_hotels = self.hotel_sentiment.filter(
            (F.col("review_count") >= min_reviews) &
            (F.col("avg_sentiment") >= min_sentiment)
        ).orderBy(
            F.desc("overall_sentiment_score")
        ).limit(n)
        
        # Collect recommendations
        recommendations = []
        for row in top_hotels.collect():
            recommendations.append({
                "hotel_id": row["hotel_id"],
                "score": float(row["overall_sentiment_score"]),
                "avg_sentiment": float(row["avg_sentiment"]),
                "model": "nlp_sentiment",
                "method": "sentiment_ranking"
            })
        
        return recommendations
    
    def recommend_for_user(
        self,
        user_id: str,
        n: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Recommend hotels matching user's sentiment preferences.
        
        Args:
            user_id: User ID
            n: Number of recommendations
            
        Returns:
            List of recommendation dictionaries
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Call train() first.")
        
        # Get user preference
        user_pref_row = self.user_sentiment_prefs.filter(
            F.col("user_id") == user_id
        ).first()
        
        if not user_pref_row:
            logger.warning(f"User {user_id} not found (cold start)")
            return []
        
        user_avg_sentiment = user_pref_row["avg_sentiment_preference"]
        user_pos_neg_ratio = user_pref_row["positive_negative_ratio"]
        
        # Find hotels with similar sentiment profile
        # Calculate similarity score
        similar_hotels = self.hotel_sentiment.withColumn(
            "sentiment_similarity",
            1.0 - F.abs(F.col("avg_sentiment") - F.lit(user_avg_sentiment))
        ).withColumn(
            "ratio_similarity",
            1.0 / (1.0 + F.abs(F.col("positive_negative_ratio") - F.lit(user_pos_neg_ratio)))
        ).withColumn(
            "match_score",
            F.col("sentiment_similarity") * 0.6 + F.col("ratio_similarity") * 0.4
        ).orderBy(
            F.desc("match_score")
        ).limit(n)
        
        # Collect recommendations
        recommendations = []
        for row in similar_hotels.collect():
            recommendations.append({
                "hotel_id": row["hotel_id"],
                "score": float(row["match_score"]),
                "model": "nlp_sentiment",
                "method": "sentiment_matching"
            })
        
        return recommendations
    
    def recommend_by_aspects(
        self,
        aspect_preferences: Dict[str, float],
        n: int = 10,
        min_mentions: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Recommend hotels by aspect-level sentiment.
        
        Args:
            aspect_preferences: Dict of aspect -> importance weight
            n: Number of recommendations
            min_mentions: Minimum mentions per aspect
            
        Returns:
            List of recommendation dictionaries
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Call train() first.")
        
        # Build weighted aspect score
        aspect_expr = None
        for aspect, weight in aspect_preferences.items():
            sentiment_col = f"{aspect}_sentiment"
            mention_col = f"{aspect}_mentions"
            
            if sentiment_col in self.aspect_sentiments.columns:
                # Weight by sentiment and mention count
                weighted_col = (
                    F.coalesce(F.col(sentiment_col), F.lit(0.0)) * weight
                )
                
                if aspect_expr is None:
                    aspect_expr = weighted_col
                else:
                    aspect_expr = aspect_expr + weighted_col
        
        if aspect_expr is None:
            logger.warning("No valid aspects found")
            return []
        
        # Normalize by total weight
        total_weight = sum(aspect_preferences.values())
        aspect_expr = aspect_expr / total_weight
        
        # Get top hotels by aspect sentiment
        top_hotels = self.aspect_sentiments.withColumn(
            "aspect_score",
            aspect_expr
        ).orderBy(
            F.desc("aspect_score")
        ).limit(n)
        
        # Collect recommendations
        recommendations = []
        for row in top_hotels.collect():
            recommendations.append({
                "hotel_id": row["hotel_id"],
                "score": float(row["aspect_score"]),
                "model": "nlp_sentiment",
                "method": "aspect_sentiment"
            })
        
        return recommendations
    
    def save(self, path: str):
        """Save model artifacts."""
        logger.info(f"Saving NLP/Sentiment model to {path}...")
        
        self.hotel_sentiment.write.mode("overwrite").parquet(f"{path}/hotel_sentiment.parquet")
        self.aspect_sentiments.write.mode("overwrite").parquet(f"{path}/aspect_sentiments.parquet")
        self.user_sentiment_prefs.write.mode("overwrite").parquet(f"{path}/user_sentiment_prefs.parquet")
        
        logger.info("✅ Model saved")
    
    def load(self, path: str, spark: SparkSession):
        """Load model artifacts."""
        logger.info(f"Loading NLP/Sentiment model from {path}...")
        
        self.hotel_sentiment = spark.read.parquet(f"{path}/hotel_sentiment.parquet")
        self.aspect_sentiments = spark.read.parquet(f"{path}/aspect_sentiments.parquet")
        self.user_sentiment_prefs = spark.read.parquet(f"{path}/user_sentiment_prefs.parquet")
        
        self.hotel_sentiment.cache()
        self.aspect_sentiments.cache()
        self.user_sentiment_prefs.cache()
        
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
    
    spark = create_spark_session("NLPSentiment-Test")
    
    try:
        # Load data
        train_df = spark.read.parquet("../data/processed/train.parquet")
        text_features_df = spark.read.parquet("../data/processed/features/text_features_complete.parquet")
        
        # Train model
        model = NLPSentimentRecommender()
        model.train(train_df, text_features_df)
        
        # Test recommendations
        print("\n" + "="*80)
        print("TESTING RECOMMENDATIONS")
        print("="*80)
        
        print("\n😊 Top 10 Hotels by Sentiment:")
        sentiment_recs = model.recommend_by_sentiment(n=10)
        for i, rec in enumerate(sentiment_recs, 1):
            print(f"  {i}. {rec['hotel_id']}: {rec['score']:.3f} (sentiment: {rec['avg_sentiment']:.3f})")
        
        # Get a sample user
        sample_user = train_df.select("user_id").first()[0]
        print(f"\n👤 Sentiment-based recommendations for user: {sample_user}")
        
        user_recs = model.recommend_for_user(sample_user, n=10)
        for i, rec in enumerate(user_recs, 1):
            print(f"  {i}. {rec['hotel_id']}: {rec['score']:.3f}")
        
        # Test aspect-based recommendations
        print(f"\n🎯 Top hotels for cleanliness and service sentiment:")
        aspect_recs = model.recommend_by_aspects({
            "cleanliness": 0.6,
            "service": 0.4
        }, n=5)
        for i, rec in enumerate(aspect_recs, 1):
            print(f"  {i}. {rec['hotel_id']}: {rec['score']:.3f}")
        
        # Save model
        model.save("../artifacts/models/nlp_sentiment")
        print("\n✅ Model saved to artifacts/models/nlp_sentiment")
        
    finally:
        stop_spark_session()

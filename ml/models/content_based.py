"""
Content-Based Filtering Recommender

Recommends hotels based on content similarity and user preferences.
Uses hotel features and aspect ratings to find similar items.
"""
import logging
from typing import List, Dict, Any, Optional
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.linalg import Vectors, VectorUDT
from pyspark.sql.types import FloatType
import numpy as np

logger = logging.getLogger(__name__)


class ContentBasedRecommender:
    """
    Content-based filtering using hotel features and aspect ratings.
    
    Strategies:
    1. Feature-based similarity (aspect ratings)
    2. User preference matching
    3. Category-based filtering
    """
    
    def __init__(self):
        self.hotel_features = None
        self.hotel_vectors = None
        self.user_preferences = None
        self.similarity_matrix = None
        self.is_trained = False
        
        # Feature columns to use
        self.feature_cols = [
            "avg_cleanliness",
            "avg_service",
            "avg_location",
            "avg_rooms",
            "avg_value",
            "hotel_avg_rating",
            "hotel_review_count_log",
            "pct_5star",
            "pct_4star",
            "pct_3star",
            "pct_2star",
            "pct_1star",
            "rating_consistency"
        ]
    
    def _build_hotel_feature_vectors(self, hotel_features_df: DataFrame) -> DataFrame:
        """
        Build feature vectors for each hotel.
        
        Args:
            hotel_features_df: Hotel features DataFrame
            
        Returns:
            DataFrame with (hotel_id, features_vector)
        """
        logger.info("\n🔧 Building hotel feature vectors...")
        
        # Add log-transformed review count
        hotel_features_enriched = hotel_features_df.withColumn(
            "hotel_review_count_log",
            F.log1p(F.col("hotel_review_count"))
        )
        
        # Fill missing values with column means
        for col in self.feature_cols:
            if col in hotel_features_enriched.columns:
                mean_val = hotel_features_enriched.agg(
                    F.mean(col).alias("mean")
                ).first()["mean"]
                hotel_features_enriched = hotel_features_enriched.fillna(
                    {col: mean_val if mean_val else 0.0}
                )
        
        # Assemble feature vectors
        assembler = VectorAssembler(
            inputCols=self.feature_cols,
            outputCol="features_vector",
            handleInvalid="skip"
        )
        
        hotel_vectors = assembler.transform(hotel_features_enriched).select(
            "hotel_id",
            "features_vector",
            *self.feature_cols
        )
        
        logger.info(f"✅ Built feature vectors for {hotel_vectors.count():,} hotels")
        logger.info(f"   Feature dimensions: {len(self.feature_cols)}")
        
        return hotel_vectors
    
    def _build_user_preference_profiles(
        self,
        reviews_df: DataFrame,
        hotel_vectors: DataFrame
    ) -> DataFrame:
        """
        Build user preference profiles from their review history.
        
        Args:
            reviews_df: Reviews DataFrame
            hotel_vectors: Hotel feature vectors
            
        Returns:
            DataFrame with (user_id, preference_vector)
        """
        logger.info("\n👤 Building user preference profiles...")
        
        # Join reviews with hotel features
        user_hotel_features = reviews_df.select(
            "user_id", "hotel_id", "rating"
        ).join(
            hotel_vectors.select("hotel_id", "features_vector"),
            "hotel_id"
        )
        
        # Weight features by rating (higher ratings = stronger preference)
        # Normalize ratings to 0-1 scale
        user_hotel_weighted = user_hotel_features.withColumn(
            "rating_weight",
            (F.col("rating") - 1) / 4.0  # 1-5 -> 0-1
        )
        
        # For each user, compute weighted average of hotel feature vectors
        # This is complex in PySpark, so we'll aggregate by user and compute centroid
        
        # Convert to RDD for easier vector operations
        user_features_rdd = user_hotel_weighted.rdd.map(
            lambda row: (
                row["user_id"],
                (row["features_vector"].toArray(), row["rating_weight"])
            )
        )
        
        # Group by user and compute weighted average
        def weighted_average_vectors(vectors_weights):
            vectors = [v[0] for v in vectors_weights]
            weights = [v[1] for v in vectors_weights]
            
            if len(vectors) == 0:
                return None
            
            # Weighted average
            weighted_sum = np.zeros(len(vectors[0]))
            total_weight = 0.0
            
            for vec, weight in zip(vectors, weights):
                weighted_sum += np.array(vec) * weight
                total_weight += weight
            
            if total_weight > 0:
                avg_vector = weighted_sum / total_weight
            else:
                avg_vector = weighted_sum
            
            return Vectors.dense(avg_vector.tolist())
        
        user_prefs_rdd = user_features_rdd.groupByKey().mapValues(
            lambda vectors_weights: weighted_average_vectors(list(vectors_weights))
        )
        
        # Convert back to DataFrame
        spark = reviews_df.sql_ctx.sparkSession
        user_preferences = spark.createDataFrame(
            user_prefs_rdd,
            ["user_id", "preference_vector"]
        )
        
        logger.info(f"✅ Built preference profiles for {user_preferences.count():,} users")
        
        return user_preferences
    
    def _compute_cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Compute cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Cosine similarity (0-1)
        """
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def train(
        self,
        reviews_df: DataFrame,
        hotel_features_df: DataFrame,
        user_features_df: Optional[DataFrame] = None
    ):
        """
        Train content-based model.
        
        Args:
            reviews_df: Reviews DataFrame
            hotel_features_df: Hotel features DataFrame
            user_features_df: Optional user features DataFrame
        """
        logger.info("="*80)
        logger.info("Training Content-Based Filtering Recommender")
        logger.info("="*80)
        
        # Build hotel feature vectors
        self.hotel_vectors = self._build_hotel_feature_vectors(hotel_features_df)
        
        # Build user preference profiles
        self.user_preferences = self._build_user_preference_profiles(
            reviews_df,
            self.hotel_vectors
        )
        
        # Cache for faster access
        self.hotel_vectors.cache()
        self.user_preferences.cache()
        
        # Show statistics
        logger.info("\n📊 Model Statistics:")
        logger.info(f"  Hotels: {self.hotel_vectors.count():,}")
        logger.info(f"  Users: {self.user_preferences.count():,}")
        logger.info(f"  Feature dimensions: {len(self.feature_cols)}")
        
        # Show sample hotel features
        logger.info("\n🏨 Sample Hotel Features:")
        self.hotel_vectors.select(
            "hotel_id",
            "avg_cleanliness",
            "avg_service",
            "avg_location",
            "hotel_avg_rating"
        ).show(5)
        
        self.is_trained = True
        
        logger.info("\n" + "="*80)
        logger.info("Content-Based Model Training Complete")
        logger.info("="*80)
    
    def recommend_for_user(
        self,
        user_id: str,
        n: int = 10,
        min_similarity: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Generate recommendations for a user based on their preferences.
        
        Args:
            user_id: User ID
            n: Number of recommendations
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of recommendation dictionaries
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Call train() first.")
        
        # Get user preference vector
        user_pref_row = self.user_preferences.filter(
            F.col("user_id") == user_id
        ).first()
        
        if not user_pref_row:
            logger.warning(f"User {user_id} not found (cold start)")
            return []
        
        user_pref_vec = user_pref_row["preference_vector"].toArray()
        
        # Compute similarity with all hotels
        # Using UDF for cosine similarity
        spark = self.hotel_vectors.sql_ctx.sparkSession
        
        @F.udf(FloatType())
        def cosine_sim_udf(hotel_vec):
            if hotel_vec is None:
                return 0.0
            hotel_array = hotel_vec.toArray()
            return float(self._compute_cosine_similarity(user_pref_vec, hotel_array))
        
        # Compute similarities
        hotel_similarities = self.hotel_vectors.withColumn(
            "similarity",
            cosine_sim_udf(F.col("features_vector"))
        ).filter(
            F.col("similarity") >= min_similarity
        ).orderBy(
            F.desc("similarity")
        ).limit(n)
        
        # Collect recommendations
        recommendations = []
        for row in hotel_similarities.collect():
            recommendations.append({
                "hotel_id": row["hotel_id"],
                "score": float(row["similarity"]),
                "model": "content_based",
                "method": "preference_matching"
            })
        
        return recommendations
    
    def recommend_similar_hotels(
        self,
        hotel_id: str,
        n: int = 10,
        min_similarity: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Find hotels similar to a given hotel.
        
        Args:
            hotel_id: Reference hotel ID
            n: Number of recommendations
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of similar hotel dictionaries
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Call train() first.")
        
        # Get target hotel vector
        target_hotel_row = self.hotel_vectors.filter(
            F.col("hotel_id") == hotel_id
        ).first()
        
        if not target_hotel_row:
            logger.warning(f"Hotel {hotel_id} not found")
            return []
        
        target_vec = target_hotel_row["features_vector"].toArray()
        
        # Compute similarity with all other hotels
        @F.udf(FloatType())
        def cosine_sim_udf(hotel_vec):
            if hotel_vec is None:
                return 0.0
            hotel_array = hotel_vec.toArray()
            return float(self._compute_cosine_similarity(target_vec, hotel_array))
        
        # Compute similarities
        similar_hotels = self.hotel_vectors.filter(
            F.col("hotel_id") != hotel_id  # Exclude self
        ).withColumn(
            "similarity",
            cosine_sim_udf(F.col("features_vector"))
        ).filter(
            F.col("similarity") >= min_similarity
        ).orderBy(
            F.desc("similarity")
        ).limit(n)
        
        # Collect recommendations
        recommendations = []
        for row in similar_hotels.collect():
            recommendations.append({
                "hotel_id": row["hotel_id"],
                "score": float(row["similarity"]),
                "model": "content_based",
                "method": "hotel_similarity"
            })
        
        return recommendations
    
    def recommend_by_aspects(
        self,
        aspect_preferences: Dict[str, float],
        n: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Recommend hotels based on specific aspect preferences.
        
        Args:
            aspect_preferences: Dict of aspect -> preference weight
                e.g., {"cleanliness": 0.9, "location": 0.8}
            n: Number of recommendations
            
        Returns:
            List of recommendation dictionaries
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Call train() first.")
        
        # Build aspect score
        aspect_expr = None
        for aspect, weight in aspect_preferences.items():
            col_name = f"avg_{aspect.lower()}"
            if col_name in self.hotel_vectors.columns:
                weighted_col = F.col(col_name) * weight
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
        
        # Get top hotels by aspect score
        top_hotels = self.hotel_vectors.withColumn(
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
                "model": "content_based",
                "method": "aspect_based"
            })
        
        return recommendations
    
    def save(self, path: str):
        """Save model artifacts."""
        logger.info(f"Saving content-based model to {path}...")
        
        self.hotel_vectors.write.mode("overwrite").parquet(f"{path}/hotel_vectors.parquet")
        self.user_preferences.write.mode("overwrite").parquet(f"{path}/user_preferences.parquet")
        
        logger.info("✅ Model saved")
    
    def load(self, path: str, spark: SparkSession):
        """Load model artifacts."""
        logger.info(f"Loading content-based model from {path}...")
        
        self.hotel_vectors = spark.read.parquet(f"{path}/hotel_vectors.parquet")
        self.user_preferences = spark.read.parquet(f"{path}/user_preferences.parquet")
        
        self.hotel_vectors.cache()
        self.user_preferences.cache()
        
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
    
    spark = create_spark_session("ContentBased-Test")
    
    try:
        # Load data
        train_df = spark.read.parquet("../data/processed/train.parquet")
        hotel_features_df = spark.read.parquet("../data/processed/features/hotel_features_complete.parquet")
        
        # Train model
        model = ContentBasedRecommender()
        model.train(train_df, hotel_features_df)
        
        # Test recommendations
        print("\n" + "="*80)
        print("TESTING RECOMMENDATIONS")
        print("="*80)
        
        # Get a sample user
        sample_user = train_df.select("user_id").first()[0]
        print(f"\n👤 Recommendations for user: {sample_user}")
        
        user_recs = model.recommend_for_user(sample_user, n=10)
        for i, rec in enumerate(user_recs, 1):
            print(f"  {i}. {rec['hotel_id']}: {rec['score']:.3f}")
        
        # Test similar hotels
        sample_hotel = hotel_features_df.select("hotel_id").first()[0]
        print(f"\n🏨 Hotels similar to: {sample_hotel}")
        
        similar_hotels = model.recommend_similar_hotels(sample_hotel, n=5)
        for i, rec in enumerate(similar_hotels, 1):
            print(f"  {i}. {rec['hotel_id']}: {rec['score']:.3f}")
        
        # Test aspect-based recommendations
        print(f"\n⭐ Top hotels for cleanliness and location:")
        aspect_recs = model.recommend_by_aspects({
            "cleanliness": 0.6,
            "location": 0.4
        }, n=5)
        for i, rec in enumerate(aspect_recs, 1):
            print(f"  {i}. {rec['hotel_id']}: {rec['score']:.3f}")
        
        # Save model
        model.save("../artifacts/models/content_based")
        print("\n✅ Model saved to artifacts/models/content_based")
        
    finally:
        stop_spark_session()

"""
Hotel Feature Engineering

Extracts features about hotels from their review history.
"""
import logging
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.window import Window

logger = logging.getLogger(__name__)


def compute_hotel_popularity(df: DataFrame) -> DataFrame:
    """
    Compute popularity metrics for each hotel.
    
    Features:
    - Total review count
    - Average reviews per year
    - Review count trend
    
    Args:
        df: Reviews DataFrame
        
    Returns:
        DataFrame with hotel popularity metrics
    """
    logger.info("Computing hotel popularity metrics...")
    
    hotel_pop = df.groupBy("hotel_id").agg(
        F.count("*").alias("hotel_review_count"),
        F.countDistinct("user_id").alias("hotel_unique_reviewers")
    )
    
    # Compute reviews by year for trending
    reviews_by_year = df.groupBy("hotel_id", "post_year") \
        .agg(F.count("*").alias("year_count"))
    
    # Calculate trend (recent years vs older years)
    window_spec = Window.partitionBy("hotel_id").orderBy(F.desc("post_year"))
    
    reviews_with_rank = reviews_by_year.withColumn(
        "year_rank",
        F.row_number().over(window_spec)
    )
    
    recent_reviews = reviews_with_rank.filter(F.col("year_rank") <= 2) \
        .groupBy("hotel_id") \
        .agg(F.sum("year_count").alias("recent_reviews"))
    
    older_reviews = reviews_with_rank.filter(F.col("year_rank") > 2) \
        .groupBy("hotel_id") \
        .agg(F.sum("year_count").alias("older_reviews"))
    
    # Join trending metrics
    hotel_pop = hotel_pop \
        .join(recent_reviews, "hotel_id", "left") \
        .join(older_reviews, "hotel_id", "left") \
        .fillna(0, subset=["recent_reviews", "older_reviews"])
    
    # Calculate trend ratio
    hotel_pop = hotel_pop.withColumn(
        "review_trend",
        F.when(
            F.col("older_reviews") > 0,
            F.col("recent_reviews") / F.col("older_reviews")
        ).otherwise(1.0)
    )
    
    logger.info(f"Computed popularity for {hotel_pop.count():,} hotels")
    
    return hotel_pop.drop("recent_reviews", "older_reviews")


def compute_hotel_rating_stats(df: DataFrame) -> DataFrame:
    """
    Compute rating statistics for each hotel.
    
    Features:
    - Average overall rating
    - Rating standard deviation
    - Rating distribution (% of 5-star, 4-star, etc.)
    
    Args:
        df: Reviews DataFrame
        
    Returns:
        DataFrame with hotel rating statistics
    """
    logger.info("Computing hotel rating statistics...")
    
    hotel_ratings = df.groupBy("hotel_id").agg(
        F.mean("overall").alias("hotel_avg_rating"),
        F.stddev("overall").alias("hotel_rating_std"),
        F.min("overall").alias("hotel_min_rating"),
        F.max("overall").alias("hotel_max_rating"),
        # Rating distribution
        F.sum(F.when(F.col("overall") >= 4.5, 1).otherwise(0)).alias("ratings_5star"),
        F.sum(F.when((F.col("overall") >= 3.5) & (F.col("overall") < 4.5), 1).otherwise(0)).alias("ratings_4star"),
        F.sum(F.when((F.col("overall") >= 2.5) & (F.col("overall") < 3.5), 1).otherwise(0)).alias("ratings_3star"),
        F.sum(F.when(F.col("overall") < 2.5, 1).otherwise(0)).alias("ratings_low")
    )
    
    # Fill null stddev
    hotel_ratings = hotel_ratings.fillna(0, subset=["hotel_rating_std"])
    
    # Calculate percentages
    hotel_ratings = hotel_ratings.withColumn(
        "pct_5star",
        F.col("ratings_5star") / (F.col("ratings_5star") + F.col("ratings_4star") + 
                                   F.col("ratings_3star") + F.col("ratings_low"))
    )
    
    hotel_ratings = hotel_ratings.withColumn(
        "pct_positive",
        (F.col("ratings_5star") + F.col("ratings_4star")) / 
        (F.col("ratings_5star") + F.col("ratings_4star") + 
         F.col("ratings_3star") + F.col("ratings_low"))
    )
    
    logger.info(f"Computed rating stats for {hotel_ratings.count():,} hotels")
    
    return hotel_ratings


def compute_hotel_aspect_ratings(df: DataFrame) -> DataFrame:
    """
    Compute average aspect ratings for each hotel.
    
    These are key features for content-based filtering.
    
    Args:
        df: Reviews DataFrame with aspect ratings
        
    Returns:
        DataFrame with hotel aspect ratings
    """
    logger.info("Computing hotel aspect ratings...")
    
    aspect_cols = ["cleanliness", "value", "location", "rooms", "service", "sleep_quality"]
    
    # Compute average for each aspect
    agg_exprs = [F.mean(col).alias(f"hotel_avg_{col}") for col in aspect_cols]
    agg_exprs.append(F.count(F.when(F.col("cleanliness").isNotNull(), 1)).alias("aspect_rating_count"))
    
    hotel_aspects = df.groupBy("hotel_id").agg(*agg_exprs)
    
    # Compute overall aspect score
    aspect_avg_cols = [f"hotel_avg_{col}" for col in aspect_cols]
    hotel_aspects = hotel_aspects.withColumn(
        "hotel_aspect_score",
        sum([F.coalesce(F.col(c), F.lit(0)) for c in aspect_avg_cols]) / 
        len(aspect_cols)
    )
    
    logger.info(f"Computed aspect ratings for {hotel_aspects.count():,} hotels")
    
    return hotel_aspects


def compute_hotel_text_stats(df: DataFrame) -> DataFrame:
    """
    Compute text-related statistics for each hotel.
    
    Features:
    - Average review length for hotel
    - Percentage of reviews with text
    
    Args:
        df: Reviews DataFrame
        
    Returns:
        DataFrame with hotel text statistics
    """
    logger.info("Computing hotel text statistics...")
    
    hotel_text = df.groupBy("hotel_id").agg(
        F.mean("review_length").alias("hotel_avg_review_length"),
        F.mean(F.when(F.col("review_length") > 0, 1).otherwise(0)).alias("hotel_text_ratio")
    )
    
    logger.info(f"Computed text stats for {hotel_text.count():,} hotels")
    
    return hotel_text


def compute_hotel_consistency(df: DataFrame) -> DataFrame:
    """
    Compute consistency metrics for each hotel.
    
    Features:
    - Rating consistency (inverse of std dev)
    - Aspect rating consistency
    
    Args:
        df: Reviews DataFrame
        
    Returns:
        DataFrame with consistency metrics
    """
    logger.info("Computing hotel consistency metrics...")
    
    # Overall rating consistency
    consistency = df.groupBy("hotel_id").agg(
        F.stddev("overall").alias("overall_std")
    ).fillna(0, subset=["overall_std"])
    
    # Consistency score (lower std = higher consistency)
    consistency = consistency.withColumn(
        "rating_consistency",
        1 / (1 + F.col("overall_std"))
    )
    
    # Aspect consistency (variance across aspects)
    aspect_cols = ["cleanliness", "value", "location", "rooms", "service", "sleep_quality"]
    
    aspect_variance = df.groupBy("hotel_id").agg(
        *[F.stddev(col).alias(f"{col}_std") for col in aspect_cols]
    )
    
    # Average aspect variance
    aspect_variance = aspect_variance.withColumn(
        "aspect_consistency",
        1 / (1 + (sum([F.coalesce(F.col(f"{col}_std"), F.lit(0)) 
                       for col in aspect_cols]) / len(aspect_cols)))
    )
    
    # Join
    consistency = consistency.join(
        aspect_variance.select("hotel_id", "aspect_consistency"),
        "hotel_id",
        "left"
    )
    
    logger.info(f"Computed consistency for {consistency.count():,} hotels")
    
    return consistency.drop("overall_std")


def build_hotel_features(df: DataFrame) -> DataFrame:
    """
    Build complete hotel feature matrix.
    
    Args:
        df: Cleaned reviews DataFrame
        
    Returns:
        DataFrame with all hotel features
    """
    logger.info("="*80)
    logger.info("Building Hotel Feature Matrix")
    logger.info("="*80)
    
    # Compute all feature groups
    popularity = compute_hotel_popularity(df)
    rating_stats = compute_hotel_rating_stats(df)
    aspect_ratings = compute_hotel_aspect_ratings(df)
    text_stats = compute_hotel_text_stats(df)
    consistency = compute_hotel_consistency(df)
    
    # Join all features
    logger.info("Joining hotel features...")
    hotel_features = popularity \
        .join(rating_stats, "hotel_id", "left") \
        .join(aspect_ratings, "hotel_id", "left") \
        .join(text_stats, "hotel_id", "left") \
        .join(consistency, "hotel_id", "left")
    
    # Show summary
    total_hotels = hotel_features.count()
    total_features = len(hotel_features.columns) - 1  # Exclude hotel_id
    
    logger.info(f"\n✅ Hotel Features Complete:")
    logger.info(f"  Total hotels: {total_hotels:,}")
    logger.info(f"  Total features: {total_features}")
    logger.info(f"  Features: {hotel_features.columns}")
    
    # Show sample
    logger.info("\nSample hotel features:")
    hotel_features.select(
        "hotel_id", "hotel_review_count", "hotel_avg_rating",
        "hotel_avg_cleanliness", "hotel_avg_location", "pct_5star"
    ).show(3, truncate=False)
    
    logger.info("="*80)
    
    return hotel_features


# Example usage
if __name__ == "__main__":
    from spark_setup import create_spark_session, stop_spark_session
    import sys
    sys.path.append('..')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    spark = create_spark_session("HotelFeatures-Test")
    
    try:
        # Load cleaned data
        df = spark.read.parquet("../data/processed/tripadvisor_cleaned.parquet")
        
        # Build hotel features
        hotel_features = build_hotel_features(df)
        
        # Save
        hotel_features.write.mode("overwrite").parquet(
            "../data/processed/hotel_features.parquet"
        )
        
        print("\n✅ Hotel features saved to data/processed/hotel_features.parquet")
        
    finally:
        stop_spark_session()

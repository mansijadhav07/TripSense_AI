"""
User Feature Engineering

Extracts features about users from their review history.
"""
import logging
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.window import Window

logger = logging.getLogger(__name__)


def compute_user_review_count(df: DataFrame) -> DataFrame:
    """
    Count total reviews per user.
    
    Args:
        df: Reviews DataFrame
        
    Returns:
        DataFrame with user_id and review_count
    """
    logger.info("Computing user review counts...")
    
    user_counts = df.groupBy("user_id").agg(
        F.count("*").alias("user_review_count")
    )
    
    logger.info(f"Computed review counts for {user_counts.count():,} users")
    
    return user_counts


def compute_user_rating_stats(df: DataFrame) -> DataFrame:
    """
    Compute rating statistics per user.
    
    Features:
    - Average rating given by user
    - Standard deviation of ratings
    - Min/max ratings
    
    Args:
        df: Reviews DataFrame with overall ratings
        
    Returns:
        DataFrame with user rating statistics
    """
    logger.info("Computing user rating statistics...")
    
    user_stats = df.groupBy("user_id").agg(
        F.mean("overall").alias("user_avg_rating"),
        F.stddev("overall").alias("user_rating_std"),
        F.min("overall").alias("user_min_rating"),
        F.max("overall").alias("user_max_rating")
    )
    
    # Fill null stddev with 0 (users with only 1 review)
    user_stats = user_stats.fillna(0, subset=["user_rating_std"])
    
    # User harshness: deviation from average rating
    avg_overall = df.select(F.mean("overall")).collect()[0][0]
    user_stats = user_stats.withColumn(
        "user_harshness",
        F.col("user_avg_rating") - F.lit(avg_overall)
    )
    
    logger.info(f"Computed rating stats for {user_stats.count():,} users")
    
    return user_stats


def compute_user_aspect_preferences(df: DataFrame) -> DataFrame:
    """
    Compute average aspect ratings per user to understand preferences.
    
    Args:
        df: Reviews DataFrame with aspect ratings
        
    Returns:
        DataFrame with user aspect preferences
    """
    logger.info("Computing user aspect preferences...")
    
    aspect_cols = ["cleanliness", "value", "location", "rooms", "service", "sleep_quality"]
    
    # Compute average for each aspect
    agg_exprs = [F.mean(col).alias(f"user_avg_{col}") for col in aspect_cols]
    
    user_aspects = df.groupBy("user_id").agg(*agg_exprs)
    
    # Fill nulls with overall average for that aspect
    for col in aspect_cols:
        col_avg = df.select(F.mean(col)).collect()[0][0]
        if col_avg:
            user_aspects = user_aspects.fillna(col_avg, subset=[f"user_avg_{col}"])
    
    logger.info(f"Computed aspect preferences for {user_aspects.count():,} users")
    
    return user_aspects


def compute_user_text_stats(df: DataFrame) -> DataFrame:
    """
    Compute text-related statistics per user.
    
    Features:
    - Average review length
    - Percentage of reviews with text
    - Total word count
    
    Args:
        df: Reviews DataFrame with review_length
        
    Returns:
        DataFrame with user text statistics
    """
    logger.info("Computing user text statistics...")
    
    user_text = df.groupBy("user_id").agg(
        F.mean("review_length").alias("user_avg_review_length"),
        F.sum("review_length").alias("user_total_word_count"),
        F.mean(F.when(F.col("review_length") > 0, 1).otherwise(0)).alias("user_text_ratio")
    )
    
    logger.info(f"Computed text stats for {user_text.count():,} users")
    
    return user_text


def compute_user_temporal_features(df: DataFrame) -> DataFrame:
    """
    Compute temporal features per user.
    
    Features:
    - Days since first review
    - Days since last review
    - Review frequency (reviews per year)
    
    Args:
        df: Reviews DataFrame with post_year and post_month
        
    Returns:
        DataFrame with user temporal features
    """
    logger.info("Computing user temporal features...")
    
    # Convert post_year and post_month to approximate date
    df_with_date = df.withColumn(
        "review_date",
        F.make_date(
            F.col("post_year"),
            F.col("post_month"),
            F.lit(1)  # Use first day of month
        )
    )
    
    user_temporal = df_with_date.groupBy("user_id").agg(
        F.min("review_date").alias("first_review_date"),
        F.max("review_date").alias("last_review_date"),
        F.count("*").alias("total_reviews")
    )
    
    # Calculate days active and review frequency
    user_temporal = user_temporal.withColumn(
        "days_active",
        F.datediff(F.col("last_review_date"), F.col("first_review_date"))
    )
    
    user_temporal = user_temporal.withColumn(
        "reviews_per_year",
        F.when(
            F.col("days_active") > 0,
            F.col("total_reviews") / (F.col("days_active") / 365.0)
        ).otherwise(F.col("total_reviews"))
    )
    
    # Days since last review (from current date)
    user_temporal = user_temporal.withColumn(
        "days_since_last_review",
        F.datediff(F.current_date(), F.col("last_review_date"))
    )
    
    logger.info(f"Computed temporal features for {user_temporal.count():,} users")
    
    return user_temporal.drop("total_reviews")  # Already have user_review_count


def build_user_features(df: DataFrame) -> DataFrame:
    """
    Build complete user feature matrix.
    
    Args:
        df: Cleaned reviews DataFrame
        
    Returns:
        DataFrame with all user features
    """
    logger.info("="*80)
    logger.info("Building User Feature Matrix")
    logger.info("="*80)
    
    # Compute all feature groups
    review_counts = compute_user_review_count(df)
    rating_stats = compute_user_rating_stats(df)
    aspect_prefs = compute_user_aspect_preferences(df)
    text_stats = compute_user_text_stats(df)
    temporal = compute_user_temporal_features(df)
    
    # Join all features
    logger.info("Joining user features...")
    user_features = review_counts \
        .join(rating_stats, "user_id", "left") \
        .join(aspect_prefs, "user_id", "left") \
        .join(text_stats, "user_id", "left") \
        .join(temporal, "user_id", "left")
    
    # Show summary
    total_users = user_features.count()
    total_features = len(user_features.columns) - 1  # Exclude user_id
    
    logger.info(f"\n✅ User Features Complete:")
    logger.info(f"  Total users: {total_users:,}")
    logger.info(f"  Total features: {total_features}")
    logger.info(f"  Features: {user_features.columns}")
    
    # Show sample
    logger.info("\nSample user features:")
    user_features.show(3, truncate=False)
    
    logger.info("="*80)
    
    return user_features


# Example usage
if __name__ == "__main__":
    from spark_setup import create_spark_session, stop_spark_session
    import sys
    sys.path.append('..')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    spark = create_spark_session("UserFeatures-Test")
    
    try:
        # Load cleaned data
        df = spark.read.parquet("../data/processed/tripadvisor_cleaned.parquet")
        
        # Build user features
        user_features = build_user_features(df)
        
        # Save
        user_features.write.mode("overwrite").parquet(
            "../data/processed/user_features.parquet"
        )
        
        print("\n✅ User features saved to data/processed/user_features.parquet")
        
    finally:
        stop_spark_session()

"""
Train/Test Data Splitting

Implements temporal split strategy for recommendation systems.
"""
import logging
from typing import Tuple
from pyspark.sql import DataFrame
from pyspark.sql import functions as F

logger = logging.getLogger(__name__)


def temporal_train_test_split(
    df: DataFrame,
    test_ratio: float = 0.2,
    date_column: str = "post_year_month"
) -> Tuple[DataFrame, DataFrame]:
    """
    Split data temporally: older reviews for training, recent for testing.
    
    This mimics real-world scenario where we predict future preferences.
    
    Args:
        df: Reviews DataFrame with date column
        test_ratio: Proportion of data for testing (default 0.2)
        date_column: Column to use for temporal ordering
        
    Returns:
        Tuple of (train_df, test_df)
    """
    logger.info(f"Performing temporal split with {test_ratio*100}% test size...")
    
    # Get total count
    total_count = df.count()
    test_count = int(total_count * test_ratio)
    train_count = total_count - test_count
    
    # Sort by date and assign row numbers
    from pyspark.sql.window import Window
    
    window_spec = Window.orderBy(F.col(date_column))
    df_with_rn = df.withColumn("row_num", F.row_number().over(window_spec))
    
    # Split based on row number
    train_df = df_with_rn.filter(F.col("row_num") <= train_count).drop("row_num")
    test_df = df_with_rn.filter(F.col("row_num") > train_count).drop("row_num")
    
    logger.info(f"✅ Split complete:")
    logger.info(f"  Training: {train_df.count():,} reviews ({train_df.count()/total_count*100:.1f}%)")
    logger.info(f"  Test: {test_df.count():,} reviews ({test_df.count()/total_count*100:.1f}%)")
    
    # Show date ranges
    train_dates = train_df.select(F.min(date_column), F.max(date_column)).collect()[0]
    test_dates = test_df.select(F.min(date_column), F.max(date_column)).collect()[0]
    
    logger.info(f"  Training date range: {train_dates[0]} to {train_dates[1]}")
    logger.info(f"  Test date range: {test_dates[0]} to {test_dates[1]}")
    
    return train_df, test_df


def identify_cold_start_cases(
    train_df: DataFrame,
    test_df: DataFrame,
    min_user_reviews: int = 5,
    min_hotel_reviews: int = 10
) -> dict:
    """
    Identify cold start users and hotels in test set.
    
    Cold start = users/hotels with insufficient training data.
    
    Args:
        train_df: Training reviews
        test_df: Test reviews
        min_user_reviews: Minimum reviews needed for user
        min_hotel_reviews: Minimum reviews needed for hotel
        
    Returns:
        Dictionary with cold start statistics
    """
    logger.info("Identifying cold start cases...")
    
    # Count reviews in training set
    train_user_counts = train_df.groupBy("user_id").agg(
        F.count("*").alias("train_review_count")
    )
    
    train_hotel_counts = train_df.groupBy("hotel_id").agg(
        F.count("*").alias("train_review_count")
    )
    
    # Join with test set
    test_with_user_counts = test_df.join(train_user_counts, "user_id", "left")
    test_with_hotel_counts = test_df.join(train_hotel_counts, "hotel_id", "left")
    
    # Identify cold start cases
    cold_start_users = test_with_user_counts.filter(
        (F.col("train_review_count").isNull()) | 
        (F.col("train_review_count") < min_user_reviews)
    ).count()
    
    cold_start_hotels = test_with_hotel_counts.filter(
        (F.col("train_review_count").isNull()) | 
        (F.col("train_review_count") < min_hotel_reviews)
    ).count()
    
    # New users/hotels (never seen in training)
    new_users = test_with_user_counts.filter(
        F.col("train_review_count").isNull()
    ).count()
    
    new_hotels = test_with_hotel_counts.filter(
        F.col("train_review_count").isNull()
    ).count()
    
    total_test = test_df.count()
    
    results = {
        "total_test_reviews": total_test,
        "cold_start_user_reviews": cold_start_users,
        "cold_start_hotel_reviews": cold_start_hotels,
        "new_user_reviews": new_users,
        "new_hotel_reviews": new_hotels,
        "cold_start_user_pct": (cold_start_users / total_test * 100) if total_test > 0 else 0,
        "cold_start_hotel_pct": (cold_start_hotels / total_test * 100) if total_test > 0 else 0
    }
    
    logger.info(f"✅ Cold start analysis:")
    logger.info(f"  Cold start user cases: {cold_start_users:,} ({results['cold_start_user_pct']:.1f}%)")
    logger.info(f"  Cold start hotel cases: {cold_start_hotels:,} ({results['cold_start_hotel_pct']:.1f}%)")
    logger.info(f"  Completely new users: {new_users:,}")
    logger.info(f"  Completely new hotels: {new_hotels:,}")
    
    return results


def create_interaction_matrix(
    df: DataFrame,
    user_col: str = "user_id",
    item_col: str = "hotel_id",
    rating_col: str = "overall"
) -> DataFrame:
    """
    Create user-item interaction matrix for collaborative filtering.
    
    Args:
        df: Reviews DataFrame
        user_col: User ID column
        item_col: Item ID column
        rating_col: Rating column
        
    Returns:
        DataFrame with user-item-rating triples
    """
    logger.info("Creating interaction matrix...")
    
    # For multiple reviews of same user-item, take the most recent
    from pyspark.sql.window import Window
    
    window_spec = Window.partitionBy(user_col, item_col).orderBy(F.desc("review_id"))
    
    interactions = df.withColumn("rn", F.row_number().over(window_spec)) \
        .filter(F.col("rn") == 1) \
        .select(user_col, item_col, rating_col) \
        .drop("rn")
    
    num_interactions = interactions.count()
    num_users = interactions.select(user_col).distinct().count()
    num_items = interactions.select(item_col).distinct().count()
    
    logger.info(f"✅ Interaction matrix created:")
    logger.info(f"  Users: {num_users:,}")
    logger.info(f"  Items: {num_items:,}")
    logger.info(f"  Interactions: {num_interactions:,}")
    logger.info(f"  Sparsity: {(1 - num_interactions/(num_users*num_items))*100:.4f}%")
    
    return interactions


def split_and_prepare_data(
    df: DataFrame,
    test_ratio: float = 0.2,
    output_dir: str = "../data/processed/splits"
) -> dict:
    """
    Complete data splitting and preparation pipeline.
    
    Args:
        df: Cleaned reviews DataFrame
        test_ratio: Proportion for test set
        output_dir: Directory to save outputs
        
    Returns:
        Dictionary with dataset information
    """
    logger.info("="*80)
    logger.info("DATA SPLITTING & PREPARATION")
    logger.info("="*80)
    
    # Temporal split
    train_df, test_df = temporal_train_test_split(df, test_ratio)
    
    # Cold start analysis
    cold_start_stats = identify_cold_start_cases(train_df, test_df)
    
    # Create interaction matrices
    logger.info("\nCreating interaction matrices...")
    train_interactions = create_interaction_matrix(train_df)
    test_interactions = create_interaction_matrix(test_df)
    
    # Save datasets
    logger.info(f"\nSaving datasets to {output_dir}...")
    
    train_df.write.mode("overwrite").parquet(f"{output_dir}/train_reviews.parquet")
    test_df.write.mode("overwrite").parquet(f"{output_dir}/test_reviews.parquet")
    train_interactions.write.mode("overwrite").parquet(f"{output_dir}/train_interactions.parquet")
    test_interactions.write.mode("overwrite").parquet(f"{output_dir}/test_interactions.parquet")
    
    logger.info("✅ All datasets saved")
    
    # Return summary
    results = {
        "train_reviews": train_df.count(),
        "test_reviews": test_df.count(),
        "train_interactions": train_interactions.count(),
        "test_interactions": test_interactions.count(),
        **cold_start_stats
    }
    
    logger.info("\n" + "="*80)
    logger.info("SPLITTING COMPLETE")
    logger.info("="*80)
    
    return results


# Example usage
if __name__ == "__main__":
    import sys
    sys.path.append('..')
    from spark_setup import create_spark_session, stop_spark_session
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    spark = create_spark_session("DataSplitting-Test")
    
    try:
        # Load cleaned data with text features
        df = spark.read.parquet("../data/processed/features/reviews_with_text_features.parquet")
        
        # Split and prepare
        results = split_and_prepare_data(df)
        
        # Save results
        import json
        with open("../data/processed/splits/split_info.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print("\n✅ Data splitting complete!")
        print(json.dumps(results, indent=2))
        
    finally:
        stop_spark_session()

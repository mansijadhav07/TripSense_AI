"""
Data Cleaning Pipeline

Cleans and standardizes TripAdvisor dataset.
"""
import logging
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.window import Window

logger = logging.getLogger(__name__)


def remove_duplicates(df: DataFrame) -> DataFrame:
    """
    Remove duplicate records based on user_id, hotel_id, and post_date.
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame without duplicates
    """
    logger.info("Removing duplicates...")
    
    initial_count = df.count()
    
    # Remove duplicates based on key columns
    df_clean = df.dropDuplicates(["user_id", "hotel_id", "post_date"])
    
    final_count = df_clean.count()
    removed = initial_count - final_count
    
    logger.info(f"Removed {removed:,} duplicate records ({removed/initial_count*100:.2f}%)")
    
    return df_clean


def handle_missing_values(df: DataFrame) -> DataFrame:
    """
    Handle missing values in the dataset.
    
    Strategy:
    - Drop rows with missing critical fields (user_id, hotel_id, overall)
    - Keep rows with missing aspect ratings (they provide overall rating)
    - Keep rows with missing text (some reviews don't have text)
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with missing values handled
    """
    logger.info("Handling missing values...")
    
    initial_count = df.count()
    
    # Drop rows missing critical fields
    df_clean = df.filter(
        F.col("user_id").isNotNull() &
        F.col("hotel_id").isNotNull() &
        F.col("overall").isNotNull()
    )
    
    final_count = df_clean.count()
    removed = initial_count - final_count
    
    logger.info(f"Removed {removed:,} records with missing critical fields")
    
    # Log null counts for each column
    null_counts = df_clean.select([
        F.sum(F.col(c).isNull().cast("int")).alias(c)
        for c in df_clean.columns
    ]).collect()[0].asDict()
    
    logger.info("Null counts after cleaning:")
    for col, count in sorted(null_counts.items(), key=lambda x: -x[1]):
        if count > 0:
            logger.info(f"  {col}: {count:,} ({count/final_count*100:.2f}%)")
    
    return df_clean


def standardize_columns(df: DataFrame) -> DataFrame:
    """
    Standardize column names and formats.
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with standardized columns
    """
    logger.info("Standardizing columns...")
    
    # Ensure column names are lowercase and snake_case (already are)
    # Add any necessary computed columns
    
    df_clean = df \
        .withColumn("review_id", F.monotonically_increasing_id()) \
        .withColumn("ingestion_timestamp", F.current_timestamp())
    
    logger.info("✅ Columns standardized")
    
    return df_clean


def validate_ratings(df: DataFrame) -> DataFrame:
    """
    Validate and clean rating values.
    
    Ratings should be between 1.0 and 5.0.
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with valid ratings
    """
    logger.info("Validating ratings...")
    
    initial_count = df.count()
    
    # Filter rows with invalid overall rating
    df_clean = df.filter(
        (F.col("overall") >= 1.0) & (F.col("overall") <= 5.0)
    )
    
    # For aspect ratings, set invalid values to null
    aspect_cols = ["cleanliness", "value", "location", "rooms", "service", "sleep_quality"]
    
    for col in aspect_cols:
        df_clean = df_clean.withColumn(
            col,
            F.when(
                (F.col(col).isNotNull()) & 
                ((F.col(col) < 1.0) | (F.col(col) > 5.0)),
                None
            ).otherwise(F.col(col))
        )
    
    final_count = df_clean.count()
    removed = initial_count - final_count
    
    if removed > 0:
        logger.warning(f"Removed {removed:,} records with invalid ratings")
    else:
        logger.info("✅ All ratings are valid")
    
    return df_clean


def add_derived_fields(df: DataFrame) -> DataFrame:
    """
    Add derived/computed fields useful for analysis and modeling.
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with additional fields
    """
    logger.info("Adding derived fields...")
    
    df_enriched = df
    
    # Review text length
    df_enriched = df_enriched.withColumn(
        "review_length",
        F.when(F.col("text").isNotNull(), F.length(F.col("text"))).otherwise(0)
    )
    
    # Has text indicator
    df_enriched = df_enriched.withColumn(
        "has_text",
        F.col("review_length") > 0
    )
    
    # Count of aspect ratings provided
    aspect_cols = ["cleanliness", "value", "location", "rooms", "service", "sleep_quality"]
    df_enriched = df_enriched.withColumn(
        "aspect_count",
        sum([F.when(F.col(c).isNotNull(), 1).otherwise(0) for c in aspect_cols])
    )
    
    # Average of aspect ratings (where available)
    aspect_sum = sum([F.coalesce(F.col(c), F.lit(0)) for c in aspect_cols])
    df_enriched = df_enriched.withColumn(
        "aspect_avg",
        F.when(
            F.col("aspect_count") > 0,
            aspect_sum / F.col("aspect_count")
        ).otherwise(None)
    )
    
    # Rating deviation (overall vs aspect average)
    df_enriched = df_enriched.withColumn(
        "rating_deviation",
        F.when(
            F.col("aspect_avg").isNotNull(),
            F.col("overall") - F.col("aspect_avg")
        ).otherwise(None)
    )
    
    # Year-month for temporal analysis
    df_enriched = df_enriched.withColumn(
        "post_year_month",
        F.concat(
            F.col("post_year").cast("string"),
            F.lit("-"),
            F.lpad(F.col("post_month").cast("string"), 2, "0")
        )
    )
    
    logger.info(f"✅ Added {len(df_enriched.columns) - len(df.columns)} derived fields")
    
    return df_enriched


def clean_tripadvisor_data(df: DataFrame) -> DataFrame:
    """
    Main cleaning pipeline for TripAdvisor data.
    
    Args:
        df: Raw DataFrame from ingestion
        
    Returns:
        Cleaned DataFrame ready for feature engineering
    """
    logger.info("="*80)
    logger.info("Starting Data Cleaning Pipeline")
    logger.info("="*80)
    
    # Pipeline stages
    df_clean = df
    df_clean = remove_duplicates(df_clean)
    df_clean = handle_missing_values(df_clean)
    df_clean = validate_ratings(df_clean)
    df_clean = standardize_columns(df_clean)
    df_clean = add_derived_fields(df_clean)
    
    # Final statistics
    logger.info("\nCleaning Statistics:")
    logger.info(f"  Initial records: {df.count():,}")
    logger.info(f"  Final records: {df_clean.count():,}")
    logger.info(f"  Columns: {len(df.columns)} → {len(df_clean.columns)}")
    
    # Show sample
    logger.info("\nSample cleaned data:")
    df_clean.select(
        "review_id", "user_id", "hotel_id", "overall", 
        "aspect_avg", "review_length", "post_year_month"
    ).show(5, truncate=50)
    
    logger.info("="*80)
    logger.info("Data Cleaning Complete")
    logger.info("="*80)
    
    return df_clean


# Example usage
if __name__ == "__main__":
    from spark_setup import create_spark_session, stop_spark_session
    from data_ingestion import ingest_tripadvisor_data
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create Spark session
    spark = create_spark_session("TripSense-DataCleaning")
    
    try:
        # Load raw data
        data_path = "../data/raw/tripadvisor_reviews.csv"
        df_raw = ingest_tripadvisor_data(spark, data_path, validate=False)
        
        # Clean data
        df_clean = clean_tripadvisor_data(df_raw)
        
        # Show statistics
        print(f"\nFinal Record Count: {df_clean.count():,}")
        print(f"Final Column Count: {len(df_clean.columns)}")
        
    finally:
        # Cleanup
        stop_spark_session()

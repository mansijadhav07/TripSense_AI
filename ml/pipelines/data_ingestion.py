"""
Data Ingestion Pipeline

Loads raw TripAdvisor dataset into Spark DataFrame and validates schema.
"""
import logging
from pathlib import Path
from typing import Optional

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import types as T

logger = logging.getLogger(__name__)


# Define expected schema for TripAdvisor dataset
TRIPADVISOR_SCHEMA = T.StructType([
    T.StructField("hotel_id", T.StringType(), nullable=False),
    T.StructField("user_id", T.StringType(), nullable=False),
    T.StructField("overall", T.DoubleType(), nullable=False),
    T.StructField("text", T.StringType(), nullable=True),
    T.StructField("cleanliness", T.DoubleType(), nullable=True),
    T.StructField("value", T.DoubleType(), nullable=True),
    T.StructField("location", T.DoubleType(), nullable=True),
    T.StructField("rooms", T.DoubleType(), nullable=True),
    T.StructField("service", T.DoubleType(), nullable=True),
    T.StructField("sleep_quality", T.DoubleType(), nullable=True),
    T.StructField("stay_year", T.IntegerType(), nullable=True),
    T.StructField("post_month", T.IntegerType(), nullable=True),
    T.StructField("post_year", T.IntegerType(), nullable=True),
    T.StructField("hotel_name", T.StringType(), nullable=True),
    T.StructField("user_name", T.StringType(), nullable=True),
    T.StructField("post_date", T.StringType(), nullable=True),
])


def load_raw_data(
    spark: SparkSession,
    data_path: str,
    schema: Optional[T.StructType] = None
) -> DataFrame:
    """
    Load raw TripAdvisor CSV data into Spark DataFrame.
    
    Args:
        spark: Active SparkSession
        data_path: Path to raw CSV file
        schema: Optional explicit schema (uses TRIPADVISOR_SCHEMA if None)
        
    Returns:
        Spark DataFrame with raw data
    """
    logger.info(f"Loading raw data from: {data_path}")
    
    # Check file exists
    if not Path(data_path).exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    # Use defined schema or infer
    if schema is None:
        logger.info("Using predefined TripAdvisor schema")
        schema = TRIPADVISOR_SCHEMA
    
    # Load CSV
    df = spark.read.format("csv") \
        .option("header", "true") \
        .option("inferSchema", "false") \
        .schema(schema) \
        .load(data_path)
    
    # Log statistics
    count = df.count()
    logger.info(f"Loaded {count:,} records with {len(df.columns)} columns")
    
    return df


def validate_schema(df: DataFrame, expected_columns: list) -> bool:
    """
    Validate that DataFrame has expected columns.
    
    Args:
        df: DataFrame to validate
        expected_columns: List of required column names
        
    Returns:
        True if validation passes
        
    Raises:
        ValueError: If required columns are missing
    """
    actual_columns = set(df.columns)
    expected_columns = set(expected_columns)
    
    missing = expected_columns - actual_columns
    extra = actual_columns - expected_columns
    
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    if extra:
        logger.warning(f"DataFrame has unexpected columns: {extra}")
    
    logger.info("✅ Schema validation passed")
    return True


def validate_data_types(df: DataFrame) -> bool:
    """
    Validate data types are as expected.
    
    Args:
        df: DataFrame to validate
        
    Returns:
        True if validation passes
    """
    logger.info("Validating data types...")
    
    # Check numeric columns
    numeric_cols = ["overall", "cleanliness", "value", "location", 
                   "rooms", "service", "sleep_quality"]
    
    for col in numeric_cols:
        if col in df.columns:
            dtype = dict(df.dtypes)[col]
            if dtype not in ["double", "float", "int", "bigint"]:
                logger.warning(f"Column {col} has unexpected type: {dtype}")
    
    logger.info("✅ Data type validation completed")
    return True


def ingest_tripadvisor_data(
    spark: SparkSession,
    input_path: str,
    validate: bool = True
) -> DataFrame:
    """
    Main ingestion pipeline for TripAdvisor data.
    
    Args:
        spark: Active SparkSession
        input_path: Path to raw CSV file
        validate: Whether to run validation checks
        
    Returns:
        DataFrame with ingested data
    """
    logger.info("="*80)
    logger.info("Starting Data Ingestion Pipeline")
    logger.info("="*80)
    
    # Load data
    df = load_raw_data(spark, input_path)
    
    # Validation
    if validate:
        required_cols = ["hotel_id", "user_id", "overall"]
        validate_schema(df, required_cols)
        validate_data_types(df)
    
    # Show sample
    logger.info("\nSample data:")
    df.show(5, truncate=50)
    
    logger.info("\nSchema:")
    df.printSchema()
    
    logger.info("="*80)
    logger.info("Data Ingestion Complete")
    logger.info("="*80)
    
    return df


# Example usage
if __name__ == "__main__":
    from spark_setup import create_spark_session, stop_spark_session
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create Spark session
    spark = create_spark_session("TripSense-DataIngestion")
    
    # Define data path
    data_path = "../data/raw/tripadvisor_reviews.csv"
    
    try:
        # Run ingestion
        df = ingest_tripadvisor_data(spark, data_path)
        
        # Show statistics
        print(f"\nTotal Records: {df.count():,}")
        print(f"Total Columns: {len(df.columns)}")
        
    finally:
        # Cleanup
        stop_spark_session()

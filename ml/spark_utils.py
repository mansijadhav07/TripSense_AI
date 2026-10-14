"""
Spark Utility Functions
"""
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StructType


logger = logging.getLogger(__name__)


def read_csv(
    spark: SparkSession,
    path: str,
    header: bool = True,
    infer_schema: bool = True,
    schema: Optional[StructType] = None,
    **options
) -> DataFrame:
    """
    Read CSV file into Spark DataFrame
    
    Args:
        spark: SparkSession
        path: Path to CSV file
        header: Whether CSV has header row
        infer_schema: Whether to infer schema automatically
        schema: Explicit schema (overrides infer_schema)
        **options: Additional CSV reading options
        
    Returns:
        Spark DataFrame
    """
    logger.info(f"Reading CSV from: {path}")
    
    reader = spark.read.format("csv")
    
    if header:
        reader = reader.option("header", "true")
    
    if schema is not None:
        reader = reader.schema(schema)
    elif infer_schema:
        reader = reader.option("inferSchema", "true")
    
    # Apply additional options
    for key, value in options.items():
        reader = reader.option(key, value)
    
    df = reader.load(path)
    
    logger.info(f"Read {df.count():,} rows with {len(df.columns)} columns")
    
    return df


def read_parquet(
    spark: SparkSession,
    path: str,
    columns: Optional[List[str]] = None
) -> DataFrame:
    """
    Read Parquet file into Spark DataFrame
    
    Args:
        spark: SparkSession
        path: Path to Parquet file/directory
        columns: Specific columns to read (reads all if None)
        
    Returns:
        Spark DataFrame
    """
    logger.info(f"Reading Parquet from: {path}")
    
    df = spark.read.parquet(path)
    
    if columns:
        df = df.select(columns)
        logger.info(f"Selected {len(columns)} columns")
    
    logger.info(f"Read {df.count():,} rows")
    
    return df


def write_parquet(
    df: DataFrame,
    path: str,
    mode: str = "overwrite",
    partition_by: Optional[List[str]] = None,
    compression: str = "snappy"
):
    """
    Write DataFrame to Parquet format
    
    Args:
        df: DataFrame to write
        path: Output path
        mode: Write mode (overwrite, append, etc.)
        partition_by: Columns to partition by
        compression: Compression codec (snappy, gzip, etc.)
    """
    logger.info(f"Writing Parquet to: {path}")
    logger.info(f"Mode: {mode}, Compression: {compression}")
    
    writer = df.write.mode(mode).option("compression", compression)
    
    if partition_by:
        writer = writer.partitionBy(*partition_by)
        logger.info(f"Partitioning by: {partition_by}")
    
    writer.parquet(path)
    
    logger.info(f"Successfully wrote {df.count():,} rows")


def show_dataframe_info(df: DataFrame, name: str = "DataFrame"):
    """
    Display comprehensive DataFrame information
    
    Args:
        df: DataFrame to inspect
        name: Name for logging
    """
    print(f"\n{'='*80}")
    print(f"{name} Information")
    print(f"{'='*80}")
    
    # Row count
    count = df.count()
    print(f"\nRow Count: {count:,}")
    
    # Schema
    print(f"\nSchema:")
    df.printSchema()
    
    # Column count and names
    print(f"\nColumns ({len(df.columns)}):")
    print(", ".join(df.columns))
    
    # Sample data
    print(f"\nSample Data (5 rows):")
    df.show(5, truncate=50)
    
    # Basic statistics
    print(f"\nSummary Statistics:")
    df.describe().show()
    
    # Null counts
    print(f"\nNull Counts:")
    null_counts = df.select([
        F.sum(F.col(c).isNull().cast("int")).alias(c)
        for c in df.columns
    ])
    null_counts.show(truncate=False)
    
    print(f"{'='*80}\n")


def get_data_quality_metrics(df: DataFrame) -> Dict[str, Any]:
    """
    Calculate data quality metrics for DataFrame
    
    Args:
        df: DataFrame to analyze
        
    Returns:
        Dictionary of quality metrics
    """
    total_rows = df.count()
    total_cols = len(df.columns)
    
    # Null counts per column
    null_counts = {}
    for col in df.columns:
        null_count = df.filter(F.col(col).isNull()).count()
        null_counts[col] = {
            "count": null_count,
            "percentage": (null_count / total_rows * 100) if total_rows > 0 else 0
        }
    
    # Duplicate rows
    duplicate_count = total_rows - df.distinct().count()
    
    metrics = {
        "total_rows": total_rows,
        "total_columns": total_cols,
        "duplicate_rows": duplicate_count,
        "duplicate_percentage": (duplicate_count / total_rows * 100) if total_rows > 0 else 0,
        "null_counts": null_counts,
        "memory_usage_mb": df.rdd.map(lambda x: len(str(x))).sum() / (1024 * 1024)
    }
    
    return metrics


def cache_dataframe(df: DataFrame, name: str) -> DataFrame:
    """
    Cache DataFrame with logging
    
    Args:
        df: DataFrame to cache
        name: Name for logging
        
    Returns:
        Cached DataFrame
    """
    logger.info(f"Caching DataFrame: {name}")
    cached_df = df.cache()
    # Force caching by triggering an action
    count = cached_df.count()
    logger.info(f"Cached {count:,} rows")
    return cached_df


def unpersist_dataframe(df: DataFrame, name: str):
    """
    Unpersist (uncache) DataFrame with logging
    
    Args:
        df: DataFrame to unpersist
        name: Name for logging
    """
    logger.info(f"Unpersisting DataFrame: {name}")
    df.unpersist()


def repartition_dataframe(
    df: DataFrame,
    num_partitions: int,
    *cols
) -> DataFrame:
    """
    Repartition DataFrame for optimal processing
    
    Args:
        df: DataFrame to repartition
        num_partitions: Number of partitions
        *cols: Optional columns to partition by
        
    Returns:
        Repartitioned DataFrame
    """
    logger.info(f"Repartitioning to {num_partitions} partitions")
    
    if cols:
        logger.info(f"Partitioning by columns: {cols}")
        return df.repartition(num_partitions, *cols)
    else:
        return df.repartition(num_partitions)


def coalesce_dataframe(
    df: DataFrame,
    num_partitions: int
) -> DataFrame:
    """
    Coalesce DataFrame to fewer partitions
    
    Args:
        df: DataFrame to coalesce
        num_partitions: Target number of partitions
        
    Returns:
        Coalesced DataFrame
    """
    current_partitions = df.rdd.getNumPartitions()
    logger.info(f"Coalescing from {current_partitions} to {num_partitions} partitions")
    return df.coalesce(num_partitions)


# Example usage
if __name__ == "__main__":
    from spark_setup import create_spark_session, stop_spark_session
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create Spark session
    spark = create_spark_session("SparkUtils-Test")
    
    # Create test data
    test_data = [
        (1, "Alice", 25, "Engineering"),
        (2, "Bob", 30, "Marketing"),
        (3, "Charlie", 35, "Engineering"),
        (4, "Diana", None, "Sales"),
        (5, "Eve", 28, None)
    ]
    
    df = spark.createDataFrame(
        test_data,
        ["id", "name", "age", "department"]
    )
    
    # Show DataFrame info
    show_dataframe_info(df, "Test DataFrame")
    
    # Get quality metrics
    metrics = get_data_quality_metrics(df)
    print("\nData Quality Metrics:")
    import json
    print(json.dumps(metrics, indent=2))
    
    # Clean up
    stop_spark_session()

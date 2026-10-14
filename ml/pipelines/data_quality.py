"""
Data Quality Checks

Validates data quality metrics and generates quality reports.
"""
import logging
from typing import Dict, Any
from pyspark.sql import DataFrame
from pyspark.sql import functions as F

logger = logging.getLogger(__name__)


def check_completeness(df: DataFrame) -> Dict[str, Any]:
    """
    Check data completeness (non-null percentages).
    
    Args:
        df: DataFrame to check
        
    Returns:
        Dictionary with completeness metrics
    """
    logger.info("Checking data completeness...")
    
    total_rows = df.count()
    
    completeness = {}
    for col in df.columns:
        non_null_count = df.filter(F.col(col).isNotNull()).count()
        completeness[col] = {
            "non_null_count": non_null_count,
            "null_count": total_rows - non_null_count,
            "completeness_pct": (non_null_count / total_rows * 100) if total_rows > 0 else 0
        }
    
    return completeness


def check_uniqueness(df: DataFrame, key_columns: list) -> Dict[str, Any]:
    """
    Check uniqueness of key columns.
    
    Args:
        df: DataFrame to check
        key_columns: List of columns that should be unique together
        
    Returns:
        Dictionary with uniqueness metrics
    """
    logger.info(f"Checking uniqueness for: {key_columns}")
    
    total_rows = df.count()
    unique_rows = df.select(key_columns).distinct().count()
    duplicate_rows = total_rows - unique_rows
    
    return {
        "total_rows": total_rows,
        "unique_rows": unique_rows,
        "duplicate_rows": duplicate_rows,
        "uniqueness_pct": (unique_rows / total_rows * 100) if total_rows > 0 else 0
    }


def check_value_ranges(df: DataFrame, numeric_columns: Dict[str, tuple]) -> Dict[str, Any]:
    """
    Check if numeric values fall within expected ranges.
    
    Args:
        df: DataFrame to check
        numeric_columns: Dict mapping column names to (min, max) tuples
        
    Returns:
        Dictionary with range validation results
    """
    logger.info("Checking value ranges...")
    
    range_checks = {}
    
    for col, (min_val, max_val) in numeric_columns.items():
        if col not in df.columns:
            continue
        
        total = df.filter(F.col(col).isNotNull()).count()
        valid = df.filter(
            (F.col(col) >= min_val) & (F.col(col) <= max_val)
        ).count()
        invalid = total - valid
        
        range_checks[col] = {
            "total": total,
            "valid": valid,
            "invalid": invalid,
            "validity_pct": (valid / total * 100) if total > 0 else 0
        }
    
    return range_checks


def check_distributions(df: DataFrame, columns: list) -> Dict[str, Any]:
    """
    Check statistical distributions of numeric columns.
    
    Args:
        df: DataFrame to check
        columns: List of numeric columns to analyze
        
    Returns:
        Dictionary with distribution statistics
    """
    logger.info("Checking distributions...")
    
    distributions = {}
    
    for col in columns:
        if col not in df.columns:
            continue
        
        stats = df.select(
            F.mean(col).alias("mean"),
            F.stddev(col).alias("stddev"),
            F.min(col).alias("min"),
            F.max(col).alias("max"),
            F.expr(f"percentile_approx({col}, 0.25)").alias("q25"),
            F.expr(f"percentile_approx({col}, 0.50)").alias("median"),
            F.expr(f"percentile_approx({col}, 0.75)").alias("q75")
        ).collect()[0]
        
        distributions[col] = {
            "mean": float(stats["mean"]) if stats["mean"] else None,
            "stddev": float(stats["stddev"]) if stats["stddev"] else None,
            "min": float(stats["min"]) if stats["min"] else None,
            "max": float(stats["max"]) if stats["max"] else None,
            "q25": float(stats["q25"]) if stats["q25"] else None,
            "median": float(stats["median"]) if stats["median"] else None,
            "q75": float(stats["q75"]) if stats["q75"] else None,
        }
    
    return distributions


def check_sparsity(df: DataFrame, user_col: str = "user_id", item_col: str = "hotel_id") -> Dict[str, Any]:
    """
    Calculate sparsity metrics for collaborative filtering.
    
    Args:
        df: DataFrame to check
        user_col: Name of user column
        item_col: Name of item column
        
    Returns:
        Dictionary with sparsity metrics
    """
    logger.info("Calculating sparsity metrics...")
    
    num_users = df.select(user_col).distinct().count()
    num_items = df.select(item_col).distinct().count()
    num_interactions = df.count()
    
    # Theoretical maximum interactions
    max_interactions = num_users * num_items
    
    # Sparsity
    sparsity = 1 - (num_interactions / max_interactions)
    
    # Average interactions per user
    avg_per_user = num_interactions / num_users if num_users > 0 else 0
    
    # Average interactions per item
    avg_per_item = num_interactions / num_items if num_items > 0 else 0
    
    return {
        "num_users": num_users,
        "num_items": num_items,
        "num_interactions": num_interactions,
        "max_possible_interactions": max_interactions,
        "sparsity": sparsity,
        "density": 1 - sparsity,
        "avg_interactions_per_user": avg_per_user,
        "avg_interactions_per_item": avg_per_item
    }


def generate_quality_report(df: DataFrame) -> Dict[str, Any]:
    """
    Generate comprehensive data quality report.
    
    Args:
        df: DataFrame to analyze
        
    Returns:
        Complete quality report dictionary
    """
    logger.info("="*80)
    logger.info("Generating Data Quality Report")
    logger.info("="*80)
    
    report = {}
    
    # Basic stats
    report["basic_stats"] = {
        "total_records": df.count(),
        "total_columns": len(df.columns),
        "columns": df.columns
    }
    
    # Completeness
    report["completeness"] = check_completeness(df)
    
    # Uniqueness
    report["uniqueness"] = check_uniqueness(df, ["user_id", "hotel_id", "post_date"])
    
    # Value ranges for ratings
    rating_ranges = {
        "overall": (1.0, 5.0),
        "cleanliness": (1.0, 5.0),
        "value": (1.0, 5.0),
        "location": (1.0, 5.0),
        "rooms": (1.0, 5.0),
        "service": (1.0, 5.0),
        "sleep_quality": (1.0, 5.0)
    }
    report["value_ranges"] = check_value_ranges(df, rating_ranges)
    
    # Distributions
    rating_cols = ["overall", "cleanliness", "value", "location", "rooms", "service", "sleep_quality"]
    report["distributions"] = check_distributions(df, rating_cols)
    
    # Sparsity
    report["sparsity"] = check_sparsity(df)
    
    # Print summary
    logger.info("\n📊 Quality Report Summary:")
    logger.info(f"  Total Records: {report['basic_stats']['total_records']:,}")
    logger.info(f"  Unique User-Hotel-Date combinations: {report['uniqueness']['unique_rows']:,}")
    logger.info(f"  Sparsity: {report['sparsity']['sparsity']*100:.4f}%")
    logger.info(f"  Avg reviews per user: {report['sparsity']['avg_interactions_per_user']:.2f}")
    logger.info(f"  Avg reviews per hotel: {report['sparsity']['avg_interactions_per_item']:.2f}")
    
    logger.info("\n📈 Rating Distributions:")
    for col in ["overall", "cleanliness", "value", "location"]:
        if col in report["distributions"] and report["distributions"][col]["mean"]:
            dist = report["distributions"][col]
            logger.info(f"  {col}: mean={dist['mean']:.2f}, median={dist['median']:.2f}, std={dist['stddev']:.2f}")
    
    logger.info("="*80)
    logger.info("Quality Report Complete")
    logger.info("="*80)
    
    return report


# Example usage
if __name__ == "__main__":
    from spark_setup import create_spark_session, stop_spark_session
    from data_ingestion import ingest_tripadvisor_data
    from data_cleaning import clean_tripadvisor_data
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create Spark session
    spark = create_spark_session("TripSense-DataQuality")
    
    try:
        # Load and clean data
        data_path = "../data/raw/tripadvisor_reviews.csv"
        df_raw = ingest_tripadvisor_data(spark, data_path, validate=False)
        df_clean = clean_tripadvisor_data(df_raw)
        
        # Generate quality report
        report = generate_quality_report(df_clean)
        
        # Save report
        import json
        with open("../data/processed/quality_report.json", "w") as f:
            # Convert non-serializable types
            def convert(obj):
                if isinstance(obj, (int, float, str, bool, type(None))):
                    return obj
                elif isinstance(obj, dict):
                    return {k: convert(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert(item) for item in obj]
                else:
                    return str(obj)
            
            json.dump(convert(report), f, indent=2)
        
        print("\n✅ Quality report saved to data/processed/quality_report.json")
        
    finally:
        # Cleanup
        stop_spark_session()

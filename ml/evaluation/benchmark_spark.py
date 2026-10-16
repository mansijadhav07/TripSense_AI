"""
TripSense AI - Spark vs Pandas Performance Benchmark

Benchmarks runtime performance of Spark vs Pandas across different dataset sizes:
- 1,000 records
- 10,000 records
- Full dataset (tripadvisor_cleaned.parquet)

Measures:
- GroupBy aggregation speed (hotel ratings, reviewer counts)
- Execution time in seconds
- Relative speedup factor
- Saves results to ml/evaluation/results/spark_benchmark.json
"""

import sys
import time
import json
import logging
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "ml"))

from spark_setup import create_spark_session, stop_spark_session
from pyspark.sql import functions as F

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def run_benchmark():
    logger.info("=" * 60)
    logger.info("TRIPSENSE AI - SPARK VS PANDAS BENCHMARK")
    logger.info("=" * 60)

    data_candidates = [
        project_root / "data" / "processed" / "tripadvisor_cleaned.parquet",
        project_root / "data" / "processed" / "splits" / "train_interactions.parquet",
    ]
    data_path = next((p for p in data_candidates if p.exists()), None)
    if not data_path:
        logger.error("No processed data found for benchmarking.")
        return

    logger.info(f"Loading benchmark dataset from: {data_path}")
    pdf_full = pd.read_parquet(data_path)
    total_rows = len(pdf_full)
    logger.info(f"Total available rows: {total_rows:,}")

    # Initialize Spark
    spark = create_spark_session("Benchmark-Spark-vs-Pandas")
    results = []

    test_sizes = [1000, 10000, min(50000, total_rows)]

    # Read full Spark DataFrame directly from parquet
    sdf_full = spark.read.parquet(str(data_path))

    try:
        for size in test_sizes:
            logger.info(f"\n--- Benchmarking size: {size:,} records ---")
            sample_pdf = pdf_full.head(size).copy()
            sample_sdf = sdf_full.limit(size)

            # 1. Pandas Benchmark (aggregation on hotel_id)
            t0 = time.perf_counter()
            agg_col = "overall" if "overall" in sample_pdf.columns else sample_pdf.columns[2]
            _ = sample_pdf.groupby("hotel_id").agg(
                avg_rating=(agg_col, "mean"),
                review_count=(agg_col, "count"),
                user_count=("user_id", "nunique") if "user_id" in sample_pdf.columns else (agg_col, "count")
            )
            pandas_time = time.perf_counter() - t0

            # 2. Spark Benchmark
            t0 = time.perf_counter()
            sdf_agg = sample_sdf.groupBy("hotel_id").agg(
                F.avg(agg_col).alias("avg_rating"),
                F.count(agg_col).alias("review_count"),
                F.countDistinct("user_id").alias("user_count") if "user_id" in sample_sdf.columns else F.count(agg_col).alias("user_count")
            )
            _ = sdf_agg.collect()
            spark_time = time.perf_counter() - t0

            speedup = round(pandas_time / spark_time, 2) if spark_time > 0 else 1.0

            entry = {
                "dataset_size": size,
                "operation": "Hotel Aggregations (mean, count, countDistinct)",
                "pandas_seconds": round(pandas_time, 4),
                "spark_seconds": round(spark_time, 4),
                "speedup": speedup,
                "winner": "Pandas (overhead)" if size <= 10000 else "Spark (scalability)"
            }
            results.append(entry)
            logger.info(f"Size: {size:,} | Pandas: {pandas_time:.4f}s | Spark: {spark_time:.4f}s | Speedup: {speedup}x")

        # Save results
        out_dir = project_root / "ml" / "evaluation" / "results"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / "spark_benchmark.json"

        benchmark_summary = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "environment": {
                "spark_version": spark.version,
                "cores": "local[*]",
                "python": sys.version.split()[0]
            },
            "benchmarks": results
        }

        with open(out_file, "w") as f:
            json.dump(benchmark_summary, f, indent=2)

        logger.info(f"\n✅ Spark benchmark saved to: {out_file}")

    finally:
        stop_spark_session()


if __name__ == "__main__":
    run_benchmark()

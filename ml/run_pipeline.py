"""
Main Pipeline Runner

Orchestrates the complete data pipeline from ingestion to cleaned Parquet output.
"""
import logging
import argparse
from pathlib import Path
from datetime import datetime

from spark_setup import create_spark_session, stop_spark_session
from spark_utils import write_parquet, show_dataframe_info
from pipelines.data_ingestion import ingest_tripadvisor_data
from pipelines.data_cleaning import clean_tripadvisor_data
from pipelines.data_quality import generate_quality_report

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def run_data_pipeline(
    input_path: str,
    output_path: str,
    skip_quality_report: bool = False
):
    """
    Run complete data pipeline.
    
    Args:
        input_path: Path to raw CSV file
        output_path: Path to save cleaned Parquet file
        skip_quality_report: Whether to skip quality report generation
    """
    logger.info("="*80)
    logger.info("TRIPSENSE AI - DATA PIPELINE")
    logger.info("="*80)
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")
    logger.info(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*80)
    
    # Create Spark session
    spark = create_spark_session("TripSense-Pipeline")
    
    try:
        # Stage 1: Data Ingestion
        logger.info("\n🔄 Stage 1/4: Data Ingestion")
        df_raw = ingest_tripadvisor_data(spark, input_path, validate=True)
        logger.info(f"✅ Ingested {df_raw.count():,} records")
        
        # Stage 2: Data Cleaning
        logger.info("\n🔄 Stage 2/4: Data Cleaning")
        df_clean = clean_tripadvisor_data(df_raw)
        logger.info(f"✅ Cleaned to {df_clean.count():,} records")
        
        # Stage 3: Quality Report
        if not skip_quality_report:
            logger.info("\n🔄 Stage 3/4: Quality Report")
            report = generate_quality_report(df_clean)
            logger.info("✅ Quality report generated")
        else:
            logger.info("\n⏭️  Stage 3/4: Quality Report (skipped)")
        
        # Stage 4: Save to Parquet
        logger.info("\n🔄 Stage 4/4: Save to Parquet")
        write_parquet(
            df_clean,
            output_path,
            mode="overwrite",
            compression="snappy"
        )
        logger.info(f"✅ Saved to {output_path}")
        
        # Final summary
        logger.info("\n"+"="*80)
        logger.info("PIPELINE COMPLETE")
        logger.info("="*80)
        logger.info(f"Input records: {df_raw.count():,}")
        logger.info(f"Output records: {df_clean.count():,}")
        logger.info(f"Output columns: {len(df_clean.columns)}")
        logger.info(f"Output path: {output_path}")
        logger.info(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*80)
        
        return df_clean
        
    except Exception as e:
        logger.error(f"❌ Pipeline failed: {str(e)}", exc_info=True)
        raise
    
    finally:
        # Cleanup
        stop_spark_session()


def main():
    """Command-line interface for pipeline."""
    parser = argparse.ArgumentParser(
        description="TripSense AI Data Pipeline",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "--input",
        type=str,
        default="../data/raw/tripadvisor_reviews.csv",
        help="Path to input CSV file"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default="../data/processed/tripadvisor_cleaned.parquet",
        help="Path to output Parquet file"
    )
    
    parser.add_argument(
        "--skip-quality",
        action="store_true",
        help="Skip quality report generation"
    )
    
    args = parser.parse_args()
    
    # Validate input exists
    if not Path(args.input).exists():
        logger.error(f"Input file not found: {args.input}")
        return 1
    
    # Create output directory if needed
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    
    # Run pipeline
    try:
        run_data_pipeline(
            input_path=args.input,
            output_path=args.output,
            skip_quality_report=args.skip_quality
        )
        return 0
    except Exception:
        return 1


if __name__ == "__main__":
    exit(main())

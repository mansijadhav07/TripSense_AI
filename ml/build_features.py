"""
Main Feature Engineering Pipeline

Orchestrates building all feature sets for TripSense AI.
"""
import logging
import argparse
import sys
from pathlib import Path
from datetime import datetime

# Ensure ml directory is on sys.path
ml_dir = Path(__file__).resolve().parent
if str(ml_dir) not in sys.path:
    sys.path.insert(0, str(ml_dir))

from spark_setup import create_spark_session, stop_spark_session
from features.user_features import build_user_features
from features.hotel_features import build_hotel_features
from features.text_features import build_text_features

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('feature_engineering.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def run_feature_engineering(
    input_path: str,
    output_dir: str
):
    """
    Run complete feature engineering pipeline.
    
    Args:
        input_path: Path to cleaned Parquet data
        output_dir: Directory to save feature outputs
    """
    logger.info("="*80)
    logger.info("TRIPSENSE AI - FEATURE ENGINEERING PIPELINE")
    logger.info("="*80)
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_dir}")
    logger.info(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*80)
    
    # Create Spark session
    spark = create_spark_session("TripSense-FeatureEngineering")
    
    try:
        # Load cleaned data
        logger.info("\n📥 Loading cleaned data...")
        df = spark.read.parquet(input_path)
        logger.info(f"Loaded {df.count():,} reviews")
        
        # Stage 1: User Features
        logger.info("\n🔄 Stage 1/4: Building User Features")
        user_features = build_user_features(df)
        user_output = f"{output_dir}/user_features.parquet"
        user_features.write.mode("overwrite").parquet(user_output)
        logger.info(f"✅ User features saved to {user_output}")
        
        # Stage 2: Hotel Features
        logger.info("\n🔄 Stage 2/4: Building Hotel Features")
        hotel_features = build_hotel_features(df)
        hotel_output = f"{output_dir}/hotel_features.parquet"
        hotel_features.write.mode("overwrite").parquet(hotel_output)
        logger.info(f"✅ Hotel features saved to {hotel_output}")
        
        # Stage 3: Text Features
        logger.info("\n🔄 Stage 3/4: Building Text/NLP Features")
        review_text_features, hotel_text_features = build_text_features(df)
        
        review_text_output = f"{output_dir}/reviews_with_text_features.parquet"
        review_text_features.write.mode("overwrite").parquet(review_text_output)
        logger.info(f"✅ Review text features saved to {review_text_output}")
        
        hotel_text_output = f"{output_dir}/hotel_text_features.parquet"
        hotel_text_features.write.mode("overwrite").parquet(hotel_text_output)
        logger.info(f"✅ Hotel text features saved to {hotel_text_output}")
        
        # Stage 4: Merge Hotel Features
        logger.info("\n🔄 Stage 4/4: Merging Hotel Feature Sets")
        hotel_complete = hotel_features.join(hotel_text_features, "hotel_id", "left")
        hotel_complete_output = f"{output_dir}/hotel_features_complete.parquet"
        hotel_complete.write.mode("overwrite").parquet(hotel_complete_output)
        logger.info(f"✅ Complete hotel features saved to {hotel_complete_output}")
        
        # Final summary
        logger.info("\n"+"="*80)
        logger.info("FEATURE ENGINEERING COMPLETE")
        logger.info("="*80)
        logger.info(f"User features: {user_features.count():,} users × {len(user_features.columns)} features")
        logger.info(f"Hotel features: {hotel_complete.count():,} hotels × {len(hotel_complete.columns)} features")
        logger.info(f"Review features: {review_text_features.count():,} reviews with text features")
        logger.info(f"\nOutput directory: {output_dir}")
        logger.info(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*80)
        
        return {
            "user_features": user_features,
            "hotel_features": hotel_complete,
            "review_features": review_text_features
        }
        
    except Exception as e:
        logger.error(f"❌ Feature engineering failed: {str(e)}", exc_info=True)
        raise
    
    finally:
        # Cleanup
        stop_spark_session()


def main():
    """Command-line interface for feature engineering."""
    parser = argparse.ArgumentParser(
        description="TripSense AI Feature Engineering Pipeline",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "--input",
        type=str,
        default="../data/processed/tripadvisor_cleaned.parquet",
        help="Path to cleaned Parquet file"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default="../data/processed/features",
        help="Output directory for features"
    )
    
    args = parser.parse_args()
    
    # Robust input path resolution
    input_p = Path(args.input)
    if not input_p.exists():
        repo_root = Path(__file__).resolve().parent.parent
        candidates = [
            repo_root / args.input.lstrip("../"),
            Path("data/processed/tripadvisor_cleaned.parquet"),
            Path("../data/processed/tripadvisor_cleaned.parquet"),
        ]
        found = next((c for c in candidates if c.exists()), None)
        if found:
            input_p = found
        else:
            logger.error(f"Input file not found: {args.input}")
            return 1
    
    # Robust output path resolution
    output_p = Path(args.output)
    if not output_p.is_absolute() and not output_p.parent.exists():
        repo_root = Path(__file__).resolve().parent.parent
        output_p = repo_root / args.output.lstrip("../")

    output_p.mkdir(parents=True, exist_ok=True)
    
    # Run feature engineering
    try:
        run_feature_engineering(
            input_path=str(input_p),
            output_dir=str(output_p)
        )
        return 0
    except Exception:
        return 1


if __name__ == "__main__":
    exit(main())

"""
Master Training Script for All Recommendation Models

Trains all 5 recommendation models:
1. Popularity-Based
2. Collaborative Filtering (ALS)
3. Content-Based
4. NLP/Sentiment
5. Hybrid Ensemble

Usage:
    python train_models.py --all                    # Train all models
    python train_models.py --model popularity       # Train specific model
    python train_models.py --model hybrid           # Train hybrid (requires others)
"""
import argparse
import logging
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from spark_setup import create_spark_session, stop_spark_session
from models import (
    PopularityRecommender,
    CollaborativeFilteringRecommender,
    ContentBasedRecommender,
    NLPSentimentRecommender,
    HybridEnsembleRecommender
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('training.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def load_data(spark):
    """Load all required datasets."""
    logger.info("\n" + "="*80)
    logger.info("LOADING DATA")
    logger.info("="*80)
    
    data_dir = Path(__file__).parent / "data" / "processed"
    features_dir = data_dir / "features"
    
    # Check if data exists
    if not (data_dir / "train.parquet").exists():
        logger.error("Training data not found. Please run data pipeline first:")
        logger.error("  python ml/run_pipeline.py")
        logger.error("  python ml/build_features.py")
        logger.error("  python ml/preprocessing/split_data.py")
        sys.exit(1)
    
    datasets = {}
    
    logger.info("Loading training data...")
    datasets['train'] = spark.read.parquet(str(data_dir / "train.parquet"))
    logger.info(f"  Train: {datasets['train'].count():,} reviews")
    
    logger.info("Loading test data...")
    datasets['test'] = spark.read.parquet(str(data_dir / "test.parquet"))
    logger.info(f"  Test: {datasets['test'].count():,} reviews")
    
    logger.info("Loading user features...")
    datasets['user_features'] = spark.read.parquet(str(features_dir / "user_features_complete.parquet"))
    logger.info(f"  Users: {datasets['user_features'].count():,}")
    
    logger.info("Loading hotel features...")
    datasets['hotel_features'] = spark.read.parquet(str(features_dir / "hotel_features_complete.parquet"))
    logger.info(f"  Hotels: {datasets['hotel_features'].count():,}")
    
    logger.info("Loading text features...")
    datasets['text_features'] = spark.read.parquet(str(features_dir / "text_features_complete.parquet"))
    logger.info(f"  Reviews with text features: {datasets['text_features'].count():,}")
    
    logger.info("✅ All data loaded successfully")
    
    return datasets


def train_popularity_model(datasets, save_path):
    """Train popularity-based model."""
    logger.info("\n" + "="*80)
    logger.info("TRAINING POPULARITY MODEL")
    logger.info("="*80)
    
    model = PopularityRecommender()
    model.train(
        datasets['train'],
        datasets['hotel_features']
    )
    
    # Save model
    model.save(save_path)
    logger.info(f"✅ Popularity model saved to {save_path}")
    
    return model


def train_collaborative_model(datasets, save_path):
    """Train collaborative filtering model."""
    logger.info("\n" + "="*80)
    logger.info("TRAINING COLLABORATIVE FILTERING MODEL")
    logger.info("="*80)
    
    model = CollaborativeFilteringRecommender(
        rank=50,
        max_iter=10,
        reg_param=0.1,
        implicit_prefs=False
    )
    
    model.train(
        datasets['train'],
        datasets['user_features'],
        datasets['hotel_features'],
        validation_df=datasets['test']
    )
    
    # Save model
    model.save(save_path)
    logger.info(f"✅ Collaborative filtering model saved to {save_path}")
    
    return model


def train_content_based_model(datasets, save_path):
    """Train content-based model."""
    logger.info("\n" + "="*80)
    logger.info("TRAINING CONTENT-BASED MODEL")
    logger.info("="*80)
    
    model = ContentBasedRecommender()
    model.train(
        datasets['train'],
        datasets['hotel_features'],
        datasets['user_features']
    )
    
    # Save model
    model.save(save_path)
    logger.info(f"✅ Content-based model saved to {save_path}")
    
    return model


def train_nlp_sentiment_model(datasets, save_path):
    """Train NLP/sentiment model."""
    logger.info("\n" + "="*80)
    logger.info("TRAINING NLP/SENTIMENT MODEL")
    logger.info("="*80)
    
    model = NLPSentimentRecommender()
    model.train(
        datasets['train'],
        datasets['text_features'],
        datasets['hotel_features']
    )
    
    # Save model
    model.save(save_path)
    logger.info(f"✅ NLP/Sentiment model saved to {save_path}")
    
    return model


def train_hybrid_ensemble(datasets, save_path):
    """Train hybrid ensemble model."""
    logger.info("\n" + "="*80)
    logger.info("TRAINING HYBRID ENSEMBLE MODEL")
    logger.info("="*80)
    
    model = HybridEnsembleRecommender()
    model.train(
        datasets['train'],
        datasets['user_features'],
        datasets['hotel_features'],
        datasets['text_features'],
        validation_df=datasets['test']
    )
    
    # Save model
    model.save(save_path)
    logger.info(f"✅ Hybrid ensemble saved to {save_path}")
    
    return model


def main():
    """Main training pipeline."""
    parser = argparse.ArgumentParser(description='Train TripSense AI Recommendation Models')
    parser.add_argument(
        '--model',
        type=str,
        choices=['popularity', 'collaborative', 'content', 'sentiment', 'hybrid', 'all'],
        default='all',
        help='Which model to train (default: all)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='artifacts/models',
        help='Output directory for trained models'
    )
    
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("\n" + "="*80)
    logger.info("TRIPSENSE AI MODEL TRAINING PIPELINE")
    logger.info("="*80)
    logger.info(f"Model: {args.model}")
    logger.info(f"Output: {args.output_dir}")
    
    # Create Spark session
    spark = create_spark_session("TripSense-ModelTraining")
    
    try:
        # Load data
        datasets = load_data(spark)
        
        # Train models based on selection
        if args.model in ['popularity', 'all']:
            train_popularity_model(datasets, str(output_dir / "popularity"))
        
        if args.model in ['collaborative', 'all']:
            train_collaborative_model(datasets, str(output_dir / "collaborative_filtering"))
        
        if args.model in ['content', 'all']:
            train_content_based_model(datasets, str(output_dir / "content_based"))
        
        if args.model in ['sentiment', 'all']:
            train_nlp_sentiment_model(datasets, str(output_dir / "nlp_sentiment"))
        
        if args.model in ['hybrid', 'all']:
            train_hybrid_ensemble(datasets, str(output_dir / "hybrid_ensemble"))
        
        logger.info("\n" + "="*80)
        logger.info("✅ TRAINING COMPLETE")
        logger.info("="*80)
        logger.info(f"\nModels saved to: {output_dir}")
        logger.info("\nNext steps:")
        logger.info("  1. Evaluate models: python ml/evaluate_models.py")
        logger.info("  2. Deploy to API: Update apps/api to load models")
        logger.info("  3. Test recommendations: Use API endpoints")
        
    except Exception as e:
        logger.error(f"\n❌ Training failed: {e}", exc_info=True)
        sys.exit(1)
    
    finally:
        stop_spark_session()


if __name__ == "__main__":
    main()

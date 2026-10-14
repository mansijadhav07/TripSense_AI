"""
Text and NLP Feature Engineering

Extracts features from review text using NLP techniques.
"""
import logging
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import FloatType, ArrayType, StringType

logger = logging.getLogger(__name__)


# UDF for sentiment analysis (placeholder - requires NLTK/TextBlob in production)
def sentiment_polarity_udf():
    """
    UDF to compute sentiment polarity from text.
    
    In production, this would use TextBlob or VADER.
    For now, we use a simple heuristic based on rating.
    """
    def compute_sentiment(text, rating):
        if text is None or len(text) == 0:
            # Use rating as proxy
            return (rating - 3.0) / 2.0  # Normalize to -1 to 1
        
        # Placeholder: In production, use:
        # from textblob import TextBlob
        # return TextBlob(text).sentiment.polarity
        
        # Simple heuristic for now
        positive_words = ['excellent', 'great', 'amazing', 'wonderful', 'perfect', 
                         'best', 'loved', 'fantastic', 'outstanding']
        negative_words = ['terrible', 'awful', 'horrible', 'worst', 'disappointing',
                         'dirty', 'bad', 'poor', 'never', 'avoid']
        
        text_lower = text.lower()
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        if pos_count + neg_count == 0:
            return (rating - 3.0) / 2.0
        
        return (pos_count - neg_count) / (pos_count + neg_count)
    
    return F.udf(compute_sentiment, FloatType())


def extract_keywords_udf():
    """
    UDF to extract key phrases from text.
    
    Simplified version - in production use TF-IDF or TextRank.
    """
    def extract_keywords(text):
        if text is None or len(text) < 10:
            return []
        
        # Simple keyword extraction (in production, use proper NLP)
        common_keywords = [
            'room', 'staff', 'location', 'clean', 'service',
            'breakfast', 'pool', 'view', 'comfortable', 'noise',
            'bathroom', 'bed', 'wifi', 'parking', 'restaurant'
        ]
        
        text_lower = text.lower()
        found_keywords = [kw for kw in common_keywords if kw in text_lower]
        
        return found_keywords[:5]  # Return top 5
    
    return F.udf(extract_keywords, ArrayType(StringType()))


def compute_text_sentiment(df: DataFrame) -> DataFrame:
    """
    Compute sentiment scores for review texts.
    
    Args:
        df: DataFrame with text and overall rating
        
    Returns:
        DataFrame with sentiment_score column
    """
    logger.info("Computing text sentiment scores...")
    
    sentiment_udf = sentiment_polarity_udf()
    
    df_with_sentiment = df.withColumn(
        "sentiment_score",
        sentiment_udf(F.col("text"), F.col("overall"))
    )
    
    logger.info("✅ Sentiment scores computed")
    
    return df_with_sentiment


def compute_text_keywords(df: DataFrame) -> DataFrame:
    """
    Extract keywords from review texts.
    
    Args:
        df: DataFrame with text column
        
    Returns:
        DataFrame with keywords array column
    """
    logger.info("Extracting keywords from reviews...")
    
    keywords_udf = extract_keywords_udf()
    
    df_with_keywords = df.withColumn(
        "keywords",
        keywords_udf(F.col("text"))
    )
    
    logger.info("✅ Keywords extracted")
    
    return df_with_keywords


def compute_text_features(df: DataFrame) -> DataFrame:
    """
    Compute various text-based features.
    
    Features:
    - Word count
    - Character count
    - Average word length
    - Sentence count (approximate)
    - Capitalization ratio
    - Punctuation ratio
    
    Args:
        df: DataFrame with text column
        
    Returns:
        DataFrame with text features
    """
    logger.info("Computing text features...")
    
    df_text = df.withColumn(
        "text_clean",
        F.when(F.col("text").isNotNull(), F.col("text")).otherwise("")
    )
    
    # Word count
    df_text = df_text.withColumn(
        "word_count",
        F.size(F.split(F.col("text_clean"), "\\s+"))
    )
    
    # Character count
    df_text = df_text.withColumn(
        "char_count",
        F.length(F.col("text_clean"))
    )
    
    # Average word length
    df_text = df_text.withColumn(
        "avg_word_length",
        F.when(
            F.col("word_count") > 0,
            F.col("char_count") / F.col("word_count")
        ).otherwise(0)
    )
    
    # Sentence count (approximate by counting periods, exclamation, question marks)
    df_text = df_text.withColumn(
        "sentence_count",
        F.size(F.split(F.col("text_clean"), "[.!?]+"))
    )
    
    # Exclamation and question marks (enthusiasm/concern indicators)
    df_text = df_text.withColumn(
        "exclamation_count",
        F.length(F.col("text_clean")) - F.length(F.regexp_replace(F.col("text_clean"), "!", ""))
    )
    
    df_text = df_text.withColumn(
        "question_count",
        F.length(F.col("text_clean")) - F.length(F.regexp_replace(F.col("text_clean"), "\\?", ""))
    )
    
    # Readability proxy (simple estimate)
    df_text = df_text.withColumn(
        "readability_score",
        206.835 - 1.015 * (F.col("word_count") / F.col("sentence_count")) - 
        84.6 * (F.col("char_count") / F.col("word_count"))
    )
    
    logger.info("✅ Text features computed")
    
    return df_text.drop("text_clean")


def aggregate_hotel_text_features(df: DataFrame) -> DataFrame:
    """
    Aggregate text features at hotel level.
    
    Args:
        df: DataFrame with text features
        
    Returns:
        DataFrame with hotel-level text aggregations
    """
    logger.info("Aggregating text features by hotel...")
    
    hotel_text = df.groupBy("hotel_id").agg(
        F.mean("sentiment_score").alias("hotel_avg_sentiment"),
        F.stddev("sentiment_score").alias("hotel_sentiment_std"),
        F.mean("word_count").alias("hotel_avg_word_count"),
        F.mean("readability_score").alias("hotel_avg_readability"),
        F.sum(F.when(F.col("sentiment_score") > 0.3, 1).otherwise(0)).alias("positive_review_count"),
        F.sum(F.when(F.col("sentiment_score") < -0.3, 1).otherwise(0)).alias("negative_review_count")
    )
    
    # Sentiment ratio
    hotel_text = hotel_text.withColumn(
        "positive_ratio",
        F.col("positive_review_count") / (
            F.col("positive_review_count") + F.col("negative_review_count") + 1
        )
    )
    
    logger.info(f"Aggregated text features for {hotel_text.count():,} hotels")
    
    return hotel_text


def build_text_features(df: DataFrame) -> DataFrame:
    """
    Build complete text feature set for reviews and hotels.
    
    Args:
        df: Cleaned reviews DataFrame
        
    Returns:
        Tuple of (review_text_features, hotel_text_features)
    """
    logger.info("="*80)
    logger.info("Building Text/NLP Features")
    logger.info("="*80)
    
    # Review-level features
    df_with_features = compute_text_features(df)
    df_with_features = compute_text_sentiment(df_with_features)
    df_with_features = compute_text_keywords(df_with_features)
    
    # Hotel-level aggregations
    hotel_text_features = aggregate_hotel_text_features(df_with_features)
    
    logger.info(f"\n✅ Text Features Complete:")
    logger.info(f"  Review-level features: {len(df_with_features.columns)}")
    logger.info(f"  Hotel-level features: {len(hotel_text_features.columns)}")
    
    # Show samples
    logger.info("\nSample review text features:")
    df_with_features.select(
        "review_id", "word_count", "sentiment_score", "readability_score", "keywords"
    ).show(3, truncate=50)
    
    logger.info("\nSample hotel text features:")
    hotel_text_features.select(
        "hotel_id", "hotel_avg_sentiment", "positive_ratio", "hotel_avg_word_count"
    ).show(3, truncate=False)
    
    logger.info("="*80)
    
    return df_with_features, hotel_text_features


# Example usage
if __name__ == "__main__":
    from spark_setup import create_spark_session, stop_spark_session
    import sys
    sys.path.append('..')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    spark = create_spark_session("TextFeatures-Test")
    
    try:
        # Load cleaned data
        df = spark.read.parquet("../data/processed/tripadvisor_cleaned.parquet")
        
        # Build text features
        review_features, hotel_features = build_text_features(df)
        
        # Save
        review_features.write.mode("overwrite").parquet(
            "../data/processed/reviews_with_text_features.parquet"
        )
        hotel_features.write.mode("overwrite").parquet(
            "../data/processed/hotel_text_features.parquet"
        )
        
        print("\n✅ Text features saved!")
        
    finally:
        stop_spark_session()

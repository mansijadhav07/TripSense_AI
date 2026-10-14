"""
Apache Spark Session Setup and Management
"""
import logging
from pathlib import Path
from typing import Optional

from pyspark.sql import SparkSession
from pyspark import SparkConf

from config.spark_config import SparkConfig, DEFAULT_CONFIG


logger = logging.getLogger(__name__)


class SparkSessionManager:
    """Manages Spark session lifecycle"""
    
    _instance: Optional[SparkSession] = None
    _config: Optional[SparkConfig] = None
    
    @classmethod
    def get_session(
        cls,
        config: Optional[SparkConfig] = None,
        force_new: bool = False
    ) -> SparkSession:
        """
        Get or create Spark session
        
        Args:
            config: Spark configuration (uses default if None)
            force_new: Force creation of new session
            
        Returns:
            SparkSession instance
        """
        if force_new and cls._instance is not None:
            cls.stop()
        
        if cls._instance is None:
            config = config or DEFAULT_CONFIG
            cls._config = config
            cls._instance = cls._create_session(config)
        
        return cls._instance
    
    @classmethod
    def _create_session(cls, config: SparkConfig) -> SparkSession:
        """Create new Spark session with configuration"""
        logger.info(f"Creating Spark session: {config.app_name}")
        
        # Create Spark configuration
        spark_conf = SparkConf()
        for key, value in config.to_dict().items():
            spark_conf.set(key, value)
        
        # Build session
        builder = SparkSession.builder.config(conf=spark_conf)
        
        # Enable Hive support if available
        try:
            spark = builder.enableHiveSupport().getOrCreate()
            logger.info("Hive support enabled")
        except Exception:
            spark = builder.getOrCreate()
            logger.warning("Hive support not available")
        
        # Set log level
        spark.sparkContext.setLogLevel(config.log_level)
        
        # Create checkpoint directory if it doesn't exist
        if config.checkpoint_dir:
            checkpoint_path = Path(config.checkpoint_dir)
            checkpoint_path.mkdir(parents=True, exist_ok=True)
            spark.sparkContext.setCheckpointDir(str(checkpoint_path))
            logger.info(f"Checkpoint directory: {checkpoint_path}")
        
        logger.info(f"Spark session created successfully")
        logger.info(f"Spark version: {spark.version}")
        logger.info(f"Spark UI: {spark.sparkContext.uiWebUrl}")
        
        return spark
    
    @classmethod
    def stop(cls):
        """Stop current Spark session"""
        if cls._instance is not None:
            logger.info("Stopping Spark session")
            cls._instance.stop()
            cls._instance = None
            cls._config = None
    
    @classmethod
    def get_config(cls) -> Optional[SparkConfig]:
        """Get current configuration"""
        return cls._config


def create_spark_session(
    app_name: str = "TripSense-AI",
    config: Optional[SparkConfig] = None
) -> SparkSession:
    """
    Convenience function to create/get Spark session
    
    Args:
        app_name: Application name
        config: Spark configuration
        
    Returns:
        SparkSession instance
    """
    if config is None:
        config = DEFAULT_CONFIG
        config.app_name = app_name
    
    return SparkSessionManager.get_session(config)


def stop_spark_session():
    """Convenience function to stop Spark session"""
    SparkSessionManager.stop()


# Example usage
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create session with default config
    print("Creating Spark session with default configuration...")
    spark = create_spark_session()
    
    # Show configuration
    print(f"\nSpark Configuration:")
    print(f"  App Name: {spark.sparkContext.appName}")
    print(f"  Version: {spark.version}")
    print(f"  Master: {spark.sparkContext.master}")
    print(f"  UI: {spark.sparkContext.uiWebUrl}")
    
    # Test basic operation
    print("\nTesting basic Spark operation...")
    test_data = [(1, "Alice", 4.5), (2, "Bob", 3.8), (3, "Charlie", 4.9)]
    df = spark.createDataFrame(test_data, ["id", "name", "rating"])
    
    print("\nTest DataFrame:")
    df.show()
    
    print(f"\nRow count: {df.count()}")
    print(f"Average rating: {df.agg({'rating': 'avg'}).collect()[0][0]:.2f}")
    
    # Stop session
    print("\nStopping Spark session...")
    stop_spark_session()
    
    print("Done!")

"""
Apache Spark Configuration
"""
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional


@dataclass
class SparkConfig:
    """Spark configuration settings"""
    
    # Application
    app_name: str = "TripSense-AI"
    
    # Memory Configuration
    driver_memory: str = "4g"
    executor_memory: str = "4g"
    
    # CPU Configuration
    executor_cores: int = 4
    default_parallelism: int = 8
    
    # Storage
    warehouse_dir: Optional[str] = None
    checkpoint_dir: Optional[str] = None
    
    # Optimization
    adaptive_execution: bool = True
    dynamic_allocation: bool = False
    
    # Logging
    log_level: str = "WARN"
    
    # Serialization
    serializer: str = "org.apache.spark.serializer.KryoSerializer"
    
    def __post_init__(self):
        """Set default paths"""
        project_root = Path(__file__).parent.parent.parent
        
        if self.warehouse_dir is None:
            self.warehouse_dir = str(project_root / "data" / "spark-warehouse")
        
        if self.checkpoint_dir is None:
            self.checkpoint_dir = str(project_root / "data" / "spark-checkpoint")
    
    def to_dict(self) -> Dict[str, str]:
        """Convert config to Spark configuration dictionary"""
        return {
            "spark.app.name": self.app_name,
            "spark.driver.memory": self.driver_memory,
            "spark.executor.memory": self.executor_memory,
            "spark.executor.cores": str(self.executor_cores),
            "spark.default.parallelism": str(self.default_parallelism),
            "spark.sql.warehouse.dir": self.warehouse_dir,
            "spark.sql.adaptive.enabled": str(self.adaptive_execution).lower(),
            "spark.dynamicAllocation.enabled": str(self.dynamic_allocation).lower(),
            "spark.serializer": self.serializer,
            # Optimization settings
            "spark.sql.shuffle.partitions": str(self.default_parallelism * 2),
            "spark.sql.autoBroadcastJoinThreshold": "10485760",  # 10MB
            # Arrow optimization
            "spark.sql.execution.arrow.pyspark.enabled": "true",
            "spark.sql.execution.arrow.pyspark.fallback.enabled": "true",
        }
    
    @classmethod
    def for_local_development(cls) -> "SparkConfig":
        """Configuration optimized for local development"""
        return cls(
            driver_memory="2g",
            executor_memory="2g",
            executor_cores=2,
            default_parallelism=4,
            log_level="INFO"
        )
    
    @classmethod
    def for_production(cls) -> "SparkConfig":
        """Configuration optimized for production"""
        return cls(
            driver_memory="8g",
            executor_memory="8g",
            executor_cores=8,
            default_parallelism=16,
            log_level="WARN",
            dynamic_allocation=True
        )


# Default configuration
DEFAULT_CONFIG = SparkConfig()

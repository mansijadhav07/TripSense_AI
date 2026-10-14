# Phase 2: Apache Spark Setup Guide

## Prerequisites

- Python 3.9+
- Java 8 or 11 (required for Spark)
- Minimum 8GB RAM recommended

## Installation Steps

### 1. Check Java Installation

```bash
java -version
```

If Java is not installed, install it:

**macOS:**
```bash
brew install openjdk@11
```

**Ubuntu/Linux:**
```bash
sudo apt-get update
sudo apt-get install openjdk-11-jdk
```

### 2. Install Python Dependencies

From the `ml/` directory:

```bash
# Install all ML dependencies
pip install -r requirements.txt

# Or install individually:
pip install pyspark==3.5.0
pip install pandas==2.1.3
pip install numpy==1.26.2
pip install pyarrow==14.0.1
```

### 3. Verify Installation

```bash
cd /Users/mansijadhav/Documents/BigData/TripSense-AI/ml

# Test PySpark installation
python3 -c "import pyspark; print(f'PySpark {pyspark.__version__} installed!')"

# Test Spark session creation
python3 spark_setup.py
```

Expected output:
```
Creating Spark session with default configuration...
Spark Configuration:
  App Name: TripSense-AI
  Version: 3.5.0
  Master: local[*]
  
Test DataFrame:
+---+-------+------+
| id|   name|rating|
+---+-------+------+
|  1|  Alice|   4.5|
|  2|    Bob|   3.8|
|  3|Charlie|   4.9|
+---+-------+------+

Done!
```

## Running the Data Pipeline

### Quick Start

```bash
cd /Users/mansijadhav/Documents/BigData/TripSense-AI/ml

# Run complete pipeline
python3 run_pipeline.py

# Or with custom paths
python3 run_pipeline.py \
  --input ../data/raw/tripadvisor_reviews.csv \
  --output ../data/processed/tripadvisor_cleaned.parquet
```

### Pipeline Stages

The pipeline performs:

1. **Data Ingestion** - Load CSV into Spark DataFrame
2. **Data Cleaning** - Remove duplicates, handle missing values, validate ratings
3. **Quality Checks** - Generate data quality report
4. **Parquet Export** - Save cleaned data in compressed format

### Expected Output

```
==================================================
TRIPSENSE AI - DATA PIPELINE
==================================================
Input: ../data/raw/tripadvisor_reviews.csv
Output: ../data/processed/tripadvisor_cleaned.parquet
Started: 2026-10-14 15:30:00
==================================================

🔄 Stage 1/4: Data Ingestion
✅ Ingested 201,295 records

🔄 Stage 2/4: Data Cleaning
✅ Cleaned to 201,295 records

🔄 Stage 3/4: Quality Report
📊 Quality Report Summary:
  Total Records: 201,295
  Sparsity: 99.9999%
  Avg reviews per user: 1.20
  Avg reviews per hotel: 1.20
✅ Quality report generated

🔄 Stage 4/4: Save to Parquet
✅ Saved to ../data/processed/tripadvisor_cleaned.parquet

==================================================
PIPELINE COMPLETE
==================================================
Input records: 201,295
Output records: 201,295
Output columns: 24
Completed: 2026-10-14 15:35:00
==================================================
```

## Running Individual Components

### Test Data Ingestion Only

```bash
python3 pipelines/data_ingestion.py
```

### Test Data Cleaning Only

```bash
python3 pipelines/data_cleaning.py
```

### Generate Quality Report Only

```bash
python3 pipelines/data_quality.py
```

## Configuration

### Spark Configuration

Edit `config/spark_config.py` to adjust Spark settings:

```python
# For local development (smaller memory)
config = SparkConfig.for_local_development()

# For production (more resources)
config = SparkConfig.for_production()
```

### Memory Settings

If you encounter memory issues, adjust in `config/spark_config.py`:

```python
driver_memory = "2g"      # Reduce from 4g
executor_memory = "2g"    # Reduce from 4g
```

## Troubleshooting

### Java Not Found

```
Error: JAVA_HOME is not set
```

**Solution:**
```bash
# Find Java path
/usr/libexec/java_home

# Set JAVA_HOME (add to ~/.zshrc or ~/.bashrc)
export JAVA_HOME=$(/usr/libexec/java_home)
```

### Out of Memory Error

```
java.lang.OutOfMemoryError: Java heap space
```

**Solution:**
Reduce Spark memory settings or process smaller data chunks.

### PySpark Import Error

```
ModuleNotFoundError: No module named 'pyspark'
```

**Solution:**
```bash
pip3 install --user pyspark==3.5.0
```

## Performance Tips

1. **Use Parquet**: Always output to Parquet format (already done in pipeline)
2. **Partition Data**: For very large datasets, partition by date/year
3. **Cache Frequently Used DataFrames**: Use `.cache()` on DataFrames accessed multiple times
4. **Adjust Parallelism**: Set `spark.default.parallelism` based on CPU cores

## Output Files

After running the pipeline, you'll have:

```
data/processed/
├── tripadvisor_cleaned.parquet/     # Cleaned dataset (Parquet format)
│   ├── _SUCCESS
│   └── part-*.snappy.parquet
├── quality_report.json               # Data quality metrics
└── pipeline.log                      # Pipeline execution log
```

## Next Steps

After successful pipeline execution:

1. ✅ **Phase 2 Task 2.1-2.2 Complete** - Spark setup and data cleaning done
2. 🔄 **Move to Task 2.3** - Feature engineering
3. 🔄 **Then Task 2.4** - Train/test split

## Verification

Verify the pipeline output:

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("Verify").getOrCreate()

# Read cleaned data
df = spark.read.parquet("../data/processed/tripadvisor_cleaned.parquet")

print(f"Total records: {df.count():,}")
print(f"Total columns: {len(df.columns)}")
df.printSchema()
df.show(5)
```

## Help

For issues or questions:
1. Check `pipeline.log` for detailed error messages
2. Verify Java and PySpark versions
3. Ensure sufficient memory (8GB+ RAM recommended)
4. Review Spark configuration in `config/spark_config.py`

# TripSense AI - Data Directory

This directory contains all datasets used in the TripSense AI project.

---

## 📂 Directory Structure

```
data/
├── raw/              # Original, unmodified dataset
├── processed/        # Processed data at various pipeline stages
│   ├── validated/    # Schema-validated raw data
│   ├── cleaned/      # Deduplicated, missing values handled
│   ├── features/     # Engineered features and embeddings
│   └── splits/       # Train/test splits
└── reports/          # Data quality and processing reports
```

---

## 🎯 Dataset Information

### Primary Dataset: TripAdvisor Review Rating Dataset

**Status:** ⚠️ NOT YET DOWNLOADED

**Expected Characteristics:**
- **Size:** ~201,295 records
- **Format:** CSV or JSON
- **Content:** Hotel reviews, ratings, metadata

**Expected Fields (to be validated):**
- `user_id` - Unique user identifier
- `hotel_id` - Unique hotel identifier
- `rating` - Overall rating (1.0-5.0)
- `review_text` - Review content
- `review_date` - Timestamp (if available)
- `hotel_name` - Hotel name
- `destination` - City/location
- `cleanliness_rating` - Aspect rating (if available)
- `location_rating` - Aspect rating (if available)
- `rooms_rating` - Aspect rating (if available)
- `service_rating` - Aspect rating (if available)
- `value_rating` - Aspect rating (if available)
- `sleep_quality_rating` - Aspect rating (if available)

---

## 📥 Dataset Acquisition

### Option 1: Kaggle
1. Visit: https://www.kaggle.com/datasets
2. Search for: "TripAdvisor Hotel Reviews"
3. Look for datasets with ~200k records
4. Download and place in `data/raw/`

### Option 2: UCI Machine Learning Repository
1. Visit: https://archive.ics.uci.edu/
2. Search for: "hotel reviews" or "TripAdvisor"
3. Download and place in `data/raw/`

### Option 3: Direct Research Dataset
Some potential sources:
- Academic research repositories
- Data.gov (if applicable)
- Public data repositories from travel research

---

## ⚠️ Important Notes

### Before Using the Dataset

1. **Verify License**: Ensure dataset can be used for academic/research purposes
2. **Check Terms**: Verify no restrictions on publication or sharing
3. **Document Source**: Record exact source, version, and download date
4. **Validate Schema**: Run validation script to confirm expected fields exist

### Data Privacy

- Dataset should be anonymized (no real user identities)
- Do NOT commit raw data to version control
- Handle any PII carefully if present

---

## 🔍 Dataset Validation Checklist

After downloading, verify:

- [ ] File exists in `data/raw/`
- [ ] File size is reasonable (~50MB-500MB for 200k records)
- [ ] Can load file without errors
- [ ] Column names match expected schema (or document differences)
- [ ] Data types are correct
- [ ] No completely empty columns
- [ ] User and hotel IDs are present
- [ ] Ratings are in valid range (1-5)
- [ ] Review text is present for most records
- [ ] Document missing value percentages
- [ ] Document duplicate record count
- [ ] Calculate interaction sparsity

---

## 📊 Data Dictionary

**Will be created after dataset validation.**

The data dictionary will document:
- Actual column names and data types
- Value ranges and distributions
- Missing value patterns
- Duplicate detection results
- Interaction sparsity metrics
- Example records

---

## 🔄 Data Processing Pipeline

### Stage 1: Ingestion (`ml/pipelines/01_ingest.py`)
- Load raw CSV/JSON
- Validate schema
- Save as Parquet: `processed/validated/`

### Stage 2: Cleaning (`ml/pipelines/02_clean.py`)
- Remove duplicates
- Handle missing values
- Filter invalid ratings
- Save as Parquet: `processed/cleaned/`

### Stage 3: Feature Engineering (`ml/pipelines/03_feature_engineering.py`)
- Calculate hotel aggregates
- Create aspect-level features
- Extract review corpus
- Save feature tables: `processed/features/`

### Stage 4: NLP Processing (`ml/pipelines/04_nlp_processing.py`)
- Generate TF-IDF vectors
- Extract sentiment scores
- Aspect-level sentiment
- Save embeddings: `processed/features/`

### Stage 5: Train/Test Split (`ml/pipelines/05_train_test_split.py`)
- Create stratified or chronological split
- Save splits: `processed/splits/`

---

## 📈 Data Reports

Processing reports are saved to `data/reports/`:
- `ingestion_report.json` - Schema validation results
- `cleaning_report.json` - Cleaning statistics
- `feature_report.json` - Feature engineering summary
- `nlp_report.json` - NLP processing results
- `split_report.json` - Train/test split metadata

---

## 🚫 What NOT to Commit

**Never commit to Git:**
- Raw dataset files (can be large, licensing unclear)
- Processed Parquet files (regenerated from pipeline)
- Temporary files
- Personal data or credentials

**Keep in Git:**
- This README
- Data dictionary (once created)
- Processing scripts
- Validation schemas
- Report templates

---

## 📝 Dataset Citation

**Format:**
```
[Dataset Name]. [Author/Organization]. [Year]. 
Retrieved from [URL] on [Date].
License: [License Type]
```

**Example (placeholder):**
```
TripAdvisor Hotel Reviews Dataset. Kaggle User. 2023.
Retrieved from https://www.kaggle.com/... on October 14, 2026.
License: CC BY-SA 4.0
```

---

## 🆘 Troubleshooting

**Problem: Dataset not found**
- Verify file is in `data/raw/`
- Check file name matches configuration
- Ensure file is not corrupted

**Problem: Schema mismatch**
- Run validation notebook: `notebooks/00_dataset_exploration.ipynb`
- Document actual schema in data dictionary
- Adjust pipeline scripts to match actual schema

**Problem: Out of memory**
- Use Spark for processing (designed for this)
- Process in chunks if necessary
- Consider using subset for development

---

## 📞 Questions?

If dataset acquisition is problematic:
1. Check alternative sources
2. Consider using subset for MVP
3. Document exact dataset used in final report

---

**Status:** Setup Complete - Dataset Acquisition Pending  
**Last Updated:** October 14, 2026

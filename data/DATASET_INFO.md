# TripAdvisor Dataset Information

**Dataset Downloaded:** ✅ Success  
**Date:** October 14, 2026

---

## Dataset Details

**Dataset Name:** TripAdvisor Hotel Review Rating  
**Source:** HuggingFace  
**URL:** https://huggingface.co/datasets/jniimi/tripadvisor-review-rating  
**License:** Check HuggingFace page for current license  
**Download Method:** `load_dataset()` from HuggingFace datasets library

---

## File Information

**Location:** `/Users/mansijadhav/Documents/BigData/TripSense-AI/data/raw/tripadvisor_reviews.csv`  
**File Size:** 343.16 MB  
**Total Records:** 201,295  
**Format:** CSV

---

## Schema (16 Columns)

| # | Column Name | Data Type | Missing | Description |
|---|-------------|-----------|---------|-------------|
| 1 | hotel_id | int64 | 0 (0.00%) | Unique hotel identifier |
| 2 | user_id | object | 0 (0.00%) | User identifier (hash) |
| 3 | title | object | 0 (0.00%) | Review title/summary |
| 4 | text | object | 0 (0.00%) | Full review text |
| 5 | **overall** | **float64** | **0 (0.00%)** | **Overall rating (1-5)** |
| 6 | **cleanliness** | **float64** | **0 (0.00%)** | **Cleanliness aspect rating** |
| 7 | **value** | **float64** | **0 (0.00%)** | **Value aspect rating** |
| 8 | **location** | **float64** | **0 (0.00%)** | **Location aspect rating** |
| 9 | **rooms** | **float64** | **0 (0.00%)** | **Rooms aspect rating** |
| 10 | **sleep_quality** | **float64** | **0 (0.00%)** | **Sleep quality aspect rating** |
| 11 | stay_year | int64 | 0 (0.00%) | Year of hotel stay |
| 12 | post_date | datetime64[ns] | 0 (0.00%) | Date review was posted |
| 13 | freq | int64 | 0 (0.00%) | Frequency (possibly review count) |
| 14 | review | object | 0 (0.00%) | Combined title + text |
| 15 | char | int64 | 0 (0.00%) | Character count |
| 16 | lang | object | 0 (0.00%) | Language label |

---

## Dataset Statistics

### Size
- **Total Records:** 201,295
- **Unique Hotels:** 201,295 (appears to be 1 review per hotel in this dataset)
- **Unique Users:** 167,027
- **Unique Titles:** 151,710
- **Unique Reviews:** 201,255

### Text Statistics
- **Average Review Length:** 811 characters
- **Review Text Column:** `text` (primary)
- **Combined Review Column:** `review` (title + text)

### Ratings Distribution
**Overall Rating:** 5 distinct values (1.0 - 5.0 scale)

---

## Key Observations

### ✅ Excellent Dataset Quality

1. **Complete Data:** Zero missing values across all columns
2. **Aspect Ratings:** ✅ All 5 aspect ratings present (cleanliness, value, location, rooms, sleep_quality)
3. **Review Text:** ✅ Full review text available
4. **Timestamps:** ✅ Both stay year and post date available
5. **User IDs:** ✅ Anonymized user identifiers present

### Data Characteristics

**Strengths:**
- No missing values - exceptionally clean dataset
- Rich aspect-level ratings (cleanliness, value, location, rooms, sleep_quality)
- Substantial review text (avg 811 chars)
- Temporal information for chronological evaluation
- Language identification included

**Considerations:**
- Each hotel appears once (201,295 hotels, 201,295 records)
- This is NOT a typical user-hotel interaction matrix
- More like: 167,027 users reviewing 201,295 different hotels
- Low repeat interactions per user
- **Implication:** Collaborative filtering will be challenging due to sparse matrix

### Sparsity Analysis

With:
- 167,027 users
- 201,295 hotels  
- 201,295 interactions

**Sparsity:** ~99.999% (extremely sparse)

This means:
- Each user has reviewed very few hotels on average (~1.2 reviews/user)
- Collaborative filtering (ALS) will have limited effectiveness
- **Should emphasize:** Content-based, aspect-based, and popularity recommendations
- Hybrid model will rely more on content/aspect signals

---

## Column Mapping for Pipeline

Use these column names in all processing scripts:

```python
COLUMN_MAPPING = {
    # Core fields
    'hotel_id': 'hotel_id',
    'user_id': 'user_id',
    'rating': 'overall',          # Main rating
    'review_text': 'text',         # Review content
    
    # Aspect ratings
    'cleanliness_rating': 'cleanliness',
    'value_rating': 'value',
    'location_rating': 'location',
    'rooms_rating': 'rooms',
    'sleep_quality_rating': 'sleep_quality',
    
    # Metadata
    'review_title': 'title',
    'stay_year': 'stay_year',
    'post_date': 'post_date',
    'language': 'lang',
    
    # Derived
    'review_full': 'review',       # Title + text combined
    'char_count': 'char'
}
```

---

## Recommendations for Implementation

### 1. **Model Strategy Adjustment**

Given the sparsity:

**Prioritize:**
- ✅ **Content-Based Recommendations** (using review text, aspects)
- ✅ **Aspect-Based Matching** (excellent aspect data available)
- ✅ **Popularity Baseline** (with Bayesian averaging)
- ✅ **Sentiment Analysis** (good review text)

**De-emphasize:**
- ⚠️ **Collaborative Filtering** (ALS will struggle with this sparsity)
  - Still implement for academic completeness
  - Document limitations honestly
  - May not outperform simpler baselines

**Hybrid Approach:**
- Adjust weights: more on content/aspect, less on collaborative
- Use CF only for users with multiple reviews
- Fallback to content-based for sparse users

### 2. **Feature Engineering Focus**

**Leverage:**
- Excellent aspect ratings (all 5 present, no missing values)
- Rich review text (811 chars avg)
- Temporal patterns (stay_year, post_date)
- Language information

**Extract:**
- TF-IDF vectors from review text
- Sentiment scores from text
- Aspect importance from text analysis
- Hotel metadata from text (location keywords, amenities mentioned)

### 3. **Evaluation Strategy**

**Challenges:**
- Can't do traditional user-based train/test split (most users have 1 review)
- Can't evaluate "repeat visit prediction"

**Alternative Approaches:**
- **Leave-one-out for multi-review users** (small subset)
- **Cold-start evaluation** (new hotels/users)
- **Content similarity validation** (similar hotels should have similar ratings)
- **Aspect prediction accuracy** (predict aspect from text)
- **Qualitative assessment** (do recommendations make sense?)

### 4. **Pipeline Adaptations**

**No Changes Needed:**
- Ingestion script will work as-is
- Feature engineering can proceed
- NLP processing fully applicable

**Adjustments:**
- Don't expect strong CF performance
- Focus evaluation on content/aspect models
- Document sparsity limitations clearly
- Emphasize hybrid model strength

---

## Citation

```
Dataset: TripAdvisor Hotel Review Rating
Source: HuggingFace (jniimi/tripadvisor-review-rating)
URL: https://huggingface.co/datasets/jniimi/tripadvisor-review-rating
Access Date: October 14, 2026
Records: 201,295 hotel reviews
License: [Check HuggingFace for current license]
```

---

## Next Steps

1. ✅ **Dataset Downloaded** - Complete
2. ⏭️ **Run Exploration Notebook** - Validate and visualize
   ```bash
   jupyter notebook notebooks/00_dataset_exploration.ipynb
   ```
3. ⏭️ **Update Configuration** - Set column mappings in `.env`
4. ⏭️ **Adjust Model Expectations** - Account for sparsity
5. ⏭️ **Proceed to Phase 1** - Backend implementation

---

**Status:** ✅ Dataset Acquired and Documented  
**Quality:** Excellent (no missing values, complete aspects)  
**Challenge:** High sparsity requires emphasis on content-based approaches  
**Ready for:** Phase 1 Implementation

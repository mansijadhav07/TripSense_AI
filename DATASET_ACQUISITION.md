# TripSense AI - Dataset Acquisition Guide

**Critical Step:** This guide will help you acquire and validate the TripAdvisor hotel reviews dataset.

---

## 🎯 Dataset Requirements

We need a hotel review dataset with approximately 200,000 records containing:

**Essential Fields:**
- User identifiers
- Hotel identifiers
- Overall ratings (1-5 scale)
- Review text

**Highly Desired Fields:**
- Aspect-level ratings (cleanliness, location, rooms, service, value, sleep quality)
- Hotel metadata (name, destination, price range)
- Review timestamps

---

## 📥 Recommended Sources

### Option 1: Kaggle (RECOMMENDED)

**Dataset: "515K Hotel Reviews Data in Europe"**
- **URL:** https://www.kaggle.com/datasets/jiashenliu/515k-hotel-reviews-data-in-europe
- **Size:** 515K reviews (can use subset)
- **Format:** CSV
- **License:** CC0 Public Domain

**Steps:**
1. Create Kaggle account (if needed)
2. Download dataset
3. Place in `data/raw/`
4. Rename to `hotel_reviews.csv`

**Alternative Kaggle Datasets:**
- Search "hotel reviews" or "TripAdvisor"
- Look for datasets with 100K+ records
- Verify it includes ratings and review text

---

### Option 2: UCI Machine Learning Repository

**Dataset: "Hotel Reviews"**
- **URL:** https://archive.ics.uci.edu/
- Search for hotel-related datasets
- Download and extract

---

### Option 3: Datafiniti Hotel Reviews

**Dataset: Datafiniti Hotel Reviews**
- Available on various platforms
- May require subscription or access request

---

### Option 4: Synthetic/Sample Data (DEVELOPMENT ONLY)

If unable to access real dataset immediately:
1. Use sample for initial development
2. Clearly label as synthetic
3. Replace with real data before evaluation

---

## 📋 Step-by-Step Acquisition

### Step 1: Download Dataset

Choose one of the sources above and download the dataset.

**Recommended: Kaggle 515K Hotel Reviews**

```bash
# If you have kaggle CLI installed
kaggle datasets download -d jiashenliu/515k-hotel-reviews-data-in-europe

# Or download manually from website
```

### Step 2: Place in Correct Directory

```bash
cd /Users/mansijadhav/Documents/BigData/TripSense-AI

# Create raw data directory if not exists
mkdir -p data/raw

# Move downloaded file
mv ~/Downloads/hotel_reviews.csv data/raw/

# Or if it's a zip file
unzip ~/Downloads/515k-hotel-reviews-data-in-europe.zip -d data/raw/
```

### Step 3: Verify File

```bash
# Check file exists
ls -lh data/raw/

# Check first few lines
head -n 5 data/raw/hotel_reviews.csv

# Count rows (approximate)
wc -l data/raw/hotel_reviews.csv
```

### Step 4: Document Source

Create `data/DATASET_INFO.md`:

```markdown
# Dataset Information

**Dataset Name:** [Name]
**Source:** [URL]
**Download Date:** [Date]
**License:** [License]
**Original Size:** [Number of records]
**File Size:** [MB/GB]

**Citation:**
[How to cite this dataset]
```

---

## 🔍 Initial Validation

Once you have the dataset, run the exploration notebook:

```bash
cd /Users/mansijadhav/Documents/BigData/TripSense-AI

# Install Jupyter if needed
pip install jupyter pandas numpy matplotlib seaborn

# Start Jupyter
jupyter notebook notebooks/00_dataset_exploration.ipynb
```

The notebook will help you:
- Load and inspect the dataset
- Validate schema and data types
- Check for missing values
- Analyze distributions
- Calculate sparsity
- Create data dictionary

---

## 📊 Expected Schema Validation

After loading, verify these exist (or document alternatives):

### Core Fields (REQUIRED)
- ✅ User identifier column
- ✅ Hotel identifier column  
- ✅ Overall rating column (1-5)
- ✅ Review text column

### Metadata Fields (DESIRED)
- ⚠️ Hotel name
- ⚠️ Hotel location/destination
- ⚠️ Review timestamp
- ⚠️ Price range or category

### Aspect Ratings (DESIRED)
- ⚠️ Cleanliness rating
- ⚠️ Location rating
- ⚠️ Rooms rating
- ⚠️ Service rating
- ⚠️ Value rating
- ⚠️ Sleep quality rating

**Note:** If aspect ratings are missing, we can derive them from review text using NLP.

---

## 🔧 Schema Adaptation

If actual schema differs from expected:

1. **Document actual schema** in data dictionary
2. **Update configuration** in `.env`
3. **Adapt ingestion script** to use actual column names
4. **Modify feature engineering** based on available fields
5. **Update model design** if necessary features unavailable

**Example Mapping:**

Expected → Actual
- `user_id` → `User_ID` or `reviewer_id`
- `hotel_id` → `Hotel_ID` or `property_id`
- `rating` → `Rating` or `overall_rating`
- `review_text` → `Review` or `review_content`

---

## ⚠️ Common Issues & Solutions

### Issue 1: Dataset Too Large
**Solution:** Use a representative subset

```python
import pandas as pd

# Load full dataset
df = pd.read_csv('data/raw/hotel_reviews.csv')

# Sample 200k records
df_sample = df.sample(n=200000, random_state=42)

# Save subset
df_sample.to_csv('data/raw/hotel_reviews_subset.csv', index=False)
```

### Issue 2: Missing Aspect Ratings
**Solution:** Derive from review text using NLP

We'll use sentiment analysis to extract aspect-level opinions from review text.

### Issue 3: No User IDs (Anonymous Reviews)
**Solution:** Create pseudo-IDs

This limits collaborative filtering but we can still use:
- Content-based recommendations
- Popularity-based recommendations
- Aspect matching

### Issue 4: Dataset Not Available
**Solution:** Use alternative

Try these alternatives:
1. Amazon hotel product reviews
2. Yelp hotel reviews (if available)
3. Booking.com reviews (if available)
4. Different domain (restaurants) for algorithm demonstration

---

## 📝 Data Quality Checklist

After acquisition, verify:

- [ ] File successfully downloaded
- [ ] File can be loaded without errors
- [ ] Has at least 50,000 records (minimum)
- [ ] Contains user/reviewer identifiers
- [ ] Contains hotel/property identifiers
- [ ] Contains rating values (1-5 scale)
- [ ] Contains review text
- [ ] Document source and license
- [ ] Created data dictionary with actual schema
- [ ] Noted missing fields and adaptation strategy

---

## 🚀 Next Steps After Acquisition

Once dataset is acquired and validated:

1. ✅ Complete `notebooks/00_dataset_exploration.ipynb`
2. ✅ Create `data/data_dictionary.md`
3. ✅ Update `.env` with actual data paths
4. ✅ Document any schema differences
5. ✅ Proceed to Phase 1: Foundation

---

## 💡 Tips

**For Dataset Selection:**
- Prefer datasets with actual aspect ratings
- Timestamps enable chronological evaluation
- Hotel metadata enables better content-based recommendations
- More records = better collaborative filtering

**For Initial Development:**
- Can start with subset (50k records) for faster iteration
- Use full dataset for final evaluation
- Document which subset was used for development

**For Academic Integrity:**
- Properly cite dataset source
- Check license compatibility with academic use
- Document any transformations applied

---

## 📞 Need Help?

**Can't find dataset?**
1. Check Kaggle thoroughly - multiple hotel review datasets exist
2. Ask if you need help identifying suitable alternatives
3. Consider domain transfer (e.g., restaurant reviews)

**Dataset has different schema?**
1. Don't worry - we'll adapt
2. Focus on core fields (user, item, rating, text)
3. Document the differences
4. Adjust pipeline accordingly

**Dataset too different to use?**
1. Describe what you found
2. We'll modify requirements to fit
3. Core algorithms work with minimal fields

---

## ✅ Success Criteria

You've successfully acquired the dataset when:

1. File exists in `data/raw/`
2. Can load file in Python/Pandas
3. Has required fields (user, hotel, rating, text)
4. Source and license documented
5. Initial exploration complete
6. Data dictionary created

**Then you're ready for Phase 1!**

---

**Status:** Awaiting Dataset Acquisition  
**Priority:** HIGH - This blocks all ML development  
**Estimated Time:** 30 minutes - 2 hours depending on source

---

**Questions? Issues? Let me know and I'll help troubleshoot!**

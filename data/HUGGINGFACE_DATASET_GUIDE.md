# TripAdvisor Dataset from HuggingFace

**Dataset:** jniimi/tripadvisor-review-rating  
**Source:** https://huggingface.co/datasets/jniimi/tripadvisor-review-rating  
**Size:** ~201,295 reviews  
**License:** Check HuggingFace page for current license

---

## 📥 Download Methods

### Method 1: Using HuggingFace Datasets Library (RECOMMENDED)

This is the easiest and most reliable method:

```bash
# Navigate to project
cd /Users/mansijadhav/Documents/BigData/TripSense-AI

# Install HuggingFace datasets library
pip install datasets huggingface_hub

# Create download script
python3 << 'EOF'
from datasets import load_dataset
import pandas as pd

# Load dataset
print("Downloading TripAdvisor dataset from HuggingFace...")
dataset = load_dataset("jniimi/tripadvisor-review-rating", split="train")

# Convert to pandas DataFrame
df = pd.DataFrame(dataset)

# Save as CSV
print(f"Dataset shape: {df.shape}")
print(f"Saving to data/raw/tripadvisor_reviews.csv...")
df.to_csv("data/raw/tripadvisor_reviews.csv", index=False)

print("✅ Dataset downloaded successfully!")
print(f"Columns: {list(df.columns)}")
print(f"\nFirst row preview:")
print(df.head(1).to_string())
EOF
```

### Method 2: Direct Download via HuggingFace Hub

```bash
# Install huggingface-cli
pip install huggingface_hub

# Download dataset files
huggingface-cli download jniimi/tripadvisor-review-rating --repo-type dataset --local-dir data/raw/huggingface_download
```

### Method 3: Manual Download

1. Visit: https://huggingface.co/datasets/jniimi/tripadvisor-review-rating
2. Click "Files and versions" tab
3. Download the data files
4. Place in `data/raw/`

---

## 📊 Expected Schema (Based on Preview)

From the dataset viewer, the columns appear to be:

```
Column 0: Review ID or Index
Column 1: Hotel ID (hash)
Column 2: Review Title
Column 3: Review Text (Full)
Column 4: Overall Rating (1-5)
Column 5: Cleanliness Rating
Column 6: Location Rating
Column 7: Rooms Rating
Column 8: Service Rating
Column 9: Value Rating
Column 10: Year
Column 11: Review Date
Column 12: User ID (appears to be 1 for many)
Column 13: Review Title (duplicate?)
Column 14: Review Text Preview
...additional columns
```

**Note:** We'll validate exact column names after download.

---

## 🚀 Quick Start Script

Save this as `download_dataset.py` in the project root:

```python
"""
Download TripAdvisor dataset from HuggingFace
"""

from datasets import load_dataset
import pandas as pd
from pathlib import Path

def download_tripadvisor_dataset():
    """Download and save TripAdvisor dataset."""
    
    # Ensure raw data directory exists
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        print("=" * 60)
        print("Downloading TripAdvisor Review Dataset")
        print("=" * 60)
        print("\nSource: HuggingFace (jniimi/tripadvisor-review-rating)")
        print("This may take a few minutes...\n")
        
        # Load dataset
        dataset = load_dataset("jniimi/tripadvisor-review-rating", split="train")
        
        print(f"✅ Dataset loaded: {len(dataset)} records")
        
        # Convert to pandas
        df = pd.DataFrame(dataset)
        
        print(f"✅ Converted to DataFrame: {df.shape}")
        print(f"\nColumns ({len(df.columns)}):")
        for i, col in enumerate(df.columns, 1):
            print(f"  {i}. {col}")
        
        # Save as CSV
        output_path = raw_dir / "tripadvisor_reviews.csv"
        df.to_csv(output_path, index=False)
        
        print(f"\n✅ Saved to: {output_path}")
        print(f"   Size: {output_path.stat().st_size / 1024 / 1024:.2f} MB")
        
        # Show preview
        print("\n" + "=" * 60)
        print("Preview (first 3 rows):")
        print("=" * 60)
        print(df.head(3))
        
        # Basic stats
        print("\n" + "=" * 60)
        print("Basic Statistics:")
        print("=" * 60)
        print(f"Total Records: {len(df):,}")
        
        # Try to identify rating column
        rating_cols = [col for col in df.columns if 'rating' in str(col).lower()]
        if rating_cols:
            print(f"\nRating columns found: {rating_cols}")
            for col in rating_cols[:1]:  # Show first rating column stats
                print(f"\n{col} distribution:")
                print(df[col].value_counts().sort_index())
        
        print("\n✅ Download complete! Next steps:")
        print("1. Run: jupyter notebook notebooks/00_dataset_exploration.ipynb")
        print("2. Update column mappings in the notebook")
        print("3. Generate data dictionary")
        
        return df
        
    except Exception as e:
        print(f"\n❌ Error downloading dataset: {e}")
        print("\nTroubleshooting:")
        print("1. Check internet connection")
        print("2. Verify HuggingFace datasets library installed: pip install datasets")
        print("3. Try manual download from HuggingFace website")
        raise

if __name__ == "__main__":
    download_tripadvisor_dataset()
```

---

## 📝 Step-by-Step Instructions

### Step 1: Install Required Libraries

```bash
cd /Users/mansijadhav/Documents/BigData/TripSense-AI

# Install HuggingFace datasets
pip install datasets huggingface_hub pandas

# Verify installation
python -c "import datasets; print('✅ datasets installed')"
```

### Step 2: Download Dataset

**Option A: Use the script above**

```bash
# Create the download script
cat > download_dataset.py << 'EOF'
[paste the script from above]
EOF

# Run it
python download_dataset.py
```

**Option B: Quick one-liner**

```python
python -c "from datasets import load_dataset; import pandas as pd; df = pd.DataFrame(load_dataset('jniimi/tripadvisor-review-rating', split='train')); df.to_csv('data/raw/tripadvisor_reviews.csv', index=False); print('Done!', df.shape)"
```

### Step 3: Verify Download

```bash
# Check file exists
ls -lh data/raw/tripadvisor_reviews.csv

# Preview first 5 lines
head -5 data/raw/tripadvisor_reviews.csv

# Count rows (approximate)
wc -l data/raw/tripadvisor_reviews.csv
```

### Step 4: Document Dataset

Create `data/DATASET_INFO.md`:

```markdown
# Dataset Information

**Dataset Name:** TripAdvisor Hotel Reviews
**Source:** HuggingFace - jniimi/tripadvisor-review-rating
**URL:** https://huggingface.co/datasets/jniimi/tripadvisor-review-rating
**Download Date:** [Today's date]
**License:** [Check HuggingFace page]
**Original Size:** ~201,295 reviews
**File Size:** [Check after download]

**Citation:**
Dataset provided by jniimi on HuggingFace.
Available at: https://huggingface.co/datasets/jniimi/tripadvisor-review-rating

**Description:**
TripAdvisor hotel reviews with ratings including:
- Overall ratings
- Aspect-level ratings (cleanliness, location, rooms, service, value)
- Review text
- Timestamps
```

### Step 5: Run Validation Notebook

```bash
# Install Jupyter if needed
pip install jupyter matplotlib seaborn

# Launch notebook
jupyter notebook notebooks/00_dataset_exploration.ipynb
```

---

## 🔍 Known Characteristics

Based on the HuggingFace preview:

**✅ Has Aspect Ratings:** Yes! Cleanliness, Location, Rooms, Service, Value
**✅ Has Review Text:** Yes, full review text available
**✅ Has Timestamps:** Yes, date information included
**✅ Has Overall Rating:** Yes, 1-5 scale

**This is an excellent dataset for our needs!**

---

## ⚠️ Important Notes

### Column Names
The actual column names may be:
- Numeric (0, 1, 2, etc.)
- Or descriptive names

You'll need to map them after download.

### Data Quality
- Some reviews may be duplicates
- Some aspect ratings may be missing
- User IDs may not be unique (appears many are "1")

### Dataset Size
- Full dataset is ~201k records
- Can work with subset for development
- Use full set for final evaluation

---

## 🐛 Troubleshooting

### "Module not found: datasets"
```bash
pip install datasets huggingface_hub
```

### "Connection error"
- Check internet connection
- Try manual download from HuggingFace
- Use VPN if needed

### "File too large"
- This is normal (~100-200MB)
- Ensure sufficient disk space
- Consider using Parquet format for efficiency

### "Column names unclear"
- Run the download script to see actual columns
- Use exploration notebook to inspect
- Map columns manually

---

## ✅ Success Criteria

You've successfully downloaded the dataset when:

- [x] File exists: `data/raw/tripadvisor_reviews.csv`
- [x] File size is ~100-200 MB
- [x] Can load in pandas without errors
- [x] Has expected ~200k rows
- [x] Has rating and review text columns
- [x] Has aspect-level ratings

---

## 🚀 Next Steps After Download

1. **Run exploration notebook**
   ```bash
   jupyter notebook notebooks/00_dataset_exploration.ipynb
   ```

2. **Update column mappings** in the notebook

3. **Generate data dictionary**

4. **Proceed to Phase 1** - Backend implementation

---

**Ready to download? Run the script above! 🎉**

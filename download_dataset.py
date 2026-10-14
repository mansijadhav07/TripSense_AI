"""
TripSense AI - Download TripAdvisor Dataset from HuggingFace

This script downloads the TripAdvisor review dataset from HuggingFace
and saves it as a CSV file in the data/raw/ directory.

Usage:
    python download_dataset.py

Requirements:
    pip install datasets huggingface_hub pandas
"""

from datasets import load_dataset
import pandas as pd
from pathlib import Path
import sys


def download_tripadvisor_dataset():
    """Download and save TripAdvisor dataset from HuggingFace."""
    
    # Ensure raw data directory exists
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        print("=" * 70)
        print("TripSense AI - Dataset Download")
        print("=" * 70)
        print("\n📥 Downloading TripAdvisor Review Dataset")
        print("   Source: HuggingFace (jniimi/tripadvisor-review-rating)")
        print("   This may take a few minutes...\n")
        
        # Load dataset from HuggingFace
        dataset = load_dataset("jniimi/tripadvisor-review-rating", split="train")
        
        print(f"✅ Dataset loaded: {len(dataset):,} records")
        
        # Convert to pandas DataFrame
        df = pd.DataFrame(dataset)
        
        print(f"✅ Converted to DataFrame: {df.shape[0]:,} rows × {df.shape[1]} columns")
        
        # Display column information
        print(f"\n📋 Columns ({len(df.columns)}):")
        for i, col in enumerate(df.columns, 1):
            dtype = df[col].dtype
            null_count = df[col].isnull().sum()
            null_pct = (null_count / len(df) * 100)
            print(f"  {i:2d}. {col:30s} | {str(dtype):10s} | Nulls: {null_count:6,} ({null_pct:5.2f}%)")
        
        # Save as CSV
        output_path = raw_dir / "tripadvisor_reviews.csv"
        print(f"\n💾 Saving to: {output_path}")
        df.to_csv(output_path, index=False)
        
        file_size_mb = output_path.stat().st_size / 1024 / 1024
        print(f"✅ Saved successfully!")
        print(f"   File size: {file_size_mb:.2f} MB")
        
        # Show data preview
        print("\n" + "=" * 70)
        print("📊 Dataset Preview (first 3 rows):")
        print("=" * 70)
        
        # Display with better formatting
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', 50)
        print(df.head(3).to_string())
        
        # Basic statistics
        print("\n" + "=" * 70)
        print("📈 Basic Statistics:")
        print("=" * 70)
        print(f"Total Records: {len(df):,}")
        
        # Try to identify and show rating distribution
        rating_cols = [col for col in df.columns if 'rating' in str(col).lower() or str(col).isdigit()]
        
        if rating_cols:
            print(f"\n📊 Potential Rating Columns: {rating_cols[:6]}")
            
            # Show distribution for first numeric column that looks like ratings
            for col in df.columns:
                if df[col].dtype in ['int64', 'float64']:
                    if df[col].min() >= 1 and df[col].max() <= 5:
                        print(f"\n{col} Distribution:")
                        print(df[col].value_counts().sort_index().to_string())
                        break
        
        # Count unique values for potential ID columns
        print("\n📊 Unique Counts:")
        for col in df.columns[:5]:  # Check first 5 columns
            unique = df[col].nunique()
            print(f"  {col}: {unique:,} unique values")
        
        # Check for review text
        text_cols = [col for col in df.columns if 'review' in str(col).lower() or 'text' in str(col).lower()]
        if text_cols:
            print(f"\n📝 Text Columns Found: {text_cols[:3]}")
            # Show average text length
            for col in text_cols[:1]:
                if df[col].dtype == 'object':
                    avg_len = df[col].fillna('').str.len().mean()
                    print(f"   {col}: Average length = {avg_len:.0f} characters")
        
        print("\n" + "=" * 70)
        print("✅ Download Complete!")
        print("=" * 70)
        print("\n📝 Next Steps:")
        print("1. Review the data preview above")
        print("2. Run: jupyter notebook notebooks/00_dataset_exploration.ipynb")
        print("3. Update column mappings based on actual names")
        print("4. Generate data dictionary")
        print("5. Proceed to Phase 1 implementation")
        
        print("\n" + "=" * 70)
        
        return df
        
    except ImportError as e:
        print(f"\n❌ Error: Required library not installed")
        print(f"   {e}")
        print("\n🔧 Fix: Install required libraries:")
        print("   pip install datasets huggingface_hub pandas")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Error downloading dataset: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Check internet connection")
        print("2. Verify libraries installed: pip install datasets huggingface_hub pandas")
        print("3. Try manual download from: https://huggingface.co/datasets/jniimi/tripadvisor-review-rating")
        print("4. Check HuggingFace status: https://status.huggingface.co/")
        sys.exit(1)


if __name__ == "__main__":
    print("\n")
    df = download_tripadvisor_dataset()
    print("\n✨ Dataset ready for exploration!")
    print("\n")

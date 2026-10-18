"""
Fix Data Corruption in TripSense AI

Maps corrupted IDs (review text) to clean identifiers and rebuilds datasets
with proper user_id and hotel_id preservation.

This is a one-time fix that creates clean datasets for downstream evaluation.
"""

import logging
import json
import sys
from pathlib import Path
from typing import Dict, Tuple
import pandas as pd
import numpy as np
from collections import defaultdict

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fix_data_corruption.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class DataCorruptionFixer:
    """Fixes corrupted IDs by mapping to clean identifiers."""
    
    def __init__(self, data_dir: str = None, output_dir: str = None):
        """Initialize fixer."""
        if data_dir is None:
            self.data_dir = Path(__file__).parent.parent.parent / "data" / "processed"
        else:
            self.data_dir = Path(data_dir)
        
        if output_dir is None:
            self.output_dir = self.data_dir / "splits_fixed"
        else:
            self.output_dir = Path(output_dir)
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Mapping from corrupted IDs to clean IDs
        self.corrupted_user_mapping = {}
        self.corrupted_hotel_mapping = {}
        
        # Counter for generating clean IDs
        self.user_counter = 0
        self.hotel_counter = 0
    
    def get_clean_user_id(self, corrupted_id):
        """Get or create a clean user ID for a corrupted one."""
        if corrupted_id not in self.corrupted_user_mapping:
            self.user_counter += 1
            self.corrupted_user_mapping[corrupted_id] = f"user_{self.user_counter:06d}"
        return self.corrupted_user_mapping[corrupted_id]
    
    def get_clean_hotel_id(self, corrupted_id):
        """Get or create a clean hotel ID for a corrupted one."""
        if corrupted_id not in self.corrupted_hotel_mapping:
            self.hotel_counter += 1
            self.corrupted_hotel_mapping[corrupted_id] = f"hotel_{self.hotel_counter:06d}"
        return self.corrupted_hotel_mapping[corrupted_id]
    
    def fix_test_interactions(self) -> Tuple[pd.DataFrame, Dict]:
        """Fix corrupted IDs in test interactions."""
        logger.info("\n" + "="*80)
        logger.info("FIXING TEST INTERACTIONS")
        logger.info("="*80)
        
        test_file = self.data_dir / "splits" / "test_interactions.parquet"
        
        if not test_file.exists():
            logger.error(f"Test interactions file not found: {test_file}")
            return None, {}
        
        # Load test interactions
        df = pd.read_parquet(test_file)
        logger.info(f"Loaded {len(df)} test interactions")
        
        # Create backup
        backup_file = test_file.with_name("test_interactions_CORRUPTED_BACKUP.parquet")
        df.to_parquet(backup_file)
        logger.info(f"Backup saved to: {backup_file}")
        
        # Map IDs
        logger.info("Mapping corrupted IDs to clean IDs...")
        df["user_id_clean"] = df["user_id"].apply(self.get_clean_user_id)
        df["hotel_id_clean"] = df["hotel_id"].apply(self.get_clean_hotel_id)
        
        # Verify mapping
        unique_users_before = df["user_id"].nunique()
        unique_users_after = df["user_id_clean"].nunique()
        unique_hotels_before = df["hotel_id"].nunique()
        unique_hotels_after = df["hotel_id_clean"].nunique()
        
        logger.info(f"Users: {unique_users_before} → {unique_users_after}")
        logger.info(f"Hotels: {unique_hotels_before} → {unique_hotels_after}")
        
        # Replace corrupted IDs
        df["user_id"] = df["user_id_clean"]
        df["hotel_id"] = df["hotel_id_clean"]
        df = df.drop(columns=["user_id_clean", "hotel_id_clean"])
        
        # Save fixed version
        fixed_file = self.output_dir / "test_interactions.parquet"
        df.to_parquet(fixed_file, index=False)
        logger.info(f"✓ Fixed test interactions saved to: {fixed_file}")
        
        stats = {
            "total_interactions": len(df),
            "unique_users": unique_users_after,
            "unique_hotels": unique_hotels_after,
            "users_mapped": len(self.corrupted_user_mapping),
            "hotels_mapped": len(self.corrupted_hotel_mapping)
        }
        
        return df, stats
    
    def fix_hotel_features(self, hotel_id_mapping: Dict[str, str]) -> Tuple[pd.DataFrame, Dict]:
        """Fix corrupted IDs in hotel features."""
        logger.info("\n" + "="*80)
        logger.info("FIXING HOTEL FEATURES")
        logger.info("="*80)
        
        features_file = self.data_dir / "features" / "hotel_features_complete.parquet"
        
        if not features_file.exists():
            logger.error(f"Hotel features file not found: {features_file}")
            return None, {}
        
        # Load hotel features
        df = pd.read_parquet(features_file)
        logger.info(f"Loaded {len(df)} hotels with features")
        
        # Create backup
        backup_file = features_file.with_name("hotel_features_complete_CORRUPTED_BACKUP.parquet")
        df.to_parquet(backup_file)
        logger.info(f"Backup saved to: {backup_file}")
        
        # Map IDs - use existing mapping from test interactions
        logger.info("Mapping corrupted hotel IDs...")
        df["hotel_id_clean"] = df["hotel_id"].apply(
            lambda x: hotel_id_mapping.get(x, f"hotel_{self.hotel_counter:06d}")
        )
        
        # Count mapped vs unmapped
        mapped_count = (df["hotel_id_clean"] != f"hotel_{self.hotel_counter:06d}").sum()
        logger.info(f"Mapped {mapped_count} hotels from test set")
        
        # For hotels not in test set, generate new IDs
        for idx, row in df.iterrows():
            if row["hotel_id_clean"] == f"hotel_{self.hotel_counter:06d}":
                # This hotel wasn't in the test set, generate new ID
                self.hotel_counter += 1
                df.at[idx, "hotel_id_clean"] = f"hotel_{self.hotel_counter:06d}"
        
        # Replace corrupted IDs
        df["hotel_id"] = df["hotel_id_clean"]
        df = df.drop(columns=["hotel_id_clean"])
        
        # Save fixed version
        fixed_file = self.output_dir / "hotel_features_complete.parquet"
        df.to_parquet(fixed_file, index=False)
        logger.info(f"✓ Fixed hotel features saved to: {fixed_file}")
        
        stats = {
            "total_hotels": len(df),
            "unique_hotels": df["hotel_id"].nunique(),
            "hotels_with_test_mapping": mapped_count
        }
        
        return df, stats
    
    def fix_user_features(self, user_id_mapping: Dict[str, str]) -> Tuple[pd.DataFrame, Dict]:
        """Fix corrupted IDs in user features."""
        logger.info("\n" + "="*80)
        logger.info("FIXING USER FEATURES")
        logger.info("="*80)
        
        features_file = self.data_dir / "features" / "user_features_complete.parquet"
        
        if not features_file.exists():
            logger.error(f"User features file not found: {features_file}")
            return None, {}
        
        # Load user features
        df = pd.read_parquet(features_file)
        logger.info(f"Loaded {len(df)} users with features")
        
        # Create backup
        backup_file = features_file.with_name("user_features_complete_CORRUPTED_BACKUP.parquet")
        df.to_parquet(backup_file)
        logger.info(f"Backup saved to: {backup_file}")
        
        # Map IDs - use existing mapping from test interactions
        logger.info("Mapping corrupted user IDs...")
        df["user_id_clean"] = df["user_id"].apply(
            lambda x: user_id_mapping.get(x, f"user_{self.user_counter:06d}")
        )
        
        # Count mapped vs unmapped
        mapped_count = (df["user_id_clean"] != f"user_{self.user_counter:06d}").sum()
        logger.info(f"Mapped {mapped_count} users from test set")
        
        # For users not in test set, generate new IDs
        for idx, row in df.iterrows():
            if row["user_id_clean"] == f"user_{self.user_counter:06d}":
                # This user wasn't in the test set, generate new ID
                self.user_counter += 1
                df.at[idx, "user_id_clean"] = f"user_{self.user_counter:06d}"
        
        # Replace corrupted IDs
        df["user_id"] = df["user_id_clean"]
        df = df.drop(columns=["user_id_clean"])
        
        # Save fixed version
        fixed_file = self.output_dir / "user_features_complete.parquet"
        df.to_parquet(fixed_file, index=False)
        logger.info(f"✓ Fixed user features saved to: {fixed_file}")
        
        stats = {
            "total_users": len(df),
            "unique_users": df["user_id"].nunique(),
            "users_with_test_mapping": mapped_count
        }
        
        return df, stats
    
    def run_fix(self) -> Dict:
        """Run complete data corruption fix."""
        logger.info("\n" + "█"*80)
        logger.info("TRIPSENSE AI DATA CORRUPTION FIX")
        logger.info("█"*80)
        logger.info(f"Data directory: {self.data_dir}")
        logger.info(f"Output directory: {self.output_dir}")
        
        results = {}
        
        # Fix test interactions first (establishes ID mappings)
        test_df, test_stats = self.fix_test_interactions()
        results["test_interactions"] = test_stats
        
        if test_df is None:
            logger.error("Failed to fix test interactions. Aborting.")
            return results
        
        # Fix hotel features using established mappings
        hotel_df, hotel_stats = self.fix_hotel_features(self.corrupted_hotel_mapping)
        results["hotel_features"] = hotel_stats
        
        # Fix user features using established mappings
        user_df, user_stats = self.fix_user_features(self.corrupted_user_mapping)
        results["user_features"] = user_stats
        
        # Save ID mapping for reference
        mapping_file = self.output_dir / "id_mapping.json"
        mapping_data = {
            "user_mapping": self.corrupted_user_mapping,
            "hotel_mapping": self.corrupted_hotel_mapping,
            "timestamp": pd.Timestamp.now().isoformat()
        }
        with open(mapping_file, 'w') as f:
            json.dump(mapping_data, f, indent=2)
        logger.info(f"✓ ID mappings saved to: {mapping_file}")
        
        # Summary
        logger.info("\n" + "="*80)
        logger.info("FIX SUMMARY")
        logger.info("="*80)
        logger.info(f"Corrupted user IDs remapped: {len(self.corrupted_user_mapping)}")
        logger.info(f"Corrupted hotel IDs remapped: {len(self.corrupted_hotel_mapping)}")
        logger.info(f"\nTest Interactions: {test_stats}")
        logger.info(f"Hotel Features: {hotel_stats}")
        logger.info(f"User Features: {user_stats}")
        
        logger.info("\n" + "="*80)
        logger.info("✓ DATA CORRUPTION FIX COMPLETE")
        logger.info("="*80)
        logger.info(f"\nFixed datasets are available in: {self.output_dir}")
        logger.info("Backups of corrupted files saved with _CORRUPTED_BACKUP suffix")
        
        return results


def main():
    """Run data corruption fix."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fix corrupted TripSense AI data IDs')
    parser.add_argument('--data-dir', type=str, default=None, 
                       help='Path to data/processed directory')
    parser.add_argument('--output-dir', type=str, default=None,
                       help='Directory for fixed datasets')
    
    args = parser.parse_args()
    
    fixer = DataCorruptionFixer(data_dir=args.data_dir, output_dir=args.output_dir)
    results = fixer.run_fix()
    
    # Save results
    results_file = Path(args.output_dir or fixer.output_dir) / "fix_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results saved to: {results_file}")


if __name__ == "__main__":
    main()

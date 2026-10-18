"""
Data Integrity Validation for TripSense AI

Comprehensive checks for:
1. User ID and Hotel ID format validation
2. Detection of corrupted IDs (review text in ID columns)
3. Schema validation for processed data
4. Relationship integrity (foreign key validation)
5. Data coverage and completeness
6. Train/validation/test split quality
"""

import logging
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
import pandas as pd
import numpy as np

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_integrity_validation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class DataIntegrityValidator:
    """Validates data integrity across processed TripSense datasets."""
    
    def __init__(self, data_dir: str = None):
        """Initialize validator with data directory."""
        if data_dir is None:
            self.data_dir = Path(__file__).parent.parent.parent / "data" / "processed"
        else:
            self.data_dir = Path(data_dir)
        
        self.results = {
            "timestamp": pd.Timestamp.now().isoformat(),
            "checks_passed": [],
            "checks_failed": [],
            "warnings": [],
            "data_quality_metrics": {}
        }
    
    def log_check(self, name: str, passed: bool, details: str = ""):
        """Log a validation check result."""
        if passed:
            self.results["checks_passed"].append({"name": name, "details": details})
            logger.info(f"✓ {name}: {details}")
        else:
            self.results["checks_failed"].append({"name": name, "details": details})
            logger.error(f"✗ {name}: {details}")
    
    def log_warning(self, message: str):
        """Log a warning."""
        self.results["warnings"].append(message)
        logger.warning(f"⚠ {message}")
    
    def detect_id_corruption(self, ids: pd.Series, field_name: str = "ID") -> bool:
        """
        Detect if ID column contains review text or corrupted data.
        
        Corruption indicators:
        - Contains spaces
        - Contains punctuation (quotes, dashes, etc.)
        - Contains common review words (EXCELLENT, GOOD, etc.)
        - Very long strings (>50 chars)
        - Contains review sentiment markers
        """
        logger.info(f"Checking {field_name} column for corruption...")
        
        if ids.isna().sum() > 0:
            self.log_warning(f"{field_name} contains {ids.isna().sum()} null values")
        
        corrupted = []
        review_keywords = ['EXCELLENT', 'GOOD', 'BAD', 'GREAT', 'POOR', 'WONDERFUL', 
                          'TERRIBLE', 'AMAZING', 'AWFUL', 'FOOD', 'HOTEL', 'ROOM']
        
        for idx, val in ids.items():
            if pd.isna(val):
                continue
            
            str_val = str(val).strip()
            
            # Check for review text indicators
            has_space = ' ' in str_val
            has_punctuation = any(c in str_val for c in ['-', '"', "'", '.', ',', '!', '?'])
            has_keywords = any(kw in str_val.upper() for kw in review_keywords)
            too_long = len(str_val) > 50
            
            if has_space or has_punctuation or has_keywords or too_long:
                corrupted.append((idx, str_val[:100]))  # Store first 100 chars
        
        if corrupted:
            logger.error(f"Found {len(corrupted)} corrupted {field_name} values:")
            for idx, val in corrupted[:5]:  # Show first 5
                logger.error(f"  [{idx}]: {val}")
            self.log_check(f"ID Corruption Detection ({field_name})", False, 
                          f"Found {len(corrupted)} corrupted values")
            return True
        else:
            self.log_check(f"ID Corruption Detection ({field_name})", True, 
                          f"No corruption detected in {len(ids)} IDs")
            return False
    
    def validate_id_format(self, ids: pd.Series, field_name: str = "ID", 
                          expected_pattern: str = None) -> bool:
        """
        Validate ID format consistency.
        
        Expected: All IDs follow consistent pattern (e.g., "user_XXXXXX")
        """
        logger.info(f"Validating {field_name} format...")
        
        # Remove nulls
        ids_clean = ids.dropna()
        
        if len(ids_clean) == 0:
            self.log_check(f"ID Format Validation ({field_name})", False, 
                          "No valid IDs found")
            return False
        
        # Check for numeric-only or alphanumeric patterns
        formats = {}
        for val in ids_clean:
            str_val = str(val).strip()
            if str_val.isdigit():
                fmt = "numeric"
            elif str_val.startswith("user_") or str_val.startswith("hotel_"):
                fmt = "prefixed"
            else:
                fmt = "other"
            formats[fmt] = formats.get(fmt, 0) + 1
        
        # Check consistency
        if len(formats) > 1:
            self.log_warning(f"{field_name} has mixed formats: {formats}")
            self.log_check(f"ID Format Consistency ({field_name})", False, 
                          f"Mixed formats detected: {formats}")
            return False
        else:
            fmt = list(formats.keys())[0]
            self.log_check(f"ID Format Consistency ({field_name})", True, 
                          f"All {len(ids_clean)} IDs use format: {fmt}")
            return True
    
    def validate_test_interactions(self) -> Dict[str, Any]:
        """Validate test interactions file."""
        logger.info("\n" + "="*80)
        logger.info("VALIDATING TEST INTERACTIONS")
        logger.info("="*80)
        
        test_file = self.data_dir / "splits" / "test_interactions.parquet"
        
        if not test_file.exists():
            self.log_check("Test Interactions File Exists", False, f"File not found: {test_file}")
            return {}
        
        try:
            df = pd.read_parquet(test_file)
            self.log_check("Test Interactions File Exists", True, f"Loaded {len(df)} interactions")
        except Exception as e:
            self.log_check("Test Interactions File Load", False, str(e))
            return {}
        
        # Check required columns
        required_cols = ["user_id", "hotel_id", "overall"]
        for col in required_cols:
            if col in df.columns:
                self.log_check(f"Test Interactions Column: {col}", True, 
                              f"Column exists with {df[col].notna().sum()} non-null values")
            else:
                self.log_check(f"Test Interactions Column: {col}", False, 
                              f"Column missing (found: {list(df.columns)})")
        
        # Validate IDs
        if "user_id" in df.columns:
            self.detect_id_corruption(df["user_id"], "user_id")
            self.validate_id_format(df["user_id"], "user_id")
        
        if "hotel_id" in df.columns:
            self.detect_id_corruption(df["hotel_id"], "hotel_id")
            self.validate_id_format(df["hotel_id"], "hotel_id")
        
        # Analyze rating distribution
        if "overall" in df.columns:
            rating_stats = {
                "min": float(df["overall"].min()),
                "max": float(df["overall"].max()),
                "mean": float(df["overall"].mean()),
                "median": float(df["overall"].median()),
                "std": float(df["overall"].std()),
                "count": int(len(df))
            }
            logger.info(f"Rating statistics: {rating_stats}")
            self.results["data_quality_metrics"]["test_ratings"] = rating_stats
        
        # Check for high-rating items (relevance threshold >= 4.0)
        if "overall" in df.columns:
            relevant_count = (df["overall"] >= 4.0).sum()
            relevant_pct = (relevant_count / len(df)) * 100
            self.log_check("Relevant Items (rating >= 4.0)", True, 
                          f"{relevant_count:,} items ({relevant_pct:.1f}% of {len(df):,} total)")
            self.results["data_quality_metrics"]["relevant_items"] = {
                "count": int(relevant_count),
                "percentage": float(relevant_pct),
                "total": int(len(df))
            }
        
        # User and hotel coverage
        unique_users = df["user_id"].nunique() if "user_id" in df.columns else 0
        unique_hotels = df["hotel_id"].nunique() if "hotel_id" in df.columns else 0
        
        self.log_check("Test Interactions Coverage - Users", True, 
                      f"{unique_users:,} unique users")
        self.log_check("Test Interactions Coverage - Hotels", True, 
                      f"{unique_hotels:,} unique hotels")
        
        self.results["data_quality_metrics"]["test_interactions"] = {
            "total_interactions": int(len(df)),
            "unique_users": int(unique_users),
            "unique_hotels": int(unique_hotels),
            "sparsity": float(1 - len(df) / (unique_users * unique_hotels))
        }
        
        return self.results["data_quality_metrics"].get("test_interactions", {})
    
    def validate_hotel_features(self) -> Dict[str, Any]:
        """Validate hotel features file."""
        logger.info("\n" + "="*80)
        logger.info("VALIDATING HOTEL FEATURES")
        logger.info("="*80)
        
        features_file = self.data_dir / "features" / "hotel_features_complete.parquet"
        
        if not features_file.exists():
            self.log_check("Hotel Features File Exists", False, f"File not found: {features_file}")
            return {}
        
        try:
            df = pd.read_parquet(features_file)
            self.log_check("Hotel Features File Exists", True, f"Loaded {len(df)} hotels")
        except Exception as e:
            self.log_check("Hotel Features File Load", False, str(e))
            return {}
        
        # Check hotel_id
        if "hotel_id" in df.columns:
            self.detect_id_corruption(df["hotel_id"], "hotel_id")
            self.validate_id_format(df["hotel_id"], "hotel_id")
            unique_hotels = df["hotel_id"].nunique()
            duplicates = len(df) - unique_hotels
            if duplicates > 0:
                self.log_check("Hotel ID Uniqueness", False, 
                              f"Found {duplicates} duplicate hotel_ids")
            else:
                self.log_check("Hotel ID Uniqueness", True, 
                              f"All {len(df)} hotel_ids are unique")
        else:
            self.log_check("Hotel ID Column Exists", False, 
                          f"Column missing (found: {list(df.columns)[:5]}...)")
        
        # Check for numeric features
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        self.log_check("Numeric Features", True, 
                      f"Found {len(numeric_cols)} numeric feature columns")
        
        # Check for missing values in features
        missing_pcts = (df[numeric_cols].isna().sum() / len(df) * 100).sort_values(ascending=False)
        if missing_pcts.max() > 0:
            self.log_warning(f"Found missing values in features. Max: {missing_pcts.max():.2f}%")
        
        self.results["data_quality_metrics"]["hotel_features"] = {
            "total_hotels": int(len(df)),
            "numeric_features": int(len(numeric_cols)),
            "all_columns": int(len(df.columns))
        }
        
        return self.results["data_quality_metrics"].get("hotel_features", {})
    
    def validate_user_features(self) -> Dict[str, Any]:
        """Validate user features file."""
        logger.info("\n" + "="*80)
        logger.info("VALIDATING USER FEATURES")
        logger.info("="*80)
        
        features_file = self.data_dir / "features" / "user_features_complete.parquet"
        
        if not features_file.exists():
            self.log_check("User Features File Exists", False, f"File not found: {features_file}")
            return {}
        
        try:
            df = pd.read_parquet(features_file)
            self.log_check("User Features File Exists", True, f"Loaded {len(df)} users")
        except Exception as e:
            self.log_check("User Features File Load", False, str(e))
            return {}
        
        # Check user_id
        if "user_id" in df.columns:
            self.detect_id_corruption(df["user_id"], "user_id")
            self.validate_id_format(df["user_id"], "user_id")
            unique_users = df["user_id"].nunique()
            duplicates = len(df) - unique_users
            if duplicates > 0:
                self.log_check("User ID Uniqueness", False, 
                              f"Found {duplicates} duplicate user_ids")
            else:
                self.log_check("User ID Uniqueness", True, 
                              f"All {len(df)} user_ids are unique")
        
        # Check for numeric features
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        self.log_check("Numeric Features", True, 
                      f"Found {len(numeric_cols)} numeric feature columns")
        
        self.results["data_quality_metrics"]["user_features"] = {
            "total_users": int(len(df)),
            "numeric_features": int(len(numeric_cols)),
            "all_columns": int(len(df.columns))
        }
        
        return self.results["data_quality_metrics"].get("user_features", {})
    
    def validate_cross_references(self) -> bool:
        """Validate referential integrity between datasets."""
        logger.info("\n" + "="*80)
        logger.info("VALIDATING CROSS-REFERENCES")
        logger.info("="*80)
        
        try:
            # Load all datasets
            test_df = pd.read_parquet(self.data_dir / "splits" / "test_interactions.parquet")
            hotel_df = pd.read_parquet(self.data_dir / "features" / "hotel_features_complete.parquet")
            user_df = pd.read_parquet(self.data_dir / "features" / "user_features_complete.parquet")
        except Exception as e:
            self.log_check("Load All Datasets", False, str(e))
            return False
        
        # Check: All test users exist in user features
        test_users = set(test_df["user_id"].unique())
        feature_users = set(user_df["user_id"].unique())
        missing_users = test_users - feature_users
        
        if missing_users:
            self.log_check("Test Users in User Features", False, 
                          f"{len(missing_users)} test users not in features")
        else:
            self.log_check("Test Users in User Features", True, 
                          f"All {len(test_users)} test users have features")
        
        # Check: All test hotels exist in hotel features
        test_hotels = set(test_df["hotel_id"].unique())
        feature_hotels = set(hotel_df["hotel_id"].unique())
        missing_hotels = test_hotels - feature_hotels
        
        if missing_hotels:
            self.log_check("Test Hotels in Hotel Features", False, 
                          f"{len(missing_hotels)} test hotels not in features")
        else:
            self.log_check("Test Hotels in Hotel Features", True, 
                          f"All {len(test_hotels)} test hotels have features")
        
        # Summary
        all_ok = len(missing_users) == 0 and len(missing_hotels) == 0
        return all_ok
    
    def run_all_checks(self) -> Dict[str, Any]:
        """Run all validation checks."""
        logger.info("\n" + "█"*80)
        logger.info("TRIPSENSE AI DATA INTEGRITY VALIDATION")
        logger.info("█"*80)
        
        self.validate_test_interactions()
        self.validate_hotel_features()
        self.validate_user_features()
        self.validate_cross_references()
        
        # Summary
        logger.info("\n" + "="*80)
        logger.info("VALIDATION SUMMARY")
        logger.info("="*80)
        logger.info(f"Checks Passed: {len(self.results['checks_passed'])}")
        logger.info(f"Checks Failed: {len(self.results['checks_failed'])}")
        logger.info(f"Warnings: {len(self.results['warnings'])}")
        
        if self.results['checks_failed']:
            logger.error("\n❌ FAILURES DETECTED:")
            for check in self.results['checks_failed']:
                logger.error(f"  - {check['name']}: {check['details']}")
        
        if self.results['checks_passed']:
            logger.info("\n✓ PASSED CHECKS:")
            for check in self.results['checks_passed'][:5]:  # Show first 5
                logger.info(f"  - {check['name']}")
        
        # Save results
        output_file = Path(__file__).parent / "data_integrity_results.json"
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        logger.info(f"\n✓ Results saved to: {output_file}")
        
        # Determine overall status
        overall_status = "✓ PASS" if len(self.results['checks_failed']) == 0 else "✗ FAIL"
        logger.info(f"\n{'='*80}")
        logger.info(f"OVERALL STATUS: {overall_status}")
        logger.info(f"{'='*80}\n")
        
        return self.results


def main():
    """Run data integrity validation."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate TripSense AI data integrity')
    parser.add_argument('--data-dir', type=str, default=None, 
                       help='Path to data/processed directory')
    
    args = parser.parse_args()
    
    validator = DataIntegrityValidator(data_dir=args.data_dir)
    results = validator.run_all_checks()
    
    # Exit with appropriate code
    sys.exit(0 if len(results['checks_failed']) == 0 else 1)


if __name__ == "__main__":
    main()

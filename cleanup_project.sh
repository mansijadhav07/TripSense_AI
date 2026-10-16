#!/bin/bash
# TripSense-AI - Project Cleanup Script
# Removes temporary files and organizes documentation

echo "🧹 Cleaning up TripSense-AI project..."

# Create docs directory if it doesn't exist
mkdir -p docs/archive

# Move all unnecessary documentation to archive
echo "📦 Archiving old documentation..."
mv PHASE_0_STATUS.md docs/archive/ 2>/dev/null
mv PHASE_1_STATUS.md docs/archive/ 2>/dev/null
mv PHASE_2_STATUS.md docs/archive/ 2>/dev/null
mv PHASE_2_SUMMARY.md docs/archive/ 2>/dev/null
mv PHASE_3_STATUS.md docs/archive/ 2>/dev/null
mv PHASE_3_SUMMARY.md docs/archive/ 2>/dev/null
mv PHASE_3_COMPLETE.md docs/archive/ 2>/dev/null
mv PROJECT_SUMMARY.md docs/archive/ 2>/dev/null
mv DEMO_SUMMARY.md docs/archive/ 2>/dev/null
mv RUNNING_DEMO.md docs/archive/ 2>/dev/null
mv DATASET_ACQUISITION.md docs/archive/ 2>/dev/null
mv QUICK_TEST.md docs/archive/ 2>/dev/null
mv BUG_FIXES_SUMMARY.md docs/archive/ 2>/dev/null
mv TEST_FIXES_GUIDE.md docs/archive/ 2>/dev/null
mv FIXES_COMPLETE.md docs/archive/ 2>/dev/null
mv COMPLETE_FIX_GUIDE.md docs/archive/ 2>/dev/null
mv QUICK_REFERENCE.md docs/archive/ 2>/dev/null
mv design.md docs/archive/ 2>/dev/null
mv requirements.md docs/archive/ 2>/dev/null
mv tasks.md docs/archive/ 2>/dev/null

# Remove all log files
echo "🗑️  Removing log files..."
rm -f *.log 2>/dev/null

# Remove test scripts (keep in git history)
echo "🗑️  Removing temporary test scripts..."
rm -f test_fixes.py 2>/dev/null
rm -f test_complete_system.py 2>/dev/null
rm -f verify_all_fixes.sh 2>/dev/null

# Remove coverage files
rm -f .coverage coverage.xml 2>/dev/null
rm -rf htmlcov .pytest_cache 2>/dev/null

# Remove DS_Store files
find . -name ".DS_Store" -delete 2>/dev/null

# Remove database from root (keep in apps/api)
rm -f tripsense.db 2>/dev/null

# Keep only essential docs in root
echo "📝 Essential documentation:"
ls -1 *.md 2>/dev/null

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "📁 Project structure:"
echo "   Root: README.md, START_HERE.md, QUICK_START.md"
echo "   Archive: docs/archive/ (old documentation)"
echo "   Scripts: start-backend.sh, start-frontend.sh"

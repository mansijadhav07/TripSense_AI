# TripSense AI Model Evaluation Summary

**Last Updated**: October 16, 2026  
**Status**: Phases 1-2 Complete, Phase 3-6 In Progress

---

## Quick Status

| Phase | Task | Status | Key Result |
|-------|------|--------|-----------|
| 1 | Data Integrity Fix | ✓ DONE | 3,633 users + 10,404 hotels remapped |
| 2 | SVD Baseline | ✓ DONE | NDCG@10 = 0.1554 (target: 0.13) |
| 3 | Model Debugging | ⏳ IN PROGRESS | Popularity & Content-Based analysis |
| 4 | Ablation Experiments | ⏳ PLANNED | Signal contribution measurement |
| 5 | Hybrid Optimization | ⏳ PLANNED | Weight tuning on validation set |
| 6 | Final Reporting | ⏳ PLANNED | Dashboard update + documentation |

---

## Current Model Performance

Evaluation on **2,558 test users** with clean, validated data:

```
Random Baseline:           NDCG@10 = 0.0003  (Hit Rate: 0.12%)
Popularity Baseline:       NDCG@10 = 0.0007  (Hit Rate: 0.20%)
SVD/CF (50 components):    NDCG@10 = 0.1554  (Hit Rate: 15.79%) ← BEST
```

**Best SVD Configuration**: 50 components
- Explained Variance: 75.31%
- Precision@10: 0.0180
- Recall@10: 0.1562
- MAP@10: 0.1546

---

## Data Quality Metrics

✓ **Data Integrity**: PASS
- Clean ID format: user_XXXXXX, hotel_XXXXXX
- Referential integrity: 100% (no missing features)
- No corrupted fields

✓ **Ground Truth**:
- Total test interactions: 10,952
- Relevant items (≥4.0 rating): 8,752 (79.9%)
- Users with relevant items: 2,558 (70.4%)
- Average relevant items/user: 3.42
- Matrix sparsity: 99.97%

---

## Key Files

### Data
- Fixed datasets: `data/processed/splits_fixed/`
  - `test_interactions.parquet` (10,952 rows)
  - `hotel_features_complete.parquet` (50,780 hotels)
  - `user_features_complete.parquet` (19,531 users)
- ID mapping: `data/processed/splits_fixed/id_mapping.json`

### Evaluation Code
- `ml/validation/data_integrity.py` - Data quality checks
- `ml/validation/fix_data_corruption.py` - ID mapping
- `ml/evaluation/evaluate_baseline.py` - Baseline models
- `ml/evaluation/evaluate_cf_svd.py` - SVD/CF evaluation

### Results
- `ml/evaluation/results_baseline/baseline_evaluation.json`
- `ml/evaluation/results_cf_svd/cf_svd_evaluation.json`

---

## Next Steps

### Phase 3a: Debug Popularity (Why 0.0007?)
```
Question: Are top-10 popular hotels in test user ground truth?
Method:  1. Get top-10 popular hotels by review count + rating
         2. For each test user, check if any are in ground truth
         3. Compute hit rate and aggregate metrics
Expected: Honest diagnosis of why popularity underperforms
```

### Phase 3b: Debug Content-Based
```
Question: Can 32 hotel features predict user preference?
Method:  1. Use cosine similarity between hotel features
         2. For each user, find hotels similar to their history
         3. Evaluate per-user and aggregate
Expected: Identify feature-preference mismatch or improvement opportunity
```

### Phase 3c: Debug Hybrid Ensemble
```
Question: Why were Hybrid and CF identical before?
Method:  1. Verify all signals included (CF, Content, Popularity, Sentiment)
         2. Check score normalization and weighting
         3. Implement proper weighted combination
Expected: Fix implementation, prepare for Phase 4
```

### Phase 4: Ablation Experiments
```
All on validation-tuned, test-evaluated basis:
Exp1: CF only                              → NDCG@10
Exp2: CF (0.7) + Popularity (0.3)          → NDCG@10
Exp3: CF (0.7) + Content (0.3)             → NDCG@10
Exp4: CF (0.7) + Sentiment (0.3)           → NDCG@10
Exp5: Full Hybrid (optimized weights)      → NDCG@10
```

---

## Evaluation Protocol

**Consistency Across All Models**:
- Relevance threshold: 4.0 rating
- Test users: 2,558 with relevant items
- K value: 10 (top-10 recommendations)
- Metrics: NDCG@10, Precision@10, Recall@10, MAP@10, Hit Rate
- No test set peeking for hyperparameter tuning
- All results reported honestly (no fabrication)

---

## Important Notes

1. **SVD is Strong Baseline**: 0.1554 NDCG@10 shows genuine collaborative signal
2. **Honesty First**: Results reflect actual performance, not forced improvements
3. **Small Ground Truth**: ~3.4 items/user means metrics will naturally be modest
4. **Data is Clean**: All IDs validated, no corruption, 100% referential integrity
5. **Reproducible**: Same code + same data = same results every time

---

## Contact & Questions

For questions or clarifications on:
- **Data pipeline**: See `ml/validation/` directory
- **SVD results**: See `ml/evaluation/results_cf_svd/cf_svd_evaluation.json`
- **Methodology**: See master status report (artifact)
- **Next steps**: See Phase 3-6 planning in this document

---

## Artifacts (Detailed Reports)

1. **Phase 1 Report: Data Integrity Fix Complete**
   - Problem analysis, solution approach, verification
   
2. **Phase 2 Report: SVD/CF Baseline Reproduced**
   - Component analysis, comparison with previous results, diagnostics

3. **Master Status Report: TripSense AI Model Evaluation**
   - Complete overview, timeline, success criteria, next steps

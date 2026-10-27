> **RETRACTED METRICS:** figures in this card came from a leaky/corrupted evaluation and are not valid. See README → *Verified status* and `ml/evaluation/results/verified_evaluation.json`.

# Model Card: Hybrid Ensemble Recommender

## Model Details
- **Model Name:** HybridEnsembleRecommender
- **Model Version:** 1.0.0
- **Model Type:** Context-Aware Weighted Multi-Model Ensemble
- **Component Sub-Models:**
  - Collaborative Filtering (ALS): 35% weight (normal), 5% (cold-start)
  - Content-Based Filtering: 30% weight (normal), 35% (cold-start)
  - NLP Sentiment Recommender: 20% weight (normal), 25% (cold-start)
  - Popularity Recommender: 15% weight (normal), 35% (cold-start)

## Evaluation Metrics (Held-Out Test Set, K=10)
- **NDCG@10:** 0.1696
- **Recall@10:** 0.1775
- **MAP:** 0.1671
- **Latency:** ~60ms

## Explainability
Generates multi-attribute explanation payloads breaking down confidence scores, aspect alignment, and contributing sub-models for each recommended hotel.

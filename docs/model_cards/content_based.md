> **RETRACTED METRICS:** figures in this card came from a leaky/corrupted evaluation and are not valid. See README → *Verified status* and `ml/evaluation/results/verified_evaluation.json`.

# Model Card: Content-Based Recommender

## Model Details
- **Model Name:** ContentBasedRecommender
- **Model Version:** 1.0.0
- **Model Type:** Feature Vector Cosine Similarity & Aspect Matching
- **Feature Space:** 13 engineered hotel dimensions (cleanliness, service, location, rooms, value, sleep quality, consistency, sentiment magnitude)

## Intended Use
- **Primary Use:** Matching hotels to fine-grained user aspect priorities and finding similar properties to an existing favorite hotel.
- **Explainability:** Provides exact feature-level reasons for recommendations.

## Performance
- **Latency:** ~50ms
- **Cold Start Support:** High (depends only on hotel metadata, not user-item interaction density)

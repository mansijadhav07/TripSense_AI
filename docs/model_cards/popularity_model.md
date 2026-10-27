> **RETRACTED METRICS:** figures in this card came from a leaky/corrupted evaluation and are not valid. See README → *Verified status* and `ml/evaluation/results/verified_evaluation.json`.

# Model Card: Popularity-Based Recommender

## Model Details
- **Model Name:** PopularityRecommender
- **Model Version:** 1.0.0
- **Model Type:** Baseline non-personalized ranking algorithm
- **Framework:** Apache Spark ML & NumPy
- **Developer:** TripSense AI Team

## Intended Use
- **Primary Use:** Baseline recommendations for unauthenticated users and severe cold-start scenarios.
- **Fallback Role:** Safe fallback when user interaction history is insufficient for collaborative filtering.

## Algorithm & Formula
Combines logarithmic review counts with Bayesian-adjusted average ratings:
$$\text{Score} = 0.5 \cdot \ln(1 + \text{review\_count}) + 0.3 \cdot \text{avg\_rating} + 0.2 \cdot \ln(1 + \text{unique\_reviewers})$$

## Training Data
- **Dataset:** TripAdvisor Hotel Reviews (~201K reviews, 50K+ hotels)
- **Features Used:** Total reviews, rating mean, reviewer variance

## Evaluation Metrics (Test Set, K=10)
- **Catalog Coverage:** 100%
- **Latency:** < 15ms
- **Cold Start Support:** 100%

## Strengths & Limitations
- **Strengths:** Zero latency bottleneck, reliable fallback, robust to sparse user profiles.
- **Limitations:** No personalization; popular items dominate recommendations.

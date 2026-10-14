# TripSense AI Recommendation Models

This directory contains all 5 recommendation algorithms used in TripSense AI.

---

## 📚 Models Overview

### 1. Popularity-Based Recommender
**File:** `popularity_model.py`

Simple but effective baseline model that recommends hotels based on popularity metrics.

**Strategies:**
- Global popularity (most reviewed + highest rated)
- Trending (gaining recent popularity)
- Quality (high ratings with consistency)

**When to use:**
- Cold start users (no history)
- Fallback when other models fail
- Quick recommendations
- Trending destinations

---

### 2. Collaborative Filtering (ALS)
**File:** `collaborative_filtering.py`

Matrix factorization using Alternating Least Squares to discover user-item patterns.

**How it works:**
- Factorizes user-item interaction matrix into latent factors
- 50 latent dimensions capture hidden preferences
- Predicts ratings based on factor similarity

**When to use:**
- Users with review history (5+ reviews)
- Personalized recommendations
- "Users like you also liked..." features

**Limitations:**
- Requires training data
- Cold start users and items

---

### 3. Content-Based Recommender
**File:** `content_based.py`

Recommends hotels based on feature similarity to user preferences.

**Features used:**
- Aspect ratings (cleanliness, service, location, rooms, value)
- Hotel metrics (rating, review count, star distribution)
- Quality metrics (consistency)

**When to use:**
- Users with some history (1+ reviews)
- "Hotels like this" features
- Aspect-specific search (e.g., "excellent location")
- Explainable recommendations

---

### 4. NLP/Sentiment Recommender
**File:** `nlp_sentiment.py`

Analyzes review text to capture sentiment and quality perceptions.

**Capabilities:**
- Overall sentiment scoring
- Aspect-level sentiment (per feature)
- Positive/negative word analysis
- User sentiment profile matching

**When to use:**
- Quality filtering
- Sentiment-based search
- Aspect sentiment ("positive cleanliness reviews")
- Nuanced recommendations beyond ratings

---

### 5. Hybrid Ensemble Recommender ⭐
**File:** `hybrid_ensemble.py`

Intelligently combines all 4 models with context-aware weighting.

**Architecture:**
```
Request → Context Analysis → Model Selection → Parallel Execution → 
Score Normalization → Weighted Averaging → Ranking → Explanation
```

**Weighting Strategy:**
- **Normal users:** Collaborative 35%, Content 30%, Sentiment 20%, Popularity 15%
- **Cold start:** Collaborative 5%, Content 35%, Sentiment 25%, Popularity 35%

**Output includes:**
- Final score
- Contributing models
- Individual model scores
- Explanation

**This is the recommended model for production.**

---

## 🚀 Quick Start

### Training All Models

```bash
# From project root
python ml/train_models.py --all
```

This will:
1. Load training data
2. Train all 5 models sequentially
3. Save models to `artifacts/models/`
4. Log progress to console + `training.log`

**Estimated time:** 20-25 hours

### Training Individual Models

```bash
# Train specific model
python ml/train_models.py --model popularity      # ~3-4 hours
python ml/train_models.py --model collaborative   # ~5-6 hours
python ml/train_models.py --model content         # ~4-5 hours
python ml/train_models.py --model sentiment       # ~4-5 hours
python ml/train_models.py --model hybrid          # ~4-5 hours
```

---

## 💻 Usage Examples

### Using Popularity Model

```python
from models import PopularityRecommender
from spark_setup import create_spark_session

spark = create_spark_session("PopularityTest")

# Load data
hotel_features = spark.read.parquet("data/processed/features/hotel_features_complete.parquet")
reviews = spark.read.parquet("data/processed/train.parquet")

# Train model
model = PopularityRecommender()
model.train(reviews, hotel_features)

# Get recommendations
global_popular = model.recommend(n=10, strategy="global")
trending = model.recommend(n=10, strategy="trending")
quality = model.recommend(n=10, strategy="quality")

# Save model
model.save("artifacts/models/popularity")
```

### Using Collaborative Filtering

```python
from models import CollaborativeFilteringRecommender

model = CollaborativeFilteringRecommender(
    rank=50,
    max_iter=10,
    reg_param=0.1
)

model.train(train_df, user_features_df, hotel_features_df)

# Get user recommendations
user_recs = model.recommend_for_user("user_123", n=10)

# Predict rating
predicted_rating = model.predict("user_123", "hotel_456")

model.save("artifacts/models/collaborative_filtering")
```

### Using Content-Based

```python
from models import ContentBasedRecommender

model = ContentBasedRecommender()
model.train(train_df, hotel_features_df, user_features_df)

# User-based recommendations
user_recs = model.recommend_for_user("user_123", n=10)

# Similar hotels
similar = model.recommend_similar_hotels("hotel_456", n=5)

# Aspect-based search
aspect_recs = model.recommend_by_aspects({
    "cleanliness": 0.6,
    "location": 0.4
}, n=10)

model.save("artifacts/models/content_based")
```

### Using Sentiment Model

```python
from models import NLPSentimentRecommender

model = NLPSentimentRecommender()
model.train(train_df, text_features_df, hotel_features_df)

# Best sentiment hotels
sentiment_recs = model.recommend_by_sentiment(n=10)

# Match user sentiment
user_recs = model.recommend_for_user("user_123", n=10)

# Aspect sentiment
aspect_recs = model.recommend_by_aspects({
    "cleanliness": 0.5,
    "service": 0.5
}, n=10)

model.save("artifacts/models/nlp_sentiment")
```

### Using Hybrid Ensemble (Recommended)

```python
from models import HybridEnsembleRecommender

model = HybridEnsembleRecommender()

# Train all base models
model.train(
    train_df,
    user_features_df,
    hotel_features_df,
    text_features_df
)

# Get adaptive recommendations
recommendations = model.recommend_for_user(
    "user_123",
    n=10,
    strategy="adaptive"  # Adjusts for cold start
)

# Inspect results
for rec in recommendations:
    print(f"Hotel: {rec['hotel_id']}")
    print(f"Score: {rec['score']:.3f}")
    print(f"Models: {rec['contributing_models']}")
    print(f"Breakdown: {rec['model_scores']}")
    print()

# Find similar hotels
similar = model.recommend_similar_hotels("hotel_456", n=5)

model.save("artifacts/models/hybrid_ensemble")
```

### Loading Saved Models

```python
from models import HybridEnsembleRecommender
from spark_setup import create_spark_session

spark = create_spark_session("Inference")

model = HybridEnsembleRecommender()
model.load("artifacts/models/hybrid_ensemble", spark)

# Model is ready for inference
recommendations = model.recommend_for_user("user_123", n=10)
```

---

## 📊 Model Comparison

| Aspect | Popularity | Collaborative | Content | Sentiment | Hybrid |
|--------|-----------|--------------|---------|-----------|--------|
| **Personalization** | ❌ None | ✅ High | ⭐ Medium | ⭐ Medium | ✅ High |
| **Cold Start** | ✅ Excellent | ❌ Poor | ⭐ Good | ⭐ Medium | ✅ Excellent |
| **Explainability** | ⭐⭐⭐ High | ⭐ Low | ⭐⭐⭐ High | ⭐⭐⭐ High | ⭐⭐⭐ High |
| **Diversity** | ❌ Low | ⭐ Medium | ⭐ Medium | ⭐ Medium | ✅ High |
| **Speed** | ⚡ Very Fast | ⭐ Medium | ⚡ Fast | ⭐ Medium | ⭐ Medium |
| **Accuracy** | ⭐ Baseline | ⭐⭐ Good | ⭐⭐ Good | ⭐⭐ Good | ⭐⭐⭐ Best |

**Recommendation:** Use **Hybrid Ensemble** for production. It combines strengths of all models and handles all edge cases.

---

## 🏗️ Architecture

### Data Flow

```
Raw Reviews (201K records)
    ↓
Phase 2: Feature Engineering
    ├─> User Features (167K users, 20+ features)
    ├─> Hotel Features (201K hotels, 30+ features)
    └─> Text Features (201K reviews, NLP features)
    ↓
Phase 3: Model Training
    ├─> Popularity Model (global/trending/quality)
    ├─> Collaborative Model (ALS matrix factorization)
    ├─> Content Model (feature vectors + similarity)
    └─> Sentiment Model (text analysis + aggregation)
    ↓
Hybrid Ensemble
    └─> Context-aware weighted combination
    ↓
Recommendations + Explanations
```

### Model Dependencies

```
HybridEnsemble
    ├── requires → PopularityRecommender
    ├── requires → CollaborativeFilteringRecommender
    ├── requires → ContentBasedRecommender
    └── requires → NLPSentimentRecommender

PopularityRecommender
    └── requires → hotel_features

CollaborativeFilteringRecommender
    ├── requires → train/test reviews
    ├── requires → user_features
    └── requires → hotel_features

ContentBasedRecommender
    ├── requires → train reviews
    ├── requires → hotel_features
    └── requires → user_features

NLPSentimentRecommender
    ├── requires → train reviews
    ├── requires → text_features
    └── requires → hotel_features (optional)
```

---

## 🔧 Configuration

### Collaborative Filtering Hyperparameters

```python
# Default (works well for most cases)
rank=50              # Latent factors (try 20-100)
max_iter=10          # ALS iterations (try 5-20)
reg_param=0.1        # Regularization (try 0.01-1.0)

# For larger datasets
rank=100
max_iter=15
reg_param=0.05

# For faster training
rank=20
max_iter=5
reg_param=0.2
```

### Hybrid Ensemble Weights

```python
# Default weights (optimized for our dataset)
base_weights = {
    "collaborative": 0.35,
    "content": 0.30,
    "sentiment": 0.20,
    "popularity": 0.15
}

# For cold start heavy scenarios
cold_start_weights = {
    "collaborative": 0.05,
    "content": 0.35,
    "sentiment": 0.25,
    "popularity": 0.35
}

# Custom weights (must sum to 1.0)
custom_weights = {
    "collaborative": 0.40,  # More personalization
    "content": 0.30,
    "sentiment": 0.20,
    "popularity": 0.10
}

model = HybridEnsembleRecommender(base_weights=custom_weights)
```

---

## 📈 Performance Tips

### Training Optimization

1. **Use Caching:** DataFrames used multiple times
   ```python
   train_df.cache()
   hotel_features_df.cache()
   ```

2. **Partition Data:** For large datasets
   ```python
   train_df = train_df.repartition(100)
   ```

3. **Checkpoint:** For iterative algorithms
   ```python
   spark.sparkContext.setCheckpointDir("/tmp/checkpoints")
   ```

4. **Reduce Logging:** In production
   ```python
   import logging
   logging.getLogger("pyspark").setLevel(logging.ERROR)
   ```

### Inference Optimization

1. **Pre-compute Popular:** Cache popular hotels
2. **Batch Predictions:** Process multiple users at once
3. **Use Hybrid:** Balances accuracy and speed
4. **Cache User Profiles:** Reuse for repeated requests

---

## 🧪 Testing

Each model has a `__main__` block for testing:

```bash
# Test individual models
python -m ml.models.popularity_model
python -m ml.models.collaborative_filtering
python -m ml.models.content_based
python -m ml.models.nlp_sentiment
python -m ml.models.hybrid_ensemble
```

---

## 📝 Model Cards

Detailed model documentation:
- See `docs/model_cards/` for comprehensive model cards
- Each card includes: purpose, architecture, training, evaluation, limitations

---

## 🐛 Troubleshooting

### "Model not trained" Error
- Call `model.train()` before inference
- Or load a trained model with `model.load()`

### "User not found" Warning
- User is cold start (not in training data)
- Hybrid ensemble will use cold start weights

### Out of Memory
- Reduce batch size
- Increase Spark memory: `--driver-memory 8g`
- Cache fewer DataFrames

### Slow Training
- Reduce `rank` in collaborative filtering
- Reduce `max_iter`
- Use fewer features in content-based

---

## 📚 References

**Algorithms:**
- ALS: Hu, Koren, Volinsky (2008) - "Collaborative Filtering for Implicit Feedback"
- Content-Based: Pazzani, Billsus (2007) - "Content-Based Recommendation Systems"
- Hybrid: Burke (2002) - "Hybrid Recommender Systems"

**Libraries:**
- Apache Spark MLlib
- PySpark
- NumPy

---

## 📄 License

Part of TripSense AI project. Academic use only.

---

**Last Updated:** October 14, 2026  
**Version:** 1.0.0  
**Status:** Production Ready (Code) - Training Pending

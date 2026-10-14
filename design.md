# TripSense AI — Design & Architecture Specification

**Version:** 1.0.0  
**Last Updated:** October 14, 2026  
**Status:** Draft for Review

---

## 1. System Architecture Overview

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     USER INTERFACE LAYER                     │
│  Next.js App Router + React + TypeScript + Tailwind CSS     │
│              (Responsive Web Application)                    │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTPS/REST API
                     ↓
┌─────────────────────────────────────────────────────────────┐
│                  APPLICATION API LAYER                       │
│        FastAPI + Pydantic + SQLAlchemy + Alembic            │
│                  (Backend Services)                          │
└───────┬──────────────────────────┬──────────────────────────┘
        │                          │
        ↓                          ↓
┌──────────────────┐      ┌────────────────────────────┐
│  PostgreSQL DB   │      │   ML MODEL SERVING LAYER   │
│  (Structured)    │      │   (Recommendation Engine)  │
│  - Users         │      │   - Model Artifacts        │
│  - Preferences   │      │   - Feature Loaders        │
│  - Saved Hotels  │      │   - Scoring Functions      │
│  - Experiments   │      └────────────────────────────┘
└──────────────────┘                   │
                                       ↓
                     ┌─────────────────────────────────┐
                     │  PROCESSED DATA LAYER           │
                     │  (Parquet Files)                │
                     │  - Hotel Features               │
                     │  - User Interactions            │
                     │  - Review Embeddings            │
                     │  - Aspect Scores                │
                     └─────────────────────────────────┘
                                       ↑
                     ┌─────────────────────────────────┐
                     │  BIG DATA PROCESSING PIPELINE   │
                     │  Apache Spark / PySpark         │
                     │  - Ingestion & Validation       │
                     │  - Cleaning & Transformation    │
                     │  - Feature Engineering          │
                     │  - Model Training               │
                     │  - Evaluation & Benchmarking    │
                     └─────────────────────────────────┘
                                       ↑
                     ┌─────────────────────────────────┐
                     │  RAW DATA STORAGE               │
                     │  TripAdvisor Review Dataset     │
                     │  (CSV/JSON - Read Only)         │
                     └─────────────────────────────────┘
```

### 1.2 Architecture Principles

**1. Separation of Concerns**
- Frontend: Pure presentation and user interaction
- Backend API: Business logic, validation, orchestration
- ML Layer: Model serving and recommendation logic
- Data Pipeline: Offline processing and training

**2. Modularity**
- Each recommendation model is independent and testable
- Clear interfaces between layers
- Pluggable components for easy enhancement

**3. Data Integrity**
- Raw data is immutable (read-only)
- All transformations are reproducible
- Clear lineage from raw data to recommendations

**4. Production Readiness**
- Health checks and monitoring
- Structured logging
- Error handling at all boundaries
- Security by default

**5. Scalability Considerations**
- Stateless API for horizontal scaling
- Cached model artifacts for fast serving
- Batch processing for expensive computations
- Database indexing for common queries

---

## 2. Technology Stack

### 2.1 Frontend Stack

**Core Framework:**
- **Next.js 14+** with App Router (React 18+)
- **TypeScript** for type safety
- **Tailwind CSS** for styling

**UI Components:**
- **shadcn/ui** - Accessible, customizable components
- **Lucide React** - Icon library
- **Recharts** - Data visualization
- **React Hook Form** - Form handling
- **Zod** - Schema validation

**State Management:**
- React Context for global state (auth, preferences)
- Server Components for data fetching
- Client Components for interactivity

**Build & Development:**
- **ESLint** + **Prettier** for code quality
- **Vitest** or **Jest** for testing
- **Playwright** for E2E testing

### 2.2 Backend Stack

**Core Framework:**
- **Python 3.10+**
- **FastAPI** - Modern async API framework
- **Pydantic V2** - Data validation
- **SQLAlchemy 2.0** - ORM
- **Alembic** - Database migrations

**Database:**
- **PostgreSQL 15+** - Primary database
- **psycopg2** or **asyncpg** - Database driver

**Authentication:**
- **python-jose** - JWT handling
- **passlib** with **bcrypt** - Password hashing

**Development & Testing:**
- **Pytest** - Testing framework
- **Ruff** or **Black** - Formatting
- **mypy** - Static type checking

### 2.3 Big Data & ML Stack

**Processing Engine:**
- **Apache Spark 3.5+** (PySpark)
- **Pandas** for local baselines
- **NumPy** for numerical operations

**Machine Learning:**
- **Spark MLlib** - ALS collaborative filtering
- **scikit-learn** - Content-based models, evaluation
- **NLTK** or **spaCy** - NLP preprocessing
- **Sentence Transformers** (optional) - Review embeddings
- **transformers** (optional) - Sentiment analysis

**Data Storage:**
- **Parquet** - Processed dataset format
- **Pickle** or **joblib** - Model serialization

### 2.4 Infrastructure

**Containerization:**
- **Docker** - Container runtime
- **docker-compose** - Multi-container orchestration

**Development Tools:**
- **Git** - Version control
- **pre-commit** - Git hooks for quality checks
- **.env** files - Configuration management

---

## 3. Data Architecture

### 3.1 Data Flow

```
┌──────────────────┐
│  Raw Dataset     │  TripAdvisor CSV/JSON
│  (~200k records) │
└────────┬─────────┘
         │
         ↓  [Spark: Ingestion]
┌──────────────────┐
│ Schema Validated │  Column types, required fields
│ Raw Data         │
└────────┬─────────┘
         │
         ↓  [Spark: Cleaning]
┌──────────────────┐
│ Clean Data       │  Deduplicated, missing handled
│ (Parquet)        │
└────────┬─────────┘
         │
         ↓  [Spark: Feature Engineering]
┌──────────────────────────────────────┐
│ Feature Tables (Parquet)             │
│ - hotel_features.parquet             │
│ - user_interactions.parquet          │
│ - review_embeddings.parquet          │
│ - aspect_scores.parquet              │
└────────┬─────────────────────────────┘
         │
         ↓  [Model Training]
┌──────────────────────────────────────┐
│ Model Artifacts                      │
│ - popularity_model.pkl               │
│ - als_model/                         │
│ - content_model.pkl                  │
│ - sentiment_model.pkl                │
│ - hybrid_config.json                 │
└────────┬─────────────────────────────┘
         │
         ↓  [Model Serving]
┌──────────────────────────────────────┐
│ Recommendation API                   │
│ - Load models on startup             │
│ - Cache feature lookups              │
│ - Generate Top-N recommendations     │
└──────────────────────────────────────┘
```

### 3.2 Dataset Schema (Expected)

**Note:** Actual schema must be validated after dataset download.

#### Raw Hotel Reviews Table
```python
{
    "user_id": str,           # Unique user identifier
    "hotel_id": str,          # Unique hotel identifier
    "rating": float,          # Overall rating (1.0-5.0)
    "review_text": str,       # Review content
    "review_date": str,       # Timestamp (if available)
    "hotel_name": str,        # Hotel name
    "destination": str,       # City/location
    "price_range": str,       # Budget category (if available)
    
    # Aspect-level ratings (if available)
    "cleanliness_rating": float,
    "location_rating": float,
    "rooms_rating": float,
    "service_rating": float,
    "value_rating": float,
    "sleep_quality_rating": float,
}
```

### 3.3 Processed Data Schemas

#### hotel_features.parquet
```python
{
    "hotel_id": str,
    "hotel_name": str,
    "destination": str,
    "avg_rating": float,
    "review_count": int,
    "bayesian_avg": float,         # Adjusted for review count
    "avg_cleanliness": float,
    "avg_location": float,
    "avg_rooms": float,
    "avg_service": float,
    "avg_value": float,
    "avg_sleep_quality": float,
    "sentiment_score": float,       # From NLP
    "content_vector": List[float],  # TF-IDF or embeddings
    "metadata_hash": str,           # For change detection
}
```

#### user_interactions.parquet
```python
{
    "user_id": str,
    "hotel_id": str,
    "rating": float,
    "timestamp": datetime,          # If available
    "interaction_type": str,        # "rating", "review", "implicit"
}
```

#### aspect_scores.parquet
```python
{
    "hotel_id": str,
    "aspect": str,                  # "cleanliness", "location", etc.
    "score": float,
    "review_count": int,
    "sentiment": float,             # From NLP
}
```

### 3.4 Application Database Schema (PostgreSQL)

#### users
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
```

#### user_preferences
```sql
CREATE TABLE user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    destination VARCHAR(255),
    min_budget DECIMAL(10,2),
    max_budget DECIMAL(10,2),
    min_rating DECIMAL(2,1),
    cleanliness_weight DECIMAL(3,2) DEFAULT 1.0,
    location_weight DECIMAL(3,2) DEFAULT 1.0,
    rooms_weight DECIMAL(3,2) DEFAULT 1.0,
    service_weight DECIMAL(3,2) DEFAULT 1.0,
    value_weight DECIMAL(3,2) DEFAULT 1.0,
    travel_style VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id)
);
```

#### saved_hotels
```sql
CREATE TABLE saved_hotels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    hotel_id VARCHAR(255) NOT NULL,
    saved_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, hotel_id)
);

CREATE INDEX idx_saved_hotels_user ON saved_hotels(user_id);
CREATE INDEX idx_saved_hotels_hotel ON saved_hotels(hotel_id);
```

#### model_experiments
```sql
CREATE TABLE model_experiments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_name VARCHAR(255) NOT NULL,
    model_type VARCHAR(50) NOT NULL,
    parameters JSONB,
    metrics JSONB,
    dataset_version VARCHAR(50),
    training_date TIMESTAMP DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'running'
);

CREATE INDEX idx_experiments_date ON model_experiments(training_date DESC);
```

---

## 4. Recommendation Engine Design

### 4.1 Model Components

#### Model 1: Popularity Baseline

**Algorithm:** Bayesian Average
```python
def bayesian_average(rating_sum, review_count, global_mean, min_reviews=10):
    """
    Weighted rating that accounts for review count variance.
    Prevents hotels with few perfect ratings from dominating.
    """
    return (rating_sum + min_reviews * global_mean) / (review_count + min_reviews)
```

**Features Used:**
- Overall rating
- Review count
- Global average rating

**Output:** Ranked list by adjusted rating

**Use Case:** Cold-start, baseline comparison

---

#### Model 2: Collaborative Filtering (ALS)

**Algorithm:** Alternating Least Squares (Spark MLlib)

**Training:**
```python
from pyspark.ml.recommendation import ALS

als = ALS(
    maxIter=10,
    regParam=0.1,
    userCol="user_id_encoded",
    itemCol="hotel_id_encoded",
    ratingCol="rating",
    coldStartStrategy="drop",  # or "nan"
    implicitPrefs=False
)

model = als.fit(training_data)
```

**Features Used:**
- User-hotel interaction matrix
- Rating values

**Output:** Predicted rating for (user, hotel) pairs

**Challenges:**
- Sparse matrix handling
- Cold-start for new users/hotels
- Computational cost for large matrices

**Mitigation:**
- Hybrid approach for sparse users
- Fallback to content-based for cold-start
- Batch prediction with caching

---

#### Model 3: Content-Based Filtering

**Algorithm:** Cosine Similarity + TF-IDF

**Process:**
1. Extract hotel features (metadata + review text)
2. Create TF-IDF vectors from review corpus
3. Compute user preference vector from interactions
4. Rank hotels by cosine similarity to user profile

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Build hotel content vectors
vectorizer = TfidfVectorizer(max_features=500, stop_words='english')
hotel_vectors = vectorizer.fit_transform(hotel_review_texts)

# User preference vector (weighted avg of liked hotels)
user_vector = weighted_mean(hotel_vectors[user_liked_indices], weights)

# Rank by similarity
similarities = cosine_similarity(user_vector, hotel_vectors)
```

**Features Used:**
- Review text (TF-IDF)
- Hotel metadata (destination, price_range)
- Aspect-level ratings

**Output:** Similarity scores for each hotel

**Advantages:**
- Works for new users with preferences
- Explainable (can show matching features)
- No cold-start problem for hotels with reviews

---

#### Model 4: NLP & Sentiment Analysis

**Components:**

**A. Sentiment Scoring**
```python
# Option 1: Pretrained model (VADER, TextBlob)
from nltk.sentiment import SentimentIntensityAnalyzer

sia = SentimentIntensityAnalyzer()
sentiment = sia.polarity_scores(review_text)['compound']

# Option 2: Transformers (if compute allows)
from transformers import pipeline

sentiment_pipeline = pipeline("sentiment-analysis")
result = sentiment_pipeline(review_text)[0]
```

**B. Aspect Extraction**
```python
aspect_keywords = {
    "cleanliness": ["clean", "dirty", "spotless", "tidy", "hygiene"],
    "location": ["location", "convenient", "central", "accessible"],
    "service": ["staff", "service", "friendly", "helpful", "rude"],
    "rooms": ["room", "bed", "comfortable", "spacious", "cramped"],
    "value": ["value", "worth", "expensive", "cheap", "price"]
}

def extract_aspect_sentiment(review_text, aspect_keywords):
    # Sentence-level analysis for aspect mentions
    sentences = sent_tokenize(review_text)
    aspect_sentiments = {}
    
    for aspect, keywords in aspect_keywords.items():
        relevant_sentences = [s for s in sentences if any(k in s.lower() for k in keywords)]
        if relevant_sentences:
            sentiments = [sia.polarity_scores(s)['compound'] for s in relevant_sentences]
            aspect_sentiments[aspect] = np.mean(sentiments)
    
    return aspect_sentiments
```

**Features Used:**
- Review text
- Aspect-level ratings (ground truth for validation)

**Output:**
- Overall sentiment score per hotel
- Aspect-level sentiment scores

---

#### Model 5: Hybrid Recommendation

**Scoring Function:**
```python
def hybrid_score(user_id, hotel_id, user_prefs, weights):
    """
    Combine multiple recommendation signals into unified score.
    
    Args:
        user_id: User identifier
        hotel_id: Hotel identifier
        user_prefs: User preference object
        weights: Dict of model weights
    
    Returns:
        Normalized hybrid score (0-1)
    """
    scores = {}
    
    # 1. Collaborative filtering score (if available)
    if has_cf_score(user_id, hotel_id):
        scores['cf'] = normalize(cf_model.predict(user_id, hotel_id), 1, 5)
    else:
        scores['cf'] = 0.0
        weights['cf'] = 0.0  # Disable if unavailable
    
    # 2. Content similarity score
    scores['content'] = content_similarity(user_prefs, hotel_id)
    
    # 3. Aspect match score
    scores['aspect'] = aspect_match(user_prefs.aspect_weights, hotel_id)
    
    # 4. Sentiment score
    scores['sentiment'] = get_sentiment_score(hotel_id)
    
    # 5. Popularity score (dampening for diversity)
    scores['popularity'] = popularity_score(hotel_id) * 0.5
    
    # Normalize weights
    total_weight = sum(weights.values())
    norm_weights = {k: v/total_weight for k, v in weights.items()}
    
    # Weighted combination
    hybrid = sum(scores[k] * norm_weights[k] for k in scores.keys())
    
    return hybrid

# Default weight configuration (tunable)
DEFAULT_WEIGHTS = {
    "cf": 0.35,
    "content": 0.30,
    "aspect": 0.20,
    "sentiment": 0.10,
    "popularity": 0.05
}
```

**Features Used:** All model outputs

**Ranking:**
1. Generate hybrid scores for candidate hotels
2. Apply hard constraint filters (budget, min_rating)
3. Exclude already-seen hotels (if applicable)
4. Rank by hybrid score
5. Return Top-N with explanations

---

### 4.2 Cold-Start Strategy

**New User (No Interaction History):**
```python
def recommend_new_user(user_prefs, n=10):
    candidates = filter_hotels(
        destination=user_prefs.destination,
        min_rating=user_prefs.min_rating,
        budget_range=(user_prefs.min_budget, user_prefs.max_budget)
    )
    
    # Use content-based + aspect match + popularity
    scores = {}
    for hotel in candidates:
        scores[hotel.id] = (
            0.4 * content_match(user_prefs, hotel) +
            0.4 * aspect_match(user_prefs.aspect_weights, hotel) +
            0.2 * popularity_score(hotel)
        )
    
    return top_n(scores, n)
```

**New Hotel (No Interaction Data):**
```python
def recommend_new_hotel(hotel_id, users):
    # Use hotel metadata + reviews for content-based
    hotel_features = extract_features(hotel_id)
    
    recommendations = []
    for user in users:
        if content_similarity(user.profile, hotel_features) > threshold:
            recommendations.append(user.id)
    
    return recommendations
```

**Sparse User (Few Interactions):**
```python
def recommend_sparse_user(user_id, interaction_count, n=10):
    if interaction_count < 3:
        # Mostly content-based
        return recommend_new_user(get_user_prefs(user_id), n)
    else:
        # Blend CF with content
        cf_scores = cf_model.predict(user_id, candidate_hotels) * 0.5
        content_scores = content_model.score(user_id, candidate_hotels) * 0.5
        hybrid = cf_scores + content_scores
        return top_n(hybrid, n)
```

---

### 4.3 Explainability Design

Each recommendation includes structured explanations:

```python
@dataclass
class RecommendationExplanation:
    hotel_id: str
    hotel_name: str
    score: float
    reasons: List[ExplanationReason]

@dataclass
class ExplanationReason:
    factor: str  # "aspect_match", "similarity", "popularity", "cf_signal"
    weight: float
    description: str
    
# Example generation
def generate_explanation(hotel, user_prefs, scores):
    reasons = []
    
    # Top aspect matches
    aspect_matches = get_aspect_matches(hotel, user_prefs.aspect_weights)
    if aspect_matches:
        top_aspect = max(aspect_matches, key=aspect_matches.get)
        reasons.append(ExplanationReason(
            factor="aspect_match",
            weight=aspect_matches[top_aspect],
            description=f"Excellent {top_aspect} ratings ({hotel.aspects[top_aspect]:.1f}/5.0)"
        ))
    
    # Content similarity
    if scores.get('content', 0) > 0.7:
        reasons.append(ExplanationReason(
            factor="similarity",
            weight=scores['content'],
            description=f"Similar to hotels you've liked"
        ))
    
    # Budget match
    if hotel.price_in_range(user_prefs.min_budget, user_prefs.max_budget):
        reasons.append(ExplanationReason(
            factor="budget_match",
            weight=1.0,
            description=f"Within your budget ({hotel.price_range})"
        ))
    
    return sorted(reasons, key=lambda r: r.weight, reverse=True)[:3]
```

---

## 5. Frontend Design

### 5.1 Design System

**Color Palette:**
```css
:root {
  /* Primary Brand Colors */
  --color-primary-900: #0c2340;      /* Deep navy - headers, key elements */
  --color-primary-700: #1e3a5f;      /* Dark blue - navigation */
  --color-primary-500: #2563eb;      /* Brand blue - CTAs, links */
  --color-primary-300: #60a5fa;      /* Light blue - hover states */
  --color-primary-100: #dbeafe;      /* Pale blue - backgrounds */
  
  /* Accent Colors */
  --color-accent-500: #0891b2;       /* Teal - secondary actions */
  --color-accent-300: #22d3ee;       /* Light teal - highlights */
  
  /* Neutral Colors */
  --color-neutral-950: #0a0a0a;      /* Almost black - text */
  --color-neutral-700: #404040;      /* Dark gray - secondary text */
  --color-neutral-400: #a3a3a3;      /* Medium gray - borders */
  --color-neutral-200: #e5e5e5;      /* Light gray - dividers */
  --color-neutral-50: #fafafa;       /* Off-white - backgrounds */
  
  /* Semantic Colors */
  --color-success: #10b981;
  --color-warning: #f59e0b;
  --color-error: #ef4444;
  --color-info: #3b82f6;
  
  /* Spacing Scale */
  --space-xs: 0.25rem;    /* 4px */
  --space-sm: 0.5rem;     /* 8px */
  --space-md: 1rem;       /* 16px */
  --space-lg: 1.5rem;     /* 24px */
  --space-xl: 2rem;       /* 32px */
  --space-2xl: 3rem;      /* 48px */
  --space-3xl: 4rem;      /* 64px */
  
  /* Typography */
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-display: 'Plus Jakarta Sans', var(--font-sans);
  
  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.07);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
  --shadow-xl: 0 20px 25px rgba(0, 0, 0, 0.15);
  
  /* Border Radius */
  --radius-sm: 0.375rem;  /* 6px */
  --radius-md: 0.5rem;    /* 8px */
  --radius-lg: 0.75rem;   /* 12px */
  --radius-xl: 1rem;      /* 16px */
}
```

**Typography Scale:**
```css
.text-display-xl { font-size: 3.75rem; line-height: 1.1; }  /* 60px */
.text-display-lg { font-size: 3rem; line-height: 1.15; }    /* 48px */
.text-display-md { font-size: 2.25rem; line-height: 1.2; }  /* 36px */
.text-heading-lg { font-size: 1.875rem; line-height: 1.3; } /* 30px */
.text-heading-md { font-size: 1.5rem; line-height: 1.35; }  /* 24px */
.text-heading-sm { font-size: 1.25rem; line-height: 1.4; }  /* 20px */
.text-body-lg { font-size: 1.125rem; line-height: 1.6; }    /* 18px */
.text-body-md { font-size: 1rem; line-height: 1.6; }        /* 16px */
.text-body-sm { font-size: 0.875rem; line-height: 1.5; }    /* 14px */
.text-caption { font-size: 0.75rem; line-height: 1.4; }     /* 12px */
```

### 5.2 Page Layouts

#### Landing Page Structure
```
┌─────────────────────────────────────────────┐
│ Navigation Bar                               │
│ [Logo] [Features] [How It Works] [Sign In]  │
└─────────────────────────────────────────────┘
│                                             │
│ Hero Section                                │
│ "Travel smarter. Stay better."              │
│ [Destination Search Input] → [Discover]     │
│                                             │
├─────────────────────────────────────────────┤
│ Featured Destinations                        │
│ [Card] [Card] [Card] [Card]                 │
├─────────────────────────────────────────────┤
│ How Recommendations Work                     │
│ [Icon + Text] [Icon + Text] [Icon + Text]   │
├─────────────────────────────────────────────┤
│ Feature Highlights                           │
│ • Personalized Discovery                     │
│ • Smart Matching                             │
│ • Explainable Results                        │
├─────────────────────────────────────────────┤
│ Call to Action                               │
│ "Find Your Perfect Stay"                     │
│ [Get Started Button]                         │
├─────────────────────────────────────────────┤
│ Footer                                       │
│ [Links] [Social] [Copyright]                 │
└─────────────────────────────────────────────┘
```

#### Discovery Dashboard
```
┌─────────────────────────────────────────────┐
│ Top Nav: [Logo] [Search] [Saved] [Profile]  │
└─────────────────────────────────────────────┘
│                                             │
│ Search & Filter Bar                          │
│ [Destination] [Budget] [Rating] [Aspects]   │
│                                             │
├─────────────────────────────────────────────┤
│ Left Sidebar (Desktop)    │ Main Content    │
│ • Your Preferences        │                 │
│ • Saved Hotels (count)    │ [Hotel Card 1]  │
│ • Recent Searches         │ • Image         │
│                           │ • Name, Location│
│                           │ • Rating        │
│                           │ • Match Score   │
│                           │ • Why Recommended│
│                           │ • [Save] [View] │
│                           │                 │
│                           │ [Hotel Card 2]  │
│                           │ ...             │
│                           │                 │
│                           │ [Pagination]    │
└───────────────────────────┴─────────────────┘
```

#### Hotel Detail Page
```
┌─────────────────────────────────────────────┐
│ Breadcrumb: Home > Search > [Hotel Name]    │
└─────────────────────────────────────────────┘
│ Hero Image Gallery                           │
│ [Main Image] [Thumbnail] [Thumbnail] ...     │
├─────────────────────────────────────────────┤
│ Hotel Header                                 │
│ [Hotel Name]                 [Save Button]   │
│ [Location] • [Historical Rating]             │
├─────────────────────────────────────────────┤
│ Why Recommended                              │
│ • [Reason 1 with icon]                       │
│ • [Reason 2 with icon]                       │
│ • [Reason 3 with icon]                       │
├─────────────────────────────────────────────┤
│ Aspect Breakdown                             │
│ Cleanliness  ████████░░ 4.5                  │
│ Location     █████████░ 4.7                  │
│ Service      ███████░░░ 4.2                  │
│ ...                                          │
├─────────────────────────────────────────────┤
│ Review Insights                              │
│ "Overall Positive Sentiment (87%)"           │
│ • Most praised: [aspects]                    │
│ • Watch out for: [aspects]                   │
├─────────────────────────────────────────────┤
│ Similar Hotels You Might Like                │
│ [Card] [Card] [Card]                         │
└─────────────────────────────────────────────┘
```

### 5.3 Component Library

**Core Reusable Components:**

1. **HotelCard** - Display hotel in list/grid
2. **AspectRating** - Visual aspect score bar
3. **RecommendationBadge** - Match score indicator
4. **ExplanationList** - Why recommended reasons
5. **SearchBar** - Destination/filter input
6. **FilterPanel** - Multi-criteria filters
7. **LoadingSkeleton** - Loading placeholder
8. **EmptyState** - No results messaging
9. **ErrorBoundary** - Error handling wrapper
10. **ProtectedRoute** - Auth-required pages

**Example HotelCard Component:**
```tsx
interface HotelCardProps {
  hotel: {
    id: string;
    name: string;
    location: string;
    imageUrl: string;
    rating: number;
    reviewCount: number;
    matchScore?: number;
    reasons?: string[];
  };
  onSave?: (hotelId: string) => void;
  isSaved?: boolean;
}

export function HotelCard({ hotel, onSave, isSaved }: HotelCardProps) {
  return (
    <div className="bg-white rounded-xl shadow-md hover:shadow-lg transition-shadow">
      <div className="relative h-48 w-full">
        <Image src={hotel.imageUrl} alt={hotel.name} fill className="object-cover rounded-t-xl" />
        {hotel.matchScore && (
          <div className="absolute top-2 right-2 bg-primary-500 text-white px-3 py-1 rounded-full text-sm font-semibold">
            {Math.round(hotel.matchScore * 100)}% Match
          </div>
        )}
      </div>
      
      <div className="p-4">
        <h3 className="text-heading-sm font-bold text-neutral-950 mb-1">
          {hotel.name}
        </h3>
        <p className="text-body-sm text-neutral-700 mb-2">
          <MapPin className="inline w-4 h-4 mr-1" />
          {hotel.location}
        </p>
        
        <div className="flex items-center gap-2 mb-3">
          <div className="flex items-center">
            <Star className="w-5 h-5 text-yellow-400 fill-current" />
            <span className="ml-1 font-semibold">{hotel.rating.toFixed(1)}</span>
          </div>
          <span className="text-body-sm text-neutral-600">
            ({hotel.reviewCount} reviews)
          </span>
        </div>
        
        {hotel.reasons && hotel.reasons.length > 0 && (
          <div className="mb-3 p-2 bg-blue-50 rounded-lg">
            <p className="text-body-sm text-neutral-700 font-medium mb-1">
              Why recommended:
            </p>
            <ul className="text-body-sm text-neutral-600 space-y-1">
              {hotel.reasons.slice(0, 2).map((reason, idx) => (
                <li key={idx} className="flex items-start">
                  <Check className="w-4 h-4 text-primary-500 mr-1 mt-0.5 flex-shrink-0" />
                  {reason}
                </li>
              ))}
            </ul>
          </div>
        )}
        
        <div className="flex gap-2">
          <Button variant="outline" size="sm" className="flex-1">
            View Details
          </Button>
          <Button
            variant={isSaved ? "secondary" : "ghost"}
            size="sm"
            onClick={() => onSave?.(hotel.id)}
          >
            <Heart className={isSaved ? "fill-current" : ""} />
          </Button>
        </div>
      </div>
    </div>
  );
}
```

### 5.4 Responsive Breakpoints

```css
/* Mobile First Approach */
/* Default: Mobile (< 640px) */

/* Tablet */
@media (min-width: 640px) { /* sm */ }
@media (min-width: 768px) { /* md */ }

/* Desktop */
@media (min-width: 1024px) { /* lg */ }
@media (min-width: 1280px) { /* xl */ }
@media (min-width: 1536px) { /* 2xl */ }
```

**Layout Adaptations:**
- Mobile: Single column, stacked filters, bottom navigation
- Tablet: 2-column grid, sidebar filters, top navigation
- Desktop: 3-column grid, left sidebar, full navigation

---

## 6. API Design

### 6.1 API Structure

**Base URL:** `http://localhost:8000/api/v1`

**Authentication:** JWT Bearer tokens

**Response Format:**
```json
{
  "success": true,
  "data": { ... },
  "message": "Optional message",
  "timestamp": "2026-10-14T10:30:00Z"
}
```

**Error Format:**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input parameters",
    "details": [
      {"field": "min_rating", "issue": "Must be between 1.0 and 5.0"}
    ]
  },
  "timestamp": "2026-10-14T10:30:00Z"
}
```

### 6.2 Endpoint Specifications

#### Health & Status

**GET /health**
```json
Response 200:
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": 3600
}
```

**GET /ready**
```json
Response 200:
{
  "database": "connected",
  "models": "loaded",
  "ready": true
}
```

#### Authentication

**POST /auth/register**
```json
Request:
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}

Response 201:
{
  "success": true,
  "data": {
    "user_id": "uuid",
    "email": "user@example.com",
    "created_at": "2026-10-14T10:30:00Z"
  }
}
```

**POST /auth/login**
```json
Request:
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}

Response 200:
{
  "success": true,
  "data": {
    "access_token": "jwt_token_here",
    "token_type": "bearer",
    "expires_in": 3600
  }
}
```

#### Recommendations

**POST /recommendations/generate**
```json
Request:
Headers: Authorization: Bearer <token>
{
  "user_id": "uuid",
  "destination": "New York",
  "filters": {
    "min_rating": 4.0,
    "max_budget": 300,
    "aspect_priorities": {
      "cleanliness": 1.5,
      "location": 1.2,
      "service": 1.0
    }
  },
  "exclude_seen": true,
  "top_n": 10
}

Response 200:
{
  "success": true,
  "data": {
    "recommendations": [
      {
        "hotel_id": "hotel_123",
        "hotel_name": "Grand Plaza",
        "location": "Manhattan, New York",
        "match_score": 0.92,
        "rating": 4.6,
        "review_count": 1250,
        "aspects": {
          "cleanliness": 4.8,
          "location": 4.9,
          "service": 4.5
        },
        "explanations": [
          {
            "factor": "aspect_match",
            "description": "Excellent cleanliness ratings (4.8/5.0)",
            "weight": 0.35
          },
          {
            "factor": "location",
            "description": "Prime Manhattan location",
            "weight": 0.30
          }
        ],
        "image_url": "/images/hotel_123.jpg"
      }
    ],
    "total_candidates": 150,
    "filtered_count": 45,
    "model_version": "hybrid_v1.2"
  }
}
```

**GET /recommendations/explain/{hotel_id}**
```json
Request:
Headers: Authorization: Bearer <token>
Params: user_id=uuid

Response 200:
{
  "success": true,
  "data": {
    "hotel_id": "hotel_123",
    "model_scores": {
      "collaborative": 0.85,
      "content": 0.92,
      "aspect": 0.88,
      "sentiment": 0.91,
      "popularity": 0.75
    },
    "hybrid_score": 0.87,
    "explanations": [...],
    "similar_hotels": ["hotel_456", "hotel_789"]
  }
}
```

#### Hotels

**GET /hotels/search**
```json
Request:
Params:
  destination=Paris
  min_rating=4.0
  max_budget=250
  page=1
  per_page=20

Response 200:
{
  "success": true,
  "data": {
    "hotels": [...],
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 156,
      "pages": 8
    }
  }
}
```

**GET /hotels/{hotel_id}**
```json
Response 200:
{
  "success": true,
  "data": {
    "hotel_id": "hotel_123",
    "name": "Grand Plaza",
    "location": "Manhattan, New York",
    "rating": 4.6,
    "review_count": 1250,
    "aspects": {
      "cleanliness": 4.8,
      "location": 4.9,
      "rooms": 4.5,
      "service": 4.5,
      "value": 4.2,
      "sleep_quality": 4.6
    },
    "sentiment_summary": {
      "overall": 0.87,
      "positive_percentage": 89,
      "top_praised": ["location", "cleanliness", "staff"],
      "areas_for_improvement": ["breakfast", "parking"]
    },
    "metadata": {
      "destination": "New York",
      "price_range": "$$",
      "last_updated": "2026-10-01"
    }
  }
}
```

#### User Preferences

**GET /users/{user_id}/preferences**
**PUT /users/{user_id}/preferences**
**POST /users/{user_id}/saved-hotels**
**DELETE /users/{user_id}/saved-hotels/{hotel_id}**
**GET /users/{user_id}/saved-hotels**

#### Analytics

**GET /analytics/dataset-stats**
```json
Response 200:
{
  "success": true,
  "data": {
    "total_records": 201295,
    "unique_users": 35610,
    "unique_hotels": 1493,
    "date_range": {
      "earliest": "2002-01-01",
      "latest": "2015-12-31"
    },
    "rating_distribution": {
      "1": 2340,
      "2": 5670,
      "3": 15890,
      "4": 67200,
      "5": 110195
    },
    "sparsity": 0.996,
    "missing_values": {
      "review_text": 340,
      "cleanliness": 12500
    }
  }
}
```

**GET /analytics/model-performance**
```json
Response 200:
{
  "success": true,
  "data": {
    "experiments": [
      {
        "experiment_id": "exp_001",
        "model_type": "hybrid",
        "version": "v1.2",
        "training_date": "2026-10-10",
        "metrics": {
          "precision_at_10": 0.67,
          "recall_at_10": 0.42,
          "ndcg_at_10": 0.71,
          "map": 0.58
        },
        "baseline_comparison": {
          "baseline_type": "popularity",
          "improvement": {
            "precision": "+15.2%",
            "ndcg": "+23.4%"
          }
        }
      }
    ]
  }
}
```

---

## 7. Security Architecture

### 7.1 Authentication Flow

```
1. User submits credentials → Frontend
2. Frontend → POST /api/v1/auth/login → Backend
3. Backend validates credentials (bcrypt comparison)
4. Backend generates JWT with expiration
5. Backend → JWT → Frontend
6. Frontend stores token (httpOnly cookie or secure storage)
7. Subsequent requests include: Authorization: Bearer <token>
8. Backend validates token on protected routes
```

### 7.2 Security Measures

**Password Security:**
- Minimum 8 characters
- bcrypt hashing (cost factor 12)
- No plaintext storage
- Rate limiting on login attempts

**Token Security:**
- JWT with HS256 or RS256
- Short expiration (1 hour)
- Refresh token strategy
- httpOnly, secure, sameSite cookies

**Input Validation:**
- Pydantic schemas for all inputs
- SQL injection prevention (parameterized queries)
- XSS prevention (sanitized outputs)
- CSRF tokens for state-changing operations

**API Security:**
- Rate limiting (100 req/min per user)
- CORS configuration
- HTTPS only (production)
- Secure headers (HSTS, CSP)

**Data Privacy:**
- No logging of passwords or tokens
- Minimal PII collection
- User data isolation (row-level security)
- GDPR considerations (data export, deletion)

---

## 8. Big Data Processing Architecture

### 8.1 Spark Job Structure

```
ml/
├── pipelines/
│   ├── ingestion.py          # Load and validate raw data
│   ├── cleaning.py            # Deduplication, missing values
│   ├── feature_engineering.py # Create derived features
│   └── model_training.py      # Train and evaluate models
├── models/
│   ├── popularity.py
│   ├── collaborative.py       # ALS implementation
│   ├── content_based.py
│   ├── sentiment.py
│   └── hybrid.py
├── evaluation/
│   ├── metrics.py             # Precision, Recall, NDCG
│   └── benchmarks.py          # Performance measurements
└── utils/
    ├── spark_setup.py
    └── data_utils.py
```

### 8.2 Processing Pipeline

**Job 1: Data Ingestion**
```python
# ml/pipelines/ingestion.py
from pyspark.sql import SparkSession
from pyspark.sql.types import *

def ingest_raw_data(spark, input_path, output_path):
    """
    Load raw CSV and validate schema.
    """
    # Define expected schema
    schema = StructType([
        StructField("user_id", StringType(), False),
        StructField("hotel_id", StringType(), False),
        StructField("rating", FloatType(), False),
        StructField("review_text", StringType(), True),
        # ... more fields
    ])
    
    # Load with validation
    df = spark.read.csv(input_path, header=True, schema=schema)
    
    # Basic validation
    assert df.count() > 0, "Empty dataset"
    assert df.select("user_id").distinct().count() > 0, "No users"
    
    # Save as Parquet
    df.write.mode("overwrite").parquet(output_path)
    
    return df
```

**Job 2: Feature Engineering**
```python
# ml/pipelines/feature_engineering.py
from pyspark.sql import functions as F
from pyspark.sql.window import Window

def create_hotel_features(spark, interactions_path, reviews_path, output_path):
    """
    Aggregate hotel-level features.
    """
    interactions = spark.read.parquet(interactions_path)
    reviews = spark.read.parquet(reviews_path)
    
    # Aggregate statistics
    hotel_stats = interactions.groupBy("hotel_id").agg(
        F.avg("rating").alias("avg_rating"),
        F.count("*").alias("review_count"),
        F.avg("cleanliness_rating").alias("avg_cleanliness"),
        F.avg("location_rating").alias("avg_location"),
        # ... more aspects
    )
    
    # Calculate Bayesian average
    global_mean = interactions.agg(F.avg("rating")).collect()[0][0]
    min_reviews = 10
    
    hotel_stats = hotel_stats.withColumn(
        "bayesian_avg",
        (F.col("avg_rating") * F.col("review_count") + global_mean * min_reviews) /
        (F.col("review_count") + min_reviews)
    )
    
    # Join with review text for NLP
    hotel_features = hotel_stats.join(
        reviews.groupBy("hotel_id").agg(
            F.collect_list("review_text").alias("all_reviews")
        ),
        on="hotel_id",
        how="left"
    )
    
    hotel_features.write.mode("overwrite").parquet(output_path)
    
    return hotel_features
```

**Job 3: Model Training (ALS)**
```python
# ml/models/collaborative.py
from pyspark.ml.recommendation import ALS
from pyspark.ml.evaluation import RegressionEvaluator

def train_als_model(spark, interactions_path, model_output_path):
    """
    Train collaborative filtering model.
    """
    data = spark.read.parquet(interactions_path)
    
    # Encode IDs to integers
    from pyspark.ml.feature import StringIndexer
    
    user_indexer = StringIndexer(inputCol="user_id", outputCol="user_id_encoded")
    hotel_indexer = StringIndexer(inputCol="hotel_id", outputCol="hotel_id_encoded")
    
    data = user_indexer.fit(data).transform(data)
    data = hotel_indexer.fit(data).transform(data)
    
    # Split data
    train, test = data.randomSplit([0.8, 0.2], seed=42)
    
    # Train ALS
    als = ALS(
        maxIter=10,
        regParam=0.1,
        userCol="user_id_encoded",
        itemCol="hotel_id_encoded",
        ratingCol="rating",
        coldStartStrategy="drop"
    )
    
    model = als.fit(train)
    
    # Evaluate
    predictions = model.transform(test)
    evaluator = RegressionEvaluator(
        metricName="rmse",
        labelCol="rating",
        predictionCol="prediction"
    )
    rmse = evaluator.evaluate(predictions)
    
    print(f"Test RMSE: {rmse}")
    
    # Save model
    model.write().overwrite().save(model_output_path)
    
    return model
```

### 8.3 Benchmarking Strategy

**Benchmark Script:**
```python
# ml/evaluation/benchmarks.py
import time
import psutil
from pyspark.sql import SparkSession

def benchmark_spark_vs_pandas(dataset_sizes=[1000, 10000, 100000]):
    """
    Compare Spark vs Pandas processing times.
    """
    results = []
    
    for size in dataset_sizes:
        # Pandas baseline
        start = time.time()
        df_pandas = pd.read_csv(f"data/sample_{size}.csv")
        df_pandas = df_pandas.dropna()
        df_pandas["bayesian_avg"] = calculate_bayesian(df_pandas)
        pandas_time = time.time() - start
        
        # Spark
        spark = SparkSession.builder.appName("benchmark").getOrCreate()
        start = time.time()
        df_spark = spark.read.csv(f"data/sample_{size}.csv", header=True)
        df_spark = df_spark.dropna()
        df_spark = df_spark.withColumn("bayesian_avg", ...)
        df_spark.write.parquet(f"output_{size}.parquet")
        spark_time = time.time() - start
        
        results.append({
            "size": size,
            "pandas_time": pandas_time,
            "spark_time": spark_time,
            "speedup": pandas_time / spark_time
        })
    
    return pd.DataFrame(results)
```

---

## 9. Deployment Architecture

### 9.1 Docker Compose Setup

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: tripsense
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./apps/api
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/tripsense
      SECRET_KEY: ${SECRET_KEY}
      MODEL_PATH: /app/artifacts
    volumes:
      - ./artifacts:/app/artifacts:ro
      - ./data/processed:/app/data:ro
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
    command: uvicorn main:app --host 0.0.0.0 --port 8000

  frontend:
    build:
      context: ./apps/web
      dockerfile: Dockerfile
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
    ports:
      - "3000:3000"
    depends_on:
      - backend

volumes:
  postgres_data:
```

### 9.2 Environment Configuration

**.env.example**
```bash
# Database
DB_USER=tripsense_user
DB_PASSWORD=CHANGEME
DB_HOST=localhost
DB_PORT=5432
DB_NAME=tripsense

# API
SECRET_KEY=GENERATE_SECURE_KEY_HERE
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Paths
RAW_DATA_PATH=./data/raw/tripadvisor.csv
PROCESSED_DATA_PATH=./data/processed
MODEL_ARTIFACTS_PATH=./artifacts

# Spark
SPARK_MASTER=local[*]
SPARK_DRIVER_MEMORY=4g
SPARK_EXECUTOR_MEMORY=4g

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 10. Testing Strategy

### 10.1 Testing Pyramid

```
        /\
       /E2E\       (Few) - Critical user journeys
      /──────\
     /Integr.\    (Some) - API contracts, DB interactions
    /──────────\
   /   Unit     \  (Many) - Business logic, utils, components
  /──────────────\
```

### 10.2 Test Categories

**Frontend Tests:**
- Unit: Component rendering, utility functions
- Integration: Form submissions, API mocking
- E2E: User registration → preference setup → hotel discovery

**Backend Tests:**
- Unit: Recommendation scoring, filters, validators
- Integration: Database queries, model loading
- API: Request/response validation, error handling

**ML Tests:**
- Unit: Feature extraction, similarity calculations
- Integration: Model training pipeline
- Evaluation: Metrics calculation, baseline comparisons

---

## 11. Risks and Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Dataset schema mismatch | High | Medium | Early validation, flexible parsers |
| Sparse interaction data | High | Medium | Emphasize content-based, document limits |
| Spark setup complexity | Medium | Medium | Docker support, clear documentation |
| Model performance below baseline | Medium | Low | Multiple baselines, honest reporting |
| Frontend-backend integration issues | Medium | Low | Clear API contracts, integration tests |
| Cold-start recommendations poor | Medium | Medium | Fallback strategies, user feedback |

---

## 12. Next Steps

This design document is ready for review. Upon approval, proceed to:

1. **Task Breakdown** - Create detailed tasks.md
2. **Prototype Setup** - Initialize project structure
3. **Data Validation** - Download and inspect dataset
4. **MVP Implementation** - Begin Phase 1 development

**Document Status:** Draft for Review  
**Last Updated:** October 14, 2026  
**Reviewers:** [Pending]

---

**END OF DESIGN SPECIFICATION**

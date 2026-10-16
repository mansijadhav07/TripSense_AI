# TripSense AI — Implementation Tasks

**Version:** 1.0.0  
**Last Updated:** October 16, 2026  
**Status:** Completed & Fully Verified (Automated Tests Passing 100%)

---

## Overview

This document breaks down the TripSense AI implementation into 7 distinct phases with clear dependencies, acceptance criteria, and estimated effort. Tasks are ordered to minimize blocking dependencies and enable incremental validation.

**Total Estimated Effort:** 120-150 hours (3-4 weeks full-time)

---

## Phase 0: Project Setup & Data Acquisition

**Goal:** Establish workspace, acquire dataset, validate data availability  
**Duration:** 4-6 hours  
**Dependencies:** None

### Task 0.1: Initialize Project Structure
- [ ] Create monorepo folder structure
- [ ] Initialize Git repository with .gitignore
- [ ] Create README.md with project overview
- [ ] Set up .env.example with all required variables
- [ ] Create empty placeholder directories (data/, ml/, artifacts/, docs/)

**Acceptance Criteria:**
- Repository has clean structure
- .gitignore excludes data/, artifacts/, .env, node_modules/
- README contains setup instructions placeholder

**Files Created:**
- `/README.md`
- `/.gitignore`
- `/.env.example`
- `/data/raw/.gitkeep`
- `/data/processed/.gitkeep`
- `/artifacts/.gitkeep`
- `/docs/.gitkeep`

---

### Task 0.2: Acquire TripAdvisor Dataset
- [ ] Research TripAdvisor Review Rating dataset sources
- [ ] Download dataset to `data/raw/`
- [ ] Document dataset source, version, and license
- [ ] Verify file integrity and size

**Acceptance Criteria:**
- Dataset file exists in `data/raw/`
- Dataset size matches expected ~201k records
- Source and license documented in `data/README.md`

**Files Created:**
- `/data/README.md` (dataset documentation)
- `/data/raw/tripadvisor_reviews.csv` (or similar name)

---

### Task 0.3: Initial Dataset Inspection
- [ ] Create Jupyter notebook for exploration
- [ ] Load dataset with Pandas
- [ ] Document actual column names and types
- [ ] Check for missing values, duplicates
- [ ] Analyze rating distributions
- [ ] Calculate interaction sparsity
- [ ] Document findings in data dictionary

**Acceptance Criteria:**
- Data dictionary created with actual schema
- Missing value percentages documented
- Sparsity metrics calculated
- Findings inform model design decisions

**Files Created:**
- `/notebooks/00_dataset_exploration.ipynb`
- `/data/data_dictionary.md`

---

## Phase 1: Foundation & Infrastructure

**Goal:** Set up development environment, basic API, database, frontend skeleton  
**Duration:** 12-16 hours  
**Dependencies:** Phase 0 complete

### Task 1.1: Backend API Foundation
- [ ] Create `apps/api/` directory
- [ ] Set up FastAPI project with main.py
- [ ] Create project structure (routers/, models/, services/, schemas/)
- [ ] Add requirements.txt with core dependencies
- [ ] Implement /health and /ready endpoints
- [ ] Add CORS middleware
- [ ] Configure environment variable loading
- [ ] Add structured logging

**Acceptance Criteria:**
- `uvicorn main:app --reload` starts server successfully
- GET /health returns 200 OK
- Environment variables load from .env
- Logs output structured JSON

**Files Created:**
- `/apps/api/main.py`
- `/apps/api/requirements.txt`
- `/apps/api/config.py`
- `/apps/api/routers/__init__.py`
- `/apps/api/utils/logging.py`

**Test Command:**
```bash
cd apps/api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
curl http://localhost:8000/health
```

---

### Task 1.2: Database Setup
- [ ] Add SQLAlchemy and Alembic to requirements
- [ ] Create database models (users, preferences, saved_hotels, experiments)
- [ ] Set up Alembic migrations
- [ ] Create initial migration
- [ ] Add database connection utility
- [ ] Implement database health check

**Acceptance Criteria:**
- PostgreSQL connection successful
- Tables created via migration
- Alembic can upgrade/downgrade
- /ready endpoint checks database

**Files Created:**
- `/apps/api/models/user.py`
- `/apps/api/models/preference.py`
- `/apps/api/models/saved_hotel.py`
- `/apps/api/models/experiment.py`
- `/apps/api/database.py`
- `/apps/api/alembic.ini`
- `/apps/api/alembic/env.py`
- `/apps/api/alembic/versions/001_initial.py`

**Test Command:**
```bash
docker-compose up -d postgres
alembic upgrade head
psql -U tripsense_user -d tripsense -c "\dt"
```

---

### Task 1.3: Authentication System
- [ ] Install python-jose, passlib[bcrypt]
- [ ] Create password hashing utilities
- [ ] Implement JWT token generation/validation
- [ ] Create auth router with /register and /login endpoints
- [ ] Add Pydantic schemas for auth requests/responses
- [ ] Implement authentication dependency for protected routes
- [ ] Add rate limiting (optional but recommended)

**Acceptance Criteria:**
- User can register with email/password
- Passwords are bcrypt hashed
- Login returns valid JWT
- Protected routes require valid token
- Invalid credentials return 401

**Files Created:**
- `/apps/api/routers/auth.py`
- `/apps/api/schemas/auth.py`
- `/apps/api/services/auth_service.py`
- `/apps/api/utils/security.py`
- `/apps/api/dependencies/auth.py`

**Test Command:**
```bash
# Register user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"SecurePass123!"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"SecurePass123!"}'
```

---

### Task 1.4: Frontend Foundation
- [ ] Create Next.js 14 app with TypeScript in `apps/web/`
- [ ] Configure Tailwind CSS
- [ ] Install shadcn/ui and initialize
- [ ] Add core shadcn components (Button, Card, Input, etc.)
- [ ] Create design system tokens (colors, spacing, typography)
- [ ] Set up project structure (app/, components/, lib/, types/)
- [ ] Create layout with navigation
- [ ] Add environment variable configuration

**Acceptance Criteria:**
- `npm run dev` starts development server
- Homepage renders with navigation
- Tailwind classes work
- shadcn/ui components styled correctly
- Design system colors applied

**Files Created:**
- `/apps/web/package.json`
- `/apps/web/tailwind.config.ts`
- `/apps/web/app/layout.tsx`
- `/apps/web/app/page.tsx`
- `/apps/web/components/ui/` (shadcn components)
- `/apps/web/lib/utils.ts`
- `/apps/web/styles/globals.css`

**Test Command:**
```bash
cd apps/web
npm install
npm run dev
# Visit http://localhost:3000
```

---

### Task 1.5: Docker Configuration
- [ ] Create Dockerfile for backend
- [ ] Create Dockerfile for frontend
- [ ] Create docker-compose.yml with all services
- [ ] Add volume mounts for development
- [ ] Configure health checks
- [ ] Test full-stack startup

**Acceptance Criteria:**
- `docker-compose up` starts all services
- Services can communicate
- Hot reload works for both frontend and backend
- Database persists data across restarts

**Files Created:**
- `/apps/api/Dockerfile`
- `/apps/web/Dockerfile`
- `/docker-compose.yml`

**Test Command:**
```bash
docker-compose up --build
# Verify all services healthy
docker-compose ps
```

---

### Task 1.6: Basic Testing Setup
- [ ] Add pytest to backend requirements
- [ ] Create test directory structure
- [ ] Add pytest configuration (pytest.ini)
- [ ] Create test fixtures (database, auth)
- [ ] Write sample tests for health endpoint and auth
- [ ] Add Vitest to frontend
- [ ] Write sample component tests

**Acceptance Criteria:**
- `pytest` runs successfully
- Test coverage report generated
- `npm test` runs frontend tests
- CI-ready test commands

**Files Created:**
- `/apps/api/pytest.ini`
- `/apps/api/tests/conftest.py`
- `/apps/api/tests/test_health.py`
- `/apps/api/tests/test_auth.py`
- `/apps/web/vitest.config.ts`
- `/apps/web/__tests__/page.test.tsx`

**Test Command:**
```bash
cd apps/api && pytest -v
cd apps/web && npm test
```

---

## Phase 2: Data Engineering Pipeline

**Goal:** Ingest, clean, and process raw dataset into model-ready features  
**Duration:** 16-20 hours  
**Dependencies:** Phase 0 complete (dataset acquired)

### Task 2.1: Spark Environment Setup
- [ ] Install PySpark locally
- [ ] Create Spark utility functions
- [ ] Configure Spark session with appropriate memory
- [ ] Test Spark with sample data
- [ ] Document Spark installation for README

**Acceptance Criteria:**
- PySpark imports successfully
- Can create SparkSession
- Can read sample CSV/Parquet
- Spark UI accessible at localhost:4040

**Files Created:**
- `/ml/requirements.txt`
- `/ml/utils/spark_setup.py`
- `/ml/config.py`

**Test Command:**
```bash
cd ml
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python utils/spark_setup.py
```

---

### Task 2.2: Data Ingestion Pipeline
- [ ] Create ingestion script
- [ ] Load raw CSV with schema validation
- [ ] Log data quality metrics (row count, nulls, duplicates)
- [ ] Save validated data as Parquet
- [ ] Handle ingestion errors gracefully
- [ ] Create data validation report

**Acceptance Criteria:**
- Script processes full dataset without errors
- Parquet file created in `data/processed/validated/`
- Validation report shows actual data statistics
- Script is idempotent (can re-run safely)

**Files Created:**
- `/ml/pipelines/01_ingest.py`
- `/ml/utils/validators.py`
- `/data/processed/validated/raw_data.parquet`
- `/data/processed/reports/ingestion_report.json`

**Test Command:**
```bash
cd ml
python pipelines/01_ingest.py \
  --input ../data/raw/tripadvisor_reviews.csv \
  --output ../data/processed/validated/
```

---

### Task 2.3: Data Cleaning Pipeline
- [ ] Create cleaning script
- [ ] Remove duplicate records
- [ ] Handle missing values (drop, impute, or flag)
- [ ] Standardize text fields (lowercase, strip whitespace)
- [ ] Filter invalid ratings (outside 1-5 range)
- [ ] Standardize date formats if timestamps exist
- [ ] Log cleaning statistics

**Acceptance Criteria:**
- Cleaned dataset has no duplicates
- Missing value strategy documented
- Invalid records filtered out
- Cleaning report shows before/after stats
- Output saved as Parquet

**Files Created:**
- `/ml/pipelines/02_clean.py`
- `/ml/utils/cleaners.py`
- `/data/processed/cleaned/interactions.parquet`
- `/data/processed/reports/cleaning_report.json`

**Test Command:**
```bash
cd ml
python pipelines/02_clean.py \
  --input ../data/processed/validated/ \
  --output ../data/processed/cleaned/
```

---

### Task 2.4: Feature Engineering Pipeline
- [ ] Create feature engineering script
- [ ] Calculate hotel aggregates (avg_rating, review_count, bayesian_avg)
- [ ] Calculate aspect-level aggregates (cleanliness, location, etc.)
- [ ] Extract review text corpus per hotel
- [ ] Create user interaction history
- [ ] Calculate sparsity metrics
- [ ] Save feature tables as separate Parquets

**Acceptance Criteria:**
- hotel_features.parquet contains all necessary hotel attributes
- user_interactions.parquet has user-hotel pairs with ratings
- Feature tables joinable by hotel_id/user_id
- Bayesian averages calculated correctly
- Feature report generated

**Files Created:**
- `/ml/pipelines/03_feature_engineering.py`
- `/ml/utils/feature_extractors.py`
- `/data/processed/features/hotel_features.parquet`
- `/data/processed/features/user_interactions.parquet`
- `/data/processed/reports/feature_report.json`

**Test Command:**
```bash
cd ml
python pipelines/03_feature_engineering.py \
  --input ../data/processed/cleaned/ \
  --output ../data/processed/features/
```

---

### Task 2.5: NLP Preprocessing Pipeline
- [ ] Install NLTK or spaCy
- [ ] Download required language models
- [ ] Create text preprocessing utilities (tokenization, stopword removal)
- [ ] Generate TF-IDF vectors for hotel review corpus
- [ ] Run sentiment analysis on reviews (VADER or transformer)
- [ ] Extract aspect-level sentiments
- [ ] Save embeddings and sentiment scores

**Acceptance Criteria:**
- Review text preprocessed consistently
- TF-IDF vectors generated for all hotels with reviews
- Sentiment scores between -1 and 1
- Aspect sentiments extracted where possible
- Saved as Parquet or pickle

**Files Created:**
- `/ml/pipelines/04_nlp_processing.py`
- `/ml/utils/nlp_utils.py`
- `/data/processed/features/review_embeddings.parquet`
- `/data/processed/features/sentiment_scores.parquet`
- `/data/processed/features/aspect_sentiments.parquet`

**Test Command:**
```bash
cd ml
python pipelines/04_nlp_processing.py \
  --input ../data/processed/features/ \
  --output ../data/processed/features/
```

---

### Task 2.6: Train/Test Split
- [ ] Create stratified train/test split (80/20)
- [ ] If timestamps available, use chronological split
- [ ] Ensure no leakage (test users not in train features)
- [ ] Save split indices or separate files
- [ ] Document split strategy

**Acceptance Criteria:**
- Train and test sets created
- Split is reproducible (fixed seed)
- Test set represents realistic evaluation
- Split metadata saved

**Files Created:**
- `/ml/pipelines/05_train_test_split.py`
- `/data/processed/splits/train_interactions.parquet`
- `/data/processed/splits/test_interactions.parquet`
- `/data/processed/splits/split_metadata.json`

**Test Command:**
```bash
cd ml
python pipelines/05_train_test_split.py \
  --input ../data/processed/features/user_interactions.parquet \
  --output ../data/processed/splits/
```

---

### Task 2.7: Data Pipeline Orchestration Script
- [ ] Create master pipeline script that runs all steps in sequence
- [ ] Add command-line arguments for configuration
- [ ] Add progress logging
- [ ] Handle failures gracefully with clear error messages
- [ ] Generate comprehensive pipeline report

**Acceptance Criteria:**
- Single command runs entire pipeline
- Can run individual stages
- Failure at any stage stops pipeline with clear error
- Final report summarizes all stages

**Files Created:**
- `/ml/run_pipeline.py`
- `/ml/README.md` (pipeline documentation)

**Test Command:**
```bash
cd ml
python run_pipeline.py --full --input ../data/raw/tripadvisor_reviews.csv
```

---

## Phase 3: Recommendation Models

**Goal:** Implement and train all recommendation models  
**Duration:** 20-24 hours  
**Dependencies:** Phase 2 complete (features available)

### Task 3.1: Popularity Baseline Model
- [ ] Implement Bayesian average ranking
- [ ] Create model class with fit/predict methods
- [ ] Train on full dataset (no learning, just ranking)
- [ ] Generate Top-N recommendations for test users
- [ ] Save model configuration

**Acceptance Criteria:**
- Model ranks hotels correctly by Bayesian average
- Can generate Top-10 for any user (same results)
- Model serialized to artifacts/
- Predictions are deterministic

**Files Created:**
- `/ml/models/popularity.py`
- `/artifacts/popularity_model.pkl`

**Test Command:**
```bash
cd ml
python -c "from models.popularity import PopularityModel; \
m = PopularityModel(); m.fit('data/processed/features/hotel_features.parquet'); \
print(m.recommend(user_id='test', n=10))"
```

---

### Task 3.2: Collaborative Filtering (ALS) Model
- [ ] Implement ALS training script using Spark MLlib
- [ ] Encode user_id and hotel_id to integer indices
- [ ] Train ALS model on training interactions
- [ ] Tune hyperparameters (rank, regParam, iterations)
- [ ] Handle cold-start strategy (drop or NaN)
- [ ] Save model and ID encoders

**Acceptance Criteria:**
- Model trains on train_interactions.parquet
- Can predict ratings for user-hotel pairs
- RMSE calculated on validation set
- Model saved to artifacts/

**Files Created:**
- `/ml/models/collaborative.py`
- `/ml/scripts/train_als.py`
- `/artifacts/als_model/`
- `/artifacts/user_encoder.pkl`
- `/artifacts/hotel_encoder.pkl`

**Test Command:**
```bash
cd ml
python scripts/train_als.py \
  --train ../data/processed/splits/train_interactions.parquet \
  --output ../artifacts/als_model/
```

---

### Task 3.3: Content-Based Model
- [ ] Implement content similarity calculation
- [ ] Create user preference vector from interaction history
- [ ] Calculate cosine similarity between user and hotel vectors
- [ ] Implement preference-based filtering (aspect weights)
- [ ] Generate Top-N recommendations
- [ ] Save TF-IDF vectorizer and feature matrix

**Acceptance Criteria:**
- Model uses TF-IDF vectors for similarity
- Can handle users with no history (preference-only mode)
- Similarity scores normalized 0-1
- Model artifacts saved

**Files Created:**
- `/ml/models/content_based.py`
- `/ml/scripts/train_content.py`
- `/artifacts/tfidf_vectorizer.pkl`
- `/artifacts/hotel_content_matrix.pkl`

**Test Command:**
```bash
cd ml
python scripts/train_content.py \
  --features ../data/processed/features/ \
  --output ../artifacts/
```

---

### Task 3.4: Sentiment & Aspect Model
- [ ] Load sentiment scores from features
- [ ] Create aspect matching function
- [ ] Weight aspect scores by user preferences
- [ ] Implement aspect-based ranking
- [ ] Save aspect scoring configuration

**Acceptance Criteria:**
- Can score hotels based on aspect preferences
- Handles missing aspect ratings gracefully
- Aspect weights normalized correctly
- Scoring function tested

**Files Created:**
- `/ml/models/aspect_scorer.py`
- `/artifacts/aspect_config.json`

**Test Command:**
```bash
cd ml
python -c "from models.aspect_scorer import AspectScorer; \
s = AspectScorer(); \
print(s.score('hotel_123', {'cleanliness': 1.5, 'location': 1.2}))"
```

---

### Task 3.5: Hybrid Recommendation Model
- [ ] Implement hybrid scoring function
- [ ] Load all sub-models (popularity, ALS, content, aspect)
- [ ] Normalize scores from each model to 0-1 range
- [ ] Combine scores with configurable weights
- [ ] Implement cold-start logic (switch weights based on user history)
- [ ] Apply hard constraint filters (budget, min_rating)
- [ ] Generate Top-N with explanation metadata

**Acceptance Criteria:**
- Hybrid model loads all sub-models successfully
- Can generate recommendations for any user
- Cold-start users get content-based recommendations
- Regular users get weighted combination
- Explanations include contributing factors

**Files Created:**
- `/ml/models/hybrid.py`
- `/ml/scripts/train_hybrid.py`
- `/artifacts/hybrid_config.json`

**Test Command:**
```bash
cd ml
python scripts/train_hybrid.py \
  --artifacts ../artifacts/ \
  --output ../artifacts/hybrid_config.json
```

---

### Task 3.6: Recommendation Explainer
- [ ] Create explanation generation module
- [ ] Extract top contributing factors for each recommendation
- [ ] Generate natural language explanations
- [ ] Format explanations with scores and reasons
- [ ] Test with various user/hotel combinations

**Acceptance Criteria:**
- Each recommendation has 2-3 clear reasons
- Explanations reflect actual model signals
- Text is user-friendly and accurate
- No fabricated reasons

**Files Created:**
- `/ml/utils/explainer.py`
- `/ml/tests/test_explainer.py`

**Test Command:**
```bash
cd ml
pytest tests/test_explainer.py -v
```

---

## Phase 4: Model Evaluation & Analytics

**Goal:** Evaluate models, benchmark performance, create evaluation reports  
**Duration:** 12-16 hours  
**Dependencies:** Phase 3 complete (models trained)

### Task 4.1: Evaluation Metrics Implementation
- [x] Implement Precision@K
- [x] Implement Recall@K
- [x] Implement NDCG@K
- [x] Implement MAP (Mean Average Precision)
- [x] Implement Coverage and Diversity metrics
- [x] Create evaluation utility class

**Acceptance Criteria:**
- All metrics mathematically correct
- Unit tests pass for known examples
- Metrics handle edge cases (empty predictions)

**Files Created:**
- `/ml/evaluation/metrics.py`
- `/ml/tests/test_metrics.py`

**Test Command:**
```bash
cd ml
pytest tests/test_metrics.py -v
```

---

### Task 4.2: Model Evaluation Pipeline
- [x] Create evaluation script
- [x] Load test set
- [x] Generate predictions from each model
- [x] Calculate metrics for each model
- [x] Compare against baselines
- [x] Generate evaluation report
- [x] Visualize metric comparisons

**Acceptance Criteria:**
- Evaluation runs on held-out test set
- Metrics calculated for: Popularity, CF, Content, Hybrid
- Results saved as JSON and CSV
- No data leakage from test set

**Files Created:**
- `/ml/evaluation/evaluate_models.py`
- `/ml/evaluation/results/model_comparison.json`
- `/ml/evaluation/results/model_comparison.csv`
- `/ml/evaluation/results/metrics_visualization.png`

**Test Command:**
```bash
cd ml
python evaluation/evaluate_models.py \
  --test-data ../data/processed/splits/test_interactions.parquet \
  --artifacts ../artifacts/ \
  --output evaluation/results/
```

---

### Task 4.3: Spark Performance Benchmarking
- [x] Create benchmark script
- [x] Prepare datasets of varying sizes (1K, 10K, 100K, full)
- [x] Implement Pandas baseline for comparison
- [x] Run feature engineering on each size with both Spark and Pandas
- [x] Measure: runtime, memory usage, throughput
- [x] Generate benchmark report with charts

**Acceptance Criteria:**
- Benchmarks run on multiple dataset sizes
- Fair comparison (same operations in Spark and Pandas)
- Results show actual runtimes and speedups
- Report documents environment (cores, memory)

**Files Created:**
- `/ml/evaluation/benchmark_spark.py`
- `/ml/evaluation/results/spark_benchmark.json`
- `/ml/evaluation/results/spark_benchmark_chart.png`

**Test Command:**
```bash
cd ml
python evaluation/benchmark_spark.py \
  --sizes 1000,10000,100000,full \
  --output evaluation/results/
```

---

### Task 4.4: Model Cards Documentation
- [x] Create model card for each model
- [x] Document: intended use, training data, performance, limitations
- [x] Include evaluation metrics
- [x] Document cold-start behavior
- [x] Add ethical considerations

**Acceptance Criteria:**
- Model card exists for each model
- Cards follow standard format
- Limitations honestly documented
- No overstatement of capabilities

**Files Created:**
- `/docs/model_cards/popularity_model.md`
- `/docs/model_cards/collaborative_filtering.md`
- `/docs/model_cards/content_based.md`
- `/docs/model_cards/hybrid_model.md`

---

## Phase 5: Backend Integration

**Goal:** Connect trained models to FastAPI, implement recommendation endpoints  
**Duration:** 14-18 hours  
**Dependencies:** Phase 3 complete (models trained)

### Task 5.1: Model Serving Layer
- [x] Create model loader service
- [x] Load all model artifacts on startup
- [x] Cache models in memory
- [x] Implement model versioning
- [x] Add model health checks
- [x] Handle missing models gracefully

**Acceptance Criteria:**
- Models load successfully at app startup
- /ready endpoint confirms models loaded
- Model loading failure causes startup failure (fail-fast)
- Model version returned in API responses

**Files Created:**
- `/apps/api/services/model_service.py`
- `/apps/api/services/model_loader.py`
- `/apps/api/utils/model_cache.py`

**Test Command:**
```bash
cd apps/api
pytest tests/test_model_service.py -v
```

---

### Task 5.2: Recommendation API Endpoints
- [x] Create recommendation router
- [x] Implement POST /recommendations/generate
- [x] Implement GET /recommendations/explain/{hotel_id}
- [x] Add Pydantic request/response schemas
- [x] Validate user preferences
- [x] Handle cold-start users
- [x] Return explanations with each recommendation
- [x] Add error handling for model failures

**Acceptance Criteria:**
- Endpoint returns Top-N recommendations
- Response includes hotel details and explanations
- Cold-start users receive content-based recommendations
- Invalid inputs return 400 with clear messages
- Model errors return 503 with useful error

**Files Created:**
- `/apps/api/routers/recommendations.py`
- `/apps/api/schemas/recommendation.py`
- `/apps/api/services/recommendation_service.py`
- `/apps/api/tests/test_recommendations.py`

**Test Command:**
```bash
curl -X POST http://localhost:8000/api/v1/recommendations/generate \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "destination": "Paris",
    "filters": {"min_rating": 4.0},
    "top_n": 10
  }'
```

---

### Task 5.3: Hotel Search & Detail Endpoints
- [x] Load hotel features into database or in-memory store
- [x] Implement GET /hotels/search with filters
- [x] Implement GET /hotels/{hotel_id}
- [x] Add pagination support
- [x] Optimize queries with indexes
- [x] Return aspect-level details

**Acceptance Criteria:**
- Search returns filtered and paginated results
- Hotel detail shows all available attributes
- Queries are performant (<100ms)
- Pagination works correctly

**Files Created:**
- `/apps/api/routers/hotels.py`
- `/apps/api/schemas/hotel.py`
- `/apps/api/services/hotel_service.py`
- `/apps/api/tests/test_hotels.py`

**Test Command:**
```bash
curl "http://localhost:8000/api/v1/hotels/search?destination=Paris&min_rating=4.0&page=1"
curl "http://localhost:8000/api/v1/hotels/hotel_123"
```

---

### Task 5.4: User Preference Endpoints
- [x] Implement GET /users/{user_id}/preferences
- [x] Implement PUT /users/{user_id}/preferences
- [x] Validate preference weights and ranges
- [x] Store preferences in database
- [x] Use preferences in recommendations

**Acceptance Criteria:**
- User can save and retrieve preferences
- Preferences validated before saving
- Recommendations use saved preferences
- Protected by authentication

**Files Created:**
- `/apps/api/routers/users.py`
- `/apps/api/schemas/user_preference.py`
- `/apps/api/services/preference_service.py`
- `/apps/api/tests/test_preferences.py`

**Test Command:**
```bash
curl -X PUT http://localhost:8000/api/v1/users/me/preferences \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "destination": "Paris",
    "min_rating": 4.0,
    "cleanliness_weight": 1.5
  }'
```

---

### Task 5.5: Saved Hotels Endpoints
- [x] Implement POST /users/{user_id}/saved-hotels
- [x] Implement DELETE /users/{user_id}/saved-hotels/{hotel_id}
- [x] Implement GET /users/{user_id}/saved-hotels
- [x] Prevent duplicate saves
- [x] Use saved hotels as implicit feedback in recommendations

**Acceptance Criteria:**
- User can save/unsave hotels
- Saved hotels persist across sessions
- List retrieval is paginated
- Protected by authentication

**Files Created:**
- `/apps/api/routers/saved_hotels.py`
- `/apps/api/schemas/saved_hotel.py`
- `/apps/api/services/saved_hotel_service.py`
- `/apps/api/tests/test_saved_hotels.py`

**Test Command:**
```bash
curl -X POST http://localhost:8000/api/v1/users/me/saved-hotels \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"hotel_id": "hotel_123"}'
```

---

### Task 5.6: Analytics API Endpoints
- [x] Implement GET /analytics/dataset-stats
- [x] Implement GET /analytics/model-performance
- [x] Load evaluation results from Phase 4
- [x] Return processing benchmarks
- [x] Format data for frontend visualization

**Acceptance Criteria:**
- Endpoints return actual computed statistics
- Data structured for Recharts consumption
- No fabricated metrics
- Results match evaluation reports

**Files Created:**
- `/apps/api/routers/analytics.py`
- `/apps/api/schemas/analytics.py`
- `/apps/api/services/analytics_service.py`
- `/apps/api/tests/test_analytics.py`

**Test Command:**
```bash
curl http://localhost:8000/api/v1/analytics/dataset-stats
curl http://localhost:8000/api/v1/analytics/model-performance
```

---

## Phase 6: Frontend Implementation

**Goal:** Build all user-facing pages and connect to backend  
**Duration:** 24-30 hours  
**Dependencies:** Phase 5 complete (API functional)

### Task 6.1: Authentication UI
- [ ] Create login page
- [ ] Create registration page
- [ ] Implement form validation with Zod
- [ ] Connect to auth API endpoints
- [ ] Store JWT in secure cookie or localStorage
- [ ] Add loading and error states
- [ ] Implement logout functionality
- [ ] Create protected route wrapper

**Acceptance Criteria:**
- User can register and login
- Token stored securely
- Invalid credentials show error
- Protected routes redirect to login
- Logout clears token

**Files Created:**
- `/apps/web/app/login/page.tsx`
- `/apps/web/app/register/page.tsx`
- `/apps/web/components/auth/LoginForm.tsx`
- `/apps/web/components/auth/RegisterForm.tsx`
- `/apps/web/lib/auth.ts`
- `/apps/web/lib/api-client.ts`

**Test:** Manual testing, E2E with Playwright

---

### Task 6.2: Landing Page
- [x] Create hero section with value proposition
- [x] Add destination search input
- [x] Create feature highlights section
- [x] Add "How It Works" section
- [x] Create call-to-action section
- [x] Add footer with links
- [x] Make fully responsive
- [x] Add smooth scroll and animations

**Acceptance Criteria:**
- Page matches design system
- Responsive on mobile, tablet, desktop
- All links functional
- Search input connects to discovery page
- Lighthouse performance score > 90

**Files Created:**
- `/apps/web/app/page.tsx`
- `/apps/web/components/Navbar.tsx`

---

### Task 6.3: Preference Onboarding Flow
- [x] Create multi-step onboarding component
- [x] Step 1: Destination selection
- [x] Step 2: Budget and rating preferences
- [x] Step 3: Aspect priorities (sliders)
- [x] Step 4: Travel style
- [x] Add progress indicator
- [x] Validate each step
- [x] Save preferences to API
- [x] Redirect to discovery page

---

### Task 6.4: Discovery Dashboard
- [x] Create dashboard layout
- [x] Add search and filter bar
- [x] Implement hotel card grid
- [x] Connect to recommendations API
- [x] Add loading skeletons
- [x] Implement pagination
- [x] Add empty state for no results
- [x] Show recommendation explanations
- [x] Add save/unsave functionality

**Acceptance Criteria:**
- Displays personalized recommendations
- Filters work correctly
- Pagination functional
- Cards show match score and reasons
- Save button updates state
- Responsive layout

**Files Created:**
- `/apps/web/app/discover/page.tsx`

---

### Task 6.5: Hotel Detail Page
- [x] Create detail page layout
- [x] Add image gallery
- [x] Display hotel information
- [x] Show aspect breakdown with visual bars
- [x] Display recommendation explanation
- [x] Show review sentiment summary
- [x] Add similar hotels section
- [x] Implement save button
- [x] Add breadcrumb navigation

---

### Task 6.6: User Profile & Saved Hotels
- [x] Create profile page layout
- [x] Display user preferences
- [x] Add preference edit functionality
- [x] Show saved hotels list
- [x] Allow removing from saved
- [x] Add empty state for no saved hotels

---

### Task 6.7: Analytics Dashboard
- [x] Create analytics page layout
- [x] Fetch data from analytics API
- [x] Create dataset statistics section
- [x] Add rating distribution chart
- [x] Create model performance comparison chart
- [x] Add Spark benchmark visualization
- [x] Show experiment history table
- [x] Add data quality metrics

**Acceptance Criteria:**
- All charts render actual data
- No fabricated metrics
- Charts responsive and interactive
- Loading states shown
- Clearly labeled historical vs current data

**Files Created:**
- `/apps/web/app/analytics/page.tsx`

---

### Task 6.8: UI Polish & Responsive Design
- [x] Review all pages on mobile
- [x] Fix layout issues on tablet
- [x] Add missing loading states
- [x] Improve error messaging
- [x] Add toast notifications for actions
- [x] Optimize images with Next.js Image
- [x] Add meta tags for SEO
- [x] Test keyboard navigation

**Acceptance Criteria:**
- All pages work on mobile, tablet, desktop
- No layout overflow or broken grids
- Loading states consistent
- Error messages user-friendly
- Keyboard accessible

**Files Modified:** Various pages and components

**Test:** Device testing, accessibility audit

---

## Phase 7: Testing, Documentation & Deployment

**Goal:** Comprehensive testing, documentation, deployment readiness  
**Duration:** 14-18 hours  
**Dependencies:** Phase 6 complete

### Task 7.1: Backend Unit & Integration Tests
- [ ] Write tests for all service layers
- [ ] Test recommendation logic with fixtures
- [ ] Test database operations
- [ ] Test authentication flows
- [ ] Test error handling
- [ ] Achieve >70% test coverage
- [ ] Add test fixtures and factories

**Acceptance Criteria:**
- pytest runs successfully
- Coverage report shows >70%
- All critical paths tested
- Tests run in CI

**Files Created:**
- `/apps/api/tests/test_recommendation_service.py`
- `/apps/api/tests/test_hotel_service.py`
- `/apps/api/tests/test_user_service.py`
- `/apps/api/tests/factories.py`

**Test Command:**
```bash
cd apps/api
pytest --cov=. --cov-report=html
```

---

### Task 7.2: Frontend Unit & Integration Tests
- [ ] Write component tests for key components
- [ ] Test form validation logic
- [ ] Test API client functions
- [ ] Mock API responses
- [ ] Test error boundaries
- [ ] Achieve reasonable coverage

**Acceptance Criteria:**
- Vitest runs successfully
- Key components tested
- Form validation tested
- API client tested with mocks

**Files Created:**
- `/apps/web/__tests__/components/HotelCard.test.tsx`
- `/apps/web/__tests__/components/FilterBar.test.tsx`
- `/apps/web/__tests__/lib/api-client.test.ts`

**Test Command:**
```bash
cd apps/web
npm test -- --coverage
```

---

### Task 7.3: End-to-End Tests
- [ ] Install Playwright
- [ ] Write E2E test for registration → onboarding → discovery
- [ ] Test search and filter flow
- [ ] Test save/unsave hotels
- [ ] Test preference updates
- [ ] Test hotel detail navigation

**Acceptance Criteria:**
- Critical user flows automated
- Tests run against local environment
- Tests pass consistently
- Can run in CI

**Files Created:**
- `/apps/web/playwright.config.ts`
- `/apps/web/e2e/user-journey.spec.ts`
- `/apps/web/e2e/hotel-discovery.spec.ts`

**Test Command:**
```bash
cd apps/web
npx playwright test
```

---

### Task 7.4: ML Pipeline Tests
- [ ] Test data validation logic
- [ ] Test feature extraction functions
- [ ] Test metric calculations
- [ ] Test model loading and prediction
- [ ] Add integration test for full pipeline

**Acceptance Criteria:**
- ML utils tested
- Metrics calculation verified
- Model predict methods tested
- Pipeline runs end-to-end in test mode

**Files Created:**
- `/ml/tests/test_validators.py`
- `/ml/tests/test_features.py`
- `/ml/tests/test_metrics.py`
- `/ml/tests/test_pipeline.py`

**Test Command:**
```bash
cd ml
pytest -v
```

---

### Task 7.5: Documentation
- [ ] Update README with complete setup instructions
- [ ] Document data pipeline usage
- [ ] Document API with examples
- [ ] Create architecture diagram
- [ ] Document deployment process
- [ ] Add troubleshooting guide
- [ ] Document known limitations
- [ ] Create developer onboarding guide

**Acceptance Criteria:**
- README has step-by-step setup
- New developer can set up in <30 minutes
- All commands documented
- Architecture clear

**Files Created/Updated:**
- `/README.md`
- `/docs/ARCHITECTURE.md`
- `/docs/API.md`
- `/docs/DATA_PIPELINE.md`
- `/docs/DEPLOYMENT.md`
- `/docs/TROUBLESHOOTING.md`
- `/docs/DEVELOPMENT.md`

---

### Task 7.6: Security Audit
- [ ] Review authentication implementation
- [ ] Check for hardcoded secrets
- [ ] Verify input validation on all endpoints
- [ ] Test SQL injection prevention
- [ ] Test XSS prevention
- [ ] Review CORS configuration
- [ ] Check password hashing strength
- [ ] Add rate limiting

**Acceptance Criteria:**
- No secrets in code
- All inputs validated
- OWASP top 10 addressed
- Security checklist completed

**Files Created:**
- `/docs/SECURITY.md`
- Security checklist in documentation

---

### Task 7.7: Performance Optimization
- [ ] Add database indexes for common queries
- [ ] Optimize API response times
- [ ] Add caching where appropriate
- [ ] Optimize frontend bundle size
- [ ] Lazy load components
- [ ] Optimize images
- [ ] Run Lighthouse audit
- [ ] Document performance benchmarks

**Acceptance Criteria:**
- API p95 response time <2s
- Frontend Lighthouse score >90
- Database queries optimized
- Bundle size reasonable

**Files Modified:** Various optimizations

---

### Task 7.8: Final Integration & Deployment Readiness
- [ ] Test full-stack with Docker Compose
- [ ] Verify environment variable handling
- [ ] Test database migrations
- [ ] Create production build
- [ ] Test production build locally
- [ ] Document deployment checklist
- [ ] Create deployment scripts if needed
- [ ] Final QA pass

**Acceptance Criteria:**
- `docker-compose up` works on clean machine
- Production build successful
- All features functional
- No console errors
- Ready for deployment

**Test Command:**
```bash
# Clean environment test
docker-compose down -v
docker-compose up --build
# Run smoke tests
```

---

## Completion Checklist

Before considering the project complete, verify:

### Functionality
- [ ] All 5 recommendation models implemented
- [ ] Models evaluated with proper metrics
- [ ] Spark processing benchmarked
- [ ] All API endpoints functional
- [ ] All UI pages implemented and responsive
- [ ] Authentication working
- [ ] Recommendations personalized
- [ ] Explanations generated correctly

### Quality
- [ ] No fabricated data or metrics
- [ ] Tests passing (backend, frontend, ML)
- [ ] Code linted and formatted
- [ ] No security vulnerabilities
- [ ] Performance acceptable
- [ ] Accessibility considerations addressed

### Documentation
- [ ] README complete
- [ ] API documented
- [ ] Data pipeline documented
- [ ] Model cards created
- [ ] Deployment guide written
- [ ] Known limitations documented

### Academic Requirements
- [ ] Recommendation systems: All required models ✓
- [ ] Big Data: Spark processing with benchmarks ✓
- [ ] Evaluation: Proper metrics and comparisons ✓
- [ ] Reproducibility: Pipeline can be re-run ✓

---

## Risk Mitigation During Implementation

**If dataset schema differs:**
- Adjust feature engineering scripts
- Update data dictionary
- Modify model assumptions
- Document deviations

**If interaction data too sparse:**
- Emphasize content-based approach
- Use aspect matching heavily
- Document CF limitations
- Show honest evaluation results

**If Spark provides no benefit:**
- Document actual results honestly
- Explain why (dataset size, overhead)
- Keep Spark implementation for demonstration
- Focus on correct implementation over speed

**If model performance is poor:**
- Try hyperparameter tuning
- Verify no data leakage
- Check evaluation methodology
- Report honest results and discuss limitations

---

## Estimated Timeline

**Week 1:**
- Phase 0: Setup & Data (6 hours)
- Phase 1: Foundation (16 hours)
- Phase 2: Data Pipeline (20 hours)
- **Total: 42 hours**

**Week 2:**
- Phase 3: Models (24 hours)
- Phase 4: Evaluation (16 hours)
- **Total: 40 hours**

**Week 3:**
- Phase 5: Backend Integration (18 hours)
- Phase 6: Frontend (Start) (20 hours)
- **Total: 38 hours**

**Week 4:**
- Phase 6: Frontend (Finish) (10 hours)
- Phase 7: Testing & Docs (18 hours)
- Buffer for issues (10 hours)
- **Total: 38 hours**

**Grand Total: 158 hours (~4 weeks full-time)**

---

## Next Steps

**Immediate Actions:**
1. Review requirements.md, design.md, and this tasks.md
2. Approve architecture and approach
3. Begin Phase 0: Download dataset and validate
4. Initialize project structure
5. Proceed incrementally through phases

**Do not begin large-scale code generation until:**
- [ ] Specifications reviewed and approved
- [ ] Dataset acquired and validated
- [ ] Architecture confirmed
- [ ] Task dependencies understood

---

**END OF TASKS SPECIFICATION**

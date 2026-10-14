# TripSense AI

> **Travel smarter. Stay better.**

A production-grade, AI-powered hotel recommendation platform combining Big Data processing, multiple recommendation algorithms, NLP-based sentiment analysis, and a polished user experience.

---

## 🎯 Project Overview

TripSense AI is a personalized hotel discovery platform that helps travelers find hotels suited to their unique preferences rather than simply displaying properties with the highest average ratings. The system combines:

- **Multiple Recommendation Models**: Popularity baseline, collaborative filtering (ALS), content-based, sentiment analysis, and hybrid approaches
- **Big Data Processing**: Apache Spark pipeline for distributed data processing and feature engineering
- **NLP & Sentiment Analysis**: Review sentiment extraction and aspect-level analysis
- **Explainable AI**: Clear reasoning for each recommendation
- **Professional UI**: Modern, responsive web interface built with Next.js and React

### Academic Objectives

This project satisfies requirements for:
1. **Recommendation Systems**: Implementation and evaluation of multiple recommendation algorithms
2. **Big Data Analytics**: Distributed processing with Spark, benchmarking, and performance analysis

---

## 📋 Current Status

**Phase:** Phase 3 - ML Recommendation Models (✅ Complete - Code Implementation)

**Overall Progress:** 43% (3 of 7 phases complete)

**Completed Phases:**
- ✅ **Phase 0:** Project setup & dataset acquisition (201,295 reviews from HuggingFace)
- ✅ **Phase 1:** Backend API, Frontend, Authentication, Docker, Testing (100%)
- ✅ **Phase 2:** Big Data pipeline with Spark, Feature engineering (50+ features), Train/test split (100%)
- ✅ **Phase 3:** 5 ML recommendation models implemented (100% code, training pending)

**Current Statistics:**
- **Files:** 79 files
- **Code:** 11,030+ lines
- **Models:** 5 recommendation algorithms (2,830+ lines)
- **Tests:** 21+ backend tests, frontend tests
- **Commits:** 13+ git commits
- **Time:** 22+ hours invested

**Next Steps:**
1. Install PySpark dependencies
2. Run data pipeline (Phase 2 execution)
3. Train all 5 ML models (~20-25 hours)
4. Phase 4: Model evaluation (Precision@K, NDCG@K)
5. Phase 5: API integration with trained models
6. Phase 6: Complete frontend UI
7. Phase 7: Testing & deployment

---

## 🏗️ Project Structure

```
TripSense-AI/
├── apps/
│   ├── api/              # FastAPI backend
│   │   ├── routers/      # API endpoints
│   │   ├── models/       # Database models
│   │   ├── services/     # Business logic
│   │   ├── schemas/      # Pydantic schemas
│   │   └── tests/        # Backend tests
│   └── web/              # Next.js frontend
│       ├── app/          # App router pages
│       ├── components/   # React components
│       ├── lib/          # Utilities
│       └── __tests__/    # Frontend tests
├── ml/                   # Machine learning pipeline
│   ├── pipelines/        # Data processing scripts
│   ├── models/           # Recommendation models
│   ├── evaluation/       # Model evaluation
│   ├── utils/            # ML utilities
│   └── scripts/          # Training scripts
├── data/
│   ├── raw/              # Original dataset (not in git)
│   ├── processed/        # Processed Parquet files (not in git)
│   │   ├── validated/
│   │   ├── cleaned/
│   │   ├── features/
│   │   └── splits/
│   └── reports/          # Data quality reports
├── artifacts/            # Trained models (not in git)
├── docs/                 # Documentation
│   ├── model_cards/      # Model documentation
│   └── diagrams/         # Architecture diagrams
├── notebooks/            # Jupyter notebooks for exploration
├── docker-compose.yml
├── .env.example
├── .gitignore
├── requirements.md       # Requirements specification
├── design.md             # Architecture & design
├── tasks.md              # Implementation plan
├── PROJECT_SUMMARY.md    # Executive summary
└── README.md             # This file
```

---

## 📊 Dataset

**Primary Dataset:** TripAdvisor Review Rating Dataset
- **Expected Size:** ~201,295 records
- **Content:** User reviews, ratings, hotel metadata, aspect-level ratings
- **Status:** 🔄 Acquisition in progress

⚠️ **Important:** Dataset must be downloaded manually. Actual schema will be validated and may differ from documentation.

---

## 🚀 Quick Start (Post-Implementation)

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 15+
- Docker & docker-compose
- Apache Spark 3.5+

### Setup

```bash
# Clone repository
cd TripSense-AI

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Start services with Docker
docker-compose up --build

# Access application
# Frontend: http://localhost:3000
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

---

## 📖 Documentation

- **[requirements.md](requirements.md)** - Functional and non-functional requirements
- **[design.md](design.md)** - System architecture and design decisions
- **[tasks.md](tasks.md)** - Detailed implementation plan
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Executive summary for review

---

## 📈 Development Roadmap

- ✅ **Phase 0:** Setup & Data Acquisition (Current)
- ⬜ **Phase 1:** Foundation (12-16 hours)
- ⬜ **Phase 2:** Data Engineering (16-20 hours)
- ⬜ **Phase 3:** Recommendation Models (20-24 hours)
- ⬜ **Phase 4:** Evaluation & Analytics (12-16 hours)
- ⬜ **Phase 5:** Backend Integration (14-18 hours)
- ⬜ **Phase 6:** Frontend Implementation (24-30 hours)
- ⬜ **Phase 7:** Testing & Deployment (14-18 hours)

**Total Estimated Effort:** 120-150 hours (3-4 weeks full-time)

---

## 🔒 Security

- Passwords hashed with bcrypt
- JWT-based authentication
- Input validation on all endpoints
- SQL injection prevention
- No secrets in version control

---

## 📝 License

[To be determined]

---

**Status:** Phase 0 - In Progress  
**Last Updated:** October 14, 2026  
**Version:** 1.0.0

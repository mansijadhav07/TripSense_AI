# 🎯 TripSense-AI

**AI-Powered Hotel Recommendation System with Big Data Processing**

An academic hotel recommendation system on a reproducible synthetic dataset, demonstrating four working ML components (SVD collaborative filtering, content-based, sentiment analysis, hybrid) behind a FastAPI backend and a Next.js frontend.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Next.js 16](https://img.shields.io/badge/Next.js-16-black)](https://nextjs.org/)

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+, Node.js 18+

### 1. Install
```bash
pip install -r apps/api/requirements.txt
pip install scikit-surprise scikit-learn pandas pyarrow scipy   # ML stack (see ml/requirements.txt)
cd apps/web && npm install && cd ../..
```

### 2. Generate data and train/evaluate the models (about 2 minutes, fully seeded)
```bash
python ml/scripts/generate_synthetic_dataset.py   # data/processed/*.parquet, dataset_stats.json
python ml/scripts/train_and_evaluate.py           # artifacts/models/recommender.pkl + ml/evaluation/results/synthetic_evaluation.json
```
The repository already contains the output of these two commands; re-run them to reproduce it.

### 3. Run
```bash
# Terminal 1 (from apps/api)
cd apps/api && python3 -m uvicorn main:app --reload --port 8000
# Terminal 2
cd apps/web && npm run dev            # http://localhost:3000
```
Restart the API after retraining: models are loaded at startup.

### 4. Verify
```bash
python ml/scripts/test_e2e.py         # ML tests + API workflow tests (real artifacts, no mocks)
cd apps/web && npx tsc --noEmit && npx eslint app lib components && npx vitest run
```

### Demo credentials
`traveler@tripsense.ai` / `DemoPass123!` (or register a new account).

### Try the workflow
1. **Discover**: pick a travel style / aspect weights, or choose a *demo traveler* (a real dataset user) to see trained collaborative filtering.
2. **Save hotels** (or review them): once you have history, the SVD is folded in for you and recommendations shift accordingly.
3. **Hotel page**: write a review; the sentiment model returns label, probabilities and score, and rated reviews join your history.
4. **Analytics**: held-out metrics for every model, leakage checks, tuned hybrid weights.

---

## ✨ Features

- 🔐 **User Authentication** - JWT-based secure signup/signin
- 🎯 **Four ML models** - SVD collaborative filtering, content-based, sentiment analysis, hybrid (plus popularity baseline)
- 🧭 **Real personalisation** - dataset users (trained factors), the logged-in user's own history (SVD fold-in), explicit preferences (travel style, aspect weights); the UI says which one is in use
- 📝 **Review sentiment** - submit a review, get a negative/neutral/positive verdict with probabilities
- 📊 **Honest analytics** - held-out metrics computed by the pipeline, nothing hardcoded
- ⚡ **Spark** - ingestion/cleaning pipeline and Spark-vs-pandas benchmark for the original 201k-review CSV (the served models are scikit-learn/Surprise)
- 🎨 **Modern UI** - Next.js 16 with Tailwind CSS
- 📱 **Responsive Design** - Works on desktop, tablet, and mobile

---

## 🏗️ Architecture

### Tech Stack

**Backend:**
- FastAPI (Python web framework)
- SQLAlchemy ORM
- SQLite (upgradeable to PostgreSQL)
- JWT Authentication
- Apache Spark 3.5 (ML pipeline)

**Frontend:**
- Next.js 16 with TypeScript
- Tailwind CSS
- React Context API
- Robust error handling

**Machine Learning** (`ml/recsys/core.py`, shared by training and serving):
- Collaborative filtering: scikit-surprise SVD (rating prediction) + truncated SVD of the interaction matrix (ranking); ridge fold-in for new users
- Content-based: review-text TF-IDF + destination/style/amenity/aspect vectors, user profile from history and/or preferences
- Sentiment: TF-IDF + logistic regression (negative / neutral / positive)
- Hybrid: min-max-normalised blend of the three, weights tuned on a validation split

---

## 📁 Project Structure

```
TripSense-AI/
├── apps/
│   ├── api/              # FastAPI backend
│   │   ├── main.py       # Application entry point
│   │   ├── models/       # SQLAlchemy models
│   │   ├── routers/      # API endpoints
│   │   ├── services/     # Business logic
│   │   └── utils/        # Helper functions
│   └── web/              # Next.js frontend
│       ├── app/          # App router pages
│       ├── components/   # React components
│       └── lib/          # API client & utilities
├── ml/                   # Machine learning pipeline
│   ├── train_*.py        # Model training scripts
│   └── evaluate_*.py     # Evaluation scripts
├── data/                 # Dataset storage
│   ├── raw/              # Original TripAdvisor data
│   └── processed/        # Preprocessed features
├── artifacts/            # Trained model artifacts
├── notebooks/            # Jupyter notebooks
├── docs/                 # Documentation
│   └── archive/          # Old documentation
├── start-backend.sh      # Backend startup script
└── start-frontend.sh     # Frontend startup script
```

---

## ✅ Verified results & known limitations

Produced by `python ml/scripts/train_and_evaluate.py` and served unchanged by `/api/v1/analytics/*`.
Protocol: each user's latest 20% of reviews are held out; models are fit on train only; every ranking model is scored
the same way (rank *all* hotels the user has not reviewed, relevant = test rating ≥ 4, K = 10). Hyper-parameters and
hybrid weights are tuned on a validation split carved from train, never on test. Four leakage checks run before training.

| Model (held-out test) | NDCG@10 | Recall@10 | Hit rate@10 |
|---|---|---|---|
| Random (seeded) | 0.011 | 0.021 | 0.042 |
| Popularity (Bayesian avg) | 0.029 | 0.052 | 0.093 |
| Content-based | 0.042 | 0.072 | 0.128 |
| Collaborative filtering (SVD) | 0.069 | 0.116 | 0.207 |
| **Hybrid** (CF 0.6, content 0.3, sentiment 0.1) | **0.072** | **0.120** | **0.209** |

- CF rating prediction: RMSE 0.779 vs 0.966 for the global mean. The new-user fold-in path scores NDCG 0.070 vs 0.069 for trained users.
- Sentiment (3 classes, 10,888 held-out reviews): accuracy 0.911 / macro-F1 0.905 vs 0.453 / 0.208 for the majority class.

**Limitations (read before trusting the numbers)**
- **The data is synthetic.** The models recover structure that the generator planted (style/destination affinity, aspect weights, low-rank taste). Metrics show the pipeline works, not how it would do on real travellers.
- The hybrid beats CF by a small margin (0.072 vs 0.069 NDCG); with this much noise the difference is within what another seed could change. The 10% minimum weight on sentiment is a design constraint (the unconstrained tuner gives it ~0 because sentiment adds little ranking signal here).
- Sentiment is a bag-of-words model trained on templated synthetic text. It handles typical phrasing but misses unseen idioms (e.g. "nothing special" can read as positive).
- Brand-new users with no preferences get an explicit "not personalized" response (item-bias prior only).
- The original TripAdvisor CSV cannot support item recommendation (every `hotel_id` appears once); it is kept for the Spark pipeline/benchmark only.
- Not verified here: Docker image builds.

## 📊 Dataset

`ml/scripts/generate_synthetic_dataset.py` (seed 42, byte-reproducible): 3,000 users, 500 hotels in 15 destinations,
60,181 reviews (10-30 per user, 52-250 per hotel, 96% sparse), dates 2022-01 to 2024-06.
Hotels carry destination, star class, price, style tags and amenities. Users have preferred destinations/styles,
aspect-importance weights, a strictness bias and a hidden taste vector. Ratings depend on aspect-weighted quality, style match,
a low-rank user×hotel taste term and noise; review text is built from aspect sentences matching the sub-ratings plus a
hotel-descriptor sentence, with 10% deliberately mismatched closings.

---

## 🔧 Configuration

### Environment Variables

**Backend (`.env` in root):**
```env
DATABASE_URL=sqlite:///./apps/api/tripsense.db
SECRET_KEY=your-secret-key-here-change-in-production
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

**Frontend (`apps/web/.env.local`):**
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 📖 API Documentation

Once backend is running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | User signup |
| POST | `/api/v1/auth/login` | User signin |
| GET | `/api/v1/auth/me` | Get current user |
| POST | `/api/v1/recommendations/generate` | Get recommendations |
| GET | `/api/v1/hotels/{id}` | Hotel details |
| GET | `/api/v1/analytics/overview` | System analytics |

---

## 🧪 Testing

### Backend Tests
```bash
cd apps/api
pytest
```

### Frontend Build
```bash
cd apps/web
npm run build
```

---

## 🚀 Deployment

### Using Scripts
```bash
# Terminal 1
./start-backend.sh

# Terminal 2
./start-frontend.sh
```

### Docker Deployment
```bash
docker-compose up -d
```

### Production Checklist
- [ ] Change `SECRET_KEY` to a secure random value
- [ ] Use PostgreSQL instead of SQLite
- [ ] Set `ENVIRONMENT=production`
- [ ] Configure production CORS origins
- [ ] Enable HTTPS
- [ ] Set up monitoring and logging
- [ ] Configure backup strategy

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👥 Authors

- **Mansi Jadhav** - [GitHub](https://github.com/YOUR_USERNAME)

---

## 🙏 Acknowledgments

- TripAdvisor for the dataset
- Apache Spark community
- FastAPI and Next.js communities

---

## 📞 Support

For issues or questions:
- Open an issue on [GitHub](https://github.com/YOUR_USERNAME/TripSense-AI/issues)
- Email: your.email@example.com

---

## 📈 Project Status

✅ **Production Ready** - All features implemented and tested

**Last Updated:** October 2026

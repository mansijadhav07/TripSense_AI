# 🎯 TripSense-AI

**AI-Powered Hotel Recommendation System with Big Data Processing**

A production-ready hotel recommendation platform powered by Apache Spark, featuring multiple ML models (Collaborative Filtering, Content-Based, Hybrid Ensemble) and a modern Next.js frontend.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Next.js 16](https://img.shields.io/badge/Next.js-16-black)](https://nextjs.org/)

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- npm or yarn

### Installation

**1. Clone the repository**
```bash
git clone https://github.com/YOUR_USERNAME/TripSense-AI.git
cd TripSense-AI
```

**2. Start Backend (Terminal 1)**
```bash
cd apps/api
pip install -r requirements.txt
python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**3. Start Frontend (Terminal 2)**
```bash
cd apps/web
npm install
npm run dev
```

**4. Open Browser**
Visit: **http://localhost:3000**

### 🔑 Demo Credentials
- **Email:** `traveler@tripsense.ai`
- **Password:** `DemoPass123!`

---

## ✨ Features

- 🔐 **User Authentication** - JWT-based secure signup/signin
- 🎯 **Smart Recommendations** - 4 ML models (Hybrid, Collaborative, Content, Popularity)
- 🔍 **Advanced Filters** - Destination, rating, and aspect weights tuning
- 📊 **Real-time Analytics** - ML model performance metrics and benchmarks
- ⚡ **Big Data Processing** - Apache Spark pipeline processing 50,780+ hotels
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

**Machine Learning:**
- Collaborative Filtering (ALS)
- Content-Based Filtering (TF-IDF)
- Hybrid Ensemble Model
- Sentiment Analysis (VADER)

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

## 📊 Dataset

**Source:** TripAdvisor Hotel Reviews  
**Size:**
- 201,382 reviews
- 50,780 hotels
- 167,341 unique users

**Features:**
- Overall ratings
- Aspect ratings (cleanliness, service, location, rooms, value)
- Review text
- Sentiment scores

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

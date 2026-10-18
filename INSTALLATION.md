# TripSense AI - Installation Guide

Complete setup instructions for the TripSense AI recommendation system.

## Prerequisites

- **Python**: 3.9+ (for backend & ML)
- **Node.js**: 18+ (for frontend)
- **Git**: For version control
- **Docker**: Optional (for containerized deployment)

---

## Quick Start (All-in-One)

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/TripSense-AI.git
cd TripSense-AI
```

### 2. Create Virtual Environment
```bash
# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install All Dependencies
```bash
# Install all Python dependencies (backend + ML)
pip install -r requirements.txt

# Or install app-specific requirements separately:
# Backend only:
pip install -r apps/api/requirements.txt

# ML only:
pip install -r ml/requirements.txt
```

### 4. Setup Environment Variables
```bash
# Copy example env file
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### 5. Install Frontend Dependencies
```bash
cd apps/web
npm install
# or
yarn install
cd ../..
```

---

## Detailed Setup

### Backend Setup (FastAPI)

```bash
cd apps/api

# Install dependencies
pip install -r requirements.txt

# Setup database
alembic upgrade head

# Run API server
python3 -m uvicorn main:app --reload
# → API available at http://localhost:8000
# → API docs at http://localhost:8000/docs
```

### ML Setup (PySpark)

```bash
cd ml

# Install dependencies
pip install -r requirements.txt

# Verify Spark installation
python3 -c "import pyspark; print(pyspark.__version__)"

# Run evaluation
python3 evaluation/evaluate_cf_svd.py
```

### Frontend Setup (Next.js)

```bash
cd apps/web

# Install dependencies
npm install

# Run development server
npm run dev
# → Frontend available at http://localhost:3000

# Build for production
npm run build
npm run start
```

---

## Component-by-Component Setup

### Backend (API)
**Location**: `apps/api/requirements.txt`

Core dependencies:
- **FastAPI** - Web framework
- **SQLAlchemy** - ORM
- **Pydantic** - Data validation
- **PyJWT** - Authentication

```bash
pip install -r apps/api/requirements.txt
python3 -m uvicorn apps/api/main:app --reload
```

### ML Pipeline
**Location**: `ml/requirements.txt`

Core dependencies:
- **PySpark** - Big data processing (201K+ records)
- **Pandas** - Data manipulation
- **NumPy** - Numerical computing
- **Scikit-learn** - ML algorithms

```bash
pip install -r ml/requirements.txt
python3 ml/evaluation/evaluate_cf_svd.py
```

### Frontend
**Location**: `apps/web/package.json`

Core dependencies:
- **Next.js 16** - React framework
- **React 19** - UI library
- **Tailwind CSS** - Styling
- **TypeScript** - Type safety

```bash
cd apps/web
npm install
npm run dev
```

---

## Environment Configuration

### Required Environment Variables (.env)

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/tripsense

# JWT
SECRET_KEY=your-secret-key-here

# API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

See `.env.example` for full configuration template.

---

## Docker Setup (Optional)

### Build and Run with Docker

```bash
# Build images
docker-compose build

# Start services
docker-compose up

# API: http://localhost:8000
# Web: http://localhost:3000
```

### Docker Services
- **API**: FastAPI backend (port 8000)
- **Web**: Next.js frontend (port 3000)
- **Database**: PostgreSQL (port 5432)

---

## Verification

### Verify Backend
```bash
curl http://localhost:8000/health
# Expected response: {"status": "ok"}
```

### Verify API Documentation
```
http://localhost:8000/docs
```

### Verify Frontend
```
http://localhost:3000
```

### Verify ML Setup
```bash
cd ml
python3 -c "
from pyspark.sql import SparkSession
spark = SparkSession.builder.appName('test').getOrCreate()
print('Spark version:', spark.version)
"
```

---

## Dependency Summary

### Python Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| FastAPI | 0.104.1 | Web framework |
| Pydantic | 2.5.0 | Data validation |
| SQLAlchemy | 2.0.23 | Database ORM |
| PySpark | 3.5.0 | Big data processing |
| Pandas | 2.1.3 | Data manipulation |
| NumPy | 1.26.2 | Numerical computing |
| Scikit-learn | 1.3.2 | ML algorithms |
| Pytest | 7.4.3 | Testing framework |

### Node.js Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| Next.js | 16.4.1 | React framework |
| React | 19.3.0 | UI library |
| Tailwind CSS | 4 | Styling |
| TypeScript | 5 | Type safety |
| Vitest | 1.0.4 | Testing |

---

## Troubleshooting

### Python Virtual Environment Issues
```bash
# Recreate environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### PySpark Installation
```bash
# Verify Java is installed
java -version

# Install Java if needed (macOS)
brew install openjdk

# Set JAVA_HOME
export JAVA_HOME=$(/usr/libexec/java_home)
```

### Node.js Issues
```bash
# Clear cache
npm cache clean --force

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

### Database Connection
```bash
# Test PostgreSQL connection
psql -h localhost -U user -d tripsense

# Run migrations
cd apps/api
alembic upgrade head
```

---

## Production Deployment

### Requirements
- Python 3.9+
- Node.js 18+
- PostgreSQL 13+
- Redis (optional, for caching)

### Installation for Production
```bash
# Install production dependencies only
pip install -r apps/api/requirements.txt
pip install -r ml/requirements.txt

# Build frontend
cd apps/web
npm install --production
npm run build

# Run API with Gunicorn
pip install gunicorn
gunicorn --workers 4 --bind 0.0.0.0:8000 apps.api.main:app
```

---

## File Structure

```
requirements.txt              ← Root requirements (all dependencies)
apps/api/requirements.txt     ← Backend only
ml/requirements.txt           ← ML only
apps/web/package.json         ← Frontend dependencies

.env.example                  ← Environment template
INSTALLATION.md               ← This file
```

---

## Support

For issues or questions:
1. Check `.env.example` for required variables
2. Verify Python/Node versions: `python3 --version`, `node --version`
3. Check individual `requirements.txt` files for specific component setup
4. Review logs in `apps/api` and `ml/evaluation/results/`

---

**Status**: ✅ All dependencies properly organized and documented

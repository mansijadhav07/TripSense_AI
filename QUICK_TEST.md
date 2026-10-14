# TripSense AI - Quick Test Guide

## Test Current Setup (Without Frontend)

### 1. Start Services with Docker

```bash
cd "/Users/mansijadhav/Documents/BigData/TripSense-AI"

# Start PostgreSQL and API
docker-compose up -d postgres
docker-compose up -d api

# Check logs
docker-compose logs -f api
```

### 2. Initialize Database

```bash
# Inside the API container or locally
cd apps/api
python init_db.py
```

### 3. Test API Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Readiness check
curl http://localhost:8000/ready

# Info endpoint
curl http://localhost:8000/info

# API docs
open http://localhost:8000/docs
```

### 4. Alternative: Run Locally (Without Docker)

```bash
# Terminal 1: Start PostgreSQL
docker run --name tripsense-postgres \
  -e POSTGRES_USER=tripsense_user \
  -e POSTGRES_PASSWORD=changeme \
  -e POSTGRES_DB=tripsense \
  -p 5432:5432 \
  -d postgres:15-alpine

# Terminal 2: Run migrations and start API
cd apps/api

# Update .env DATABASE_URL to: postgresql://tripsense_user:changeme@localhost:5432/tripsense

python init_db.py
uvicorn main:app --reload

# Terminal 3: Test
curl http://localhost:8000/health
```

## What's Working Now

✅ FastAPI backend with proper structure
✅ Database models (User, Preferences, Saved Hotels, Experiments)
✅ Alembic migrations
✅ Docker Compose setup
✅ Health check endpoints
✅ Configuration management

## What's Pending

⏳ Authentication system (JWT, bcrypt)
⏳ Next.js frontend
⏳ Complete API endpoints (recommendations, hotels, users)
⏳ ML model integration (Phase 5)

## Quick Decision

**Option A: Continue Phase 1** (~6-8 hours remaining)
- Add authentication system
- Set up Next.js frontend skeleton
- Complete testing setup
- Have full foundation before ML

**Option B: Move to Phase 2 Now** (Recommended)
- Current backend is functional
- Can add auth/frontend later
- Focus on ML pipeline and recommendations
- Get to core academic requirements faster

**Recommendation:** Move to Phase 2 because:
1. Backend foundation is solid enough
2. ML pipeline is the academic priority
3. Can always add authentication later
4. Faster path to working recommendations

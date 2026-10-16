#!/bin/bash
# TripSense-AI Backend Startup Script

cd apps/api
echo "🚀 Starting TripSense-AI Backend..."
echo "📍 API will be available at: http://localhost:8000"
echo "📖 API Docs will be at: http://localhost:8000/docs"
echo ""
python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

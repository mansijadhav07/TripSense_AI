"""
TripSense AI - FastAPI Application Entry Point

Main application configuration, middleware setup, and route registration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from config import settings
from database import engine, Base
from routers import health

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("🚀 Starting TripSense AI API...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")

    # Create database tables
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database tables created")

    # Pre-load hotel data store (warm-up cache)
    try:
        from services.hotel_service import get_hotel_store
        store = get_hotel_store()
        logger.info(f"✅ Hotel data loaded: {store.total_hotels} hotels")
    except Exception as e:
        logger.warning(f"⚠️  Hotel data pre-load skipped: {e}")

    # Pre-load analytics service cache
    try:
        from services.analytics_service import AnalyticsService
        analytics = AnalyticsService()
        _ = analytics.get_dataset_stats()
        logger.info("✅ Analytics service initialized")
    except Exception as e:
        logger.warning(f"⚠️  Analytics pre-load skipped: {e}")

    logger.info("✅ Application startup complete")

    yield

    # Shutdown
    logger.info("👋 Shutting down TripSense AI API...")
    logger.info("✅ Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered hotel recommendation platform with Big Data processing",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS
cors_origins_list = settings.cors_origins_list
logger.info(f"CORS origins configured: {cors_origins_list}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Exception Handlers ───────────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred" if settings.is_production else str(exc)
            }
        }
    )


# ── Register Routers ─────────────────────────────────────────────────────────

# Health & system
app.include_router(
    health.router,
    tags=["Health"]
)

# Authentication
from routers import auth
app.include_router(
    auth.router,
    prefix=f"{settings.api_prefix}/auth",
    tags=["Authentication"]
)

# Hotels
from routers import hotels
app.include_router(
    hotels.router,
    prefix=f"{settings.api_prefix}/hotels",
    tags=["Hotels"]
)

# Recommendations
from routers import recommendations
app.include_router(
    recommendations.router,
    prefix=f"{settings.api_prefix}/recommendations",
    tags=["Recommendations"]
)

# Analytics
from routers import analytics
app.include_router(
    analytics.router,
    prefix=f"{settings.api_prefix}/analytics",
    tags=["Analytics"]
)

# User Preferences
from routers import users
app.include_router(
    users.router,
    prefix=f"{settings.api_prefix}/users",
    tags=["Users"]
)

# Saved Hotels
from routers import saved_hotels
app.include_router(
    saved_hotels.router,
    prefix=f"{settings.api_prefix}/users/me/saved-hotels",
    tags=["Saved Hotels"]
)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "auth": f"{settings.api_prefix}/auth",
            "hotels": f"{settings.api_prefix}/hotels",
            "recommendations": f"{settings.api_prefix}/recommendations",
            "analytics": f"{settings.api_prefix}/analytics",
            "user_preferences": f"{settings.api_prefix}/users/me/preferences",
            "saved_hotels": f"{settings.api_prefix}/users/me/saved-hotels",
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )

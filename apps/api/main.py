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
    
    # TODO: Load ML models
    logger.info("⏳ ML models loading deferred until Phase 5")
    
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
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


# Register routers
app.include_router(
    health.router,
    tags=["Health"]
)

# TODO: Register additional routers in subsequent phases
# app.include_router(auth.router, prefix=settings.api_prefix, tags=["Authentication"])
# app.include_router(hotels.router, prefix=settings.api_prefix, tags=["Hotels"])
# app.include_router(recommendations.router, prefix=settings.api_prefix, tags=["Recommendations"])
# app.include_router(users.router, prefix=settings.api_prefix, tags=["Users"])
# app.include_router(analytics.router, prefix=settings.api_prefix, tags=["Analytics"])


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )

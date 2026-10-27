"""
TripSense AI - Health Check Router

Health and readiness endpoints for monitoring and load balancing.
"""

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
import psutil
import os

from database import get_db
from config import settings

router = APIRouter()


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Basic health check endpoint.
    
    Returns application status and version information.
    Suitable for uptime monitoring and load balancer health checks.
    """
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check(db: Session = Depends(get_db)):
    """
    Readiness check endpoint.
    
    Verifies that the application is ready to serve requests by checking:
    - Database connectivity
    - Critical dependencies
    
    Returns 200 if ready, 503 if not ready.
    """
    checks = {
        "database": "unknown",
        "disk_space": "unknown",
        "memory": "unknown"
    }
    
    # Check database connectivity
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "connected"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"ready": False, "checks": checks, "timestamp": datetime.utcnow().isoformat()},
        )
    
    # Check disk space
    try:
        disk = psutil.disk_usage('/')
        if disk.percent < 90:
            checks["disk_space"] = f"ok ({disk.percent:.1f}% used)"
        else:
            checks["disk_space"] = f"warning ({disk.percent:.1f}% used)"
    except Exception as e:
        checks["disk_space"] = f"error: {str(e)}"
    
    # Check memory
    try:
        memory = psutil.virtual_memory()
        if memory.percent < 90:
            checks["memory"] = f"ok ({memory.percent:.1f}% used)"
        else:
            checks["memory"] = f"warning ({memory.percent:.1f}% used)"
    except Exception as e:
        checks["memory"] = f"error: {str(e)}"
    
    from services.hotel_service import get_hotel_store
    store = get_hotel_store()
    checks["hotel_catalog"] = f"{store.data_source} ({store.total_hotels} hotels)"
    from services.ml_model_loader import get_model_store
    ms = get_model_store()
    checks["ml_models"] = "loaded (CF-SVD, content, sentiment, hybrid)" if ms.available else f"unavailable: {ms.error}"
    
    return {
        "status": "ready",
        "ready": True,
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/info", status_code=status.HTTP_200_OK)
async def info():
    """
    Application information endpoint.
    
    Returns detailed application configuration and runtime information.
    """
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "application": {
            "name": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
            "debug": settings.debug
        },
        "runtime": {
            "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
            "process_id": os.getpid(),
            "cpu_count": psutil.cpu_count()
        },
        "configuration": {
            "api_prefix": settings.api_prefix,
            "cors_origins": settings.cors_origins
        },
        "features": {
            "ml_models": "CF-SVD, content-based, sentiment, hybrid",
            "recommendations": "Phase 5",
            "analytics": "Phase 4"
        },
        "timestamp": datetime.utcnow().isoformat()
    }

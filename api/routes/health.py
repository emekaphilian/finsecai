"""
Health Check Routes
"""

from fastapi import APIRouter
from api.schemas.common import HealthResponse
from api.core.config import settings

router = APIRouter()


@router.get("/", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint
    
    Returns basic service status and version information
    """
    return HealthResponse(
        status="ok",
        service="FinSecAI API",
        version=settings.API_VERSION,
        environment=settings.ENVIRONMENT
    )


@router.get("/ready", response_model=HealthResponse)
async def readiness_check() -> HealthResponse:
    """
    Readiness check endpoint
    
    Indicates if service is ready to accept traffic
    """
    return HealthResponse(
        status="ok",
        service="FinSecAI API",
        version=settings.API_VERSION,
        environment=settings.ENVIRONMENT
    )

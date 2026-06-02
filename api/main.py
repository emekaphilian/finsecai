"""
FinSecAI v2 FastAPI Backend
Enterprise AI Fraud + Risk Intelligence Platform

This is the new backbone of the FinSecAI system, replacing the monolithic
Streamlit-based architecture with a proper backend/frontend separation.

Architecture:
- FastAPI Backend (this file) → handles API requests and orchestration
- AI Core (src/) → unchanged, but now wrapped by API services
- Data Layer (upcoming) → PostgreSQL + SQLAlchemy
- Frontend → Streamlit/React consuming this API

Entry Point: uvicorn api.main:app --host 0.0.0.0 --port 8000
"""

import logging
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from api.core.config import settings
from api.core.logging import setup_logging
from api.routes import health, incidents, analysis, reports, auth
from api.database.init_db import init_database, seed_demo_users, seed_sample_transactions, seed_sample_incidents

# Setup logging
logger = setup_logging()


# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage app startup and shutdown events
    """
    # Startup
    logger.info(f"Starting FinSecAI API v{settings.API_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"AI Pipeline: {'Enabled' if settings.ENABLE_AI_PIPELINE else 'Disabled'}")
    
    # Initialize database
    try:
        logger.info("🔧 Initializing database schema...")
        init_database()
        logger.info("✅ Database schema initialized")
        
        logger.info("🌱 Seeding demo data...")
        seed_demo_users()
        seed_sample_transactions()
        seed_sample_incidents()
        logger.info("✅ Demo data seeded")
        
    except Exception as e:
        logger.error(f"❌ Database initialization error: {e}", exc_info=True)
    
    yield
    
    # Shutdown
    logger.info("👋 Shutting down FinSecAI API")


# Create FastAPI application
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request ID middleware
@app.middleware("http")
async def add_request_id_middleware(request: Request, call_next):
    """Add request ID to all requests"""
    request_id = request.headers.get("X-Request-ID", "N/A")
    
    # Add to logger context
    logger.info(f"Request: {request.method} {request.url.path} - ID: {request_id}")
    
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An internal server error occurred"
            }
        }
    )


# Include routers
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(analysis.router, prefix="/analysis", tags=["Analysis"])
app.include_router(incidents.router, prefix="/incidents", tags=["Incidents"])
app.include_router(reports.router, prefix="/reports", tags=["Reports"])


# Root endpoint
@app.get("/")
async def root():
    """Root API endpoint"""
    return {
        "service": settings.API_TITLE,
        "version": settings.API_VERSION,
        "status": "operational",
        "docs_url": "/docs",
        "api_endpoints": {
            "health": "/health",
            "analysis": "/analysis/transaction",
            "incidents": "/incidents",
            "reports": "/reports",
            "auth": "/auth"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        log_level=settings.LOG_LEVEL.lower()
    )

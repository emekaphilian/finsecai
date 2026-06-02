"""
Database configuration and session factory
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import Generator
import logging

from api.core.config import settings

logger = logging.getLogger(__name__)

# SQLAlchemy declarative base
Base = declarative_base()

# Database connection string
# Format: postgresql://username:password@host:port/dbname
if settings.DATABASE_URL:
    DATABASE_URL = settings.DATABASE_URL
else:
    # Default local development setup
    DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/finsecai"

logger.info(f"Database URL: {DATABASE_URL.split('@')[0]}@{DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'localhost'}")

# Create engine
engine = create_engine(
    DATABASE_URL,
    echo=settings.DEBUG,  # Log SQL statements in development
    pool_size=10,
    max_overflow=20
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db() -> Generator:
    """
    Dependency for FastAPI to get database session
    
    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database (create all tables)"""
    logger.info("Initializing database...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully")


def drop_db():
    """Drop all tables (DANGEROUS - dev only)"""
    logger.warning("Dropping all database tables...")
    Base.metadata.drop_all(bind=engine)
    logger.warning("Database tables dropped")

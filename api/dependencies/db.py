"""
Database dependency injection for FastAPI
"""

from sqlalchemy.orm import Session
from api.database import DatabaseManager


def get_db() -> Session:
    """
    Dependency to get database session
    Used in FastAPI route handlers with automatic cleanup
    """
    db = DatabaseManager.get_session()
    try:
        yield db
    finally:
        db.close()

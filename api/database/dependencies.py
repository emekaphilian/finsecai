"""
Database dependency injection for FastAPI
"""

from sqlalchemy.orm import Session
from api.database import get_db
from api.database.repositories import IncidentRepository, UserRepository, ReportRepository


def get_incident_repository(db: Session = None) -> IncidentRepository:
    """Get incident repository instance"""
    if db is None:
        from api.database import DatabaseManager
        db = DatabaseManager.get_session()
    return IncidentRepository(db)


def get_user_repository(db: Session = None) -> UserRepository:
    """Get user repository instance"""
    if db is None:
        from api.database import DatabaseManager
        db = DatabaseManager.get_session()
    return UserRepository(db)


def get_report_repository(db: Session = None) -> ReportRepository:
    """Get report repository instance"""
    if db is None:
        from api.database import DatabaseManager
        db = DatabaseManager.get_session()
    return ReportRepository(db)

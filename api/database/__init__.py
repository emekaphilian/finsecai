"""
Database Configuration and Connection Management
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import NullPool
import logging
from api.core.config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """SQLAlchemy base class for all models"""
    pass


class DatabaseManager:
    """Manages database connections and sessions"""
    
    _engine = None
    _SessionLocal = None
    
    @classmethod
    def get_engine(cls):
        """Get or create database engine"""
        if cls._engine is None:
            # Use database URL from config
            database_url = settings.DATABASE_URL or "sqlite:///./finsecai.db"
            
            logger.info(f"Connecting to database: {database_url.split('://')[0]}")
            
            # SQLite for development, PostgreSQL for production
            if database_url.startswith("sqlite"):
                # SQLite doesn't support connection pooling
                cls._engine = create_engine(
                    database_url,
                    connect_args={"check_same_thread": False},
                    poolclass=NullPool,
                    echo=settings.DEBUG
                )
            else:
                # PostgreSQL with connection pooling
                cls._engine = create_engine(
                    database_url,
                    pool_size=10,
                    max_overflow=20,
                    pool_pre_ping=True,  # Verify connections before using
                    echo=settings.DEBUG
                )
            
            # Setup foreign key support for SQLite
            if database_url.startswith("sqlite"):
                @event.listens_for(cls._engine, "connect")
                def set_sqlite_pragma(dbapi_conn, connection_record):
                    cursor = dbapi_conn.cursor()
                    cursor.execute("PRAGMA foreign_keys=ON")
                    cursor.close()
        
        return cls._engine
    
    @classmethod
    def get_session_factory(cls):
        """Get or create session factory"""
        if cls._SessionLocal is None:
            engine = cls.get_engine()
            cls._SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=engine
            )
        
        return cls._SessionLocal
    
    @classmethod
    def get_session(cls):
        """Get a new database session"""
        SessionLocal = cls.get_session_factory()
        return SessionLocal()
    
    @classmethod
    def create_all_tables(cls):
        """Create all tables in the database"""
        engine = cls.get_engine()
        Base.metadata.create_all(bind=engine)
        logger.info("All database tables created successfully")
    
    @classmethod
    def drop_all_tables(cls):
        """Drop all tables in the database (WARNING: Use carefully!)"""
        engine = cls.get_engine()
        Base.metadata.drop_all(bind=engine)
        logger.warning("All database tables dropped")
    
    @classmethod
    def close(cls):
        """Close database connections"""
        if cls._engine is not None:
            cls._engine.dispose()
            logger.info("Database connections closed")


# Default session dependency for FastAPI
def get_db():
    """FastAPI dependency to get database session"""
    session = DatabaseManager.get_session()
    try:
        yield session
    finally:
        session.close()

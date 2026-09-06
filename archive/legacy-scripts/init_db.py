#!/usr/bin/env python3
"""
FinSecAI Database Initialization Script
Sets up PostgreSQL and creates schema
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.core import engine, init_db, Base
from database.models import (
    User, UserRole, Incident, IncidentStatus, IncidentSeverity,
    Transaction, TransactionStatus, RiskScore, Report, AuditLog, AuditAction
)
from api.core.security import get_password_hash
from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_tables():
    """Create all database tables"""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database tables created")


def create_default_users():
    """Create default admin user"""
    logger.info("Creating default users...")
    
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Check if admin already exists
        from sqlalchemy import select
        existing = db.query(User).filter(User.username == "admin").first()
        
        if existing:
            logger.info("⚠️  Admin user already exists")
            return
        
        # Create admin user
        admin_user = User(
            username="admin",
            email="admin@finsecai.dev",
            password_hash=get_password_hash("admin123"),
            full_name="System Administrator",
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True
        )
        
        # Create analyst user
        analyst_user = User(
            username="analyst",
            email="analyst@finsecai.dev",
            password_hash=get_password_hash("analyst123"),
            full_name="Security Analyst",
            role=UserRole.ANALYST_TIER1,
            is_active=True,
            is_verified=True
        )
        
        db.add(admin_user)
        db.add(analyst_user)
        db.commit()
        
        logger.info("✅ Default users created")
        logger.info("  - admin / admin123")
        logger.info("  - analyst / analyst123")
        
    except Exception as e:
        logger.error(f"❌ Error creating default users: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def verify_connection():
    """Verify database connection"""
    logger.info("Verifying database connection...")
    
    try:
        with engine.connect() as connection:
            result = connection.execute("SELECT 1")
            logger.info("✅ Database connection successful")
            return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        logger.error("Make sure PostgreSQL is running and DATABASE_URL is set correctly")
        return False


def main():
    """Main initialization workflow"""
    print("\n" + "="*60)
    print("🗄️  FinSecAI Database Initialization")
    print("="*60 + "\n")
    
    # Verify connection
    if not verify_connection():
        sys.exit(1)
    
    # Create tables
    try:
        create_tables()
    except Exception as e:
        logger.error(f"❌ Failed to create tables: {e}")
        sys.exit(1)
    
    # Create default users
    try:
        create_default_users()
    except Exception as e:
        logger.error(f"❌ Failed to create default users: {e}")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("✅ Database initialization complete!")
    print("="*60)
    print("\nNext steps:")
    print("1. Start the API: python -m uvicorn api.main:app --reload")
    print("2. Access documentation: http://localhost:8000/docs")
    print("3. Login with credentials:")
    print("   - admin / admin123")
    print("   - analyst / analyst123")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()

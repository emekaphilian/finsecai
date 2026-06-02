"""
Database Initialization and Migration Management
"""

import logging
from pathlib import Path
from api.database import DatabaseManager, Base
from api.database.models import User, Transaction, Incident, RiskScore, Report, AuditLog
from api.core.security import get_password_hash

logger = logging.getLogger(__name__)


def init_database():
    """Initialize database schema"""
    logger.info("Initializing database schema...")
    DatabaseManager.create_all_tables()
    logger.info("✅ Database schema initialized")


def seed_demo_users():
    """Seed demo users for development"""
    session = DatabaseManager.get_session()
    
    try:
        # Check if users already exist
        existing_count = session.query(User).count()
        if existing_count > 0:
            logger.info("Demo users already exist, skipping seed")
            return
        
        demo_users = [
            {
                "id": "admin_001",
                "username": "admin",
                "email": "admin@finsecai.local",
                "full_name": "Admin User",
                "hashed_password": get_password_hash("admin123"),
                "role": "admin",
                "is_active": True
            },
            {
                "id": "analyst_001",
                "username": "analyst",
                "email": "analyst@finsecai.local",
                "full_name": "Security Analyst",
                "hashed_password": get_password_hash("analyst123"),
                "role": "analyst",
                "is_active": True
            },
            {
                "id": "viewer_001",
                "username": "viewer",
                "email": "viewer@finsecai.local",
                "full_name": "Report Viewer",
                "hashed_password": get_password_hash("viewer123"),
                "role": "readonly",
                "is_active": True
            }
        ]
        
        for user_data in demo_users:
            user = User(**user_data)
            session.add(user)
        
        session.commit()
        logger.info(f"✅ Seeded {len(demo_users)} demo users")
        
    except Exception as e:
        session.rollback()
        logger.error(f"❌ Error seeding demo users: {str(e)}")
    finally:
        session.close()


def seed_sample_transactions():
    """Seed sample transactions for development"""
    import random
    from datetime import datetime, timedelta
    
    session = DatabaseManager.get_session()
    
    try:
        # Check if transactions already exist
        existing_count = session.query(Transaction).count()
        if existing_count > 0:
            logger.info("Sample transactions already exist, skipping seed")
            return
        
        transactions = []
        for i in range(50):
            transaction = Transaction(
                id=f"TXN-{10000+i}",
                user_id=f"USER-{random.randint(1, 10):04d}",
                amount=random.uniform(10, 10000),
                currency="USD",
                country=random.choice(["US", "UK", "CA", "AU", "JP"]),
                merchant=f"Merchant-{random.randint(1, 100)}",
                merchant_category=random.choice(["5411", "5412", "5300", "6211"]),
                device_id=f"DEV-{random.randint(1, 50):05d}",
                ip_address=f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}",
                created_at=datetime.utcnow() - timedelta(hours=random.randint(1, 168)),
                metadata={"source": "sample"}
            )
            transactions.append(transaction)
        
        session.add_all(transactions)
        session.commit()
        logger.info(f"✅ Seeded {len(transactions)} sample transactions")
        
    except Exception as e:
        session.rollback()
        logger.error(f"❌ Error seeding sample transactions: {str(e)}")
    finally:
        session.close()


def seed_sample_incidents():
    """Seed sample incidents for development"""
    import random
    from datetime import datetime, timedelta
    
    session = DatabaseManager.get_session()
    
    try:
        # Check if incidents already exist
        existing_count = session.query(Incident).count()
        if existing_count > 0:
            logger.info("Sample incidents already exist, skipping seed")
            return
        
        # Get sample transactions to link to
        transactions = session.query(Transaction).all()
        if not transactions:
            logger.warning("No transactions found to link incidents to")
            return
        
        incidents = []
        for i in range(20):
            txn = random.choice(transactions)
            incident = Incident(
                id=f"INC-{20000+i}",
                transaction_id=txn.id,
                user_id=txn.user_id,
                status=random.choice(["open", "investigating", "resolved"]),
                severity=random.choice(["low", "medium", "high", "critical"]),
                description=f"Sample incident {i}: Automated test data",
                risk_score=random.uniform(0.1, 0.95),
                confidence=random.uniform(0.5, 0.99),
                evidence_coverage=random.uniform(0.4, 1.0),
                explanation="Automated sample incident for testing",
                governance_flags=["LOW_EVIDENCE"] if random.random() < 0.3 else [],
                created_at=datetime.utcnow() - timedelta(hours=random.randint(1, 168))
            )
            incidents.append(incident)
        
        session.add_all(incidents)
        session.commit()
        logger.info(f"✅ Seeded {len(incidents)} sample incidents")
        
    except Exception as e:
        session.rollback()
        logger.error(f"❌ Error seeding sample incidents: {str(e)}")
    finally:
        session.close()


def reset_database():
    """Drop and recreate all tables (WARNING: Destructive!)"""
    logger.warning("⚠️  RESETTING DATABASE - ALL DATA WILL BE LOST")
    DatabaseManager.drop_all_tables()
    init_database()
    logger.info("✅ Database reset complete")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Initialize database
    init_database()
    
    # Seed demo data
    seed_demo_users()
    seed_sample_transactions()
    seed_sample_incidents()
    
    logger.info("✅ Database initialization and seeding complete")

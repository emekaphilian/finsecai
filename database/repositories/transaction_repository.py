"""
Transaction repository - Transaction database operations
"""

from sqlalchemy.orm import Session
from typing import Optional, List
import uuid
from datetime import datetime

from database.models import Transaction, TransactionStatus


class TransactionRepository:
    """Repository for transaction operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_transaction(
        self,
        transaction_id: str,
        user_id: str,
        amount: float,
        currency: str,
        country: str,
        merchant: Optional[str] = None,
        merchant_category: Optional[str] = None,
        device_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> Transaction:
        """Create a new transaction record"""
        transaction = Transaction(
            transaction_id=transaction_id,
            user_id=user_id,
            amount=amount,
            currency=currency,
            country=country,
            merchant=merchant,
            merchant_category=merchant_category,
            device_id=device_id,
            ip_address=ip_address,
            metadata=metadata or {},
            status=TransactionStatus.PENDING
        )
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        return transaction
    
    def get_transaction_by_id(self, transaction_id: str) -> Optional[Transaction]:
        """Get transaction by transaction_id"""
        return self.db.query(Transaction).filter(
            Transaction.transaction_id == transaction_id
        ).first()
    
    def list_transactions(
        self,
        user_id: Optional[str] = None,
        status: Optional[TransactionStatus] = None,
        skip: int = 0,
        limit: int = 20
    ) -> tuple:
        """List transactions with filters - returns (transactions, total_count)"""
        query = self.db.query(Transaction)
        
        if user_id:
            query = query.filter(Transaction.user_id == user_id)
        if status:
            query = query.filter(Transaction.status == status)
        
        total = query.count()
        transactions = query.order_by(Transaction.created_at.desc()).offset(skip).limit(limit).all()
        
        return transactions, total
    
    def update_transaction(
        self,
        transaction_id: str,
        risk_score: Optional[float] = None,
        risk_level: Optional[str] = None,
        status: Optional[TransactionStatus] = None,
        incident_id: Optional[uuid.UUID] = None
    ) -> Optional[Transaction]:
        """Update transaction with analysis results"""
        transaction = self.get_transaction_by_id(transaction_id)
        if not transaction:
            return None
        
        if risk_score is not None:
            transaction.risk_score = risk_score
        if risk_level:
            transaction.risk_level = risk_level
        if status:
            transaction.status = status
        if incident_id:
            transaction.incident_id = incident_id
        
        transaction.analyzed_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(transaction)
        return transaction

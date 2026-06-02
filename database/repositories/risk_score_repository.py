"""
Risk Score repository - Risk history database operations
"""

from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from database.models import RiskScore


class RiskScoreRepository:
    """Repository for risk score operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_risk_score(
        self,
        transaction_id: str,
        user_id: str,
        risk_score: float,
        risk_level: str,
        confidence: float,
        evidence_coverage: float,
        explanation: Optional[str] = None,
        governance_flags: Optional[list] = None,
        model_name: Optional[str] = None,
        model_version: Optional[str] = None
    ) -> RiskScore:
        """Create a new risk score record"""
        score = RiskScore(
            transaction_id=transaction_id,
            user_id=user_id,
            risk_score=risk_score,
            risk_level=risk_level,
            confidence=confidence,
            evidence_coverage=evidence_coverage,
            explanation=explanation,
            governance_flags=governance_flags or [],
            model_name=model_name,
            model_version=model_version
        )
        self.db.add(score)
        self.db.commit()
        self.db.refresh(score)
        return score
    
    def get_risk_scores_for_transaction(self, transaction_id: str) -> List[RiskScore]:
        """Get all risk scores for a transaction"""
        return self.db.query(RiskScore).filter(
            RiskScore.transaction_id == transaction_id
        ).order_by(RiskScore.created_at.desc()).all()
    
    def get_risk_scores_for_user(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 20
    ) -> tuple:
        """Get risk scores for a user - returns (scores, total_count)"""
        query = self.db.query(RiskScore).filter(RiskScore.user_id == user_id)
        total = query.count()
        scores = query.order_by(RiskScore.created_at.desc()).offset(skip).limit(limit).all()
        return scores, total

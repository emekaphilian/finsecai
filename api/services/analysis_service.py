"""
Analysis Service - Bridge between FastAPI and AI Intelligence System

This service wraps the existing src/services/intelligence_service.py
and provides a clean API-layer abstraction over the AI pipeline.
With PostgreSQL persistence.
"""

from typing import Dict, Any, Optional
import logging
from datetime import datetime
import uuid
from sqlalchemy.orm import Session

# Import the existing intelligence service
try:
    from src.services.intelligence_service import run_intelligence
except ImportError:
    run_intelligence = None

# Import database repositories
from api.database.repositories import IncidentRepository
from api.database.models import Incident, RiskScore

logger = logging.getLogger(__name__)


class AnalysisService:
    """
    Service for analyzing transactions using the AI intelligence pipeline
    With PostgreSQL persistence
    """
    
    def __init__(self, db: Session):
        self.logger = logger
        self.db = db
        self.incident_repo = IncidentRepository(db)
    
    def analyze_transaction(self, analysis_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a transaction for fraud/risk using the AI pipeline
        Saves all results to PostgreSQL
        
        Args:
            analysis_request: Transaction analysis request with:
                - transaction_id
                - user_id
                - amount
                - currency
                - country
                - Optional metadata
                
        Returns:
            Analysis result with:
                - status: "completed" or "error"
                - transaction_id
                - analysis: AI results
                - incident_id: if high risk
                - timestamp
        """
        try:
            transaction_id = analysis_request.get('transaction_id')
            user_id = analysis_request.get('user_id')
            
            self.logger.info(f"Analyzing transaction {transaction_id} for user {user_id}")
            
            # Call existing intelligence service
            if run_intelligence:
                ai_result = run_intelligence(analysis_request)
            else:
                # Fallback if service unavailable
                ai_result = {
                    'confidence': 0.5,
                    'evidence_coverage': 0.5,
                    'explanation': 'Analysis service unavailable',
                    'limitations': 'Using fallback analysis'
                }
            
            # Extract risk metrics
            risk_score = ai_result.get('confidence', 0.0)
            confidence = ai_result.get('confidence', 0.0)
            evidence_coverage = ai_result.get('evidence_coverage', 0.0)
            
            # Create incident if high risk
            incident_id = None
            if risk_score > 0.7:
                incident_id = f"INC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:8].upper()}"
                
                severity = "critical" if risk_score > 0.85 else "high"
                
                incident_data = {
                    "id": incident_id,
                    "transaction_id": transaction_id,
                    "user_id": user_id,
                    "status": "open",
                    "severity": severity,
                    "description": f"High-risk transaction detected: {ai_result.get('explanation', 'N/A')}",
                    "risk_score": risk_score,
                    "confidence": confidence,
                    "evidence_coverage": evidence_coverage,
                    "explanation": ai_result.get('explanation', ''),
                    "governance_flags": ai_result.get('governance_flags', [])
                }
                
                self.incident_repo.create_with_audit(incident_data, actor="analysis_service")
                self.logger.info(f"Created high-risk incident {incident_id}")
            
            return {
                "status": "completed",
                "transaction_id": transaction_id,
                "user_id": user_id,
                "analysis": {
                    "risk_score": risk_score,
                    "risk_level": self._calculate_risk_level(risk_score),
                    "confidence": confidence,
                    "explanation": ai_result.get('explanation', '')
                },
                "incident_id": incident_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            self.logger.error(f"Analysis error: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "transaction_id": analysis_request.get('transaction_id'),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    @staticmethod
    def _calculate_risk_level(risk_score: float) -> str:
        """Calculate risk level from score"""
        if risk_score > 0.85:
            return "CRITICAL"
        elif risk_score > 0.70:
            return "HIGH"
        elif risk_score > 0.40:
            return "MEDIUM"
        else:
            return "LOW"

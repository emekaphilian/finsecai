"""
Transaction Analysis Request/Response schemas
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime


class AnalysisRequest(BaseModel):
    """Transaction analysis request payload"""
    
    transaction_id: str = Field(..., description="Unique transaction identifier")
    user_id: str = Field(..., description="User account identifier")
    amount: float = Field(..., gt=0, description="Transaction amount (must be positive)")
    currency: str = Field(default="USD", description="ISO 4217 currency code")
    country: str = Field(..., description="Transaction country")
    merchant: Optional[str] = Field(None, description="Merchant name")
    merchant_category: Optional[str] = Field(None, description="Merchant category code")
    device_id: Optional[str] = Field(None, description="Device fingerprint")
    ip_address: Optional[str] = Field(None, description="Client IP address")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    
    class Config:
        example = {
            "transaction_id": "TXN-2024-001",
            "user_id": "USER-123",
            "amount": 5000.00,
            "currency": "USD",
            "country": "US",
            "merchant": "Premium Retailer",
            "merchant_category": "5411",
            "metadata": {"device_type": "mobile", "app_version": "2.1.0"}
        }


class AnalysisResult(BaseModel):
    """Analysis result from AI pipeline"""
    
    explanation: str = Field(..., description="Human-readable risk explanation")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
    evidence_coverage: float = Field(..., ge=0.0, le=1.0, description="Evidence coverage (0-1)")
    governance_flags: list = Field(default_factory=list, description="Compliance/governance flags")
    analysis_status: str = Field(default="success", description="Analysis status")
    risk_score: Optional[float] = Field(None, ge=0.0, le=100.0, description="Risk score 0-100")
    risk_level: Optional[str] = Field(None, description="Risk level: LOW, MEDIUM, HIGH, CRITICAL")


class AnalysisResponse(BaseModel):
    """Transaction analysis response"""
    
    status: str = Field(default="completed", description="Response status")
    transaction_id: str = Field(..., description="Transaction ID being analyzed")
    analysis: AnalysisResult = Field(..., description="Analysis results")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    incident_id: Optional[str] = Field(None, description="Associated incident ID if created")
    
    class Config:
        example = {
            "status": "completed",
            "transaction_id": "TXN-2024-001",
            "analysis": {
                "explanation": "Risk detected for USER-123 - Amount: $5000.00",
                "confidence": 0.75,
                "evidence_coverage": 0.80,
                "governance_flags": [],
                "analysis_status": "success",
                "risk_score": 68.5,
                "risk_level": "HIGH"
            },
            "timestamp": "2024-06-02T10:30:00",
            "incident_id": "INC-2024-001"
        }

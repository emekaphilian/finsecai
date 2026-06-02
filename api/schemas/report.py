"""
Report schemas
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime


class ReportRequest(BaseModel):
    """Generate report request"""
    
    incident_id: str = Field(..., description="Incident to report on")
    format: str = Field(default="pdf", description="Report format: pdf, json, html")
    include_evidence: bool = Field(default=True, description="Include evidence details")
    include_timeline: bool = Field(default=True, description="Include event timeline")


class ReportResponse(BaseModel):
    """Report response"""
    
    report_id: str = Field(..., description="Unique report ID")
    incident_id: str = Field(...)
    format: str
    status: str = Field(default="completed", description="Generation status")
    created_at: datetime
    report_url: Optional[str] = Field(None, description="URL to download report")
    summary: Optional[Dict[str, Any]] = None
    
    class Config:
        example = {
            "report_id": "RPT-2024-001",
            "incident_id": "INC-2024-001",
            "format": "pdf",
            "status": "completed",
            "created_at": "2024-06-02T10:30:00",
            "report_url": "/api/reports/download/RPT-2024-001",
            "summary": {
                "title": "Security Incident Analysis Report",
                "severity": "high",
                "risk_score": 85.5
            }
        }

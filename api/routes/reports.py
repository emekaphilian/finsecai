"""
Report Generation Routes
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.orm import Session
import logging
from typing import Optional
from api.schemas.report import ReportRequest, ReportResponse
from api.services.report_service import ReportService
from api.dependencies.db import get_db

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/generate", response_model=ReportResponse)
async def generate_report(
    payload: ReportRequest,
    db: Session = Depends(get_db)
) -> ReportResponse:
    """
    Generate a report for an incident
    
    **Request Body:**
    - `incident_id`: Incident to report on
    - `format`: Report format (pdf, json, html) - default: pdf
    - `include_evidence`: Include evidence details - default: true
    - `include_timeline`: Include event timeline - default: true
    
    **Response:**
    - `report_id`: Generated report ID
    - `report_url`: URL to download report
    - `status`: Generation status
    - `summary`: Report summary data
    """
    try:
        service = ReportService(db)
        report = service.generate_report(
            incident_id=payload.incident_id,
            format=payload.format,
            include_evidence=payload.include_evidence,
            include_timeline=payload.include_timeline
        )
        
        return ReportResponse(**report)
        
    except Exception as e:
        logger.error(f"Failed to generate report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate report"
        )


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: str,
    db: Session = Depends(get_db)
) -> ReportResponse:
    """
    Retrieve report metadata
    
    **Path Parameters:**
    - `report_id`: Report identifier
    
    **Response:** Report metadata
    """
    service = ReportService(db)
    report = service.get_report(report_id)
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    return ReportResponse(**report)


@router.get("/")
async def list_reports(
    incident_id: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
) -> dict:
    """
    List generated reports
    
    **Query Parameters:**
    - `incident_id`: Filter by incident ID (optional)
    - `limit`: Pagination limit
    - `offset`: Pagination offset
    
    **Response:** List of reports
    """
    service = ReportService(db)
    result = service.list_reports(
        incident_id=incident_id,
        limit=limit,
        offset=offset
    )
    
    return {
        "status": "success",
        "data": result["reports"],
        "pagination": result["pagination"]
        }
    }

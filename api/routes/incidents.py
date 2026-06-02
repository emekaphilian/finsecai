"""
Incident Routes - Incident management endpoints
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.orm import Session
import logging
from typing import Optional

from api.schemas.incident import (
    IncidentCreateRequest, IncidentUpdateRequest, IncidentResponse
)
from api.services.incident_service import IncidentService
from api.dependencies.db import get_db

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=dict)
async def create_incident(
    payload: IncidentCreateRequest,
    db: Session = Depends(get_db)
) -> dict:
    """
    Create a new incident
    
    **Request Body:**
    - `transaction_id`: Associated transaction ID
    - `user_id`: Affected user ID
    - `severity`: Incident severity (low, medium, high, critical)
    - `description`: Incident description
    - `tags`: Optional tags (array)
    - `metadata`: Optional metadata (object)
    
    **Response:**
    - `incident_id`: Created incident ID
    - `status`: "created"
    """
    try:
        service = IncidentService(db)
        incident_id = service.create_incident(
            transaction_id=payload.transaction_id,
            user_id=payload.user_id,
            severity=payload.severity,
            description=payload.description,
            tags=payload.tags,
            metadata=payload.metadata
        )
        
        return {
            "status": "created",
            "incident_id": incident_id
        }
        
    except Exception as e:
        logger.error(f"Failed to create incident: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create incident"
        )


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: str,
    db: Session = Depends(get_db)
) -> IncidentResponse:
    """
    Retrieve an incident by ID
    
    **Path Parameters:**
    - `incident_id`: Incident identifier
    
    **Response:** Incident details
    """
    service = IncidentService(db)
    incident = service.get_incident(incident_id)
    
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found"
        )
    
    return IncidentResponse(**incident)


@router.get("/", response_model=dict)
async def list_incidents(
    status: Optional[str] = Query(None, description="Filter by status"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
) -> dict:
    """
    List incidents with optional filtering
    
    **Query Parameters:**
    - `status`: Filter by status (open, in_progress, resolved, closed, escalated)
    - `severity`: Filter by severity (low, medium, high, critical)
    - `limit`: Pagination limit (1-100, default 20)
    - `offset`: Pagination offset (default 0)
    
    **Response:** List of incidents with pagination info
    """
    service = IncidentService(db)
    result = service.list_incidents(
        status=status,
        severity=severity,
        limit=limit,
        offset=offset
    )
    
    return {
        "status": "success",
        "data": result["incidents"],
        "pagination": result["pagination"]
    }


@router.patch("/{incident_id}", response_model=IncidentResponse)
async def update_incident(
    incident_id: str,
    payload: IncidentUpdateRequest,
    db: Session = Depends(get_db)
) -> IncidentResponse:
    """
    Update an existing incident
    
    **Path Parameters:**
    - `incident_id`: Incident identifier
    
    **Request Body:**
    - `status`: New status (optional)
    - `severity`: New severity (optional)
    - `description`: New description (optional)
    - `resolution_notes`: Resolution notes (optional)
    
    **Response:** Updated incident details
    """
    service = IncidentService(db)
    updated = service.update_incident(
        incident_id=incident_id,
        status=payload.status,
        severity=payload.severity,
        description=payload.description,
        resolution_notes=payload.resolution_notes
    )
    
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found"
        )
    
    return IncidentResponse(**updated)


@router.post("/{incident_id}/escalate", response_model=IncidentResponse)
async def escalate_incident(
    incident_id: str,
    db: Session = Depends(get_db)
) -> IncidentResponse:
    """
    Escalate an incident to a higher severity level
    
    **Path Parameters:**
    - `incident_id`: Incident identifier
    
    **Response:** Updated incident with escalated status/severity
    """
    service = IncidentService(db)
    escalated = service.escalate_incident(incident_id)
    
    if not escalated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found"
        )
    
    return IncidentResponse(**escalated)

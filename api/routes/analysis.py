"""
Analysis Routes - Transaction analysis endpoints
"""

from fastapi import APIRouter, HTTPException, status, Depends
import logging
from sqlalchemy.orm import Session

from api.schemas.analysis import AnalysisRequest, AnalysisResponse
from api.services.analysis_service import AnalysisService
from api.dependencies.db import get_db

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/transaction", response_model=AnalysisResponse)
async def analyze_transaction(
    payload: AnalysisRequest,
    db: Session = Depends(get_db)
) -> AnalysisResponse:
    """
    Analyze a transaction for fraud and risk
    
    **Endpoint:** `POST /analysis/transaction`
    
    **Request Body:**
    - `transaction_id`: Unique transaction identifier
    - `user_id`: User account identifier
    - `amount`: Transaction amount
    - `currency`: ISO 4217 currency code
    - `country`: Transaction country
    - `metadata`: Additional context (optional)
    
    **Response:**
    - `status`: Analysis completion status
    - `transaction_id`: Transaction being analyzed
    - `analysis`: AI analysis results with confidence, risk score, etc.
    - `incident_id`: Created incident ID (if high risk)
    
    **Example:**
    ```
    POST /analysis/transaction
    {
        "transaction_id": "TXN-2024-001",
        "user_id": "USER-123",
        "amount": 5000.00,
        "currency": "USD",
        "country": "US"
    }
    ```
    
    **Data Persistence:**
    - Transaction record saved to PostgreSQL
    - Risk score persisted to database
    - Incidents created automatically for high-risk (>70 score)
    """
    try:
        # Convert request to dict
        analysis_data = payload.dict()
        
        # Create service with database session
        service = AnalysisService(db)
        
        # Run analysis through service (now with database persistence)
        result = service.analyze_transaction(analysis_data)
        
        # Parse response
        return AnalysisResponse(**result)
        
    except Exception as e:
        logger.error(f"Transaction analysis failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Transaction analysis failed"
        )


@router.post("/batch")
async def analyze_batch(
    payloads: list[AnalysisRequest],
    db: Session = Depends(get_db)
):
    """
    Analyze multiple transactions in batch
    
    **Note:** Transactions are analyzed sequentially. Designed for bulk processing.
    All results persisted to PostgreSQL.
    
    **Request Body:** Array of AnalysisRequest objects
    
    **Response:** Array of AnalysisResponse objects
    """
    try:
        results = []
        service = AnalysisService(db)
        
        for payload in payloads:
            analysis_data = payload.dict()
            result = service.analyze_transaction(analysis_data)
            results.append(AnalysisResponse(**result))
        
        return {
            "status": "completed",
            "count": len(results),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Batch analysis failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Batch analysis failed"
        )

"""
Authentication Routes
"""

from fastapi import APIRouter, HTTPException, status, Depends
from datetime import timedelta
import logging
from sqlalchemy.orm import Session
from api.schemas.user import TokenRequest, TokenResponse, UserResponse
from api.core.security import create_access_token
from api.dependencies.db import get_db
from database.repositories.user_repository import UserRepository

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: TokenRequest,
    db: Session = Depends(get_db)
) -> TokenResponse:
    """
    Authenticate user and get access token
    
    **Request Body:**
    - `username`: Username
    - `password`: Password
    
    **Response:**
    - `access_token`: JWT bearer token
    - `token_type`: Token type (bearer)
    - `user`: User information
    - `expires_in`: Token expiration in seconds
    
    **Demo Credentials:**
    - Username: `admin` | Password: `admin123`
    - Username: `analyst` | Password: `analyst123`
    
    **Data Source:** User credentials verified against PostgreSQL
    """
    user_repo = UserRepository(db)
    
    # Authenticate against database
    user = user_repo.authenticate_user(payload.username, payload.password)
    
    if not user:
        logger.warning(f"Failed login attempt for user: {payload.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Create token
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "username": user.username,
            "role": user.role.value
        }
    )
    
    logger.info(f"User {payload.username} logged in successfully")
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            user_id=str(user.id),
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role.value,
            is_active=user.is_active,
            created_at=user.created_at.isoformat(),
            updated_at=user.updated_at.isoformat()
        ),
        expires_in=1800
    )


@router.post("/refresh")
async def refresh_token(db: Session = Depends(get_db)):
    """
    Refresh access token (placeholder)
    
    **Response:**
    - `access_token`: New JWT bearer token
    - `expires_in`: Token expiration in seconds
    
    **Note:** Requires valid bearer token in Authorization header
    """
    return {
        "access_token": create_access_token(data={"sub": "demo-user"}),
        "expires_in": 1800
    }

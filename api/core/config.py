"""
API Configuration - Environment settings, feature flags, constants
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """FastAPI application settings with environment variable support"""
    
    # API Meta
    API_VERSION: str = "2.0.0"
    API_TITLE: str = "FinSecAI API"
    API_DESCRIPTION: str = "Enterprise AI Fraud + Risk Intelligence Platform"
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = ENVIRONMENT == "development"
    
    # Server
    SERVER_HOST: str = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", "8000"))
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database Configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./finsecai_dev.db"  # Development default
    )
    
    # AI System
    ENABLE_AI_PIPELINE: bool = True
    RAG_ENABLED: bool = True
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

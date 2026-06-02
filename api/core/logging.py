"""
Logging configuration for FastAPI application
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from api.core.config import settings


def setup_logging() -> None:
    """Configure structured logging for the application"""
    
    # Create logger
    logger = logging.getLogger("finsecai")
    logger.setLevel(settings.LOG_LEVEL)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(settings.LOG_LEVEL)
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        "logs/api.log",
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(settings.LOG_LEVEL)
    
    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)

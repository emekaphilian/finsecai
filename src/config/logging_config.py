"""
Production Logging Configuration
Comprehensive logging with structured JSON output for centralized log aggregation
"""

import logging
import json
from datetime import datetime
from pythonjsonlogger import jsonlogger
import os


def setup_production_logging(log_dir: str = '/var/log/finsecai', 
                            log_level: str = 'INFO') -> None:
    """
    Configure production-grade logging with multiple outputs
    
    Args:
        log_dir: Directory for log files
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    
    # Create log directory
    os.makedirs(log_dir, exist_ok=True)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    
    # Remove default handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Formatters
    json_formatter = jsonlogger.JsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s',
        timestamp=True
    )
    
    standard_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # ===== FILE HANDLERS =====
    
    # Main application log (JSON format for ELK)
    app_handler = logging.FileHandler(os.path.join(log_dir, 'application.log'))
    app_handler.setFormatter(json_formatter)
    app_handler.setLevel(logging.INFO)
    root_logger.addHandler(app_handler)
    
    # Error log (for quick reference)
    error_handler = logging.FileHandler(os.path.join(log_dir, 'errors.log'))
    error_handler.setFormatter(standard_formatter)
    error_handler.setLevel(logging.ERROR)
    root_logger.addHandler(error_handler)
    
    # Performance metrics
    perf_handler = logging.FileHandler(os.path.join(log_dir, 'performance.log'))
    perf_handler.setFormatter(json_formatter)
    perf_handler.setLevel(logging.DEBUG)
    root_logger.addHandler(perf_handler)
    
    # Security events
    security_handler = logging.FileHandler(os.path.join(log_dir, 'security.log'))
    security_handler.setFormatter(json_formatter)
    security_handler.setLevel(logging.WARNING)
    root_logger.addHandler(security_handler)
    
    # Audit trail (permanent record)
    audit_handler = logging.FileHandler(os.path.join(log_dir, 'audit.log'))
    audit_handler.setFormatter(json_formatter)
    audit_handler.setLevel(logging.INFO)
    root_logger.addHandler(audit_handler)
    
    # ===== CONSOLE HANDLER =====
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(standard_formatter)
    console_handler.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    
    # ===== LOGGER-SPECIFIC CONFIGURATION =====
    
    # Quiet down noisy loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('boto3').setLevel(logging.WARNING)
    logging.getLogger('botocore').setLevel(logging.WARNING)
    
    # Streamlit logger
    logging.getLogger('streamlit').setLevel(logging.INFO)
    
    # App-specific loggers
    logging.getLogger('finsecai').setLevel(getattr(logging, log_level))
    logging.getLogger('finsecai.security').setLevel(logging.DEBUG)
    logging.getLogger('finsecai.pipeline').setLevel(logging.INFO)
    logging.getLogger('finsecai.database').setLevel(logging.INFO)


class StructuredLogger:
    """Wrapper for structured logging with context"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.context = {}
    
    def set_context(self, **kwargs):
        """Set context for all subsequent logs"""
        self.context.update(kwargs)
    
    def clear_context(self):
        """Clear context"""
        self.context = {}
    
    def _format_message(self, message: str, **kwargs) -> dict:
        """Format message with context"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'message': message,
            **self.context,
            **kwargs
        }
        return log_entry
    
    def debug(self, message: str, **kwargs):
        self.logger.debug(json.dumps(self._format_message(message, **kwargs)))
    
    def info(self, message: str, **kwargs):
        self.logger.info(json.dumps(self._format_message(message, **kwargs)))
    
    def warning(self, message: str, **kwargs):
        self.logger.warning(json.dumps(self._format_message(message, **kwargs)))
    
    def error(self, message: str, **kwargs):
        self.logger.error(json.dumps(self._format_message(message, **kwargs)))
    
    def critical(self, message: str, **kwargs):
        self.logger.critical(json.dumps(self._format_message(message, **kwargs)))


# Initialize logging on import
setup_production_logging()

# Create structured loggers for different components
logger_app = StructuredLogger('finsecai.app')
logger_security = StructuredLogger('finsecai.security')
logger_pipeline = StructuredLogger('finsecai.pipeline')
logger_database = StructuredLogger('finsecai.database')
logger_api = StructuredLogger('finsecai.api')
logger_audit = StructuredLogger('finsecai.audit')

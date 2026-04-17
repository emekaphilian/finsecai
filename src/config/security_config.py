"""
Production Security Configuration
Implements rate limiting, API security, CORS, and request validation
"""

import os
from dataclasses import dataclass
from typing import List, Dict, Any
from datetime import timedelta
import hashlib
import hmac

from functools import wraps
import time
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class SecurityConfig:
    """Global security configuration"""
    
    # API Security
    API_KEY_HEADER = 'X-API-Key'
    JWT_SECRET = os.getenv('JWT_SECRET', 'change-me-in-production')
    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRATION = timedelta(hours=24)
    
    # CORS Configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'https://localhost:3000').split(',')
    CORS_ALLOW_CREDENTIALS = True
    CORS_ALLOW_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
    CORS_ALLOW_HEADERS = ['*']
    
    # Rate Limiting
    RATE_LIMIT_ENABLED = True
    RATE_LIMIT_PER_MINUTE_USER = 100
    RATE_LIMIT_PER_MINUTE_IP = 500
    RATE_LIMIT_PER_MINUTE_GLOBAL = 10000
    
    # Per-endpoint limits
    RATE_LIMITS = {
        '/api/analyze': 10,  # 10 per minute
        '/api/generate-report': 5,  # 5 per minute
        '/api/bulk-upload': 20,  # 20 per minute
        '/api/export': 30,  # 30 per minute
    }
    
    # Session Security
    SESSION_TIMEOUT = timedelta(hours=8)
    MAX_SESSIONS_PER_USER = 5
    REQUIRE_HTTPS = True
    
    # Password Policy
    MIN_PASSWORD_LENGTH = 12
    REQUIRE_SPECIAL_CHARS = True
    REQUIRE_NUMBERS = True
    REQUIRE_UPPERCASE = True
    PASSWORD_EXPIRY_DAYS = 90
    PASSWORD_HISTORY_COUNT = 5
    
    # Data Protection
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', 'change-me-in-production')
    ENABLE_PII_REDACTION = True
    ENABLE_DATA_MASKING = True
    AUDIT_LOG_RETENTION_DAYS = 365
    
    # Security Headers
    SECURITY_HEADERS = {
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'",
        'Referrer-Policy': 'strict-origin-when-cross-origin',
    }
    
    # IP Whitelist/Blacklist
    IP_WHITELIST = os.getenv('IP_WHITELIST', '').split(',') if os.getenv('IP_WHITELIST') else []
    IP_BLACKLIST = os.getenv('IP_BLACKLIST', '').split(',') if os.getenv('IP_BLACKLIST') else []
    
    # File Upload Security
    MAX_UPLOAD_SIZE_MB = 200
    ALLOWED_UPLOAD_TYPES = ['.csv', '.json', '.xlsx', '.txt']
    SCAN_UPLOADS_FOR_MALWARE = True


class RateLimiter:
    """Per-user, per-IP, and global rate limiter"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.user_buckets = defaultdict(lambda: [])
        self.ip_buckets = defaultdict(lambda: [])
        self.global_bucket = []
    
    def is_allowed(self, user_id: str = None, ip_address: str = None, endpoint: str = None) -> tuple[bool, str]:
        """
        Check if request is allowed based on rate limits.
        Returns: (allowed: bool, reason: str)
        """
        current_time = time.time()
        window = 60  # 1 minute window
        
        # Check per-endpoint limit
        if endpoint and endpoint in self.config.RATE_LIMITS:
            endpoint_limit = self.config.RATE_LIMITS[endpoint]
            if self._check_bucket(self.user_buckets.get(f"{user_id}:{endpoint}", []), 
                                 endpoint_limit, current_time, window):
                return False, f"Rate limit exceeded for {endpoint}"
        
        # Check per-user limit
        if user_id:
            user_bucket = self.user_buckets.get(user_id, [])
            if self._check_bucket(user_bucket, self.config.RATE_LIMIT_PER_MINUTE_USER, 
                                 current_time, window):
                return False, "Rate limit exceeded: too many requests from your account"
            self.user_buckets[user_id].append(current_time)
        
        # Check per-IP limit
        if ip_address:
            ip_bucket = self.ip_buckets.get(ip_address, [])
            if self._check_bucket(ip_bucket, self.config.RATE_LIMIT_PER_MINUTE_IP, 
                                 current_time, window):
                return False, "Rate limit exceeded: too many requests from your IP"
            self.ip_buckets[ip_address].append(current_time)
        
        # Check global limit
        if self._check_bucket(self.global_bucket, self.config.RATE_LIMIT_PER_GLOBAL, 
                             current_time, window):
            return False, "System rate limit exceeded"
        self.global_bucket.append(current_time)
        
        return True, ""
    
    @staticmethod
    def _check_bucket(bucket: List[float], limit: int, current_time: float, window: int) -> bool:
        """Check if bucket exceeds limit within time window"""
        # Remove old entries
        bucket[:] = [t for t in bucket if current_time - t < window]
        return len(bucket) >= limit


class APIKeyValidator:
    """Validate API keys and manage API key authentication"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.valid_keys = set(os.getenv('API_KEYS', '').split(',')) if os.getenv('API_KEYS') else set()
    
    def validate_key(self, api_key: str) -> bool:
        """Validate API key format and existence"""
        if not api_key:
            return False
        
        # Check against valid keys
        if api_key in self.valid_keys:
            logger.info(f"API key validated")
            return True
        
        logger.warning(f"Invalid API key attempted")
        return False
    
    def hash_key(self, api_key: str) -> str:
        """Hash API key for storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()


class DataProtection:
    """Implements PII redaction and data masking"""
    
    PII_PATTERNS = {
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'phone': r'\b(\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b',
        'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
        'credit_card': r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
        'ip_address': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
    }
    
    @staticmethod
    def redact_pii(text: str) -> str:
        """Redact PII from text"""
        import re
        
        redacted = text
        for pii_type, pattern in DataProtection.PII_PATTERNS.items():
            redacted = re.sub(pattern, f'[REDACTED_{pii_type.upper()}]', redacted)
        
        return redacted
    
    @staticmethod
    def mask_sensitive_fields(data: Dict[str, Any]) -> Dict[str, Any]:
        """Mask sensitive fields in dictionary"""
        sensitive_fields = [
            'password', 'api_key', 'secret', 'token', 'credit_card',
            'ssn', 'phone', 'email', 'address'
        ]
        
        masked = data.copy()
        for key in sensitive_fields:
            if key in masked:
                masked[key] = '***MASKED***'
        
        return masked


class AuditLogger:
    """Log all user actions and system events for audit trails"""
    
    def __init__(self, log_dir: str = '/var/log/finsecai'):
        self.log_dir = log_dir
        self.logger = logging.getLogger('audit')
        
        # Create audit log file handler
        os.makedirs(log_dir, exist_ok=True)
        handler = logging.FileHandler(os.path.join(log_dir, 'audit.log'))
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def log_user_action(self, user_id: str, action: str, resource: str, 
                       result: str, details: Dict = None):
        """Log user action"""
        message = f"USER_ACTION: user_id={user_id}, action={action}, resource={resource}, result={result}"
        if details:
            message += f", details={details}"
        self.logger.info(message)
    
    def log_api_access(self, user_id: str, endpoint: str, method: str, 
                      status_code: int, response_time_ms: float):
        """Log API access"""
        self.logger.info(
            f"API_ACCESS: user_id={user_id}, endpoint={endpoint}, method={method}, "
            f"status_code={status_code}, response_time_ms={response_time_ms:.2f}"
        )
    
    def log_security_event(self, event_type: str, severity: str, details: Dict):
        """Log security event"""
        self.logger.warning(
            f"SECURITY_EVENT: type={event_type}, severity={severity}, details={details}"
        )
    
    def log_data_access(self, user_id: str, data_type: str, access_type: str, 
                       record_count: int, tenant_id: str = None):
        """Log data access for compliance"""
        self.logger.info(
            f"DATA_ACCESS: user_id={user_id}, data_type={data_type}, access_type={access_type}, "
            f"record_count={record_count}, tenant_id={tenant_id}"
        )


def security_middleware(config: SecurityConfig):
    """Middleware factory for security checks"""
    
    rate_limiter = RateLimiter(config)
    api_validator = APIKeyValidator(config)
    audit_logger = AuditLogger()
    
    def middleware_wrapper(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # TODO: Implement actual request/response interception
            # This is a template for Streamlit or FastAPI middleware
            return func(*args, **kwargs)
        return wrapper
    
    return {
        'rate_limiter': rate_limiter,
        'api_validator': api_validator,
        'audit_logger': audit_logger,
        'data_protection': DataProtection(),
    }


# Initialize security components
config = SecurityConfig()
security = security_middleware(config)

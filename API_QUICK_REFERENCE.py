#!/usr/bin/env python3
"""
FinSecAI v2 API - Quick Reference & Examples
Copy-paste ready cURL commands and Python examples
"""

# =============================================================================
# QUICK START
# =============================================================================

"""
1. Start the API:
   python -m uvicorn api.main:app --reload

2. Access documentation:
   http://localhost:8000/docs

3. Test with Python:
   python test_api.py
"""

# =============================================================================
# DEMO CREDENTIALS (Hardcoded for development)
# =============================================================================

CREDENTIALS = {
    "admin": {
        "username": "admin",
        "password": "admin123",
        "role": "admin"
    },
    "analyst": {
        "username": "analyst", 
        "password": "analyst123",
        "role": "analyst_tier1"
    }
}

# =============================================================================
# cURL EXAMPLES (Copy-paste ready)
# =============================================================================

"""
=== 1. HEALTH CHECK ===

curl http://localhost:8000/health

curl http://localhost:8000/health/ready


=== 2. LOGIN & GET TOKEN ===

TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  | jq -r '.access_token')

echo "Token: $TOKEN"


=== 3. ANALYZE TRANSACTION (Core Feature) ===

curl -X POST http://localhost:8000/analysis/transaction \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "TXN-2024-06-02-001",
    "user_id": "USER-12345",
    "amount": 5000.00,
    "currency": "USD",
    "country": "US",
    "merchant": "Tech Retailer",
    "metadata": {"device_type": "mobile"}
  }'


=== 4. ANALYZE MULTIPLE (BATCH) ===

curl -X POST http://localhost:8000/analysis/batch \
  -H "Content-Type: application/json" \
  -d '[
    {"transaction_id": "TXN-001", "user_id": "USR-001", "amount": 100, "currency": "USD", "country": "US"},
    {"transaction_id": "TXN-002", "user_id": "USR-002", "amount": 5000, "currency": "USD", "country": "GB"}
  ]'


=== 5. LIST INCIDENTS ===

curl "http://localhost:8000/incidents/?limit=10&status=open"


=== 6. GET INCIDENT DETAILS ===

curl http://localhost:8000/incidents/{incident_id}


=== 7. CREATE INCIDENT MANUALLY ===

curl -X POST http://localhost:8000/incidents/ \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "TXN-001",
    "user_id": "USER-123",
    "severity": "high",
    "description": "Suspicious transaction detected",
    "tags": ["fraud", "review"]
  }'


=== 8. UPDATE INCIDENT ===

curl -X PATCH http://localhost:8000/incidents/{incident_id} \
  -H "Content-Type: application/json" \
  -d '{
    "status": "in_progress",
    "severity": "critical"
  }'


=== 9. ESCALATE INCIDENT ===

curl -X POST http://localhost:8000/incidents/{incident_id}/escalate


=== 10. GENERATE REPORT ===

curl -X POST http://localhost:8000/reports/generate \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "INC-001",
    "format": "pdf",
    "include_evidence": true
  }'


=== 11. GET REPORT ===

curl http://localhost:8000/reports/{report_id}


=== 12. LIST REPORTS ===

curl http://localhost:8000/reports/?limit=5
"""

# =============================================================================
# PYTHON EXAMPLES
# =============================================================================

"""
import requests

BASE_URL = "http://localhost:8000"

# === 1. Login ===
response = requests.post(f"{BASE_URL}/auth/login", json={
    "username": "admin",
    "password": "admin123"
})
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# === 2. Analyze Transaction ===
response = requests.post(
    f"{BASE_URL}/analysis/transaction",
    json={
        "transaction_id": "TXN-2024-001",
        "user_id": "USER-123",
        "amount": 5000.00,
        "currency": "USD",
        "country": "US"
    },
    headers=headers
)
result = response.json()
print(f"Risk Level: {result['analysis']['risk_level']}")
print(f"Confidence: {result['analysis']['confidence']}")

# === 3. Get Incident ===
incident_id = result.get("incident_id")
if incident_id:
    response = requests.get(
        f"{BASE_URL}/incidents/{incident_id}",
        headers=headers
    )
    incident = response.json()
    print(f"Incident Status: {incident['status']}")

# === 4. List Incidents ===
response = requests.get(
    f"{BASE_URL}/incidents/?status=open",
    headers=headers
)
incidents = response.json()["data"]
print(f"Open Incidents: {len(incidents)}")

# === 5. Escalate Incident ===
if incident_id:
    response = requests.post(
        f"{BASE_URL}/incidents/{incident_id}/escalate",
        headers=headers
    )
    escalated = response.json()
    print(f"New Status: {escalated['status']}")
"""

# =============================================================================
# API ENDPOINTS SUMMARY
# =============================================================================

ENDPOINTS = {
    "Health": [
        ("GET", "/health", "Service status"),
        ("GET", "/health/ready", "Readiness probe"),
    ],
    "Authentication": [
        ("POST", "/auth/login", "Login & get JWT token"),
        ("POST", "/auth/refresh", "Refresh token"),
    ],
    "Analysis (CORE)": [
        ("POST", "/analysis/transaction", "Analyze single transaction"),
        ("POST", "/analysis/batch", "Analyze multiple transactions"),
    ],
    "Incidents": [
        ("POST", "/incidents/", "Create incident"),
        ("GET", "/incidents/", "List incidents"),
        ("GET", "/incidents/{id}", "Get incident details"),
        ("PATCH", "/incidents/{id}", "Update incident"),
        ("POST", "/incidents/{id}/escalate", "Escalate incident"),
    ],
    "Reports": [
        ("POST", "/reports/generate", "Generate report"),
        ("GET", "/reports/{id}", "Get report details"),
        ("GET", "/reports/", "List reports"),
    ]
}

# =============================================================================
# RESPONSE EXAMPLES
# =============================================================================

SAMPLE_ANALYSIS_RESPONSE = {
    "status": "completed",
    "transaction_id": "TXN-2024-001",
    "analysis": {
        "explanation": "Risk detected for USER-123 - Amount: $5000.00",
        "confidence": 0.75,
        "evidence_coverage": 0.80,
        "governance_flags": [],
        "analysis_status": "success",
        "risk_score": 75,
        "risk_level": "HIGH"
    },
    "timestamp": "2024-06-02T10:30:00.123456",
    "incident_id": "INC-20240602103000-A7F3C2B1"
}

SAMPLE_INCIDENT = {
    "incident_id": "INC-20240602103000-A7F3C2B1",
    "transaction_id": "TXN-2024-001",
    "user_id": "USER-123",
    "status": "open",
    "severity": "high",
    "description": "Risk detected for USER-123 - Amount: $5000.00",
    "created_at": "2024-06-02T10:30:00",
    "updated_at": "2024-06-02T10:30:00",
    "tags": ["fraud"],
    "metadata": {}
}

SAMPLE_LOGIN_RESPONSE = {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user": {
        "user_id": "USR-001",
        "username": "admin",
        "email": "admin@finsecai.dev",
        "full_name": "System Administrator",
        "role": "admin",
        "is_active": True,
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00"
    },
    "expires_in": 1800
}

# =============================================================================
# RISK SCORES & LEVELS
# =============================================================================

"""
Risk Score Breakdown:
- 0-30: LOW (green)
- 30-50: MEDIUM (yellow)
- 50-70: HIGH (orange)
- 70-100: CRITICAL (red)

Auto-Incident Creation:
- Incidents are automatically created for risk_score > 70
- Manual incidents can be created anytime
"""

# =============================================================================
# STATUS CODES
# =============================================================================

"""
200 OK - Request succeeded
201 Created - Resource created
400 Bad Request - Invalid request body
401 Unauthorized - Missing or invalid token
404 Not Found - Resource not found
500 Internal Server Error - Server error
"""

# =============================================================================
# QUERY PARAMETERS
# =============================================================================

"""
GET /incidents/
  ?status=open              Filter by status
  ?severity=high            Filter by severity
  ?limit=20                 Pagination limit (1-100)
  ?offset=0                 Pagination offset

GET /reports/
  ?incident_id=INC-001      Filter by incident
  ?limit=20                 Pagination limit
  ?offset=0                 Pagination offset

Valid Status Values: open, in_progress, resolved, closed, escalated
Valid Severity Values: low, medium, high, critical
"""

# =============================================================================
# COMMON WORKFLOWS
# =============================================================================

"""
### Workflow 1: Quick Transaction Check
1. POST /auth/login → get token
2. POST /analysis/transaction → analyze
3. Check response.incident_id if high risk

### Workflow 2: Review Incident
1. GET /incidents/ → list open incidents
2. GET /incidents/{id} → view details
3. PATCH /incidents/{id} → update status/notes

### Workflow 3: Escalate Alert
1. GET /incidents/{id} → check status
2. POST /incidents/{id}/escalate → escalate
3. POST /reports/generate → generate report

### Workflow 4: Batch Analysis
1. POST /analysis/batch → analyze multiple
2. GET /incidents/ → check created incidents
3. Update each as needed
"""

# =============================================================================
# AUTHENTICATION HEADER
# =============================================================================

"""
After login, include token in requests:

Authorization: Bearer <token>

Example with Bearer token in all requests:
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}
"""

# =============================================================================
# API DOCS & REDOC
# =============================================================================

"""
OpenAPI Docs (Swagger UI): http://localhost:8000/docs
- Try-it-out buttons for each endpoint
- Request/response examples
- Schema validation info

ReDoc: http://localhost:8000/redoc
- Alternative documentation format
- Good for reading on mobile
"""

if __name__ == "__main__":
    print("FinSecAI v2 API - Quick Reference")
    print("=" * 60)
    print("\nEndpoints by Category:\n")
    
    for category, endpoints in ENDPOINTS.items():
        print(f"\n{category}:")
        for method, path, desc in endpoints:
            print(f"  {method:6} {path:40} {desc}")
    
    print("\n" + "=" * 60)
    print("Start API: python -m uvicorn api.main:app --reload")
    print("Run tests: python test_api.py")
    print("=" * 60)

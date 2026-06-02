# FinSecAI v2 - FastAPI Backend Implementation Guide

## 🎯 Overview

You've successfully built the **FinSecAI v2 FastAPI backbone** — the new core entry point for your AI system. This replaces direct Streamlit → AI calls with a proper backend service architecture.

## 🏗️ Architecture Summary

```
User / Frontend (Streamlit/React)
    ↓
FastAPI Backend (NEW - /api/main.py)
    ↓
Authentication + RBAC Middleware
    ↓
Route Handlers (incidents, analysis, reports, auth)
    ↓
Service Layer (bridge to AI)
    ↓
Existing AI System (src/services/intelligence_service.py)
    ↓
RAG + LangGraph (unchanged for now)
```

## 📁 New Directory Structure

```
api/
├── main.py                      # FastAPI app entry point
├── core/
│   ├── config.py               # Environment settings
│   ├── security.py             # JWT, auth utilities
│   └── logging.py              # Logging setup
├── routes/
│   ├── health.py              # Health checks
│   ├── analysis.py            # Transaction analysis endpoints
│   ├── incidents.py           # Incident management
│   ├── auth.py                # Authentication/login
│   └── reports.py             # Report generation
├── schemas/
│   ├── analysis.py            # Request/response validation
│   ├── incident.py            # Incident schemas
│   ├── user.py                # User/auth schemas
│   ├── report.py              # Report schemas
│   └── common.py              # Standard responses
├── services/
│   ├── analysis_service.py    # Bridge to AI intelligence
│   ├── incident_service.py    # Incident management logic
│   └── report_service.py      # Report generation logic
├── middleware/                 # (Reserved for auth, request ID, etc.)
└── dependencies/               # (Reserved for database connections, etc.)
```

## 🚀 Getting Started

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the API Server

**On macOS/Linux:**
```bash
bash run_api.sh
```

**On Windows:**
```bash
run_api.bat
```

**Or directly with uvicorn:**
```bash
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Access the API

- **OpenAPI Docs (Swagger UI):** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health

## 📚 API Endpoints Reference

### Health

```http
GET /health
GET /health/ready
```

### Authentication

```http
POST /auth/login
{
  "username": "admin",
  "password": "admin123"
}

POST /auth/refresh
```

**Demo Credentials:**
- `admin` / `admin123`
- `analyst` / `analyst123`

### Transaction Analysis (CORE ENDPOINT)

```http
POST /analysis/transaction
{
  "transaction_id": "TXN-2024-001",
  "user_id": "USER-123",
  "amount": 5000.00,
  "currency": "USD",
  "country": "US",
  "merchant": "Premium Retailer",
  "metadata": {...}
}
```

Response includes AI analysis results, confidence, risk score, and auto-created incident IDs for high-risk transactions.

### Batch Analysis

```http
POST /analysis/batch
[
  { "transaction_id": "TXN1", ... },
  { "transaction_id": "TXN2", ... }
]
```

### Incident Management

```http
# Create incident
POST /incidents/
{
  "transaction_id": "TXN-001",
  "user_id": "USER-123",
  "severity": "high",
  "description": "Suspicious activity detected",
  "tags": ["fraud", "alert"]
}

# Get incident
GET /incidents/{incident_id}

# List incidents
GET /incidents/?status=open&severity=high&limit=20

# Update incident
PATCH /incidents/{incident_id}
{
  "status": "in_progress",
  "severity": "critical"
}

# Escalate incident
POST /incidents/{incident_id}/escalate
```

### Report Generation

```http
# Generate report
POST /reports/generate
{
  "incident_id": "INC-001",
  "format": "pdf",
  "include_evidence": true,
  "include_timeline": true
}

# Get report
GET /reports/{report_id}

# List reports
GET /reports/?incident_id=INC-001
```

## 🔐 Security Features (Ready for Enhancement)

- ✅ JWT token-based authentication
- ✅ RBAC foundation (admin, analyst_tier1, analyst_tier2, readonly)
- ✅ Password hashing with bcrypt
- ✅ Request ID tracking
- ✅ CORS middleware
- ⏳ Database-backed user management (coming)

## 🔧 Configuration

Create a `.env` file to override defaults:

```env
ENVIRONMENT=production
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
LOG_LEVEL=INFO
SECRET_KEY=your-super-secret-key-here
DATABASE_URL=postgresql://user:password@localhost/finsecai
```

## 🧪 Testing the API

### Quick Test with cURL

```bash
# Health check
curl http://localhost:8000/health

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Analyze transaction
curl -X POST http://localhost:8000/analysis/transaction \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "TXN-2024-001",
    "user_id": "USER-123",
    "amount": 5000.00,
    "currency": "USD",
    "country": "US"
  }'
```

### Using Python Requests

```python
import requests

BASE_URL = "http://localhost:8000"

# Login
response = requests.post(f"{BASE_URL}/auth/login", json={
    "username": "admin",
    "password": "admin123"
})
token = response.json()["access_token"]

# Analyze transaction
headers = {"Authorization": f"Bearer {token}"}
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

print(response.json())
```

## 🔄 Connecting Streamlit to the API

Instead of calling intelligence_service directly:

```python
# OLD (Direct call)
from src.services.intelligence_service import run_intelligence
result = run_intelligence(transaction_data)

# NEW (Via API)
import requests
response = requests.post(
    "http://localhost:8000/analysis/transaction",
    json=transaction_data
)
result = response.json()
```

## 📊 Next Steps (2-3 Day Roadmap)

### Day 1-2: PostgreSQL Integration
- [ ] Add SQLAlchemy models
- [ ] Create database migrations (Alembic)
- [ ] Replace in-memory incident storage with database
- [ ] Add user table with hashed passwords

### Day 2: Testing & Validation
- [ ] Write pytest test suite
- [ ] Load test with multiple transactions
- [ ] Validate token expiration
- [ ] Test incident escalation workflow

### Day 3: Streamlit Integration
- [ ] Update Streamlit app to call FastAPI
- [ ] Add API error handling in dashboard
- [ ] Implement request caching for performance
- [ ] Add API usage metrics

### Production Readiness (Week 2)
- [ ] Docker containerization
- [ ] CI/CD pipeline setup
- [ ] Prometheus metrics
- [ ] Request rate limiting
- [ ] API key management

## 🛠️ Development Tips

### Reload on File Changes
The `--reload` flag in `run_api.sh` watches for changes and auto-reloads.

### Debug Mode
Set `DEBUG=true` in `.env` to enable detailed logging.

### Database Queries
Once PostgreSQL is added, test queries with:
```python
from sqlalchemy import inspect
inspector = inspect(engine)
print(inspector.get_table_names())
```

### Add New Endpoint
1. Create schema in `api/schemas/`
2. Create route in `api/routes/`
3. Create service method if needed
4. Include router in `api/main.py`

Example:
```python
# api/routes/my_feature.py
from fastapi import APIRouter
router = APIRouter()

@router.get("/my-endpoint")
def my_endpoint():
    return {"status": "ok"}

# api/main.py - add to imports and include_router
from api.routes import my_feature
app.include_router(my_feature.router, prefix="/my-feature", tags=["My Feature"])
```

## 📝 Important Notes

### What This API Does (Today)
- ✅ Receives transaction data
- ✅ Calls your AI intelligence service
- ✅ Returns risk scores and analysis
- ✅ Creates incidents automatically
- ✅ Manages incident lifecycle
- ✅ Generates reports (placeholder)

### What This API Doesn't Do Yet
- ❌ Persist data (in-memory only — Day 1-2 work)
- ❌ Real JWT token validation (demo only)
- ❌ Database user management
- ❌ Real PDF report generation
- ❌ Multi-tenant support

### Key Integration Points
- **AI Pipeline:** `api/services/analysis_service.py` → `src/services/intelligence_service.py`
- **Current Dashboard:** Update to call `http://localhost:8000/analysis/transaction`
- **Future Agents:** LangGraph agents will plug into services layer

## 🚨 Troubleshooting

### `ModuleNotFoundError: No module named 'fastapi'`
```bash
pip install -r requirements.txt
```

### Port 8000 already in use
```bash
# Use a different port
python -m uvicorn api.main:app --port 8001

# Or kill the process
lsof -ti:8000 | xargs kill -9  # macOS/Linux
netstat -ano | findstr :8000   # Windows
```

### CORS errors in Streamlit
The CORS middleware is configured to allow all origins in development. Update `api/main.py` CORS settings for production.

### Token authentication failing
Demo credentials are hardcoded in `api/routes/auth.py`. Replace with database lookup after PostgreSQL integration.

## 📖 Related Documentation

- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **Pydantic Docs:** https://docs.pydantic.dev/
- **Uvicorn Docs:** https://www.uvicorn.org/

---

**Status:** ✅ Backend API v2 foundation complete
**Next Review:** After PostgreSQL integration

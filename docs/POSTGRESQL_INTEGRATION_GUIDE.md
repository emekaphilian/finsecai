# PostgreSQL + SQLAlchemy Integration Guide

## Overview

FinSecAI v2 now includes **enterprise-grade database persistence** using PostgreSQL and SQLAlchemy ORM. This transforms the system from in-memory state to permanent, auditable financial records.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│      FastAPI Backend                │
│  (api/routes/*.py)                  │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      Service Layer                  │
│  (api/services/*.py)                │
│  - AnalysisService                  │
│  - IncidentService                  │
│  - ReportService                    │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      Repository Layer               │
│  (api/database/repositories/*.py)   │
│  - IncidentRepository               │
│  - UserRepository                   │
│  - ReportRepository                 │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      Database Models (ORM)          │
│  (api/database/models/__init__.py)  │
│  - User                             │
│  - Transaction                      │
│  - Incident                         │
│  - RiskScore                        │
│  - Report                           │
│  - AuditLog                         │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│    PostgreSQL / SQLite              │
│    Persistent Storage               │
└─────────────────────────────────────┘
```

---

## 📊 Database Schema

### Core Tables

**users**
- User accounts with roles (admin, analyst, readonly)
- Password hashing with bcrypt
- Login tracking and auditing

**transactions**
- Financial transaction records
- Amount, currency, location data
- Device and IP tracking
- Links to incidents and risk scores

**incidents**
- Security incidents with severity levels
- Risk scores from AI analysis
- Status tracking (open, investigating, resolved)
- Governance flags for compliance

**risk_scores**
- Historical risk assessment records
- Model version tracking
- Evidence coverage metrics
- Confidence scores

**reports**
- Generated incident reports
- Multiple formats (PDF, JSON, HTML)
- File path and size tracking

**audit_logs**
- Complete audit trail for compliance
- Captures state changes with before/after
- Actor tracking (user or system)

---

## 🚀 Quick Start

### Option 1: Using Docker Compose (Recommended)

```bash
# Set up environment
cp .env.example .env

# Start PostgreSQL + API
docker-compose -f docker-compose.local.yml up -d

# Initialize database with seed data
docker-compose -f docker-compose.local.yml exec api python api/database/init_db.py

# Access API
curl http://localhost:8000/docs
```

### Option 2: Local Development (SQLite)

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database
python api/database/init_db.py

# Run FastAPI
python -m uvicorn api.main:app --reload

# Access at http://localhost:8000/docs
```

---

## 💾 Database Operations

### Initialization

The system auto-initializes with SQLite by default. For PostgreSQL:

```bash
# Set connection string
export DATABASE_URL=postgresql://user:password@localhost:5432/finsecai

# Initialize schema
python api/database/init_db.py
```

### Seeding Data

Demo users are automatically created on first run:

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | admin |
| analyst | analyst123 | analyst |
| viewer | viewer123 | readonly |

Sample transactions and incidents are also auto-generated.

### Reset Database

```python
# DESTRUCTIVE - Clears all data
from api.database.init_db import reset_database
reset_database()
```

---

## 🔄 Using the Repository Pattern

### Example: Query Incidents

```python
from sqlalchemy.orm import Session
from api.database.repositories import IncidentRepository

def get_high_risk_incidents(db: Session):
    repo = IncidentRepository(db)
    
    # Get incidents by risk score
    incidents = repo.list_high_risk(min_risk_score=0.7, limit=10)
    
    # Get incidents by status
    open_incidents = repo.list_by_status("open")
    
    # Get with filters
    filtered = repo.list_with_filters(
        status="open",
        severity="high",
        skip=0,
        limit=50
    )
    
    return incidents
```

### Example: Create Incident with Audit

```python
# Repositories automatically create audit logs
incident_data = {
    "id": "INC-20240602-ABC123",
    "transaction_id": "TXN-001",
    "user_id": "USER-001",
    "status": "open",
    "severity": "high",
    "description": "Suspicious transaction pattern"
}

incident = repo.create_with_audit(
    incident_data,
    actor="analysis_service"
)

# Audit log automatically created with:
# - Action: "created"
# - Actor: "analysis_service"
# - New state: incident_data
```

---

## 🔐 Audit Trail

All incident changes are tracked for compliance:

```python
# Get complete audit history
audit_trail = repo.get_audit_trail("INC-20240602-ABC123")

for log in audit_trail:
    print(f"{log.action} by {log.actor} at {log.created_at}")
    print(f"Before: {log.previous_state}")
    print(f"After: {log.new_state}")
```

### Audit Log Fields

- **incident_id**: Associated incident
- **action**: "created", "updated", "escalated", "resolved"
- **actor**: User ID or system service name
- **previous_state**: State before change
- **new_state**: State after change
- **created_at**: Timestamp

---

## 🔗 Dependency Injection

Services receive database sessions via FastAPI dependencies:

```python
from fastapi import Depends
from api.database import get_db
from api.services.incident_service import IncidentService

@app.get("/api/incidents")
async def list_incidents(db: Session = Depends(get_db)):
    service = IncidentService(db)
    incidents = service.list_incidents(status="open")
    return incidents
```

---

## 📈 Transaction Flow Example

### Complete Workflow

```
1. Client sends transaction analysis request
   POST /analysis/transaction

2. AnalysisService receives request
   - Calls AI intelligence pipeline
   - Saves transaction record to database

3. AI returns risk analysis (e.g., score: 0.85)

4. High-risk incident created
   - Creates Incident record
   - Audit log entry added
   - Links to Transaction

5. IncidentService updates status
   - Status changes logged
   - Previous state saved
   - Actor recorded

6. Report generated and stored
   - Report linked to Incident
   - File path tracked

7. Response returned to client
   - Incident ID included
   - Audit trail available
```

---

## 🗄️ Migration Strategy

### SQLite → PostgreSQL

```bash
# 1. Export SQLite data (optional)
# python scripts/export_sqlite.py

# 2. Set PostgreSQL connection
export DATABASE_URL=postgresql://user:pass@postgres:5432/finsecai

# 3. Initialize PostgreSQL schema
python api/database/init_db.py

# 4. Seed data as needed
```

---

## 📊 Database Queries

### Common Queries

```python
# Count high-risk incidents
count = incident_repo.count_high_risk(0.7)

# Get incidents by user
user_incidents = incident_repo.list_by_user("USER-001")

# Get incidents with multiple filters
filtered = incident_repo.list_with_filters(
    status="open",
    severity="critical",
    user_id="USER-001"
)

# Get audit trail
trail = incident_repo.get_audit_trail("INC-001")
```

---

## ⚙️ Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/finsecai
DB_ECHO=false  # Set true for SQL logging

# API
API_PORT=8000
DEBUG=false

# Logging
LOG_LEVEL=INFO
```

### Connection Pooling

PostgreSQL uses connection pooling by default:
- **pool_size**: 10 connections
- **max_overflow**: 20 additional connections
- **pool_pre_ping**: Validates connections before use

---

## 🚨 Troubleshooting

### Connection Error

```python
# Error: "could not translate host name"
# Fix: Ensure DATABASE_URL is correct
export DATABASE_URL=postgresql://localhost:5432/finsecai
```

### Table Not Found

```python
# Error: "relation 'incidents' does not exist"
# Fix: Initialize database
python api/database/init_db.py
```

### Foreign Key Error

```python
# Error: "insert or update on incident violates foreign key"
# Fix: Ensure transaction_id exists before creating incident
```

---

## 📚 Next Steps

### Phase 3 (2 weeks)

- [ ] Add Alembic migration system
- [ ] Implement database backups
- [ ] Add data retention policies
- [ ] Create analytics dashboards

### Phase 4 (3 weeks)

- [ ] Real-time updates (WebSocket)
- [ ] Advanced search/filtering
- [ ] Performance optimization (indexing)
- [ ] HA/DR setup for production

---

## 🎯 Summary

**What Changed:**
- ✅ Persistent incident storage (no longer in-memory)
- ✅ Complete audit trail for compliance
- ✅ User authentication and authorization
- ✅ Risk score history tracking
- ✅ Report generation and storage

**What's the Same:**
- ✅ AI intelligence pipeline (unchanged)
- ✅ API endpoints (backward compatible)
- ✅ Streamlit frontend (can call API now)

**Impact:**
- 📊 Now enterprise-grade and audit-ready
- 🔒 Secure with role-based access control
- 💪 Scales from 1 user to thousands
- 📈 Ready for production deployment

---

## 📞 Questions?

Refer to:
- Model documentation: [api/database/models/__init__.py](api/database/models/__init__.py)
- Repository patterns: [api/database/repositories/](api/database/repositories/)
- Service layer: [api/services/](api/services/)
- Quick start: [QUICKSTART_API.md](QUICKSTART_API.md)

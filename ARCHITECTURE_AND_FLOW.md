# FinSecAI: Architecture, File Structure & Process Flow

---

## 📂 PROJECT FILE STRUCTURE

```
FinSecAI/
│
├── 🎯 ENTRY POINTS
│   ├── app.py                                 # Streamlit Cloud entry point
│   ├── dashboards/
│   │   ├── streamlit_app.py                  # Main SOC dashboard (35 KB)
│   │   ├── streamlit3_app.py                 # Alternative variant
│   │   ├── streamlit6_app.py                 # Alternative variant
│   │   ├── style.py                          # CSS design system (gold/white theme)
│   │   ├── performance_metrics.py            # Metrics dashboard
│   │   └── soc_dashboard.py                  # Alternative dashboard
│   │
│
├── 🧠 CORE AI/ML SERVICES (src/)
│   ├── src/
│   │   ├── services/
│   │   │   └── intelligence_service.py       # Incident intelligence analysis
│   │   │
│   │   ├── rag/
│   │   │   └── fusion_retriever.py           # RAG for MITRE/NIST evidence retrieval
│   │   │
│   │   ├── orchestration/
│   │   │   └── run_graph.py                  # LangGraph pipeline orchestration
│   │   │
│   │   ├── pipeline/
│   │   │   └── schema.py                     # Incident data schema validation
│   │   │
│   │   ├── evaluation/
│   │   │   ├── metrics.py                    # Evaluation: precision, recall, fairness, drift
│   │   │   └── visualizations.py             # Chart rendering for metrics
│   │   │
│   │   ├── reporting/
│   │   │   └── pdf_generator.py              # PDF incident report export
│   │   │
│   │   ├── config/
│   │   │   └── [tenant configs]
│   │   │
│   │   └── __init__.py
│   │
│
├── 🤖 LLM & NLP MODELS
│   ├── finetune_t5_soc.py                    # Fine-tune T5 for incident summarization
│   ├── test_model.py                         # Load & test LoRA adapters
│   ├── models/
│   │   ├── anomaly_model.pk                  # Serialized anomaly detection model
│   │   └── philian_soc_narrator_lora/        # LoRA adapter for T5
│   │
│   ├── models_nlp/
│   │   └── base/                             # NLP model artifacts
│   │
│
├── 📊 DATA ASSETS
│   ├── data/
│   │   ├── framework_index.faiss             # MITRE ATT&CK vector index
│   │   ├── framework_index.meta.json         # FAISS metadata
│   │   ├── rag_index.faiss                   # General evidence index
│   │   ├── rag_index.meta.json               # RAG metadata
│   │   │
│   │   ├── config/                           # Tenant configuration
│   │   ├── processed/                        # Processed incident data
│   │   ├── raw/                              # Raw logs & incident data
│   │   ├── synthetic/                        # Generated synthetic data
│   │   ├── drift/                            # Data drift detection results
│   │   ├── feedback/                         # Analyst feedback (for retraining)
│   │   ├── incidents/                        # Incident registry
│   │   ├── lora_incremental/                 # LoRA incremental fine-tuning
│   │   ├── soc_feedback/                     # SOC team feedback data
│   │   ├── external/                         # External threat intel
│   │   │
│   │   └── (and nested folders as needed)
│   │
│
├── 🛠 DATA GENERATION & TESTING
│   ├── generate_synthetic_logs.py            # Create synthetic transaction logs
│   ├── generate_sample_alerts_500.py         # Generate 500 test alerts
│   ├── generate_advanced_synthetic_data.py   # Advanced data generation
│   ├── test_model.py                         # Model testing/verification
│   ├── verify_professional_dashboard.py      # Dashboard validation
│   │
│
├── 📋 CONFIGURATION & DEPLOYMENT
│   ├── .streamlit/
│   │   ├── config.toml                       # Streamlit config (UI, cache, etc.)
│   │   └── secrets.toml                      # API keys, DB credentials (⚠️ excluded from git)
│   │
│   ├── config/
│   │   ├── analysts.json                     # RBAC: analyst role definitions
│   │   └── [other configs]
│   │
│   ├── monitoring/
│   │   ├── prometheus.yml                    # Prometheus scrape config
│   │   ├── alertmanager.yml                  # Alert routing config
│   │   └── alert_rules.yml                   # Alert threshold rules
│   │
│   ├── detection_rules/
│   │   └── [fraud/anomaly detection rules]
│   │
│   ├── sql/
│   │   └── [database schemas, migrations]
│   │
│
├── 🐳 CONTAINERIZATION & INFRASTRUCTURE
│   ├── Dockerfile                            # Development image (Python 3.11-slim)
│   ├── Dockerfile.prod                       # Production optimized image
│   ├── docker-compose.prod.yml               # Multi-service compose (app, Postgres, Redis)
│   ├── deploy.sh                             # Deployment automation script
│   │
│   ├── deployment/
│   │   └── [K8s manifests, Helm charts - if applicable]
│   │
│
├── 📚 SCRIPTS & UTILITIES
│   ├── scripts/
│   │   ├── production_smoke_tests.py         # Comprehensive smoke test suite
│   │   └── dev/
│   │       └── [development utilities]
│   │
│   ├── utils/
│   │   ├── smoke_test.py                     # Additional QA tests
│   │   └── [helpers & utilities]
│   │
│
├── 📖 DOCUMENTATION
│   ├── README.md                             # Project overview & quick start
│   ├── VETTING_REPORT.md                     # (NEW) Full vetting analysis
│   ├── PRODUCTION_DEPLOYMENT_READY.md        # Deployment checklist
│   ├── docs/
│   │   ├── PROFESSIONAL_DASHBOARD_GUIDE.md   # UI/UX documentation
│   │   ├── DEPLOYMENT_GUIDE.md               # Step-by-step deployment
│   │   ├── CLOUD_DEPLOYMENT_GUIDE.md         # Streamlit Cloud setup
│   │   ├── ADVANCED_SYNTHETIC_DATA_GUIDE.md  # Data generation walkthrough
│   │   ├── QUICK_REFERENCE.md                # Quick lookup
│   │   ├── IMPLEMENTATION_COMPLETE.md
│   │   ├── OPTIMIZATION_COMPLETE.md
│   │   ├── BUG_FIX_ANALYTICS.md
│   │   ├── UPGRADE_SUMMARY_v3.md
│   │   ├── QUICKSTART_v3.md
│   │   └── [15+ other guides]
│   │
│
├── 📔 JUPYTER NOTEBOOKS
│   ├── notebooks/
│   │   ├── Anomaly_Detection.ipynb           # Anomaly detection model dev
│   │   ├── Fraud_Detection_Model.ipynb       # Fraud classifier development
│   │   ├── feature_engineering.ipynb         # Feature development
│   │   ├── preprocessing.ipynb               # Data preprocessing
│   │   ├── correlation_engine.ipynb          # Correlation analysis
│   │   ├── pipeline_utils.ipynb              # Pipeline helpers
│   │   ├── insider_threat_model.ipynb        # Insider threat detection
│   │   ├── processed_fintech.ipynb           # Fintech data analysis
│   │   ├── processed_fintech.csv             # Sample data
│   │   └── artifacts/
│   │
│
├── 📊 REPORTS & LOGS
│   ├── generated_reports/                    # Auto-generated PDF/HTML reports
│   ├── incident_reports/                     # Incident-specific reports
│   ├── incident_response/
│   │   ├── generated_reports/
│   │   └── templates/
│   │
│   ├── logs/
│   │   ├── framework_index_build.jsonl       # FAISS index build logs
│   │   ├── pipeline_audit.jsonl              # Pipeline execution audit
│   │   └── rag_index_build.jsonl             # RAG index build logs
│   │
│   ├── visualization/
│   │   └── [chart/graph artifacts]
│   │
│
├── 🐍 DEPENDENCIES & ENV
│   ├── requirements.txt                      # Python packages (scikit-learn, streamlit, transformers, etc.)
│   ├── .venv/                                # Virtual environment (excluded from git)
│   │
│
├── 📋 GIT & METADATA
│   ├── .gitignore                            # Git ignore patterns
│   ├── check.txt                             # Setup verification checklist
│   ├── smoke_test_results.json               # Last smoke test results
│   ├── smoke_test_results.txt                # Human-readable test output
│   │
│
└── 🔧 DEVELOPMENT TOOLS
    ├── .pytest_cache/                        # Pytest cache
    ├── .qodo/                                # QodoAI code quality (if used)
    │   ├── agents/
    │   └── workflows/
    │
    └── __pycache__/                          # Python cache
```

---

## 🔄 PROCESS FLOW ARCHITECTURE

### **High-Level Data Flow**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FINANCIAL TRANSACTION STREAM                              │
│                  (Bank logs, Card transactions, Alerts)                      │
└────────────────────────────┬────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1️⃣  DATA INGESTION & PREPROCESSING                                          │
│    └─ generate_synthetic_logs.py / raw transaction data                      │
│    └─ Normalize, parse timestamps, extract features                          │
│    └─ Stored in: data/raw/ → data/processed/                                │
└────────────────────────────┬────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 2️⃣  ANOMALY & FRAUD DETECTION                                               │
│    └─ models/anomaly_model.pk (scikit-learn)                                │
│    └─ Generate risk_score (0.0 - 1.0)                                       │
│    └─ Output: Incidents with risk classification                             │
│    └─ Stored in: data/incidents/                                             │
└────────────────────────────┬────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 3️⃣  INCIDENT ANALYSIS PIPELINE (LangGraph Orchestration)                    │
│    ┌──────────────────────────────────────────────────────────────┐          │
│    │ src/orchestration/run_graph.py                               │          │
│    │ ├─ Validate incident schema (src/pipeline/schema.py)        │          │
│    │ ├─ Run intelligence analysis                                │          │
│    │ ├─ Retrieve evidence (RAG fusion retriever)                 │          │
│    │ └─ Generate governance flags                                │          │
│    └──────────────────────────────────────────────────────────────┘          │
│                                                                               │
│    Sub-steps:                                                                │
└────────────────────────────┬────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 4️⃣  INTELLIGENCE SERVICE                                                    │
│    └─ src/services/intelligence_service.py                                   │
│    └─ Analyze incident context (user behavior, transaction patterns)        │
│    └─ Generate explanations (rule-based + LLM-based)                        │
│    └─ Output: confidence score, risk assessment                             │
└────────────────────────────┬────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 5️⃣  RAG-BASED EVIDENCE RETRIEVAL                                             │
│    └─ src/rag/fusion_retriever.py                                            │
│    └─ Query FAISS indices:                                                   │
│       ├─ data/framework_index.faiss → MITRE ATT&CK techniques                │
│       ├─ data/rag_index.faiss → General threat context                       │
│    └─ Retrieve top-K similar framework controls/evidence                     │
│    └─ Output: [Evidence chunk, similarity score, framework type]             │
└────────────────────────────┬────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 6️⃣  LLM-BASED INCIDENT SUMMARIZATION                                        │
│    └─ Multi-LLM Integration (dashboards/streamlit_app.py#L120+)            │
│    │                                                                          │
│    ├─ Primary: OpenAI GPT-4o-mini                                           │
│    │   Prompt: "Summarize incident for security leadership"                 │
│    │   Max tokens: 450 | Temperature: 0.3                                   │
│    │                                                                          │
│    ├─ Fallback: Anthropic Claude 3 Haiku                                    │
│    │   Prompt: "Generate concise incident report"                           │
│    │                                                                          │
│    ├─ Fallback: Cohere                                                      │
│    │   Prompt: "Create executive summary"                                   │
│    │                                                                          │
│    └─ Fallback: Local LLM (Ollama/Llama3)                                   │
│        Endpoint: http://localhost:11434/api/generate                        │
│        Prompt: [same as above]                                               │
│                                                                               │
│    OR (if fine-tuned):                                                       │
│    └─ T5 Fine-tuned Model (models/philian_soc_narrator_lora/)              │
│       ├─ Loaded via: test_model.py                                          │
│       ├─ LoRA adapter: Lightweight, parameter-efficient                     │
│       └─ Generate: Human-friendly incident narratives                       │
└────────────────────────────┬────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 7️⃣  GOVERNANCE & COMPLIANCE EVALUATION                                      │
│    └─ src/evaluation/metrics.py                                              │
│    ├─ Fairness by segment (age, geography, user type)                       │
│    ├─ Bias detection (disparity ratio)                                      │
│    ├─ Drift detection (PSI, mean shift)                                     │
│    ├─ Model calibration (expected vs. actual)                               │
│    ├─ Compliance rate calculation                                            │
│    └─ Output: governance_flags, compliance_score                            │
└────────────────────────────┬────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 8️⃣  MULTI-CHANNEL ALERTING                                                  │
│    ├─ Slack: Webhook → #security channel (immediate)                        │
│    ├─ Email: SMTP → analyst@bank.com (formatted)                            │
│    ├─ PagerDuty: Incident escalation API (critical only)                    │
│    └─ Dashboard: Real-time update (streamlit app)                           │
└────────────────────────────┬────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 9️⃣  DASHBOARD & VISUALIZATION                                               │
│    └─ dashboards/streamlit_app.py                                            │
│    │                                                                          │
│    ├─ TAB 1: Overview                                                        │
│    │  ├─ KPI cards (total incidents, avg risk, anomalies)                   │
│    │  ├─ Risk distribution histogram                                         │
│    │  └─ Incident severity breakdown                                        │
│    │                                                                          │
│    ├─ TAB 2: Incidents (Operational)                                         │
│    │  ├─ Incident table (sortable, filterable)                              │
│    │  ├─ Batch analysis button                                              │
│    │  └─ CSV export                                                          │
│    │                                                                          │
│    ├─ TAB 3: Deep Dive (Investigation)                                       │
│    │  ├─ Incident details + risk badge                                      │
│    │  ├─ Intelligence analysis                                              │
│    │  ├─ Evidence chunks (from RAG)                                         │
│    │  ├─ Governance flags                                                   │
│    │  ├─ LLM-generated narrative                                            │
│    │  └─ PDF export button                                                  │
│    │                                                                          │
│    ├─ TAB 4: Analytics                                                       │
│    │  ├─ Evaluation metrics (precision, recall, F1)                         │
│    │  ├─ Fairness metrics by segment                                        │
│    │  ├─ Drift detection plots                                              │
│    │  ├─ Calibration curves                                                 │
│    │  └─ Governance compliance dashboard                                    │
│    │                                                                          │
│    ├─ TAB 5: Reports                                                         │
│    │  ├─ PDF generation (single incident)                                   │
│    │  ├─ Batch report export                                                │
│    │  └─ Historical report archive                                          │
│    │                                                                          │
│    └─ TAB 6: Admin                                                           │
│       ├─ Multi-tenant selector                                              │
│       ├─ User role management                                               │
│       ├─ Configuration controls                                             │
│       └─ System health check                                                │
│                                                                               │
│    Styling:                                                                  │
│    └─ dashboards/style.py (White + Gold + Grey theme)                       │
│       ├─ KPI cards with hover effects                                       │
│       ├─ Risk-colored badges (green=low, yellow=med, red=high)              │
│       └─ Professional dark mode option                                      │
└────────────────────────────┬────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🔟  MONITORING & OBSERVABILITY                                              │
│    └─ monitoring/prometheus.yml                                              │
│    ├─ Application metrics (Streamlit health, latency)                       │
│    ├─ Database metrics (PostgreSQL connections, queries/sec)                │
│    ├─ Cache metrics (Redis hit rate, memory usage)                          │
│    ├─ System metrics (CPU, memory, disk via Node Exporter)                  │
│    └─ Alert thresholds (alertmanager.yml → Slack/Email)                    │
│                                                                               │
│    Dashboards:                                                               │
│    └─ Grafana (visualization of Prometheus metrics)                         │
│       ├─ Real-time incident pipeline health                                 │
│       ├─ Model performance tracking                                         │
│       └─ SLA compliance (response time, accuracy)                           │
└────────────────────────────┬────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1️⃣1️⃣  FEEDBACK LOOP & MODEL RETRAINING                                      │
│    ├─ Analyst feedback: data/feedback/ (true labels, corrections)           │
│    ├─ Drift detection: data/drift/ (model performance degradation)          │
│    ├─ LoRA incremental fine-tuning: data/lora_incremental/                 │
│    │   └─ Retrain T5 on new incident narratives                            │
│    └─ Cycle back to step 2️⃣ with improved models                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🏗️ COMPONENT INTERACTIONS

### **Data Flow Between Modules**

```
┌──────────────────────────────────────────────────────────────────────┐
│                         STREAMLIT APP                                │
│               (dashboards/streamlit_app.py)                          │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  1. Load incidents from data/incidents/ or CSV upload                │
│  2. For each incident:                                              │
│     a. Call run_intelligence() → intelligence_service.py            │
│     b. Call fusion_retriever(query) → rag/fusion_retriever.py      │
│     c. Call run_full_pipeline() → orchestration/run_graph.py       │
│     d. Call evaluation metrics → evaluation/metrics.py              │
│  3. Generate LLM report → Multi-LLM integration (GPT-4, Claude)     │
│  4. Render dashboard with Plotly charts                             │
│  5. Generate PDF → reporting/pdf_generator.py                       │
│  6. Send alerts → Slack, Email, PagerDuty                           │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
         ↑                    ↑                  ↑
         │                    │                  │
         │                    │                  │
    ┌────┴─────────┐   ┌─────┴──────────┐   ┌──┴────────────┐
    │              │   │                │   │               │
    ▼              ▼   ▼                ▼   ▼               ▼
┌─────────┐  ┌───────────────┐  ┌────────────────┐  ┌──────────┐
│  MODELS │  │  INDICES      │  │   DATABASES    │  │ EXTERNAL │
│         │  │               │  │                │  │  SERVICES│
├─────────┤  ├───────────────┤  ├────────────────┤  ├──────────┤
│Anomaly  │  │framework_ix.  │  │PostgreSQL      │  │OpenAI    │
│Model.pk │  │faiss          │  │├─ incidents    │  │Claude    │
│         │  │               │  │├─ users        │  │Cohere    │
│T5 LoRA  │  │rag_index.     │  │├─ alerts       │  │Local LLM │
│Adapter  │  │faiss          │  │└─ feedback     │  │Slack     │
│         │  │               │  │                │  │PagerDuty │
└─────────┘  └───────────────┘  └────────────────┘  └──────────┘
```

---

## 🚀 DEPLOYMENT FLOW

### **Development to Production**

```
┌─────────────────────────────────────────────────────────────────────────┐
│  LOCAL DEVELOPMENT                                                       │
│  ├─ .venv/                                                              │
│  ├─ streamlit run dashboards/streamlit_app.py                          │
│  ├─ http://localhost:8501                                              │
│  └─ All secrets in .streamlit/secrets.toml (LOCAL ONLY)                │
└──────────────────────┬──────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  CI/CD PIPELINE (MISSING - TO BE ADDED)                                 │
│  ├─ GitHub Actions (.github/workflows/ci.yml - NOT YET CREATED)        │
│  ├─ Linting (black, flake8)                                            │
│  ├─ Testing (pytest)                                                   │
│  ├─ Docker build test                                                  │
│  └─ Smoke tests                                                        │
└──────────────────────────┬───────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  DOCKER CONTAINERIZATION                                                │
│  ├─ docker build -t finsecai:latest -f Dockerfile .                   │
│  └─ Image: Python 3.11-slim + all dependencies                         │
└──────────────────────────┬───────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  OPTION A: LOCAL DOCKER COMPOSE (PRODUCTION-LIKE)                      │
│  └─ docker-compose -f docker-compose.prod.yml up                       │
│     ├─ finsecai-app:8506 (Streamlit)                                   │
│     ├─ postgres:5432 (PostgreSQL)                                      │
│     ├─ redis:6379 (Redis)                                              │
│     ├─ prometheus:9090 (Monitoring)                                    │
│     ├─ alertmanager:9093 (Alerting)                                    │
│     └─ node-exporter:9100 (System metrics)                             │
└──────────────────────────┬───────────────────────────────────────────────┘
                           │
                ┌──────────┴──────────┐
                │                     │
                ▼                     ▼
┌──────────────────────────┐ ┌──────────────────────────────┐
│  OPTION B: STREAMLIT     │ │  OPTION C: KUBERNETES        │
│  CLOUD (Easiest)         │ │  (Not yet implemented)       │
├──────────────────────────┤ ├──────────────────────────────┤
│  1. Push to GitHub       │ │  1. Create K8s manifests     │
│  2. Connect Streamlit    │ │  2. Create Helm charts       │
│  3. Auto-deploy          │ │  3. Deploy to EKS/GKE        │
│  4. Live at              │ │  4. Auto-scaling configured  │
│     streamlit.app        │ │  5. Service mesh (Istio)     │
│                          │ │  6. GitOps (ArgoCD)          │
└──────────────────────────┘ └──────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│  MONITORING IN PRODUCTION                                                │
│  ├─ Prometheus scrapes metrics every 15s                               │
│  ├─ Grafana visualizes dashboards                                      │
│  ├─ AlertManager routes alerts                                         │
│  └─ Logs streamed to centralized logging (e.g., ELK, Datadog)         │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 DATA SCHEMA & FLOW

### **Incident Record Structure**

```python
# Incident JSON/DataFrame Schema
{
    "incident_id": "INC-2026-001234",          # Unique identifier
    "timestamp": "2026-06-02T14:23:45Z",       # When detected
    "tenant_id": "acme_001",                   # Multi-tenant isolation
    "user_id": "USER-0042",                    # Affected user
    
    # Transaction/Event Data
    "transaction_type": "wire_transfer",       # transfer, payment, login, etc.
    "amount": 50000.00,                        # Transaction amount
    "destination": "external_account_xyz",     # Counterparty
    "currency": "USD",
    
    # Risk Scoring
    "risk_score": 0.87,                        # 0.0-1.0 (model output)
    "anomaly_score": 0.92,                     # Anomaly probability
    "fraud_probability": 0.85,                 # Classification score
    "severity": "HIGH",                        # LOW, MEDIUM, HIGH, CRITICAL
    
    # Intelligence
    "explanation": "...",                      # Human-readable risk reason
    "confidence": 0.75,                        # Analyst confidence
    "evidence_coverage": 0.80,                 # % of incident explained by evidence
    
    # Evidence & Framework Mapping
    "evidence": [
        {
            "chunk_id": "chunk_001",
            "content": "MITRE ATT&CK T1078: Valid Accounts",
            "similarity": 0.92,
            "framework_type": "MITRE"
        },
        ...
    ],
    
    # Governance & Compliance
    "governance_flags": [
        "HIGH_RISK_JURISDICTION",
        "REPEAT_OFFENDER",
        "SANCTIONS_CHECK_FAILED"
    ],
    "compliance_score": 0.95,                  # 0-1 scale
    "requires_escalation": true,               # Tier-1 → Tier-2
    
    # Workflow
    "status": "OPEN",                          # OPEN, IN_PROGRESS, RESOLVED
    "assigned_to": "analyst_001",              # Analyst ID
    "sla_deadline": "2026-06-02T16:23:45Z",   # 2-hour SLA
    
    # Feedback (for retraining)
    "analyst_decision": "TRUE_POSITIVE",       # TRUE_POSITIVE, FALSE_POSITIVE, REVIEW
    "analyst_notes": "Confirmed fraudulent transfer...",
    "feedback_timestamp": "2026-06-02T14:35:00Z"
}
```

---

## 🧪 TESTING & QA FLOW

```
┌─────────────────────────────────────────────────────────┐
│  TEST HIERARCHY                                         │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  1. UNIT TESTS (Missing - To be added with pytest)     │
│     └─ test_evaluation_metrics.py                       │
│     └─ test_rag_retriever.py                            │
│     └─ test_intelligence_service.py                     │
│                                                          │
│  2. INTEGRATION TESTS (Smoke tests present)             │
│     └─ scripts/production_smoke_tests.py                │
│        ├─ Health check (Streamlit app)                  │
│        ├─ Dashboard accessibility                       │
│        ├─ API connectivity                              │
│        ├─ Database connection                           │
│        ├─ Data pipeline execution                       │
│        ├─ Incident detection                            │
│        ├─ Alerting system                               │
│        └─ Metrics evaluation                            │
│                                                          │
│  3. END-TO-END TESTS (Manual)                           │
│     ├─ Upload test CSV                                  │
│     ├─ Run analysis pipeline                            │
│     ├─ Generate PDF report                              │
│     ├─ Send alerts to Slack                             │
│     └─ Verify dashboard updates                         │
│                                                          │
│  4. PERFORMANCE TESTS (Not automated)                   │
│     ├─ Throughput: incidents/second                     │
│     ├─ Latency: incident to alert (ms)                  │
│     ├─ Scalability: handle 10K+ incidents               │
│     └─ Memory: RAM consumption under load               │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 🔒 SECURITY & SECRETS MANAGEMENT

```
┌──────────────────────────────────────────────────────┐
│  SECRETS (LOCAL DEVELOPMENT)                         │
│  .streamlit/secrets.toml (⚠️ NOT in git)             │
├──────────────────────────────────────────────────────┤
│                                                       │
│  OPENAI_API_KEY = "sk-proj-..."                     │
│  ANTHROPIC_API_KEY = "sk-ant-..."                   │
│  COHERE_API_KEY = "..."                             │
│  DATABASE_URL = "postgresql://user:pass@host/db"   │
│  REDIS_URL = "redis://localhost:6379"              │
│  SLACK_WEBHOOK_URL = "https://hooks.slack.com/..." │
│  SMTP_SERVER = "smtp.gmail.com"                     │
│  SMTP_PORT = 587                                    │
│  SMTP_USER = "alerts@example.com"                   │
│  SMTP_PASSWORD = "..."                              │
│  PAGERDUTY_API_KEY = "..."                          │
│                                                       │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│  SECRETS (PRODUCTION DEPLOYMENT)                    │
│  Environment variables (Docker, K8s)                │
├──────────────────────────────────────────────────────┤
│                                                       │
│  Use: docker-compose .env file                      │
│  Or:  K8s Secrets (kubectl create secret ...)       │
│  Or:  Cloud Secret Manager (AWS Secrets Manager)    │
│                                                       │
│  Never commit to Git!                               │
│  Use .gitignore to exclude:                         │
│    - .streamlit/secrets.toml                        │
│    - .env                                            │
│    - config/private_keys/                           │
│                                                       │
└──────────────────────────────────────────────────────┘
```

---

## 📈 SCALING CONSIDERATIONS

### **Current Setup** (Development/Small Deployment)
- Single Streamlit instance
- PostgreSQL (single node)
- Redis (single instance)
- Prometheus + AlertManager (basic)

### **Future Scaling** (Enterprise)
- Multi-Streamlit instances behind load balancer
- PostgreSQL with replication + read replicas
- Redis cluster for distributed caching
- Kafka for event streaming
- Elasticsearch for log aggregation
- Horizontal pod auto-scaling (K8s)
- Multi-region disaster recovery

---

## ✅ QUICK REFERENCE

| Component | Purpose | Status |
|-----------|---------|--------|
| **Entry Point** | app.py → dashboards/streamlit_app.py | ✅ Working |
| **Intelligence** | src/services/intelligence_service.py | ⚠️ Basic/Stub |
| **RAG Retrieval** | src/rag/fusion_retriever.py | ⚠️ Mock data |
| **Orchestration** | src/orchestration/run_graph.py | ⚠️ Minimal |
| **Evaluation** | src/evaluation/metrics.py | ✅ Framework present |
| **Fine-tuning** | finetune_t5_soc.py | ✅ Real implementation |
| **LLM Integration** | Multi-provider in streamlit_app.py | ✅ Robust |
| **Database** | PostgreSQL via docker-compose | ✅ Configured |
| **Caching** | Redis 3-tier TTL strategy | ✅ Implemented |
| **Monitoring** | Prometheus + AlertManager config | ✅ Configured |
| **Tests** | Smoke tests only | ⚠️ Unit tests missing |
| **CI/CD** | GitHub Actions | ❌ Missing |
| **Containerization** | Docker + docker-compose | ✅ Ready |

---

**Generated:** June 2, 2026  
**For:** FinSecAI Project Vetting & Architecture Understanding

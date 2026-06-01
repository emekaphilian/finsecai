# FinSecAI

[![Streamlit](https://img.shields.io/badge/streamlit-ready-brightgreen)](https://streamlit.io)

FinSecAI is an AI-powered Financial Security Operations Centre built with Streamlit for African fintech and enterprise financial security teams. It combines real-time incident monitoring, fraud and anomaly detection, NLP-based incident summarization, and multi-channel alerting into a single SOC dashboard.

## Key Features

- **Real-time SOC dashboard** for incident tracking, analytics, and response workflows
- **ML fraud detection** and anomalous transaction analysis with production-ready scoring
- **Fine-tuned T5 model** for generating incident summaries and analyst-friendly narratives
- **Multi-channel alerting** via Slack, email, and PagerDuty
- **FAISS vector search** for evidence retrieval and threat context
- **Multi-tenant architecture** for secure, tenant-aware monitoring
- **Monitoring-ready** with Prometheus and Grafana observability support
- **Plug-and-play AI services** including OpenAI, Anthropic, Cohere, and local LLM support

## Quick Start

1. Clone the repository:

   ```bash
   git clone https://github.com/your-org/FinSecAI.git
   cd FinSecAI
   ```

2. Create and activate a Python environment:

   ```bash
   python -m venv .venv
   .venv/Scripts/activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Configure secrets:

   - Create `.streamlit/secrets.toml`
   - Add keys such as `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `SLACK_WEBHOOK_URL`, `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `DATABASE_URL`, and `REDIS_URL`

5. Run the Streamlit app:

   ```bash
   streamlit run app.py
   ```

6. Open the dashboard in your browser at `http://localhost:8501`.

## Tech Stack

| Component | Technology |
| --- | --- |
| UI | Streamlit |
| Language | Python |
| ML | scikit-learn, T5 |
| Vector search | FAISS |
| NLP | LangGraph, OpenAI, Anthropic, Cohere |
| Monitoring | Prometheus, Grafana |
| Alerting | Slack, SMTP email, PagerDuty |

## Folder Structure

```
FinSecAI/
├── .streamlit/                # Streamlit secrets and config
├── dashboards/                # Streamlit dashboard implementation
├── docs/                      # Documentation and deployment guides
├── scripts/dev/               # Developer utilities and maintenance scripts
├── src/                       # Core application services and orchestration
├── data/                      # Data assets, indexes, and sample datasets
├── models/                    # Model artifacts and fine-tuned checkpoints
├── requirements.txt           # Python dependencies
├── app.py                     # Streamlit Cloud entry point
└── README.md                  # Project overview and quick start
```

## Target Market

FinSecAI is designed for African fintech companies, banks, payment processors, and enterprise financial security teams that need a modern SOC platform tailored for fraud detection, compliance, and incident response.

## Author

**Emeka Philian** — AI/ML Engineer and Cybersecurity Specialist

- LinkedIn: `https://www.linkedin.com/in/emekaphilian`
- Email: `emeka@example.com`

---

> Built for secure financial operations with AI-driven detection and incident response workflows.

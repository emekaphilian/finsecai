# FinSecAI - Streamlit Cloud Deployment Guide

## Quick Start - Deploy in 5 Steps

### 1. Login to Streamlit Cloud
Visit: https://share.streamlit.io
- Sign up with GitHub account (if new)
- Authorize Streamlit to access your repos

### 2. Deploy Your App
Click "New app" → Select your FinSecAI repository → Choose:
```
Repository:  YOUR-USERNAME/FinSecAI
Branch:      main
Main file:   dashboards/streamlit_app.py
```

### 3. Configure Secrets (In Streamlit Cloud Dashboard)
Go to your app's settings → "Secrets" → Paste:

```toml
# API Keys
OPENAI_API_KEY = "sk-..."
ANTHROPIC_API_KEY = "sk-ant-..."
COHERE_API_KEY = "..."

# Database (Optional - connect to cloud DB)
DATABASE_URL = "postgresql://..."
REDIS_URL = "redis://..."

# Notifications
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/..."
SLACK_CHANNEL = "#security-alerts"
ALERT_EMAIL_RECIPIENTS = "admin@company.com"
PAGERDUTY_SERVICE_KEY = "..."

# SMTP
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = "587"
SMTP_USER = "alerts@company.com"
SMTP_PASSWORD = "..."

# Monitoring
SENTRY_DSN = "https://..."

# App Settings
APP_ENV = "production"
DEBUG = "false"
```

### 4. Wait for Deploy
Streamlit Cloud automatically:
- ✅ Installs requirements.txt
- ✅ Builds Docker image
- ✅ Deploys to cloud
- ✅ Provides public URL

Expected time: 2-3 minutes

### 5. Access Your App
Your app will be available at:
```
https://YOUR-USERNAME-finsecai.streamlit.app
```

---

## Pre-Deployment Checklist

- [ ] GitHub account created
- [ ] Code pushed to GitHub repository
- [ ] `.gitignore` includes `.streamlit/secrets.toml`
- [ ] `requirements.txt` updated with all dependencies
- [ ] `dashboards/streamlit_app.py` verified locally
- [ ] `.streamlit/config.toml` configured
- [ ] Environment variables documented

---

## Troubleshooting

### App won't load
1. Check "Details" tab in Streamlit Cloud for build errors
2. Verify requirements.txt syntax
3. Ensure main Python file path is correct (dashboards/streamlit_app.py)

### Missing secrets/environment variables
1. Go to app settings → "Secrets"
2. Paste all required secrets as TOML
3. Click "Save"
4. Rerun app (click 🔄 in top-right)

### Performance issues
- Ensure caching decorators are applied (@st.cache_data)
- Use pagination (already implemented)
- Keep dataset small or implement pagination filters
- Consider upgrading Streamlit Cloud tier for more resources

### Database connection errors
- Whitelist Streamlit Cloud IPs in your database security group
- Use environment variable for DATABASE_URL
- Test connection locally first

---

## Important Notes

### File Structure
```
FinSecAI/
├── app.py                          # Root entry (optional)
├── dashboards/
│   ├── streamlit_app.py           # Main app ✓
│   ├── performance_metrics.py      # Metrics (separate deployment)
│   └── style.py
├── src/
│   ├── config/
│   │   ├── alert_notifications.py
│   │   └── security_config.py
│   └── ...
├── scripts/
│   └── production_smoke_tests.py
├── requirements.txt                # Must include all deps
├── .gitignore                      # Excludes secrets.toml
├── .streamlit/
│   ├── config.toml                 # Server config
│   └── secrets.toml                # Local only (git ignored)
└── README.md
```

### Database Connectivity
If connecting to external database:
1. Ensure cloud database allows inbound connections
2. Add Streamlit Cloud IP to whitelist (or use VPN)
3. Use connection pooling (pgbouncer for PostgreSQL)
4. Set connection timeout to 30 seconds

### Performance Dashboard
If you want to deploy the metrics dashboard separately:
```
Repository:  YOUR-USERNAME/FinSecAI
Main file:   dashboards/performance_metrics.py
```

---

## Public URLs After Deployment

- Main Dashboard: `https://YOUR-USERNAME-finsecai.streamlit.app`
- Metrics Dashboard: `https://YOUR-USERNAME-finsecai-metrics.streamlit.app` (separate)

---

## Monitoring Your Deployment

### Streamlit Cloud Logs
Check app logs in Settings → "Manage app" → "View logs"

### Health Checks
Add to your app:
```python
if __name__ == "__main__":
    import streamlit as st
    st.write("✅ FinSecAI is running on Streamlit Cloud")
```

### Uptime Monitoring
- Use UptimeRobot: https://uptimerobot.com
- Add your app URL
- Get alerts if app goes down

---

## Cost Estimation

**Streamlit Cloud Pricing:**
- Free tier: 1 app, limited resources
- Pro tier: $5/month per deployed app
- Deploy both dashboards: ~$10/month

**Alternatives for Production:**
- AWS EC2 (ALB + Docker)
- Google Cloud Run (serverless)
- Azure App Service
- Heroku (deprecated)
- DigitalOcean App Platform

---

## Next Steps

1. ✅ Push code to GitHub
2. ✅ Visit streamlit.io and deploy
3. ✅ Add secrets in Cloud dashboard
4. ✅ Share URL with team
5. ✅ Monitor logs and performance

**Your app will be live in minutes!** 🚀

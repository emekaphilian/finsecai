# FinSecAI Cloud Deployment Guide - Production Ready

## Overview
This guide covers deploying FinSecAI to cloud infrastructure with enterprise-grade security, monitoring, and logging.

## Quick Start Deployment

### 1. Cloud Platform Options

#### **Option 1: AWS Deployment**
```bash
# Install AWS CLI
pip install awscli

# Configure AWS credentials
aws configure

# Deploy using CloudFormation or ECS
# See aws_deployment.yaml
```

#### **Option 2: Google Cloud (GCP)**
```bash
# Install GCP SDK
pip install google-cloud-*

# Configure GCP project
gcloud init

# Deploy to Cloud Run or App Engine
# See gcp_deployment.yaml
```

#### **Option 3: Azure Deployment**
```bash
# Install Azure CLI
pip install azure-cli

# Configure Azure subscription
az login

# Deploy to Azure Container Instances or App Service
# See azure_deployment.yaml
```

### 2. Environment Configuration

#### Production Secrets (.env.production)
```
# API Keys
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
COHERE_API_KEY=your_key_here

# Database
DB_HOST=prod-db.example.com
DB_PORT=5432
DB_NAME=finsecai
DB_USER=finsecai_user
DB_PASSWORD=secure_password

# Security
JWT_SECRET=your_jwt_secret
API_KEY=your_api_key
CORS_ORIGINS=https://yourdomain.com

# Monitoring
SENTRY_DSN=your_sentry_dsn
DATADOG_API_KEY=your_datadog_key

# Feature Flags
ENABLE_ADVANCED_ANALYTICS=true
ENABLE_PDF_EXPORT=true
MAX_USERS=1000
```

### 3. Docker Containerization

Build and push container:
```bash
# Build
docker build -t finsecai:latest .
docker tag finsecai:latest your-registry/finsecai:latest

# Push to registry
docker push your-registry/finsecai:latest

# Run locally for testing
docker run -p 8506:8506 --env-file .env.production finsecai:latest
```

### 4. Database Setup

#### PostgreSQL (Recommended)
```sql
-- Run sql/init_production_db.sql
-- Creates tables with versioning, auditing, and partitioning
```

#### Connection Pooling
```python
# Uses pgbouncer/pgpool for connection management
DATABASE_URL = "postgresql://user:password@localhost:6432/finsecai"
```

### 5. Security Implementation

#### Rate Limiting
- Per-user: 1000 requests/hour
- Per-IP: 5000 requests/hour
- Per-endpoint: Varies (see security_config.py)

#### API Security
- JWT-based authentication
- API key validation
- CORS configuration
- Request validation with Pydantic
- SQL injection prevention (parameterized queries)

#### SSL/TLS
- Enable HTTPS only
- Certificate management via Let's Encrypt or cloud provider
- HSTS headers enabled

### 6. Monitoring & Alerting

#### Metrics Collected
- Request latency (p50, p95, p99)
- Error rates by endpoint
- Pipeline throughput (records/sec)
- Model inference time
- Database query performance
- Memory and CPU usage

#### Alerts Configured
- Error rate > 1% → Slack notification
- Latency p95 > 2000ms → PagerDuty alert
- Database connection errors → Immediate escalation
- Pipeline failures → Incident creation

#### Dashboards
- Main dashboard: KPIs and system health
- Incidents dashboard: Detection and response metrics
- Performance dashboard: Endpoint latencies
- Errors dashboard: Error tracking and debugging

### 7. Logging & Audit Trails

#### Log Levels
- DEBUG: Development only
- INFO: Normal operations
- WARNING: Recoverable issues
- ERROR: System errors
- CRITICAL: System failures

#### Log Destinations
- Local: /var/log/finsecai/
- CloudWatch: All logs streamed to CloudWatch Logs
- ELK Stack: Optional centralized logging
- Splunk: Optional SIEM integration

#### Audit Logging
- All user actions logged with timestamps
- Data access logged and traced
- Configuration changes tracked
- Admin actions with approval workflow

### 8. Domain & Load Balancing

#### DNS Configuration
```
finsecai.example.com → Load Balancer → Multi-zone deployment
```

#### Load Balancing Strategy
- Round-robin across 3+ instances
- Session affinity for stateful components
- Health checks every 30 seconds
- Automatic failover

### 9. Backup & Disaster Recovery

#### Backup Strategy
- Database: Daily full + hourly incremental
- Application state: Continuous replication
- Artifacts: S3/GCS with versioning

#### RTO/RPO Targets
- RTO (Recovery Time Objective): < 1 hour
- RPO (Recovery Point Objective): < 15 minutes

#### Disaster Recovery Drill
- Monthly full failover test
- Multi-region replication
- Runbook maintained and tested

### 10. Compliance & Security Certifications

#### Implemented Standards
- ✅ OWASP Top 10 mitigations
- ✅ CWE/SANS Top 25 coverage
- ✅ SOC 2 Type II controls
- ✅ NIST Cybersecurity Framework
- ✅ GDPR data protection (PII anonymization)

#### Regular Assessments
- Monthly vulnerability scans
- Quarterly penetration testing
- Annual security audit
- Continuous dependency updates

## Deployment Checklist

### Pre-Deployment
- [ ] All tests passing (smoke_test.py)
- [ ] Environment variables configured
- [ ] Database connection verified
- [ ] SSL certificates provisioned
- [ ] Backups configured and tested
- [ ] Monitoring account created
- [ ] DNS records prepared
- [ ] Load balancer configured

### Deployment Day
- [ ] Deploying to staging first
- [ ] Running smoke tests in staging
- [ ] Database migrations completed
- [ ] Cache warmed up
- [ ] Monitoring dashboards active
- [ ] Alert thresholds verified
- [ ] Support team briefed
- [ ] Rollback plan documented
- [ ] Deploy to production
- [ ] Run production smoke tests
- [ ] Monitor first hour closely
- [ ] Verify all services operational

### Post-Deployment
- [ ] All health checks passing
- [ ] No error spikes
- [ ] Performance metrics normal
- [ ] User feedback positive
- [ ] Documentation updated
- [ ] Runbook accessible
- [ ] On-call rotation assigned

## Support & Maintenance

### On-Call Procedures
1. High-severity alert → Page on-call engineer
2. Medium-severity → Email with 15min response
3. Low-severity → Batch in daily/weekly review

### Maintenance Windows
- Scheduled: Tuesdays 2-4am UTC
- Database maintenance: Monthly first Sunday
- Security patching: As needed, within 48hrs

### Escalation Path
```
Tier 1: On-call Engineer
  ↓ (unresolved in 30 min)
Tier 2: Engineering Lead
  ↓ (unresolved in 1 hour)
Tier 3: Director of Engineering
  ↓ (critical incidents)
CTO Involvement
```

## Troubleshooting

### Common Issues

**Issue: High latency after deployment**
```
Likely Cause: Cache not warmed
Solution: Run cache warmer script
Command: python utils/warm_cache.py
```

**Issue: Database connection errors**
```
Likely Cause: Connection pool exhausted
Solution: Increase pool size or add read replicas
Edit: src/config/database.py
```

**Issue: Memory usage growing**
```
Likely Cause: Memory leak in feature engineering
Solution: Restart workers on schedule or upgrade memory
Command: systemctl restart finsecai
```

## Next Steps

1. Choose cloud platform (AWS/GCP/Azure)
2. Configure environment variables
3. Build and test Docker container
4. Set up database (PostgreSQL)
5. Deploy to staging environment
6. Run full smoke test suite
7. Set up monitoring and alerting
8. Conduct security assessment
9. Deploy to production
10. Monitor for 24 hours

## References

- [Streamlit Cloud Deployment](https://docs.streamlit.io/streamlit-cloud)
- [Docker Deployment Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [OWASP Application Security Verification](https://owasp.org/www-project-application-security-verification-standard/)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)

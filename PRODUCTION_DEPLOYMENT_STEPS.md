# Production Deployment Steps for FinSecAI

## Step-by-Step Deployment Checklist

### Phase 1: Pre-Deployment (Day -1)

#### 1.1 Environment Preparation
- [ ] Choose cloud provider (AWS/GCP/Azure)
- [ ] Create cloud account and IAM roles
- [ ] Set up VPC/network resources
- [ ] Reserve static IP addresses
- [ ] Purchase domain name and configure DNS

#### 1.2 Infrastructure Setup
- [ ] Create RDS/Cloud SQL database instance
- [ ] Set up connection pooling (pgBouncer/pgPool)
- [ ] Create ElastiCache/Memorystore for Redis
- [ ] Set up S3/GCS/Azure Blob for backups
- [ ] Configure backup retention policies (30 days minimum)

#### 1.3 Security Configuration
- [ ] Create SSL certificates (Let's Encrypt or provider)
- [ ] Configure security groups/firewall rules
- [ ] Set up secrets management (AWS Secrets Manager/GCP Secret Manager)
- [ ] Create API keys and JWT secrets
- [ ] Set up IP whitelisting

#### 1.4 Monitoring Setup
- [ ] Set up Prometheus monitoring
- [ ] Configure Grafana dashboards
- [ ] Set up Alertmanager with Slack/PagerDuty
- [ ] Create CloudWatch/Cloud Logging groups
- [ ] Set up application error tracking (Sentry)

#### 1.5 Documentation & Communication
- [ ] Prepare deployment runbook
- [ ] Brief support team
- [ ] Prepare rollback plan
- [ ] Notify stakeholders of deployment window
- [ ] Set up on-call schedule

---

### Phase 2: Pre-Deployment Testing (Day 0 Morning)

#### 2.1 Local Testing
```bash
# Run full smoke test suite
python3 utils/smoke_test.py --verbose

# Expected output: 11/11 tests PASSED
```

#### 2.2 Docker Build & Test
```bash
# Build production Docker image
docker build -t finsecai:latest -f Dockerfile.prod .

# Test locally with Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# Run smoke tests in container
docker exec finsecai-app python utils/smoke_test.py --verbose

# Verify services
curl http://localhost:8506/_stcore/health
curl http://localhost:9090/metrics           # Prometheus
curl http://localhost:3000/api/health        # Grafana  
curl http://localhost:5601/api/status        # Kibana
```

#### 2.3 Database Testing
```bash
# Test database migration
psql -h localhost -U finsecai_user -d finsecai \
    -f sql/init_production_db.sql

# Verify audit tables
psql -h localhost -U finsecai_user -d finsecai \
    -c "SELECT * FROM audit.audit_log LIMIT 1;"

# Check partitioning
psql -h localhost -U finsecai_user -d finsecai \
    -c "\dt+ finsecai.incidents*"
```

#### 2.4 Security Testing
```bash
# Test rate limiting
for i in {1..150}; do curl http://localhost:8506/api/test; done

# Test authentication
curl -H "X-API-Key: invalid-key" http://localhost:8506/api/test

# Check security headers
curl -I http://localhost:8506 | grep -i "Strict-Transport-Security"
```

---

### Phase 3: Staging Deployment (Day 0 Afternoon)

#### 3.1 Deploy to Staging Environment
```bash
# Copy environment file
cp .env.production.template .env.staging

# Edit with staging values
nano .env.staging
# - Update database host to staging RDS
# - Update Redis endpoint
# - Update API keys
# - Update monitoring endpoints

# Deploy (choose your cloud provider)
./deploy.sh staging aws    # or gcp/azure
```

#### 3.2 Staging Validation
```bash
# Check all containers are running
docker ps

# Run full smoke test suite
python3 utils/smoke_test.py --verbose

# Check logs for errors
docker logs finsecai-app | tail -50

# Verify database connection
psql -h staging-db.aws.rds.amazonaws.com -U finsecai_user -d finsecai -c "SELECT now();"

# Test all endpoints
curl https://staging-app.example.com/_stcore/health
curl https://staging-app.example.com/api/status
```

#### 3.3 Load Testing (Optional)
```bash
# Install Apache Bench
apt-get install apache2-utils

# Run load test
ab -n 1000 -c 50 https://staging-app.example.com/

# Monitor metrics during test
# Check Grafana at http://staging-grafana:3000
```

#### 3.4 Staging Monitoring Handoff
- [ ] Grafana dashboards displaying correctly
- [ ] Prometheus collecting metrics
- [ ] Logs aggregating in ELK/CloudWatch
- [ ] Alerts firing (test critical alert)
- [ ] Alert notifications reaching team (Slack/PagerDuty)

---

### Phase 4: Production Deployment (Day 0 Evening)

#### 4.1 Pre-Deployment Final Checks
```bash
# 30 minutes before deployment
- [ ] Production database backed up
- [ ] Previous version running stably
- [ ] All team members ready
- [ ] Rollback plan reviewed
- [ ] Support team briefed
- [ ] Monitoring dashboards open
```

#### 4.2 Production Deployment
```bash
# Copy production environment file
cp .env.production.template .env.production

# Edit with production values (DO NOT commit!)
# Use secrets management, never commit .env.production
nano .env.production

# Deploy to production
./deploy.sh production aws  # or gcp/azure

# Monitor deployment progress
tail -f deployment_*.log

# Track container startup
docker logs -f finsecai-app
```

#### 4.3 Post-Deployment Validation (First 5 minutes)
```bash
# Health check
curl -f https://app.example.com/_stcore/health || alert!

# Error rate check
# Navigate to Grafana → Application Dashboard
# Confirm error rate = 0 or < 0.1%

# Latency check
# Check that p95 latency is < 1000ms

# Log check
# Review application.log for warnings
tail -50 /var/log/finsecai/application.log

# Database check
psql -h prod-db.aws.rds.amazonaws.com -U finsecai_user -d finsecai \
    -c "SELECT COUNT(*) FROM finsecai.incidents;"
```

#### 4.4 Smoke Tests Post-Deployment
```bash
# Run full smoke test suite against production
# This validates all 11 critical paths
python3 utils/smoke_test.py --verbose

# Expected output: 11/11 tests PASSED with metrics
```

---

### Phase 5: Immediate Post-Deployment (First Hour)

#### 5.1 Continuous Monitoring
- [ ] Monitor error dashboard every 2 minutes
- [ ] Watch latency metrics
- [ ] Review authentication logs for anomalies
- [ ] Check database connection pool usage
- [ ] Monitor cache hit rate

#### 5.2 User Feedback Collection
- [ ] Notify users deployment is complete
- [ ] Monitor support channel for issues
- [ ] Have engineers ready for quick fixes
- [ ] Keep rollback plan active for 1 hour

#### 5.3 Metrics Documentation
```bash
# Snapshot performance metrics
# Used for comparison with previous version

# Get baseline metrics
curl http://prometheus:9090/api/v1/query?query=finsecai_* > metrics_baseline.json

# Record in deployment log:
# - Error rate
# - Average latency
# - Throughput
# - Cache hit rate
# - Active user count
```

---

### Phase 6: Extended Monitoring (First 24 Hours)

#### 6.1 Performance Verification
- [ ] Monitor uptime (target: 99.9%)
- [ ] Check error rate trending (target: < 0.5%)
- [ ] Verify latency metrics (target: p95 < 1500ms)
- [ ] Monitor database performance (query time < 100ms avg)
- [ ] Check cache effectiveness (hit rate > 80%)

#### 6.2 Security Verification
- [ ] Review security logs for unauthorized access
- [ ] Verify rate limiting is working
- [ ] Check authentication success rate > 99%
- [ ] Audit log entries being recorded
- [ ] SSL certificate valid and auto-renewal configured

#### 6.3 Daily Report (Next Morning)
Create deployment report including:
- Deployment timestamp
- Duration
- Success/failure status
- Error summary
- Performance metrics
- Issues encountered
- Lessons learned
- Improvement items

---

## Rollback Procedure (If Needed)

### Quick Rollback (< 5 minutes)
```bash
# If critical issues detected in first hour:

# 1. Identify last stable version
git log --oneline -10

# 2. Rollback to previous version
git revert <commit-hash>
git push origin main

# 3. Redeploy
./deploy.sh production aws

# 4. Verify
python3 utils/smoke_test.py --verbose
```

### Database Rollback (If Application Issue)
```bash
# For non-data-destroying issues, simple app redeploy is sufficient
# Database rollback only needed if data was corrupted

# 1. Restore from backup
aws rds restore-db-instance-from-db-snapshot \
    --db-instance-identifier finsecai \
    --db-snapshot-identifier finsecai-backup-2026-04-17

# 2. Verify data integrity
psql -h prod-db -U finsecai_user -d finsecai \
    -c "SELECT COUNT(*) FROM finsecai.incidents;"

# 3. Verify no data loss
# Check restoration timestamp vs deployment time
```

---

## Environment Variables Management

### Storing Secrets Securely
```bash
# AWS Secrets Manager
aws secretsmanager create-secret \
    --name finsecai/prod/db-password \
    --secret-string "$(cat .env.production | grep DB_PASSWORD)"

# GCP Secret Manager
gcloud secrets create finsecai-db-password \
    --data-file .env.production

# Azure Key Vault
az keyvault secret set \
    --vault-name finsecai \
    --name db-password \
    --value "$(grep DB_PASSWORD .env.production)"
```

### Never Commit Secrets
```bash
# Add to .gitignore
echo ".env.production" >> .gitignore
echo ".env.staging" >> .gitignore

# Verify
git rm --cached .env.production 2>/dev/null || true
```

---

## Success Criteria

Deployment is successful when:
1. ✅ All 11 smoke tests pass
2. ✅ Error rate < 0.5% for 1 hour
3. ✅ P95 latency < 1500ms
4. ✅ Database health checks pass
5. ✅ No security alerts triggered
6. ✅ Cache hit rate > 80%
7. ✅ User authentication success > 99%
8. ✅ Audit logs being recorded
9. ✅ All monitoring dashboards populated
10. ✅ Alerts configured and working

---

## Disaster Recovery (If Deployment Fails)

### Complete Rollback Steps
1. Notify stakeholders
2. Stop current deployment
3. Revert to previous version
4. Restore from backup if needed
5. Run full smoke test suite
6. Verify all systems operational
7. Conduct post-mortem

---

## References

- [AWS best practices](https://docs.aws.amazon.com/)
- [GCP deployment guide](https://cloud.google.com/docs)
- [Azure deployment guide](https://docs.microsoft.com/azure/)
- [Docker deployment security](https://docs.docker.com/develop/security/)
- [Kubernetes deployment (future)](https://kubernetes.io/docs/)

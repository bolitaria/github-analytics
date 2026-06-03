# GitHub Analytics Dashboard Runbook

**Version:** 1.0
**Last updated:** June 2026
**Authors:** DevOps Team

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Initial Setup](#initial-setup)
5. [Configuration](#configuration)
6. [Daily Operations](#daily-operations)
7. [Maintenance](#maintenance)
8. [Troubleshooting](#troubleshooting)
9. [Backup and Recovery](#backup-and-recovery)
10. [Scalability](#scalability)
11. [Security](#security)
12. [Monitoring and Alerts](#monitoring-and-alerts)
13. [Incident Response](#incident-response)
14. [Resources](#resources)

---

## Overview

The GitHub Analytics Dashboard is a full-stack analytics platform for repository activity.
It ingests GitHub events, stores them in ClickHouse, exposes a secure REST API, runs
machine learning models for forecasting and classification, and presents dashboards via
Grafana.

This runbook provides operational guidance for deployment, monitoring, troubleshooting,
maintenance, and incident response.

---

## Architecture

### Core components

- **ETL service**: Fetches GitHub events or generates demo events when a token is not available.
- **Data storage**: ClickHouse stores raw events and forecast data.
- **API layer**: Flask-based REST API with JWT authentication.
- **Machine learning**: Forecasting and issue classification models.
- **Dashboard layer**: Grafana visualizes event trends and system health.
- **Orchestration**: Docker Compose coordinates ClickHouse, Grafana, and API services.

### Data flow

1. ETL extracts GitHub events from the API or demo generator.
2. Events are stored in ClickHouse under the `github_analytics` database.
3. ML models produce forecasts and classifications.
4. The Flask API serves authenticated requests and predictions.
5. Grafana visualizes the data using ClickHouse as the source.

### Docker services

- `clickhouse`: ClickHouse server.
- `grafana`: Grafana server.
- `predictions-api`: API service.

### External ports

- ClickHouse: 8124 -> 8123, 9001 -> 9000
- Grafana: 3001 -> 3000
- API: 8000 -> 8000
- Local Flask development: 8001

---

## Prerequisites

### Platform requirements

- Linux, macOS, or WSL2 on Windows
- Minimum 8GB RAM
- Minimum 20GB disk space

### Software requirements

- Python 3.12+
- Docker 20.10+
- Docker Compose 2.0+
- Git 2.30+

### Credentials

- GitHub token: optional for real data ingestion.
- Google Cloud service account key: optional for BigQuery export.
- JWT secret: required for secure API tokens.

### Verification

```bash
make check-env
```

---

## Initial Setup

The recommended approach combines all necessary steps into one streamlined process. For quick demo without persistence, use `make quick-start`.

### Full setup

```bash
git clone <repository-url>
cd github-analytics
make setup
make init-users
make generate-sample-data
make run-etl
make train-model
make health-check
```

### Quick demo (no persistence)

```bash
make quick-start
```

### Validation

```bash
docker ps | grep github_analytics
make health-check
curl http://localhost:3001/api/health
curl http://localhost:8001/api/health
make logs
```

---

## Configuration

### Environment variables

Create a `.env` file in the repository root with the following required variables:

```bash
# GitHub
GITHUB_TOKEN=your_github_token
GITHUB_API_BASE_URL=https://api.github.com

# ClickHouse
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=9000
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=
CLICKHOUSE_DATABASE=github_analytics

# Security
JWT_SECRET_KEY=your_secure_jwt_secret
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Scheduling
ETL_SCHEDULE_MINUTES=60
MODEL_RETRAINING_SCHEDULE_HOURS=24

# Cloud (optional)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
GITHUB_RATE_LIMIT_DELAY=1
```

### Development environment

```bash
DEBUG=True
FLASK_ENV=development
LOG_LEVEL=DEBUG
DEMO_MODE=True
```

### Grafana datasource

```bash
# Automated setup
make setup-grafana

# Manual setup:
# 1. Open http://localhost:3001
# 2. Login: admin / admin
# 3. Configuration > Data Sources
# 4. Add ClickHouse:
#    - URL: http://clickhouse:8123
#    - Database: github_analytics
#    - User: default
```

---

## Daily Operations

### Start services

```bash
make up
# or
docker-compose -f docker-compose.yml up -d
make status
```

### Run ETL

```bash
make run-etl
make run-scheduler
python scripts/scheduled_etl.py
```

### Train ML models

```bash
make train-model
```

### API usage

```bash
TOKEN=$(curl -s -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq -r '.token')

curl -H "Authorization: Bearer $TOKEN" http://localhost:8001/api/repos
curl -H "Authorization: Bearer $TOKEN" http://localhost:8001/api/repos/owner/repo-name/activity
curl -H "Authorization: Bearer $TOKEN" http://localhost:8001/api/predictions/owner/repo-name
curl -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"title":"Login fails","body":"Users cannot login"}' \
  http://localhost:8001/api/classify
```

### Query ClickHouse

```bash
python -c "from src.database.clickhouse import clickhouse_client; print(clickhouse_client.execute_query('SELECT COUNT(*) FROM github_analytics.events'))"
clickhouse-client -h localhost -p 9000 -q "SELECT COUNT(*) FROM github_analytics.events"
```

### View logs

```bash
make logs
make logs-clickhouse
make logs-grafana
python run.py
make run-scheduler
```

---

## Maintenance

### Data retention

```bash
python -c "from src.database.clickhouse import clickhouse_client; result = clickhouse_client.execute_query(\"SELECT table, formatReadableSize(sum(bytes)) AS size FROM system.parts WHERE database='github_analytics' GROUP BY table\"); print(result)"
python -c "from src.database.clickhouse import clickhouse_client; clickhouse_client.execute_query(\"ALTER TABLE github_analytics.events DELETE WHERE created_at < now() - interval 90 day\"); print('Deleted events older than 90 days')"
```

### Retrain models

```bash
make train-model
```

### Update dependencies

```bash
pip list --outdated
pip install --upgrade -r requirements.txt
make test
make restart
```

### Optimize ClickHouse

```bash
python -c "from src.database.clickhouse import clickhouse_client; clickhouse_client.execute_query('OPTIMIZE TABLE github_analytics.events FINAL'); print('Compaction started')"
```

---

## Troubleshooting

### Containers do not start

```bash
docker-compose logs clickhouse grafana
docker-compose down -v
make clean
make setup
docker logs clickhouse_github_analytics
docker logs grafana_github_analytics
```

### ClickHouse unresponsive

```bash
docker ps | grep clickhouse
make logs-clickhouse
docker restart clickhouse_github_analytics
netstat -tulpn | grep 9000 || ss -tulpn | grep 9000
python -c "from src.database.clickhouse import clickhouse_client; print(clickhouse_client.execute_query('SELECT 1'))"
```

### Grafana connection issue

```bash
curl http://localhost:3001/api/datasources
curl -X POST http://localhost:3001/api/datasources/test -H "Content-Type: application/json" -d '{"name":"ClickHouse","type":"clickhouse","url":"http://clickhouse:8123","database":"github_analytics"}'
docker network inspect github_analytics_net
```

### GitHub API rate limit

```bash
echo $GITHUB_TOKEN
export DEMO_MODE=True
make run-etl
```

### JWT token problem

```bash
TOKEN=$(curl -s -X POST http://localhost:8001/api/auth/login -H "Content-Type: application/json" -d '{"username":"admin","password":"admin123"}' | jq -r '.token')
echo $TOKEN
make restart
```

### Virtual environment issues

```bash
make venv-fix
rm -rf venv/
make venv
source venv/bin/activate
make install
```

---

## Backup and Recovery

### Strategy

- Daily backups
- 30-day retention
- Store backups under `/backups/`
- Validate restores weekly

### Backup script

```bash
#!/bin/bash
BACKUP_DIR="/backups/github-analytics"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"
docker exec clickhouse_github_analytics clickhouse-client -q "SELECT * FROM github_analytics.events FORMAT Native" > "$BACKUP_DIR/events_$DATE.ch"
tar -czf "$BACKUP_DIR/models_$DATE.tar.gz" models/
cp .env "$BACKUP_DIR/env_$DATE.backup"
cp docker-compose.yml "$BACKUP_DIR/docker-compose_$DATE.backup"
find "$BACKUP_DIR" -type f -mtime +30 -delete
echo "Backup completed in $BACKUP_DIR"
```

### Restore example

```bash
docker exec clickhouse_github_analytics clickhouse-client -q "INSERT INTO github_analytics.events FORMAT Native" < /backups/github-analytics/events_20260603_020000.ch
tar -xzf /backups/github-analytics/models_20260603_020000.tar.gz -C ./
make health-check
```

---

## Scalability

- Monitor ClickHouse partition growth.
- Archive data outside the retention window.
- Add caching and materialized views if query volume increases.
- Scale ClickHouse and API services horizontally as needed.

---

## Security

- Replace default passwords before production.
- Rotate `JWT_SECRET_KEY` regularly.
- Restrict access to admin ports.
- Terminate TLS at the network boundary.
- Store secrets in a managed vault.
- Scan dependencies with `safety` and `bandit`.

---

## Monitoring and Alerts

### Recommended checks

- API health and latency
- Grafana availability
- ClickHouse query performance
- Event ingestion volume
- Model retraining schedule

### Health checks

```bash
make health-check
curl http://localhost:8001/api/health
curl http://localhost:3001/api/health
docker exec clickhouse_github_analytics clickhouse-client -q "SELECT 1"
```

---

## CI/CD Pipeline Management

### GitHub Actions workflow ingestion

The platform automatically tracks GitHub Actions workflow runs to monitor pipeline health and identify flaky tests.

### Workflow run storage

Workflow execution data is stored in ClickHouse under:

```sql
-- CI workflow runs table
CREATE TABLE IF NOT EXISTS github_analytics.ci_workflow_runs (
    run_id UInt64,
    workflow_name String,
    status String,  -- success, failure, cancelled
    conclusion String,
    run_number Int32,
    created_at DateTime,
    updated_at DateTime,
    duration_seconds Int32,
    repo_name String
) ENGINE = MergeTree()
ORDER BY (created_at, repo_name, workflow_name);

-- Flaky test detection table
CREATE TABLE IF NOT EXISTS github_analytics.flaky_tests (
    test_name String,
    repo_name String,
    failure_rate Float32,
    recent_failures Int32,
    total_runs Int32,
    last_detected DateTime,
    severity String  -- low, medium, high
) ENGINE = MergeTree()
ORDER BY (failure_rate DESC, last_detected);
```

### Flaky test detection logic

The system automatically identifies flaky tests based on:

- **Failure rate threshold:** Tests failing 10-50% of the time
- **Recent trend:** 3+ consecutive failures in the last 10 runs
- **Impact assessment:** Tests affecting critical workflows flagged as `high` severity

Detection runs hourly via `scripts/analyze_flaky_tests.py`.

### Pipeline health dashboards

Planned dashboard location: `grafana/dashboards/ci_pipeline_health.json`.
If the file is not yet present, it is expected to be included during setup or in a future release.

Metrics tracked:

- Workflow success rate by job
- Pipeline duration trends
- Flaky test detection and severity
- Release pipeline progression
- Deployment frequency and lead time

### Release pipeline execution

The release pipeline (`release.yml`) is triggered on version tags. If this file is not yet present in the repository, it should be added as part of the CI/CD implementation or documented in a future version.

```bash
# Trigger release via git tag
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0

# Monitor release progress
make logs | grep release
curl -H "Authorization: Bearer $TOKEN" http://localhost:8001/api/releases
```

### Query CI metrics

```bash
# Flaky tests (last 30 days)
clickhouse-client -h localhost -p 9000 -q \
  "SELECT test_name, failure_rate, severity \
   FROM github_analytics.flaky_tests \
   WHERE last_detected > now() - interval 30 day \
   ORDER BY failure_rate DESC"

# Workflow run success rate
clickhouse-client -h localhost -p 9000 -q \
  "SELECT workflow_name, \
   countIf(status='success') / count() as success_rate \
   FROM github_analytics.ci_workflow_runs \
   WHERE created_at > now() - interval 7 day \
   GROUP BY workflow_name \
   ORDER BY success_rate"

# Release deployment frequency (last 90 days)
clickhouse-client -h localhost -p 9000 -q \
  "SELECT toDate(created_at) as date, count() as deployments \
   FROM github_analytics.releases \
   WHERE created_at > now() - interval 90 day \
   GROUP BY date \
   ORDER BY date DESC"
```

### CI/CD troubleshooting

**Workflow runs not appearing:**

```bash
# Check GitHub Actions sync status
make logs | grep "workflow"
docker exec clickhouse_github_analytics clickhouse-client -q \
  "SELECT COUNT(*) FROM github_analytics.ci_workflow_runs"

# Manually sync workflows
python scripts/sync_workflows.py --full
```

**Flaky test detection disabled:**

```bash
# Check if analysis script is running
ps aux | grep analyze_flaky_tests
# Restart if needed
python scripts/analyze_flaky_tests.py
```

---

## Incident Response

### Severity levels and SLOs

| Severity | Impact | Response SLO | Escalation |
|----------|--------|----------|------------|
| P1 | System outage (no data ingestion) | 15 min | DevOps lead |
| P2 | Partial degradation (slow queries, failed jobs) | 30 min | Tech lead |
| P3 | Minor issue (UI glitch, non-critical alert) | 4 hours | Backlog |

### Incident communication template

When an incident occurs, use this Slack template for async communication:

```
🚨 **INCIDENT ALERT: [P1/P2/P3] - [Component] - [Brief description]**

**Affected services:** ClickHouse / Grafana / API / ETL
**Status:** 🔴 CRITICAL | 🟠 DEGRADED | 🟢 RESOLVED
**Time detected:** [HH:MM UTC]
**Estimated impact:** [number] users / [service] affected

**Actions being taken:**
- [ ] Assess severity
- [ ] Notify on-call
- [ ] Begin remediation
- [ ] Update status

**Latest update:** [time] - [status message]
```

### P1: API unavailable

```bash
# 1. Check service status
docker ps | grep predictions-api
docker logs predictions-api --tail=50

# 2. Check dependencies
docker ps | grep clickhouse
docker logs clickhouse_github_analytics --tail=50

# 3. Restart if needed
docker-compose restart predictions-api

# 4. Verify recovery
curl http://localhost:8001/api/health
TOKEN=$(curl -s -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq -r '.token')
curl -H "Authorization: Bearer $TOKEN" http://localhost:8001/api/repos

# 5. If still failing, check git history
git log --oneline | head -5
git revert <commit-hash>
make restart
```

---

## Grafana Dashboards

Dashboards are stored as JSON in `grafana/dashboards/` and can be imported manually or via the API.

### Available dashboards

1. **GitHub Repository Analytics** (`github_analytics.json`)
   - Repository event trends
   - Issue and PR activity
   - Commit patterns by author

2. **CI Pipeline Health** (`ci_pipeline_health.json`)
   - Workflow success rates
   - Flaky test detection
   - Release deployment frequency

3. **System Health** (`system_health.json`)
   - API latency and throughput
   - ClickHouse query performance
   - Data ingestion volume

### Import a dashboard

```bash
# Method 1: Manual via UI
# 1. Open Grafana at http://localhost:3001
# 2. Go to Dashboards > Import
# 3. Upload `grafana/dashboards/[name].json`

# Method 2: Via API
TOKEN=$(curl -s -X POST http://localhost:3001/api/auth/login \
  -u admin:admin | jq -r '.message' | grep -oE '"[^"]*"' | head -1)

curl -X POST http://localhost:3001/api/dashboards/db \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @grafana/dashboards/github_analytics.json
```

---

## Resources

- [README.md](README.md) — Project overview and quick start
- [API Documentation](docs/api_documentation.md) — Full endpoint reference
- [Grafana Dashboards](grafana/dashboards/) — Pre-built visualization templates
- Makefile — All available commands
- `src/config/settings.py` — Application configuration

---

**Last review:** June 2026  
**Next review:** September 2026  
**Runbook version:** 1.1  
**CI/CD section added:** June 2026

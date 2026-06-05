# GitHub Analytics Dashboard — Runbook

**Version:** 1.0  
**Last updated:** June 2026  
**Authors:** bolitaria

## Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Initial setup](#initial-setup)
- [Configuration](#configuration)
- [Daily operations](#daily-operations)
- [Maintenance](#maintenance)
- [Troubleshooting](#troubleshooting)
- [Backup and recovery](#backup-and-recovery)
- [Scalability](#scalability)
- [Security](#security)

## Overview
The GitHub Analytics Dashboard is a full-stack analytics platform for repository activity. It ingests GitHub events, stores them in ClickHouse, exposes a secure REST API, runs machine learning models for forecasting and classification, and presents dashboards via Grafana.

This runbook provides operational guidance for deployment, monitoring, troubleshooting, maintenance, and incident response.

## Architecture
### Core components
- **ETL service:** Fetches GitHub events or generates demo events when a token is not available.
- **Data storage:** ClickHouse stores raw events and forecast data.
- **API layer:** Flask-based REST API with JWT authentication.
- **Machine learning:** Forecasting and issue-classification models.
- **Dashboard layer:** Grafana visualizes event trends and system health.
- **Orchestration:** Docker Compose coordinates ClickHouse, Grafana, and API services.

### Data flow
1. ETL extracts GitHub events from the API or demo generator.
2. Events are stored in ClickHouse under the `github_analytics` database.
3. ML models produce forecasts and classifications.
4. The Flask API serves authenticated requests and predictions.
5. Grafana visualizes the data using ClickHouse as the source.

### Docker services (examples)
- `clickhouse` — ClickHouse server
- `grafana` — Grafana server
- `predictions-api` — API service

### External ports (development)
- ClickHouse: host `8124 -> 8123`, `9001 -> 9000`
- Grafana: host `3001 -> 3000`
- API: `8000 -> 8000`
- Local Flask development: `8001`

## Prerequisites
- Supported platforms: Linux, macOS, or WSL2 on Windows
- Minimum: 8 GB RAM, 20 GB disk

### Software
- Python 3.12+
- Docker 20.10+
- Docker Compose 2.0+
- Git 2.30+

### Credentials
- `GITHUB_TOKEN` (optional for real ingestion)
- Google Cloud service account key (optional for BigQuery export)
- `JWT_SECRET_KEY` (required for secure API tokens)

### Verification
Run:

```bash
make check-env
```

## Initial setup
For a full setup follow these steps; for a quick demo use `make quick-start`.

Full setup:

```bash
git clone <repository-url>
cd github-analytics
make setup
make init-users        # create admin user
make generate-sample-data
make run-etl           # requires GITHUB_TOKEN for real data
make train-model
make health-check
```

Quick demo (no persistence):

```bash
make quick-start
```

Validation examples:

```bash
docker ps | grep github_analytics
make health-check
curl http://localhost:3001/api/health   # Grafana
curl http://localhost:8001/api/health   # API
make logs
```

## Configuration
Create a `.env` file in the repository root with required variables. Example:

```env
GITHUB_TOKEN=your_github_token
GITHUB_API_BASE_URL=https://api.github.com

CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=9000
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=
CLICKHOUSE_DATABASE=github_analytics

JWT_SECRET_KEY=your_secure_jwt_secret
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

ETL_SCHEDULE_MINUTES=60
MODEL_RETRAINING_SCHEDULE_HOURS=24

GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
GITHUB_RATE_LIMIT_DELAY=1

DEBUG=True
FLASK_ENV=development
LOG_LEVEL=DEBUG
DEMO_MODE=True
```

### Grafana datasource
Automated setup: `make setup-grafana`

Manual (development):

1. Open Grafana at `http://localhost:3001` (default `admin/admin`).
2. Configuration > Data Sources > Add ClickHouse datasource.
   - URL: `http://clickhouse:8123`
   - Database: `github_analytics`
   - User: `default`

## Daily operations
### Start services

```bash
make up
# or
docker-compose -f docker-compose.yml up -d
```

Check status:

```bash
make status
```

### Run ETL

```bash
make run-etl            # one-time full ETL
make run-scheduler      # start background scheduler
python scripts/scheduled_etl.py   # run individual script
```

### Train ML models

```bash
make train-model
```

### API usage examples
Obtain JWT token:

```bash
TOKEN=$(curl -s -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq -r '.token')
```

List repositories:

```bash
curl -H "Authorization: Bearer $TOKEN" http://localhost:8001/api/repos
```

Repository activity:

```bash
curl -H "Authorization: Bearer $TOKEN" http://localhost:8001/api/repos/owner/repo-name/activity
```

Predictions:

```bash
curl -H "Authorization: Bearer $TOKEN" http://localhost:8001/api/predictions/owner/repo-name
```

Classify an issue:

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"title":"Login fails","body":"Users cannot login"}' \
  http://localhost:8001/api/classify
```

### Query ClickHouse
Via Python:

```bash
python -c "from src.database.clickhouse import clickhouse_client; print(clickhouse_client.execute_query('SELECT COUNT(*) FROM github_analytics.events'))"
```

Via CLI (if installed):

```bash
clickhouse-client -h localhost -p 9000 -q "SELECT COUNT(*) FROM github_analytics.events"
```

View logs:

```bash
make logs
make logs-clickhouse
make logs-grafana
```

Run services locally:

```bash
python run.py           # Flask API in development
make run-scheduler      # Scheduler in separate terminal
```

## Maintenance
### Data retention

Check table sizes:

```bash
python -c "from src.database.clickhouse import clickhouse_client; result = clickhouse_client.execute_query(\
  'SELECT table, formatReadableSize(sum(bytes)) AS size FROM system.parts WHERE database=\'github_analytics\' GROUP BY table'); print(result)"
```

Delete events older than 90 days:

```bash
python -c "from src.database.clickhouse import clickhouse_client; clickhouse_client.execute_query(\
  'ALTER TABLE github_analytics.events DELETE WHERE created_at < now() - interval 90 day'); print('Deleted events older than 90 days')"
```

Retrain models:

```bash
make train-model
```

Update dependencies:

```bash
pip list --outdated
pip install --upgrade -r requirements.txt
make test
```

Force ClickHouse partition merge:

```bash
python -c "from src.database.clickhouse import clickhouse_client; clickhouse_client.execute_query('OPTIMIZE TABLE github_analytics.events FINAL'); print('Compaction started')"
```

## Troubleshooting

### Containers do not start
- Check logs:

```bash
docker-compose logs clickhouse grafana
```

- Clean and restart:

```bash
docker-compose down -v
make clean
make setup
```

### ClickHouse unresponsive
- Verify container is running: `docker ps | grep clickhouse`
- Check logs: `make logs-clickhouse`
- Restart: `docker restart clickhouse_github_analytics`
- Check port: `ss -tulpn | grep 9000`
- Test connection:

```bash
python -c "from src.database.clickhouse import clickhouse_client; print(clickhouse_client.execute_query('SELECT 1'))"
```

### Grafana connection issue
- List datasources: `curl http://localhost:3001/api/datasources`
- Test datasource:

```bash
curl -X POST http://localhost:3001/api/datasources/test \
  -H "Content-Type: application/json" \
  -d '{"name":"ClickHouse","type":"clickhouse","url":"http://clickhouse:8123","database":"github_analytics"}'
```

On Mac/Windows use `host.docker.internal` instead of `clickhouse` as host where appropriate.

### GitHub API rate limit
- Check token: `echo $GITHUB_TOKEN`
- Enable demo mode: `export DEMO_MODE=True` then `make run-etl`
- Regenerate token: https://github.com/settings/tokens

### JWT token problem
- Regenerate token (example):

```bash
TOKEN=$(curl -s -X POST http://localhost:8001/api/auth/login -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq -r '.token')
echo $TOKEN
make restart
```

### Virtual environment issues
- Auto-fix: `make venv-fix`
- Manual recreation:

```bash
rm -rf venv/
make venv
source venv/bin/activate
make install
```

## Backup and Recovery
### Strategy
- Frequency: daily
- Retention: 30 days
- Location: `/backups/`
- Validation: weekly restore test

### Backup script (backup.sh)

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

Run backup manually:

```bash
bash backup.sh
```

Automatic (cron daily at 02:00):

```cron
0 2 * * * /path/to/backup.sh >> /var/log/github-analytics-backup.log 2>&1
```

### Restore example
- List available backups:

```bash
ls -lh /backups/github-analytics/
```

- Restore ClickHouse data:

```bash
docker exec clickhouse_github_analytics clickhouse-client -q "INSERT INTO github_analytics.events FORMAT Native" < /backups/github-analytics/events_20260603_020000.ch
```

- Restore ML models:

```bash
tar -xzf /backups/github-analytics/models_20260603_020000.tar.gz -C ./
```

Validate: `make health-check`

## Scalability
- Monitor ClickHouse partition growth
- Archive data older than retention window (90 days)
- Add caching and materialized views for heavy query volume
- Scale ClickHouse and API services horizontally as needed

## Security
- Replace default passwords before production (Grafana admin, ClickHouse default user)
- Rotate `JWT_SECRET_KEY` regularly
- Restrict access to admin ports (do not expose ClickHouse port 9000 in production)
- Terminate TLS at the network boundary (reverse proxy / HTTPS)
- Store secrets in a managed vault (e.g., AWS Secrets Manager, Google Secret Manager)

## Monitoreo, alertas y respuesta a incidentes
- Configurar alertas en Grafana / Prometheus para disponibilidad y latencia
- Definir playbooks para incidentes críticos (BD, ETL, API)

---

## Recursos
- Código fuente: repository root
- Dashboards: grafana/dashboard/github_analytics.json
- Documentación API: docs/api_documentation.md

---

Si quieres, puedo también:
- añadir comprobaciones automáticas en `make test` para el runbook,
- crear el script `backup.sh` en el repositorio,
- o preparar un commit con este cambio.


Scan dependencies with safety check and code with bandit -r src/.

Monitoring and Alerts
Recommended checks
API health and latency

Grafana availability

ClickHouse query performance

Event ingestion volume

Model retraining schedule

Health checks
Full system: make health-check

Individual checks:

API: curl http://localhost:8001/api/health

Grafana: curl http://localhost:3001/api/health

ClickHouse: docker exec clickhouse_github_analytics clickhouse-client -q "SELECT 1"

CI/CD Pipeline Management
GitHub Actions workflow ingestion
The platform automatically tracks GitHub Actions workflow runs to monitor pipeline health and identify flaky tests. Workflow execution data is stored in ClickHouse.

Workflow run storage
Workflow execution data is stored in ClickHouse under tables ci_workflow_runs and flaky_tests. Example schemas:

ci_workflow_runs: columns include run_id, workflow_name, status, conclusion, run_number, created_at, updated_at, duration_seconds, repo_name.

flaky_tests: columns include test_name, repo_name, failure_rate, recent_failures, total_runs, last_detected, severity.

Flaky test detection logic
The system automatically identifies flaky tests based on:

Failure rate threshold: tests failing 10-50% of the time.

Recent trend: 3+ consecutive failures in the last 10 runs.

Impact assessment: tests affecting critical workflows flagged as high severity.

Detection runs hourly via scripts/analyze_flaky_tests.py.

Pipeline health dashboards
Planned dashboard location: grafana/dashboards/ci_pipeline_health.json. Metrics tracked: workflow success rate, pipeline duration trends, flaky test detection and severity, release pipeline progression, deployment frequency and lead time.

Release pipeline execution
The release pipeline (release.yml) is triggered on version tags. To trigger a release:

Create a tag: git tag -a v1.0.0 -m "Release version 1.0.0"

Push the tag: git push origin v1.0.0

Monitor release progress: make logs | grep release or query the releases endpoint: curl -H "Authorization: Bearer $TOKEN" http://localhost:8001/api/releases

Query CI metrics
Example queries (run via clickhouse-client):

Flaky tests in last 30 days:
SELECT test_name, failure_rate, severity FROM github_analytics.flaky_tests WHERE last_detected > now() - interval 30 day ORDER BY failure_rate DESC

Workflow run success rate (last 7 days):
SELECT workflow_name, countIf(status='success') / count() as success_rate FROM github_analytics.ci_workflow_runs WHERE created_at > now() - interval 7 day GROUP BY workflow_name ORDER BY success_rate

Release deployment frequency (last 90 days):
SELECT toDate(created_at) as date, count() as deployments FROM github_analytics.releases WHERE created_at > now() - interval 90 day GROUP BY date ORDER BY date DESC

CI/CD troubleshooting
Workflow runs not appearing:

Check logs: make logs | grep "workflow"

Check count: docker exec clickhouse_github_analytics clickhouse-client -q "SELECT COUNT(*) FROM github_analytics.ci_workflow_runs"

Manually sync: python scripts/sync_workflows.py --full

Flaky test detection disabled:

Check if analysis script is running: ps aux | grep analyze_flaky_tests

Restart if needed: python scripts/analyze_flaky_tests.py

Incident Response
Severity levels and SLOs
Severity	Impact	Response SLO	Escalation
P1	System outage (no data ingestion)	15 min	DevOps lead
P2	Partial degradation (slow queries, failed jobs)	30 min	Tech lead
P3	Minor issue (UI glitch, non-critical alert)	4 hours	Backlog
Incident communication template
When an incident occurs, use this Slack template for async communication:

text
🚨 INCIDENT ALERT: [P1/P2/P3] - [Component] - [Brief description]

Affected services: ClickHouse / Grafana / API / ETL
Status: 🔴 CRITICAL | 🟠 DEGRADED | 🟢 RESOLVED
Time detected: [HH:MM UTC]
Estimated impact: [number] users / [service] affected

Actions being taken:
- [ ] Assess severity
- [ ] Notify on-call
- [ ] Begin remediation
- [ ] Update status

Latest update: [time] - [status message]
(Note: the above template uses plain text and can be kept as is.)

P1: API unavailable
Check service status: docker ps | grep predictions-api

View logs: docker logs predictions-api --tail=50

Check dependencies: docker ps | grep clickhouse and docker logs clickhouse_github_analytics --tail=50

Restart if needed: docker-compose restart predictions-api

Verify recovery: curl http://localhost:8001/api/health and then obtain token and test repos endpoint.

If still failing, check git history: git log --oneline | head -5 and revert the last commit: git revert <commit-hash> then make restart.

Grafana Dashboards
Dashboards are stored as JSON in grafana/dashboards/ and can be imported manually or via the API.

Available dashboards
GitHub Repository Analytics (github_analytics.json): repository event trends, issue and PR activity, commit patterns by author.

CI Pipeline Health (ci_pipeline_health.json): workflow success rates, flaky test detection, release deployment frequency.

System Health (system_health.json): API latency and throughput, ClickHouse query performance, data ingestion volume.

Import a dashboard
Manual via UI:

Open Grafana at http://localhost:3001

Go to Dashboards > Import

Upload grafana/dashboards/[name].json

Via API:
Obtain a token: TOKEN=$(curl -s -X POST http://localhost:3001/api/auth/login -u admin:admin | jq -r '.message' | grep -oE '"[^"]*"' | head -1)
Then import: curl -X POST http://localhost:3001/api/dashboards/db -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d @grafana/dashboards/github_analytics.json

Resources
README.md — Project overview and quick start

docs/api_documentation.md — Full endpoint reference

grafana/dashboards/ — Pre-built visualization templates

Makefile — All available commands

src/config/settings.py — Application configuration

Last review: June 2026
Next review: September 2026
Runbook version: 1.1
CI/CD section added: June 2026


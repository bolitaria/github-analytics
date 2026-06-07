# 📘 RUNBOOK – GitHub Analytics Dashboard

**Version:** 2.1  
**Last updated:** June 2026  
**Authors:** DevOps Team, bolitaria

## Table of Contents

- Overview
- Architecture
- Prerequisites
- Initial setup
- Configuration
- Daily operations
- Maintenance
- Troubleshooting
- Backup and recovery
- Scalability
- Security
- Monitoring and alerts
- CI/CD pipeline management
- Incident response
- Grafana dashboards
- Local testing guide
- Resources

## Overview

The GitHub Analytics Dashboard is a full‑stack analytics platform for repository activity. It ingests GitHub events, stores them in ClickHouse, exposes a secure REST API, runs machine learning models for forecasting and classification, and presents dashboards via Grafana and Metabase.

This runbook provides operational guidance for deployment, monitoring, troubleshooting, maintenance, incident response, and local validation.

## Architecture

### Core components

- **ETL service**: Fetches GitHub events or generates demo events when a token is not available.
- **Data storage**: ClickHouse stores raw events and forecast data.
- **API layer**: Flask‑based REST API with JWT authentication.
- **Machine learning**: Forecasting (Prophet) and issue‑classification (scikit‑learn) models.
- **Dashboard layer**: Grafana (pre‑configured) and Metabase (optional BI).
- **Orchestration**: Docker Compose coordinates ClickHouse, Grafana, and the API service.

### Data flow

1. ETL extracts GitHub events from the API or demo generator.
2. Events are stored in ClickHouse under the `github_analytics` database.
3. ML models produce forecasts and classifications.
4. The Flask API serves authenticated requests and predictions.
5. Grafana (and optionally Metabase) visualises the data using ClickHouse as source.

### Docker services (examples)

- `clickhouse` – ClickHouse server
- `grafana` – Grafana server (port 3001 or 3003)
- `predictions-api` – API service (port 8000 or 8001/8002)
- `metabase` – optional BI add‑on (port 3002)

### External ports (development)

- ClickHouse: host 8124 → 8123 (HTTP), 9001 → 9000 (native)
- Grafana: host 3001 → 3000 (or 3003 if changed)
- API: host 8000 → 8000 (or 8002 depending on config)
- Local Flask development: 8002 (if run manually)

## Prerequisites

### Platform requirements

- Linux, macOS, or WSL2 on Windows
- Minimum 8 GB RAM, 20 GB disk space

### Software requirements

- Python 3.12+
- Docker 20.10+
- Docker Compose 2.0+
- Git 2.30+

### Credentials

- `GITHUB_TOKEN` – optional for real data ingestion (needed for production)
- Google Cloud service account key – optional for BigQuery export
- `JWT_SECRET_KEY` – required for secure API tokens

### Verification

Run: `make check-env`

## Initial setup

For a full setup follow these steps; for a quick demo use `make quick-start`.

Full setup:

git clone <repository-url>
cd github-analytics
make setup
make init-users        # creates local admin user for development (admin/admin123)
make generate-sample-data
make run-etl           # requires GITHUB_TOKEN for real data
make train-model
make health-check

Quick demo (no persistence): `make quick-start`

Validation examples:

docker ps | grep github_analytics
make health-check
curl http://localhost:3001/api/health   # Grafana
curl http://localhost:8002/api/health   # API (adjust port if needed)
make logs

## Configuration

Copy `.env.example` to `.env` and fill in local values. **Never commit `.env` or secret credential files to the repository.** Example content:

GITHUB_TOKEN=your_github_token
GITHUB_API_BASE_URL=https://api.github.com

CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=9001
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

METABASE_PORT=3002   # optional

### Grafana datasource

Automated setup: `make setup-grafana`

Manual (development):
- Open Grafana at http://localhost:3001 (default admin/admin)
- Configuration > Data Sources > Add ClickHouse datasource
   - URL: http://clickhouse:8123
   - Database: github_analytics
   - User: default

### Metabase (optional)

After starting Metabase with `make metabase-setup`, add a ClickHouse database:
- Host: clickhouse
- Port: 8123
- Database: github_analytics
- User: default
- Password: (empty)
Optionally add `?database=github_analytics` to JDBC options to avoid "Unknown table" errors.

## Daily operations

### Start services

make up
or
docker-compose -f docker-compose.yml up -d

Check status: `make status`

### Run ETL

make run-etl            # one-time full ETL
make run-scheduler      # start background scheduler
python scripts/scheduled_etl.py   # run individual script

### Train ML models

make train-model

### API usage examples

Obtain JWT token:

TOKEN=$(curl -s -X POST http://localhost:8002/api/auth/login -H "Content-Type: application/json" -d '{"username":"admin","password":"admin123"}' | jq -r '.token')

List repositories:

curl -H "Authorization: Bearer $TOKEN" http://localhost:8002/api/repos

Repository activity:

curl -H "Authorization: Bearer $TOKEN" http://localhost:8002/api/repos/owner/repo-name/activity

Predictions:

curl -H "Authorization: Bearer $TOKEN" http://localhost:8002/api/predictions/owner/repo-name

Classify an issue:

curl -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"title":"Login fails","body":"Users cannot login"}' http://localhost:8002/api/classify

(Note: adjust port if your API runs on 8001 or 8000)

### Query ClickHouse

Via Python:

python -c "from src.database.clickhouse import clickhouse_client; print(clickhouse_client.execute_query('SELECT COUNT(*) FROM github_analytics.events'))"

Via CLI (if installed):

clickhouse-client -h localhost -p 9000 -q "SELECT COUNT(*) FROM github_analytics.events"

### View logs

make logs
make logs-clickhouse
make logs-grafana

Run services locally:

python run.py           # Flask API in development (port 8002)
make run-scheduler      # scheduler in separate terminal

## Maintenance

### Data retention

Check table sizes:

python -c "from src.database.clickhouse import clickhouse_client; result = clickhouse_client.execute_query('SELECT table, formatReadableSize(sum(bytes)) AS size FROM system.parts WHERE database=''github_analytics'' GROUP BY table'); print(result)"

Delete events older than 90 days:

python -c "from src.database.clickhouse import clickhouse_client; clickhouse_client.execute_query('ALTER TABLE github_analytics.events DELETE WHERE created_at < now() - interval 90 day'); print('Deleted events older than 90 days')"

### Retrain models

make train-model

### Update dependencies

pip list --outdated
pip install --upgrade -r requirements.txt
make test

### Optimise ClickHouse

Force partition merge:

python -c "from src.database.clickhouse import clickhouse_client; clickhouse_client.execute_query('OPTIMIZE TABLE github_analytics.events FINAL'); print('Compaction started')"

## Troubleshooting

| Symptom | Likely cause | Solution |
|---------|--------------|----------|
| Containers do not start | Port conflicts or misconfiguration | Check logs: `docker-compose logs clickhouse grafana`. Clean and restart: `docker-compose down -v`, `make clean`, `make setup`. |
| ClickHouse unresponsive | Container not running or network issue | Verify with `docker ps | grep clickhouse`. Restart: `docker restart clickhouse_github_analytics`. Test connection: `python -c "from src.database.clickhouse import clickhouse_client; print(clickhouse_client.execute_query('SELECT 1'))"`. |
| Grafana connection issue | Datasource misconfigured | List datasources: `curl http://localhost:3001/api/datasources`. Test: `curl -X POST http://localhost:3001/api/datasources/test -H "Content-Type: application/json" -d '{"name":"ClickHouse","type":"clickhouse","url":"http://clickhouse:8123","database":"github_analytics"}'`. On Mac/Windows use `host.docker.internal`. |
| GitHub API rate limit | Missing or invalid token | Check token: `echo $GITHUB_TOKEN`. Enable demo mode: `export DEMO_MODE=True`, then `make run-etl`. Regenerate token at https://github.com/settings/tokens. |
| JWT token problem | Expired or invalid token | Regenerate: `TOKEN=$(curl -s -X POST http://localhost:8002/api/auth/login -H "Content-Type: application/json" -d '{"username":"admin","password":"admin123"}' | jq -r '.token')`. Restart API: `make restart`. |
| Virtual environment issues | Corrupted venv | Auto‑fix: `make venv-fix`. Manual: `rm -rf venv/`, `make venv`, `source venv/bin/activate`, `make install`. |
| Metabase cannot see tables | Wrong database name or user permissions | In Metabase, set Database name to `github_analytics` and use user `default`. Add `?database=github_analytics` to JDBC options. |
| Metabase shows "Unknown table" | Base database not set | Add `?database=github_analytics` to JDBC options in the database connection configuration. |
| API not responding (curl) | Wrong port or API not started | Check `python run.py` output; default port is 8002. Adjust curl command accordingly. |

## Backup and recovery

### Strategy

- Frequency: daily
- Retention: 30 days
- Location: /backups/
- Validation: weekly restore test

### Backup script (backup.sh)

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

Run manually: `bash backup.sh`

Automatic (cron daily at 02:00):

0 2 * * * /path/to/backup.sh >> /var/log/github-analytics-backup.log 2>&1

### Restore example

List available backups:

ls -lh /backups/github-analytics/

Restore ClickHouse data:

docker exec clickhouse_github_analytics clickhouse-client -q "INSERT INTO github_analytics.events FORMAT Native" < /backups/github-analytics/events_20260603_020000.ch

Restore ML models:

tar -xzf /backups/github-analytics/models_20260603_020000.tar.gz -C ./

Validate: `make health-check`

## Scalability

- Monitor ClickHouse partition growth.
- Archive data older than retention window (e.g., 90 days).
- Add caching and materialized views for heavy query volume.
- Scale ClickHouse and API services horizontally as needed.
- For production, use a reverse proxy (nginx) to load‑balance Metabase and Grafana.

## Security

- Replace default passwords before production (Grafana admin, ClickHouse default user).
- Rotate `JWT_SECRET_KEY` regularly.
- Restrict access to admin ports – do not expose ClickHouse port 9000 in production.
- Terminate TLS at the network boundary (reverse proxy / HTTPS).
- Store secrets in a managed vault (AWS Secrets Manager, Google Secret Manager, or GitHub Secrets).
- Scan dependencies with `safety check` and code with `bandit -r src/`.

## Monitoring and alerts

### Recommended checks

- API health and latency
- Grafana availability
- ClickHouse query performance
- Event ingestion volume
- Model retraining schedule

### Health checks

Full system: `make health-check`

Individual checks:

API: curl http://localhost:8002/api/health
Grafana: curl http://localhost:3001/api/health
ClickHouse: docker exec clickhouse_github_analytics clickhouse-client -q "SELECT 1"

### Grafana alerts (optional)

Configure alerting in Grafana for metrics like:
- API response time > 2 seconds
- ClickHouse query errors rate
- ETL failures

## CI/CD pipeline management

### GitHub Actions workflow ingestion

The platform automatically tracks GitHub Actions workflow runs to monitor pipeline health and identify flaky tests. Workflow execution data is stored in ClickHouse.

### Workflow run storage

Workflow execution data is stored in ClickHouse under tables `ci_workflow_runs` and `flaky_tests`. Example schemas:

- `ci_workflow_runs`: run_id, workflow_name, status, conclusion, run_number, created_at, updated_at, duration_seconds, repo_name.
- `flaky_tests`: test_name, repo_name, failure_rate, recent_failures, total_runs, last_detected, severity.

### Flaky test detection logic

The system automatically identifies flaky tests based on:

- Failure rate threshold: tests failing 10–50% of the time.
- Recent trend: 3+ consecutive failures in the last 10 runs.
- Impact assessment: tests affecting critical workflows flagged as `high` severity.

Detection runs hourly via `scripts/analyze_flaky_tests.py`.

### Pipeline health dashboards

Planned dashboard location: `grafana/dashboards/ci_pipeline_health.json`. Metrics tracked: workflow success rate, pipeline duration trends, flaky test detection and severity, release pipeline progression, deployment frequency and lead time.

### Release pipeline execution

The release pipeline (`release.yml`) is triggered on version tags. To trigger a release:

git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0

Monitor release progress: `make logs | grep release` or query the releases endpoint:

curl -H "Authorization: Bearer $TOKEN" http://localhost:8002/api/releases

### Query CI metrics

Example queries (run via clickhouse-client):

Flaky tests in last 30 days:

SELECT test_name, failure_rate, severity FROM github_analytics.flaky_tests WHERE last_detected > now() - interval 30 day ORDER BY failure_rate DESC

Workflow run success rate (last 7 days):

SELECT workflow_name, countIf(status='success') / count() as success_rate FROM github_analytics.ci_workflow_runs WHERE created_at > now() - interval 7 day GROUP BY workflow_name ORDER BY success_rate

Release deployment frequency (last 90 days):

SELECT toDate(created_at) as date, count() as deployments FROM github_analytics.releases WHERE created_at > now() - interval 90 day GROUP BY date ORDER BY date DESC

### CI/CD troubleshooting

Workflow runs not appearing:

- Check logs: `make logs | grep "workflow"`
- Check count: `docker exec clickhouse_github_analytics clickhouse-client -q "SELECT COUNT(*) FROM github_analytics.ci_workflow_runs"`
- Manually sync: `python scripts/sync_workflows.py --full`

Flaky test detection disabled:

- Check if analysis script is running: `ps aux | grep analyze_flaky_tests`
- Restart if needed: `python scripts/analyze_flaky_tests.py`

## Incident response

### Severity levels and SLOs

| Severity | Impact | Response SLO | Escalation |
|----------|--------|----------|------------|
| P1 | System outage (no data ingestion) | 15 min | DevOps lead |
| P2 | Partial degradation (slow queries, failed jobs) | 30 min | Tech lead |
| P3 | Minor issue (UI glitch, non-critical alert) | 4 hours | Backlog |

### Incident communication template

When an incident occurs, use this Slack template for async communication:

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

### P1: API unavailable

1. Check service status: `docker ps | grep predictions-api`
2. View logs: `docker logs predictions-api --tail=50`
3. Check dependencies: `docker ps | grep clickhouse` and `docker logs clickhouse_github_analytics --tail=50`
4. Restart if needed: `docker-compose restart predictions-api`
5. Verify recovery: `curl http://localhost:8002/api/health`, then obtain token and test repos endpoint.
6. If still failing, check git history: `git log --oneline | head -5` and revert the last commit: `git revert <commit-hash>`, then `make restart`.

## Grafana dashboards

Dashboards are stored as JSON in `grafana/dashboards/` and can be imported manually or via the API.

### Available dashboards

1. **GitHub Repository Analytics** (`github_analytics.json`): repository event trends, issue and PR activity, commit patterns by author.
2. **CI Pipeline Health** (`ci_pipeline_health.json`): workflow success rates, flaky test detection, release deployment frequency.
3. **System Health** (`system_health.json`): API latency and throughput, ClickHouse query performance, data ingestion volume.

### Import a dashboard

Manual via UI:

- Open Grafana at http://localhost:3001
- Go to Dashboards > Import
- Upload `grafana/dashboards/[name].json`

Via API:

Obtain a token:
TOKEN=$(curl -s -X POST http://localhost:3001/api/auth/login -u admin:admin | jq -r '.message' | grep -oE '"[^"]*"' | head -1)

Then import:
curl -X POST http://localhost:3001/api/dashboards/db -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d @grafana/dashboards/github_analytics.json

## Local testing guide

Use this section to verify every component works locally before pushing changes.

### Pre‑requisites

- Docker and Docker Compose installed.
- Python 3.12+ virtual environment active (`source venv/bin/activate`).

### Step 1: Validate environment

make check-env
make venv
make install

### Step 2: Start core services

make up

Wait 15 seconds, then check containers:

docker ps | grep -E "clickhouse|grafana"

Both should be `Up`.

### Step 3: Initialise database and load sample data

make init
make generate-sample-data

Verify tables exist:

docker exec -it clickhouse_github_analytics clickhouse-client --query "SHOW TABLES FROM github_analytics"

Expected output: events, forecasts, users, daily_summary.

### Step 4: Run ETL (real data – requires GITHUB_TOKEN in .env)

make run-etl

Check that events were inserted:

docker exec -it clickhouse_github_analytics clickhouse-client --query "SELECT count() FROM github_analytics.events"

It should return a number > 0.

### Step 5: Start Metabase (optional add‑on)

make metabase-driver   # downloads JDBC driver (once)
make metabase-setup    # starts Metabase and auto‑configures ClickHouse connection

Access Metabase at http://localhost:3002. Create admin account, then verify that tables appear under "Our data".

### Step 6: Test API

python run.py &

Wait a few seconds, then:

curl http://localhost:8002/api/health

Expected: `{"status":"healthy"}` (the port may be 8001 or 8002 – check the output of run.py).

### Step 7: Run pre‑push validation (CI simulation)

make pre-push        # lint + unit tests + integration tests

All tests must pass.

### Step 8: Clean up

make clean-all

This removes containers, volumes, venv, and caches.

## Resources

- README.md – Project overview and quick start
- docs/api_documentation.md – Full endpoint reference
- grafana/dashboards/ – Pre‑built visualization templates
- Makefile – All available commands
- src/config/settings.py – Application configuration

**Last review:** June 2026  
**Next review:** September 2026  
**Runbook version:** 2.1 (comprehensive, with local testing guide and CI/CD)
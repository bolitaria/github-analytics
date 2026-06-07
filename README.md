# 📘 README – GitHub Analytics Dashboard

**Version:** 2.0  
**Last updated:** June 2026

## Overview

A real‑time analytics system for GitHub repository activity using ClickHouse, Python, Flask, Grafana and Metabase.  
Includes a complete data pipeline: ETL, machine learning (forecasting and classification), secure REST API, automated dashboards, cloud integration (BigQuery, Cloud Run) and professional CI/CD (flaky test detection, database matrix testing, release pipelines).

## Features

- Real‑time ETL – fetches GitHub events (commits, issues, PRs) via API and stores them in ClickHouse.
- Machine Learning models – activity forecasting (Prophet) and issue classification (scikit‑learn).
- REST API with JWT authentication – secure endpoints to query data and use ML predictions.
- Interactive dashboards – pre‑configured Grafana dashboards and optional Metabase BI add‑on.
- Automation – scheduler for periodic ETL and model retraining.
- Cloud ready – export data to BigQuery and deploy API on Google Cloud Run.
- Dockerized – full containerized setup (ClickHouse, Grafana, API, optional Metabase).
- Scalable architecture – partitioned tables and materialized views in ClickHouse.
- Professional CI/CD – GitHub Actions workflows with linting, unit tests (5 repetitions for flaky detection), integration tests against a database matrix (ClickHouse, PostgreSQL, MySQL), security scans, and a release pipeline with manual approval.

## Tech Stack

- Backend: Python 3.12, Flask, ClickHouse Driver, scikit‑learn, Prophet
- Database: ClickHouse (columnar OLAP)
- Visualization: Grafana (core) + Metabase (optional BI)
- Containerization: Docker, Docker Compose
- Cloud: Google Cloud Platform (BigQuery, Cloud Run)
- Authentication: JWT (PyJWT) + bcrypt
- CI/CD: GitHub Actions (lint, test, security, release)

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.12+
- Git
- (Optional) Google Cloud account for BigQuery export and Cloud Run deployment

### Installation

1. Clone the repository

   git clone <repository-url>
   cd github-analytics

2. Set up environment and start services

   cp .env.example .env
   edit .env to add local credentials and settings
   make setup          # installs dependencies, starts containers, initializes DB
   make init-users     # creates local admin user for development (admin/admin123)

3. Run the demo (with sample data)

   make demo

4. Fetch real GitHub data (requires a GitHub token)

   - Set `GITHUB_TOKEN=your_token` in `.env` (never commit `.env`)
   - Run `make run-etl`

5. Train the issue classifier

   make train-model

6. Start the Flask API (in a separate terminal)

   python run.py

7. Access Grafana dashboards

   Open http://localhost:3001 (admin/admin)
   Run `make setup-grafana` to automatically configure datasources and dashboards.

8. (Optional) Start Metabase as a BI add‑on

   make metabase-driver   # download ClickHouse JDBC driver (one time)
   make metabase-setup    # starts Metabase and auto‑configures ClickHouse connection

   Then open http://localhost:3002 and follow the setup wizard. Add ClickHouse as a database using:
   - Host: clickhouse
   - Port: 8123
   - Database: github_analytics
   - User: default
   - Password: (empty)

## API Reference

All endpoints except `/api/health` require a valid JWT token obtained via `/api/auth/login`.

### Authentication

POST /api/auth/login  
Content-Type: application/json  
{ "username": "admin", "password": "admin123" }

Response: { "token": "...", "user": { "username": "admin", "role": "admin" } }

### Data Endpoints

GET /api/repos – List all repositories with events  
GET /api/repos/<owner>/<repo>/activity – Daily activity of a repository  
GET /api/predictions/<owner>/<repo> – Activity forecasts  

### ML Endpoint

POST /api/classify  
Authorization: Bearer <token>  
Content-Type: application/json  
{ "title": "Login button broken", "body": "Users cannot log in" }

Response: { "label": "bug", "confidence": 0.94 }

### Health Check

GET /api/health → { "status": "healthy" }

> Full API documentation is available in `docs/api_documentation.md`.

## Advanced Usage

### Automate ETL and Model Training

Run the scheduler in the background (uses the `schedule` library):

make run-scheduler

It will fetch new GitHub events every 60 minutes (configurable in `.env`) and retrain the issue classifier every 24 hours.

### Export Data to BigQuery

1. Create a Google Cloud service account and download its JSON key.
2. Set the environment variable:
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
3. Run:
   make export-bigquery

### Deploy API to Cloud Run

1. Install and authenticate `gcloud` CLI.
2. Build and push the Docker image, then deploy:
   make deploy-gcp
   (Uses `scripts/deploy_gcp.sh` – see the script for details.)

### CI/CD Pipeline (GitHub Actions)

This repository includes a full release pipeline (see `.github/workflows/release.yml`):

- On push to `main`:
  - Lint and test (`flake8`, `pytest`)
  - Build Docker image
  - Push to GitHub Container Registry (GHCR)
  - Deploy to **staging** environment
  - Wait for **manual approval** before deploying to **production**

Additionally, the `pr-checks.yml` workflow runs on every pull request and includes:
- Linting (black, isort, flake8)
- Unit tests executed 5 times to detect flaky tests
- Integration tests against a matrix of databases (ClickHouse, PostgreSQL, MySQL)
- Security scans (Safety, Bandit, Trivy)
- Automatic flaky test detection and PR comments
- Slack notification (optional)

## Testing

Run unit and integration tests:

make test          # unit tests
make test-integration   # integration tests (requires Docker)
make test-all      # full validation (lint, tests, security, coverage)

Test coverage report is generated in `htmlcov/`.

## Environment Variables

Create a `.env` file in the root directory from `.env.example` and populate it with local values. **Never commit `.env` or any secret file to source control.**

Example content:

# GitHub
GITHUB_TOKEN=your_github_token

# ClickHouse
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=9001
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=
CLICKHOUSE_DATABASE=github_analytics

# JWT
JWT_SECRET_KEY=your_super_secret_key_change_me
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Scheduler (minutes)
ETL_SCHEDULE_MINUTES=60
MODEL_RETRAINING_SCHEDULE_HOURS=24

# Google Cloud (optional)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/gcp-key.json

# Grafana (for auto‑setup)
GRAFANA_URL=http://localhost:3001
GRAFANA_USER=YOUR_GRAFANA_USER
GRAFANA_PASSWORD=YOUR_GRAFANA_PASSWORD

# Metabase (optional)
METABASE_PORT=3002

## Project Structure

github-analytics/
├── .github/workflows/       # CI/CD pipelines (PR checks, release)
├── src/
│   ├── api/                 # Flask routes & controllers
│   ├── auth/                # JWT authentication & middleware
│   ├── database/            # ClickHouse client + PostgreSQL/MySQL clients (matrix testing)
│   ├── etl/                 # GitHub ETL + CI workflow ingestion + flaky detection
│   ├── models/              # ML forecasting & classification
│   └── utils/               # Logging, config, helpers
├── scripts/                 # Init, backup, scheduler, consistency checks, reports
├── tests/                   # Unit & integration tests
├── grafana/dashboards/      # Dashboard JSON definitions
├── models/                  # Trained model files (ignored by git)
├── docker-compose.yml
├── Makefile
├── requirements.txt
├── README.md                # This file
└── RUNBOOK.md               # Operational runbook (troubleshooting, backups, security)

## Roadmap (Completed)

- ✅ ETL with GitHub API
- ✅ ClickHouse storage & partitioning
- ✅ Activity forecasting (Prophet)
- ✅ Issue classification (scikit‑learn)
- ✅ JWT authentication
- ✅ Automated Grafana dashboards
- ✅ Scheduler for periodic tasks
- ✅ Export to BigQuery
- ✅ CI/CD pipeline with GitHub Actions (including approval gates)
- ✅ Flaky test detection (CI jobs)
- ✅ Multi‑database matrix testing (PostgreSQL, MySQL)
- ✅ Weekly automated CI health reports
- ✅ Optional Metabase BI add‑on
- ⏳ Real‑time streaming (webhooks)
- ⏳ Slack notifications for flaky tests

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.  
For the **CI Engineer role**, focus on improving pipeline reliability, reducing flakiness, and automating release processes.

## License

MIT License – see [LICENSE](LICENSE) for details.

## Acknowledgements

- Built with ClickHouse, Prophet, Grafana, Metabase.
- Inspired by the challenges of maintaining a healthy CI infrastructure at scale.
- Designed to showcase the skills required for the **CI Engineer** position at Metabase.

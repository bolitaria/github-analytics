# 📊 GitHub Analytics Dashboard

Real-time analytics system for GitHub repositories powered by ClickHouse, Python, Flask and Grafana.  
Includes ETL pipeline, ML models, secure REST API, automated dashboards, Google Cloud integration and professional CI/CD.

## Local services

| Service            | URL / port              | Access                                                    |
|--------------------|-------------------------|-----------------------------------------------------------|
| Grafana            | http://localhost:3003   | User `admin`. Password set in docker-compose.             |
| ClickHouse HTTP    | http://localhost:8124/play | User `default`, no password.                             |
| ClickHouse native  | `localhost:9001`        | Same credentials. Used internally by the application.     |
| Flask API          | http://localhost:8003   | JWT protected. See API section.                           |
| Metabase (optional)| http://localhost:3002   | Follow first-run wizard.                                  |

> **Security:** all credentials are managed through environment variables in `.env` (never committed). Default passwords are for local development only.

## Quick start

1. Clone and install dependencies:
   ```bash
   git clone <repo-url>
   cd github-analytics
   make setup
Configure environment:

   ```bash
   cp .env.example .env

# Edit .env with your GITHUB_TOKEN and GITHUB_REPOS list
Run demo with synthetic data:

```bash
make demo

#Fetch real GitHub data:

```bash
make run-etl          # last 30 days of events
make fetch-issues     # historical issues

#Train the prediction model:

```bash
make train-model

#Deploy dashboards to Grafana:

```bash
make setup-grafana
make full-enterprise-deploy

#Then open http://localhost:3003, log in and open the dashboard "GitHub Analytics Enterprise Full".

##Project structure
'''text
github-analytics/
├── .github/workflows/       # CI/CD pipelines (PR checks, release)
├── src/
│   ├── api/                 # Flask + JWT endpoints
│   ├── auth/                # Authentication & security
│   ├── database/            # ClickHouse client
│   ├── etl/                 # GitHub ETL logic
│   ├── models/              # ML forecasting & classification
│   └── utils/               # Logging, configuration
├── scripts/                 # Init, scheduler, deployment helpers
├── tests/                   # Unit & integration tests
├── grafana/dashboards/      # Exported dashboard JSONs
├── docker-compose.yml
├── Makefile
└── requirements.txt

#REST API (port 8003)

#All protected routes require Authorization: Bearer <token>.

#POST /api/auth/login – obtain token

#GET /api/repos – list repositories

#GET /api/repos/<owner>/<repo>/activity – daily activity

#GET /api/predictions/<owner>/<repo> – activity forecasts

#POST /api/classify – classify an issue

#Full documentation in docs/api_documentation.md.

##Automation
#Scheduler (periodic ETL + model retraining): make run-scheduler

##BigQuery export:
```bash
make export-bigquery

##Cloud Run deployment:
```bash
make deploy-gcp

##Testing & CI
```bash
make test              # unit tests
make test-integration  # integration tests
make test-all          # lint + tests + security + coverage
make pre-push          # pre‑push checks
#The GitHub Actions pipeline includes flaky test detection, database matrix testing and security scans.

##Security
#Secrets stored in .env (excluded from version control).

#API authentication with JWT.

#Default passwords for local development only – change in production.

##License
#MIT – see LICENSE.

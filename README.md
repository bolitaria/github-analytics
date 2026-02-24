# GitHub Analytics Dashboard

A real-time analytics system for GitHub repository activity using **ClickHouse**, **Python**, and **Grafana**.  
This project includes a complete data pipeline: ETL, machine learning models, REST API with authentication, automated dashboards, and cloud integration (Google Cloud Platform).


## 🚀 Features

- **Real-time ETL**: Fetches GitHub events (commits, issues, PRs) via API and stores them in ClickHouse.
- **Machine Learning Models**:
  - **Activity forecasting** (Prophet) to predict future events.
  - **Issue classification** (scikit‑learn) to automatically tag issues as `bug`, `feature`, `doc`, etc.
- **REST API with JWT Authentication**: Secure endpoints to query data and use ML predictions.
- **Interactive Dashboards**: Pre‑configured Grafana dashboards for activity overview, predictions, and issue analysis.
- **Automation**: Scheduler for periodic ETL and model retraining.
- **Cloud Ready**: Export data to BigQuery and deploy the API on Google Cloud Run.
- **Dockerized**: Full containerized setup (ClickHouse, Grafana, API).
- **Scalable Architecture**: Partitioned tables and materialized views in ClickHouse.


## 🛠️ Tech Stack

- **Backend**: Python 3.12, Flask, ClickHouse Driver, scikit‑learn, Prophet
- **Database**: ClickHouse (columnar OLAP)
- **Visualization**: Grafana
- **Containerization**: Docker, Docker Compose
- **Cloud**: Google Cloud Platform (BigQuery, Cloud Run)
- **Authentication**: JWT (PyJWT) + bcrypt


## 📦 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.12+
- Git
- (Optional) Google Cloud account for BigQuery export and Cloud Run deployment

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd github-analytics
   ```

2. **Set up environment and start services**
   make setup          # Installs dependencies, starts Docker containers, initializes DB
   make init-users     # Creates default admin user (admin/admin123)

3. **Run the demo (with sample data)**
   make demo

4. **Fetch real GitHub data** (requires a GitHub token)
   - Create a `.env` file with `GITHUB_TOKEN=your_token`
   - Run `make run-etl`

5. **Train the issue classifier**
   make train-model

6. **Start the Flask API** (in a separate terminal)
   python run.py
7. **Access Grafana dashboards**
    - Open http://localhost:3001 (admin/admin)
    - Run make setup-grafana to automatically configure datasources and dashboards.


## 📚 API Reference
All endpoints except /health require a valid JWT token obtained via /api/auth/login.

### Authentication
    POST /api/auth/login

    json
    { "username": "admin", "password": "admin123" }
    Returns { "token": "...", "user": { "username": "...", "role": "..." } }

    GET /api/protected – Test endpoint (returns current user)

### Data Endpoints
    GET /api/repos – List all repositories with events
    GET /api/repos/<owner>/<repo>/activity – Daily activity of a repository
    GET /api/predictions/<owner>/<repo> – Activity forecasts

### ML Endpoint
    POST /api/classify
    json
    { "title": "Issue title", "body": "Issue description" }
    Returns { "label": "predicted_label", "confidence": 0.95 }

### Health Check
    GET /api/health – Public, returns { "status": "healthy" }


## 🤖 Advanced Usage

### Automate ETL and Model Training
- Run the scheduler in the background (use screen or a separate terminal):
    make run-scheduler

### Export Data to BigQuery
1. Set up a Google Cloud service account and download its JSON key.
2. Export the path to the key:
    ```` bash
    export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
    ````
3. Run:
    make export-bigquery
4. Deploy API to Cloud Run
5. Install the gcloud CLI and authenticate.
6. Build and push the Docker image:
    make deploy-gcp
    - (This requires a scripts/deploy_gcp.sh script; an example is provided in the repository.)


## 🧪 Testing
- Run unit and integration tests:
    make test
    make test-integration


### 📁 Project Structure

github-analytics/
├── src/
│   ├── api/               # Flask API
│   ├── auth/              # JWT authentication
│   ├── database/          # ClickHouse client
│   ├── etl/               # GitHub ETL pipeline
│   ├── models/            # ML models (forecast, classification)
│   └── utils/             # Logging, helpers
├── scripts/               # Utility scripts (init, export, scheduler, etc.)
├── tests/                 # Unit and integration tests
├── grafana/               # Dashboard JSON templates
├── models/                # Trained model files
├── docker-compose.yml
├── Makefile
├── requirements.txt
└── README.md


## 🛡️ Environment Variables
Create a .env file with the following (adjust as needed):

GITHUB_TOKEN=your_github_token
JWT_SECRET_KEY=your_secret_key
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=9001
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=
CLICKHOUSE_DATABASE=github_analytics
GRAFANA_URL=http://localhost:3001
GRAFANA_USER=admin
GRAFANA_PASSWORD=admin
GOOGLE_APPLICATION_CREDENTIALS=/path/to/gcp-key.json


## 🚀 Roadmap
- ETL with GitHub API
- ClickHouse storage
- Activity forecasting (Prophet)
- Issue classification (scikit‑learn)
- JWT authentication
- Automated Grafana dashboards
- Scheduler for periodic tasks
- Export to BigQuery
- Real‑time streaming (optional)
- CI/CD pipeline with GitHub Actions
# 📊 GitHub Analytics Dashboard

**Versión:** 2.0  
**Actualizado:** Julio 2026

Sistema de analítica en tiempo real para repositorios de GitHub usando ClickHouse, Python, Flask, Grafana y (opcionalmente) Metabase.  
Incluye pipeline de datos ETL, machine learning (forecasting, clasificación), API REST segura con JWT, dashboards automatizados, integración con Google Cloud (BigQuery, Cloud Run) y CI/CD profesional.

## 🔧 Servicios locales

| Servicio           | URL                           | Configuración de acceso                                    |
|--------------------|-------------------------------|------------------------------------------------------------|
| Grafana            | http://localhost:3003         | Usuario/contraseña definidos en variables de entorno       |
| ClickHouse (HTTP)  | http://localhost:8124/play    | Usuario/contraseña definidos en variables de entorno       |
| ClickHouse (nativo)| localhost:9001                | Usuario/contraseña definidos en variables de entorno       |
| Flask API          | http://localhost:8001         | Autenticación vía JWT (ver sección API)                    |
| Metabase (opcional)| http://localhost:3002         | Configuración guiada en el primer acceso                   |

Las credenciales reales **nunca** deben estar en este archivo. Se gestionan mediante el fichero `.env` (nunca versionado).

## 🚀 Quick Start

1. **Clonar e instalar**  
   ```bash
   git clone <repo-url>
   cd github-analytics
   make setup          # crea venv, arranca Docker, inicializa BD
Configurar variables de entorno

bash
cp .env.example .env
# Edita .env con tus tokens (GITHUB_TOKEN, GITHUB_REPOS, etc.)
Demo con datos sintéticos

bash
make demo
Ingestar datos reales de GitHub

bash
make run-etl        # eventos de los últimos 30 días
make fetch-issues   # histórico de issues
Entrenar modelo de predicción

bash
make train-model
Desplegar dashboards en Grafana

bash
make setup-grafana
make full-enterprise-deploy
Luego accede a Grafana y abre el dashboard GitHub Analytics Enterprise Full.

📦 Estructura del proyecto
text
github-analytics/
├── .github/workflows/       # CI/CD (PR checks, release)
├── src/
│   ├── api/                 # Flask + JWT
│   ├── auth/                # Autenticación y seguridad
│   ├── database/            # Cliente ClickHouse
│   ├── etl/                 # ETL de GitHub
│   ├── models/              # ML (forecasting, clasificación)
│   └── utils/               # Logging, configuración
├── scripts/                 # Inicialización, scheduler, despliegue
├── tests/                   # Unitarios e integración
├── grafana/dashboards/      # Dashboards JSON
├── docker-compose.yml
├── Makefile
└── requirements.txt
🌐 API (puerto 8001)
Login: POST /api/auth/login
Body: {"username": "<usuario>", "password": "<contraseña>"}
Respuesta: {"token": "..."}

Repositorios: GET /api/repos

Actividad: GET /api/repos/<owner>/<repo>/activity

Predicciones: GET /api/predictions/<owner>/<repo>

Clasificar issue: POST /api/classify

Todas las rutas protegidas requieren el header Authorization: Bearer <token>.

⚙️ Automatización
Scheduler (ETL periódico y reentrenamiento):

bash
make run-scheduler
Exportar a BigQuery:

bash
make export-bigquery
Desplegar en Cloud Run:

bash
make deploy-gcp
🧪 Testing y CI
bash
make test              # tests unitarios
make test-integration  # tests de integración
make test-all          # lint + tests + seguridad + cobertura
make pre-push          # chequeos antes de push
El pipeline de GitHub Actions incluye detección de flaky tests, matriz de bases de datos y escaneo de seguridad.

🛡️ Seguridad
Las credenciales se gestionan exclusivamente mediante variables de entorno (archivo .env).

El archivo .env no se versiona (está en .gitignore).

La API utiliza autenticación JWT.

📄 Licencia
MIT – ver archivo LICENSE.

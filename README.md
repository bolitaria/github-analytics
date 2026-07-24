# 📊 GitHub Analytics Dashboard

Sistema de analítica en tiempo real para repositorios de GitHub con ClickHouse, Python, Flask y Grafana.  
Incluye ETL, machine learning, API REST segura, dashboards automatizados, integración con Google Cloud y CI/CD.

## 🧰 Servicios locales

| Servicio           | URL / puerto               | Acceso                                                   |
|--------------------|----------------------------|----------------------------------------------------------|
| Grafana            | http://localhost:3003      | Usuario `admin`. La contraseña se define en docker-compose. |
| ClickHouse HTTP    | http://localhost:8124/play | Usuario `default`, sin contraseña.                       |
| ClickHouse nativo  | `localhost:9001`           | Misma autenticación. Usado internamente.                 |
| Flask API          | http://localhost:8003      | Protegida con JWT.                                       |
| Metabase (opcional)| http://localhost:3002      | Configuración guiada en el primer acceso.                |

> **Seguridad:** todas las credenciales se gestionan mediante variables de entorno en `.env` (nunca versionado). Las contraseñas por defecto son solo para desarrollo local.

## 🚀 Inicio rápido

1. Clona e instala:
   ```bash
   git clone <url-del-repo>
   cd github-analytics
   make setup
Configura el entorno:

bash
cp .env.example .env
# Edita .env con tu GITHUB_TOKEN y la lista de repositorios (GITHUB_REPOS)
Demo con datos sintéticos:

bash
make demo
Carga datos reales de GitHub:

bash
make run-etl          # eventos de los últimos 30 días
make fetch-issues     # histórico de issues
Entrena el modelo de predicción:

bash
make train-model
Despliega dashboards en Grafana:

bash
make setup-grafana
make full-enterprise-deploy
Abre http://localhost:3003, inicia sesión y busca el dashboard "GitHub Analytics Enterprise Full".

📁 Estructura del proyecto
text
github-analytics/
├── .github/workflows/       # CI/CD (checks de PR, release)
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
🌐 API REST (puerto 8003)
Todas las rutas protegidas requieren el header Authorization: Bearer <token>.

POST /api/auth/login → obtener token

GET /api/repos → listar repositorios

GET /api/repos/<owner>/<repo>/activity → actividad diaria

GET /api/predictions/<owner>/<repo> → predicciones

POST /api/classify → clasificar un issue

Documentación completa en docs/api_documentation.md.

⚙️ Automatización
Scheduler (ETL + reentrenamiento periódico): make run-scheduler

Exportar a BigQuery: make export-bigquery

Desplegar en Cloud Run: make deploy-gcp

🧪 Testing y CI
bash
make test              # tests unitarios
make test-integration  # integración
make test-all          # lint + tests + seguridad + cobertura
make pre-push          # comprobaciones antes de push
El pipeline de GitHub Actions incluye detección de flaky tests, matriz de bases de datos y escaneo de seguridad.

🛡️ Seguridad
Secretos en .env (no incluido en el control de versiones).

Autenticación JWT en la API.

Contraseñas por defecto solo para desarrollo local; deben cambiarse en producción.

📄 Licencia
MIT – ver LICENSE.

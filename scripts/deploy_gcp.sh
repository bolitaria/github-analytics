#!/bin/bash
# Script de despliegue en Google Cloud Run

set -e  # Detener en caso de error

# Configuración
PROJECT_ID=${GCP_PROJECT_ID:-"tu-proyecto"}
REGION=${GCP_REGION:-"europe-west1"}
SERVICE_NAME="github-analytics-api"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "🚀 Desplegando ${SERVICE_NAME} en ${REGION}..."

# 1. Construir la imagen Docker
echo "📦 Construyendo imagen Docker..."
docker build -t ${IMAGE_NAME} -f deploy/Dockerfile .

# 2. Subir la imagen a Google Container Registry
echo "☁️ Subiendo imagen a GCR..."
docker push ${IMAGE_NAME}

# 3. Desplegar en Cloud Run
echo "🌍 Desplegando en Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --set-env-vars "GITHUB_TOKEN=${GITHUB_TOKEN},CLICKHOUSE_HOST=clickhouse,CLICKHOUSE_PORT=9000,JWT_SECRET_KEY=${JWT_SECRET_KEY}"

echo "✅ Despliegue completado!"
echo "URL del servicio: $(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format='value(status.url)')"
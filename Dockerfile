# Usa una imagen oficial de Python
FROM python:3.12-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Install system dependencies (if needed)
RUN apt-get update && apt-get install -y --no-install-recommends gcc build-essential && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Set environment variables
ENV PORT=8080
ENV CLICKHOUSE_HOST=clickhouse
ENV CLICKHOUSE_PORT=9000
ENV CLICKHOUSE_USER=default
ENV CLICKHOUSE_PASSWORD=
ENV CLICKHOUSE_DATABASE=github_analytics

# Run the API
CMD uvicorn api:app --host 0.0.0.0 --port $PORT
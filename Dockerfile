# Dockerfile for GitHub Analytics Dashboard (API & ETL)
# Base image: Python 3.12 slim
FROM python:3.12-slim

# Avoid writing .pyc files and enable stdout logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies required for building native packages (prophet, cryptography, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    build-essential \
    wget \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .

# Upgrade pip and install dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Environment variables (can be overridden at runtime)
ENV PORT=8000 \
    CLICKHOUSE_HOST=clickhouse \
    CLICKHOUSE_PORT=9000 \
    CLICKHOUSE_USER=default \
    CLICKHOUSE_PASSWORD= \
    CLICKHOUSE_DATABASE=github_analytics

# Expose the API port
EXPOSE $PORT

# Build argument to allow switching between API and ETL entrypoints
# Default: runs the FastAPI/Flask application
ARG ENTRYPOINT_CMD="uvicorn api:app --host 0.0.0.0 --port $PORT"
CMD $ENTRYPOINT_CMD
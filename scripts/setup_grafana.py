#!/usr/bin/env python3
import requests
import json
import time
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

GRAFANA_URL = os.getenv('GRAFANA_URL', 'http://localhost:3001')
GRAFANA_USER = os.getenv('GRAFANA_USER', 'admin')
GRAFANA_PASSWORD = os.getenv('GRAFANA_PASSWORD', 'admin')

def create_datasource():
    datasource = {
        "name": "ClickHouse",
        "type": "grafana-clickhouse-datasource",
        "access": "proxy",
        "url": "http://clickhouse:8123",
        "basicAuth": False,
        "jsonData": {
            "defaultDatabase": "github_analytics",
            "protocol": "http"
        }
    }
    response = requests.post(
        f"{GRAFANA_URL}/api/datasources",
        auth=(GRAFANA_USER, GRAFANA_PASSWORD),
        headers={"Content-Type": "application/json"},
        json=datasource
    )
    if response.status_code in [200, 409]:  # 409 si ya existe
        print("Datasource creado o ya existente.")
    else:
        print(f"Error: {response.status_code} - {response.text}")

def create_dashboard():
    # Cargar dashboard desde archivo JSON (ejemplo)
    dashboard_path = os.path.join(os.path.dirname(__file__), '..', 'grafana', 'dashboards', 'main.json')
    if not os.path.exists(dashboard_path):
        print("Dashboard JSON no encontrado. Usa uno por defecto.")
        return
    with open(dashboard_path) as f:
        dashboard = json.load(f)
    payload = {
        "dashboard": dashboard,
        "overwrite": True
    }
    response = requests.post(
        f"{GRAFANA_URL}/api/dashboards/db",
        auth=(GRAFANA_USER, GRAFANA_PASSWORD),
        headers={"Content-Type": "application/json"},
        json=payload
    )
    if response.status_code in [200, 201]:
        print("Dashboard creado.")
    else:
        print(f"Error: {response.status_code} - {response.text}")

if __name__ == '__main__':
    print("Configurando Grafana...")
    # Esperar que Grafana esté listo
    time.sleep(5)
    create_datasource()
    create_dashboard()
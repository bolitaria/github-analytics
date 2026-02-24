#!/usr/bin/env python3
"""
Deploys a generated dashboard JSON to Grafana via its API.
Usage: python deploy_dashboard.py <dashboard_json_path>
"""
import json
import requests
import os
import sys

GRAFANA_URL = os.getenv('GRAFANA_URL', 'http://localhost:3001')
GRAFANA_USER = os.getenv('GRAFANA_USER', 'admin')
GRAFANA_PASSWORD = os.getenv('GRAFANA_PASSWORD', 'admin')

def load_dashboard_json(path):
    with open(path, 'r') as f:
        return json.load(f)

def deploy_dashboard(dashboard_json):
    url = f"{GRAFANA_URL}/api/dashboards/db"
    auth = (GRAFANA_USER, GRAFANA_PASSWORD)
    headers = {"Content-Type": "application/json"}
    payload = {
        "dashboard": dashboard_json,
        "overwrite": True,
        "folderId": 0
    }
    
    response = requests.post(url, auth=auth, headers=headers, json=payload)
    if response.status_code in [200, 201]:
        print("✅ Dashboard deployed successfully.")
        print("Response:", response.json())
        return True
    else:
        print(f"❌ Failed to deploy dashboard: {response.status_code}")
        print(response.text)
        return False

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python deploy_dashboard.py <dashboard_json_path>")
        sys.exit(1)
    
    path = sys.argv[1]
    if not os.path.exists(path):
        print(f"File not found: {path}")
        sys.exit(1)
    
    dashboard = load_dashboard_json(path)
    deploy_dashboard(dashboard)
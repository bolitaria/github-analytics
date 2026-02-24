#!/usr/bin/env python3
"""
Genera y despliega un dashboard completo con todas las métricas.
Usa los nombres de columna correctos y la sintaxis ${repository:csv} para variables.
"""
import json
import os
import sys
import requests
from datetime import datetime
from typing import Dict, Any

GRAFANA_URL = os.getenv('GRAFANA_URL', 'http://localhost:3001')
GRAFANA_USER = os.getenv('GRAFANA_USER', 'admin')
GRAFANA_PASSWORD = os.getenv('GRAFANA_PASSWORD', 'admin')

def load_thresholds() -> Dict[str, float]:
    try:
        with open('scripts/thresholds.json', 'r') as f:
            data = json.load(f)
            return {
                'events_per_day': float(data.get('events_per_day', 100.0)),
                'issues_per_day': float(data.get('issues_per_day', 10.0)),
                'cfr_threshold': float(data.get('cfr_threshold', 15.0)),
                'mttr_threshold': float(data.get('mttr_threshold', 72.0)),
                'lead_time_threshold': float(data.get('lead_time_threshold', 72.0))
            }
    except FileNotFoundError:
        print("⚠️ thresholds.json no encontrado. Usando valores por defecto.")
        return {
            'events_per_day': 100.0,
            'issues_per_day': 10.0,
            'cfr_threshold': 15.0,
            'mttr_threshold': 72.0,
            'lead_time_threshold': 72.0
        }

def build_dashboard(thresholds: Dict[str, float]) -> Dict[str, Any]:
    dashboard = {
        "title": "GitHub Analytics Enterprise - Full",
        "tags": ["github", "enterprise", "dora", "vodafone"],
        "timezone": "browser",
        "schemaVersion": 27,
        "version": 0,
        "panels": [],
        "templating": {
            "list": [
                {
                    "name": "repository",
                    "type": "query",
                    "datasource": "ClickHouse",
                    "query": "SELECT DISTINCT repo_name FROM github_analytics.events ORDER BY repo_name",
                    "refresh": 1,
                    "includeAll": True,
                    "multi": True,
                    "sort": 1,
                    "format": "csv"  # 🔹 Clave: formato CSV para que ${repository:csv} funcione
                },
                {
                    "name": "time_range",
                    "type": "interval",
                    "options": ["1h", "6h", "24h", "7d", "30d", "90d"],
                    "default": "7d"
                }
            ]
        },
        "time": {"from": "now-30d", "to": "now"},
        "refresh": "5m",
        "annotations": {
            "list": [
                {
                    "name": "Releases",
                    "datasource": "ClickHouse",
                    "enable": True,
                    "iconColor": "rgba(255, 96, 96, 1)",
                    "rawQuery": """
                        SELECT
                            created_at as time,
                            concat('Release: ', payload) as text,
                            'release' as tags
                        FROM github_analytics.events
                        WHERE type = 'ReleaseEvent'
                          AND repo_name IN (${repository:csv})
                          AND created_at >= now() - interval 90 day
                    """,
                    "showIn": 0,
                    "tags": ["release"]
                }
            ]
        }
    }

    # Panel 1: Deployment Frequency (semanas)
    dashboard["panels"].append({
        "id": 1,
        "title": "🚀 Deployment Frequency (Weekly)",
        "type": "timeseries",
        "datasource": "ClickHouse",
        "targets": [{
            "rawSql": """
                SELECT
                    toWeek(created_at) as time,
                    count() as deployments
                FROM github_analytics.events
                WHERE type = 'PullRequestEvent'
                  AND payload LIKE '%merged%'
                  AND repo_name IN (${repository:csv})
                  AND created_at >= now() - interval 90 day
                GROUP BY time
                ORDER BY time
            """,
            "format": "time_series",
            "legendFormat": "Deployments",
            "editorMode": "code"
        }],
        "fieldConfig": {
            "defaults": {
                "unit": "none",
                "thresholds": {
                    "mode": "absolute",
                    "steps": [
                        {"color": "red", "value": 0},
                        {"color": "yellow", "value": 5},
                        {"color": "green", "value": 10}
                    ]
                }
            }
        },
        "gridPos": {"h": 6, "w": 12, "x": 0, "y": 0}
    })

    # Panel 2: Lead Time for Changes
    dashboard["panels"].append({
        "id": 2,
        "title": "📦 Lead Time (hours)",
        "type": "stat",
        "datasource": "ClickHouse",
        "targets": [{
            "rawSql": """
                SELECT
                    ifNull(avg(dateDiff('hour', created_at, toDateTime(JSONExtractString(payload, 'pull_request', 'merged_at')))), 0) as lead_time
                FROM github_analytics.events
                WHERE type = 'PullRequestEvent'
                  AND payload LIKE '%merged%'
                  AND repo_name IN (${repository:csv})
                  AND created_at >= now() - interval 90 day
            """,
            "format": "table",
            "editorMode": "code"
        }],
        "fieldConfig": {
            "defaults": {
                "unit": "h",
                "thresholds": {
                    "mode": "absolute",
                    "steps": [
                        {"color": "green", "value": 0},
                        {"color": "yellow", "value": thresholds['lead_time_threshold'] * 0.5},
                        {"color": "red", "value": thresholds['lead_time_threshold']}
                    ]
                }
            }
        },
        "gridPos": {"h": 4, "w": 6, "x": 12, "y": 0}
    })

    # Panel 3: MTTR
    dashboard["panels"].append({
        "id": 3,
        "title": "⏱️ MTTR (hours)",
        "type": "stat",
        "datasource": "ClickHouse",
        "targets": [{
            "rawSql": """
                SELECT
                    ifNull(avg(dateDiff('hour', created_at, closed_at)), 0) as mttr
                FROM github_analytics.issues
                WHERE repo_name IN (${repository:csv})
                  AND state = 'closed'
                  AND closed_at IS NOT NULL
                  AND created_at >= now() - interval 90 day
            """,
            "format": "table",
            "editorMode": "code"
        }],
        "fieldConfig": {
            "defaults": {
                "unit": "h",
                "thresholds": {
                    "mode": "absolute",
                    "steps": [
                        {"color": "green", "value": 0},
                        {"color": "yellow", "value": thresholds['mttr_threshold'] * 0.5},
                        {"color": "red", "value": thresholds['mttr_threshold']}
                    ]
                }
            }
        },
        "gridPos": {"h": 4, "w": 6, "x": 18, "y": 0}
    })

    # Panel 4: Change Failure Rate
    dashboard["panels"].append({
        "id": 4,
        "title": "💥 Change Failure Rate (%)",
        "type": "gauge",
        "datasource": "ClickHouse",
        "targets": [{
            "rawSql": f"""
                SELECT
                    if(count() > 0,
                       (countIf(payload LIKE '%bug%' OR type = 'IssuesEvent') * 100.0) / count(),
                       0) as cfr
                FROM github_analytics.events
                WHERE repo_name IN (${{repository:csv}})
                  AND created_at >= now() - interval 7 day
            """,
            "format": "table",
            "editorMode": "code"
        }],
        "fieldConfig": {
            "defaults": {
                "unit": "percent",
                "min": 0,
                "max": 100,
                "thresholds": {
                    "mode": "absolute",
                    "steps": [
                        {"color": "green", "value": 0},
                        {"color": "yellow", "value": thresholds['cfr_threshold'] * 0.5},
                        {"color": "red", "value": thresholds['cfr_threshold']}
                    ]
                }
            }
        },
        "gridPos": {"h": 4, "w": 6, "x": 0, "y": 6}
    })

    # Panel 5: Open Issues
    dashboard["panels"].append({
        "id": 5,
        "title": "📌 Open Issues",
        "type": "stat",
        "datasource": "ClickHouse",
        "targets": [{
            "rawSql": """
                SELECT count()
                FROM github_analytics.issues
                WHERE repo_name IN (${repository:csv})
                  AND state = 'open'
            """,
            "format": "table",
            "editorMode": "code"
        }],
        "fieldConfig": {
            "defaults": {
                "unit": "none",
                "thresholds": {
                    "mode": "absolute",
                    "steps": [
                        {"color": "green", "value": 0},
                        {"color": "yellow", "value": 50},
                        {"color": "red", "value": 100}
                    ]
                }
            }
        },
        "gridPos": {"h": 4, "w": 6, "x": 6, "y": 6}
    })

    # Panel 6: Event Traffic with anomaly threshold
    dashboard["panels"].append({
        "id": 6,
        "title": "📊 Event Traffic (per day) with anomaly threshold",
        "type": "timeseries",
        "datasource": "ClickHouse",
        "targets": [{
            "rawSql": f"""
                SELECT
                    toDate(created_at) as time,
                    count() as events
                FROM github_analytics.events
                WHERE repo_name IN (${{repository:csv}})
                  AND $__timeFilter(created_at)
                GROUP BY time
                ORDER BY time
            """,
            "format": "time_series",
            "legendFormat": "Events",
            "editorMode": "code"
        }],
        "fieldConfig": {
            "defaults": {
                "unit": "none",
                "thresholds": {
                    "mode": "absolute",
                    "steps": [
                        {"color": "green", "value": None},
                        {"color": "red", "value": thresholds['events_per_day']}
                    ]
                }
            }
        },
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 10}
    })

    # Panel 7: Issues by Type
    dashboard["panels"].append({
        "id": 7,
        "title": "🥧 Issues by Type (last 7d)",
        "type": "barchart",
        "datasource": "ClickHouse",
        "targets": [{
            "rawSql": """
                SELECT
                    arrayJoin(labels) as label,
                    count() as count
                FROM github_analytics.issues
                WHERE repo_name IN (${repository:csv})
                  AND created_at >= now() - interval 7 day
                GROUP BY label
                ORDER BY count DESC
                LIMIT 10
            """,
            "format": "table",
            "editorMode": "code"
        }],
        "fieldConfig": {
            "defaults": {
                "custom": {
                    "stacking": {"mode": "normal"},
                    "fillOpacity": 80
                }
            }
        },
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 10}
    })

    # Panel 8: System Health Table
    dashboard["panels"].append({
        "id": 8,
        "title": "🩺 System Health (last 24h)",
        "type": "table",
        "datasource": "ClickHouse",
        "targets": [{
            "rawSql": f"""
                WITH daily_stats AS (
                    SELECT
                        avg(c) as mean,
                        stddevPop(c) as stddev
                    FROM (
                        SELECT count() as c
                        FROM github_analytics.events
                        WHERE created_at >= now() - interval 90 day
                        GROUP BY toDate(created_at)
                    )
                ),
                issue_stats AS (
                    SELECT
                        avg(c) as mean_issues,
                        stddevPop(c) as stddev_issues
                    FROM (
                        SELECT count() as c
                        FROM github_analytics.issues
                        WHERE created_at >= now() - interval 90 day
                        GROUP BY toDate(created_at)
                    )
                ),
                today AS (
                    SELECT
                        (SELECT count() FROM github_analytics.events WHERE created_at >= today()) as events_today,
                        (SELECT count() FROM github_analytics.issues WHERE created_at >= today()) as issues_today,
                        (SELECT if(count() > 0, (countIf(payload LIKE '%bug%') * 100.0) / count(), 0) FROM github_analytics.events WHERE created_at >= today()) as cfr_today
                )
                SELECT
                    'Events' as metric,
                    events_today as current,
                    mean + 3*stddev as threshold,
                    if(events_today > mean + 3*stddev, '🔴 UNHEALTHY', '🟢 HEALTHY') as status
                FROM daily_stats, today
                UNION ALL
                SELECT
                    'Issues',
                    issues_today,
                    mean_issues + 3*stddev_issues,
                    if(issues_today > mean_issues + 3*stddev_issues, '🔴 UNHEALTHY', '🟢 HEALTHY')
                FROM issue_stats, today
                UNION ALL
                SELECT
                    'Change Failure Rate',
                    cfr_today,
                    {thresholds['cfr_threshold']},
                    if(cfr_today > {thresholds['cfr_threshold']}, '🔴 UNHEALTHY', '🟢 HEALTHY')
                FROM today
            """,
            "format": "table",
            "editorMode": "code"
        }],
        "gridPos": {"h": 6, "w": 24, "x": 0, "y": 18}
    })

    # Panel 9: Forecast vs Actual
    dashboard["panels"].append({
        "id": 9,
        "title": "🔮 Forecast vs Actual (last 30d)",
        "type": "timeseries",
        "datasource": "ClickHouse",
        "targets": [
            {
                "rawSql": """
                    SELECT
                        toDate(created_at) as time,
                        'actual' as metric,
                        count() as value
                    FROM github_analytics.events
                    WHERE repo_name IN (${repository:csv})
                      AND created_at >= now() - interval 30 day
                    GROUP BY time
                """,
                "format": "time_series",
                "legendFormat": "Actual",
                "editorMode": "code"
            },
            {
                "rawSql": """
                    SELECT
                        forecast_date as time,
                        'predicted' as metric,
                        predicted_events as value
                    FROM github_analytics.forecasts
                    WHERE repository IN (${repository:csv})
                      AND forecast_date >= now() - interval 30 day
                """,
                "format": "time_series",
                "legendFormat": "Predicted",
                "editorMode": "code"
            }
        ],
        "fieldConfig": {
            "defaults": {
                "custom": {
                    "lineInterpolation": "smooth",
                    "showPoints": "never"
                }
            }
        },
        "gridPos": {"h": 8, "w": 24, "x": 0, "y": 24}
    })

    # Panel 10: Top Contributors
    dashboard["panels"].append({
        "id": 10,
        "title": "🏆 Top Contributors (last 30d)",
        "type": "table",
        "datasource": "ClickHouse",
        "targets": [{
            "rawSql": """
                SELECT
                    actor_login as contributor,
                    count() as events,
                    count(DISTINCT repo_name) as repos
                FROM github_analytics.events
                WHERE created_at >= now() - interval 30 day
                  AND repo_name IN (${repository:csv})
                GROUP BY actor_login
                ORDER BY events DESC
                LIMIT 15
            """,
            "format": "table",
            "editorMode": "code"
        }],
        "gridPos": {"h": 6, "w": 12, "x": 0, "y": 32}
    })

    # Panel 11: Repo Activity Ranking
    dashboard["panels"].append({
        "id": 11,
        "title": "📈 Repo Activity Ranking",
        "type": "bargauge",
        "datasource": "ClickHouse",
        "targets": [{
            "rawSql": """
                SELECT
                    repo_name,
                    count() as events,
                    count(DISTINCT actor_login) as contributors
                FROM github_analytics.events
                WHERE created_at >= now() - interval 30 day
                GROUP BY repo_name
                ORDER BY events DESC
                LIMIT 10
            """,
            "format": "table",
            "editorMode": "code"
        }],
        "gridPos": {"h": 6, "w": 12, "x": 12, "y": 32}
    })

    return dashboard

def save_dashboard(dashboard, filename="grafana/dashboards/full_enterprise.json"):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w') as f:
        json.dump(dashboard, f, indent=2)
    print(f"✅ Dashboard guardado en {filename}")

def deploy_dashboard(dashboard):
    url = f"{GRAFANA_URL}/api/dashboards/db"
    auth = (GRAFANA_USER, GRAFANA_PASSWORD)
    headers = {"Content-Type": "application/json"}
    payload = {"dashboard": dashboard, "overwrite": True, "folderId": 0}
    try:
        response = requests.post(url, auth=auth, headers=headers, json=payload)
        if response.status_code in [200, 201]:
            print("✅ Dashboard desplegado en Grafana.")
            print(f"   URL: {GRAFANA_URL}{response.json().get('url', '')}")
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Error de conexión: {e}")

def main():
    print("🚀 Generando dashboard enterprise completo...")
    thresholds = load_thresholds()
    dashboard = build_dashboard(thresholds)
    save_dashboard(dashboard)
    deploy_dashboard(dashboard)

if __name__ == '__main__':
    main()
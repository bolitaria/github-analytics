#!/usr/bin/env python3
"""
Generates an enterprise-level Grafana dashboard JSON with DORA metrics,
Golden Signals, and dynamic thresholds, using the actual ClickHouse schema.
"""
import json
import sys
import os
from datetime import datetime
from typing import Dict, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_thresholds() -> Dict[str, float]:
    """Load thresholds from JSON file or use defaults."""
    try:
        with open('scripts/thresholds.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            'events_per_day': 100.0,
            'issues_per_day': 10.0,
            'last_updated': datetime.now().isoformat()
        }

def generate_dashboard_json(thresholds: Dict[str, float]) -> Dict[str, Any]:
    """Generate the complete Grafana dashboard JSON."""
    
    dashboard = {
        "title": "GitHub Analytics Enterprise",
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
                    "sort": 1
                }
            ]
        },
        "time": {"from": "now-7d", "to": "now"},
        "refresh": "5m"
    }
    
    # Panel 1: Deployment Frequency (DORA) – number of merged PRs in last 7 days
    dashboard["panels"].append({
        "id": 1,
        "title": "🚀 Deployment Frequency (Weekly)",
        "type": "stat",
        "datasource": "ClickHouse",
        "targets": [{
            "rawSql": """
                SELECT count() as deployments
                FROM github_analytics.events
                WHERE type = 'PullRequestEvent'
                  AND payload LIKE '%merged%'
                  AND repo_name IN ($repository)
                  AND created_at >= now() - interval 7 day
            """,
            "format": "table"
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
        "gridPos": {"h": 4, "w": 6, "x": 0, "y": 0}
    })
    
    # Panel 2: Change Failure Rate (%) – issues labeled as bug or events with 'bug' in payload
    dashboard["panels"].append({
        "id": 2,
        "title": "💥 Change Failure Rate (%)",
        "type": "gauge",
        "datasource": "ClickHouse",
        "targets": [{
            "rawSql": """
                SELECT 
                    (countIf(payload LIKE '%bug%' OR type = 'IssuesEvent') * 100.0) / count() as cfr
                FROM github_analytics.events
                WHERE repo_name IN ($repository)
                  AND created_at >= now() - interval 7 day
            """,
            "format": "table"
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
                        {"color": "yellow", "value": 15},
                        {"color": "red", "value": 30}
                    ]
                }
            }
        },
        "gridPos": {"h": 4, "w": 6, "x": 6, "y": 0}
    })
    
    # Panel 3: Mean Time to Resolve (hours) – average time from issue creation to closing
    dashboard["panels"].append({
        "id": 3,
        "title": "⏱️ MTTR (hours)",
        "type": "stat",
        "datasource": "ClickHouse",
        "targets": [{
            "rawSql": """
                SELECT avg(dateDiff('hour', created_at, closed_at))
                FROM github_analytics.issues
                WHERE repo_name IN ($repository)
                  AND state = 'closed'
                  AND closed_at IS NOT NULL
                  AND created_at >= now() - interval 30 day
            """,
            "format": "table"
        }],
        "fieldConfig": {
            "defaults": {
                "unit": "h",
                "thresholds": {
                    "mode": "absolute",
                    "steps": [
                        {"color": "green", "value": 0},
                        {"color": "yellow", "value": 24},
                        {"color": "red", "value": 72}
                    ]
                }
            }
        },
        "gridPos": {"h": 4, "w": 6, "x": 12, "y": 0}
    })
    
    # Panel 4: Open Issues Count (replaces Lead Time due to data limitations)
    dashboard["panels"].append({
        "id": 4,
        "title": "📌 Open Issues",
        "type": "stat",
        "datasource": "ClickHouse",
        "targets": [{
            "rawSql": """
                SELECT count()
                FROM github_analytics.issues
                WHERE repo_name IN ($repository)
                  AND state = 'open'
            """,
            "format": "table"
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
        "gridPos": {"h": 4, "w": 6, "x": 18, "y": 0}
    })
    
    # Panel 5: Event Traffic (per day) – with dynamic threshold
    dashboard["panels"].append({
        "id": 5,
        "title": "📊 Event Traffic (per day)",
        "type": "timeseries",
        "datasource": "ClickHouse",
        "targets": [{
            "rawSql": """
                SELECT 
                    toDate(created_at) as time,
                    count() as events
                FROM github_analytics.events
                WHERE repo_name IN ($repository)
                  AND $__timeFilter(created_at)
                GROUP BY time
                ORDER BY time
            """,
            "format": "time_series",
            "legendFormat": "Events"
        }],
        "fieldConfig": {
            "defaults": {
                "unit": "none",
                "thresholds": {
                    "mode": "absolute",
                    "steps": [
                        {"color": "green", "value": None},
                        {"color": "red", "value": thresholds.get('events_per_day', 100)}
                    ]
                }
            }
        },
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 4}
    })
    
    # Panel 6: Issues by Type (Pie Chart) – using labels array
    dashboard["panels"].append({
        "id": 6,
        "title": "🥧 Issues by Type (last 7d)",
        "type": "piechart",
        "datasource": "ClickHouse",
        "targets": [{
            "rawSql": """
                SELECT 
                    arrayJoin(labels) as label,
                    count() as count
                FROM github_analytics.issues
                WHERE repo_name IN ($repository)
                  AND created_at >= now() - interval 7 day
                GROUP BY label
                ORDER BY count DESC
                LIMIT 10
            """,
            "format": "table"
        }],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 4}
    })
    
    # Panel 7: System Health (Status table)
    dashboard["panels"].append({
        "id": 7,
        "title": "🩺 System Health (last 24h)",
        "type": "table",
        "datasource": "ClickHouse",
        "targets": [{
            "rawSql": f"""
                SELECT 
                    'Events (24h)' as metric,
                    (SELECT count() FROM github_analytics.events WHERE created_at >= now() - interval 1 day) as current,
                    {thresholds.get('events_per_day', 100)} as threshold,
                    if(current > {thresholds.get('events_per_day', 100)}, '🔴 UNHEALTHY', '🟢 HEALTHY') as status
                UNION ALL
                SELECT 
                    'Issues (24h)',
                    (SELECT count() FROM github_analytics.issues WHERE created_at >= now() - interval 1 day),
                    {thresholds.get('issues_per_day', 10)},
                    if(current > {thresholds.get('issues_per_day', 10)}, '🔴 UNHEALTHY', '🟢 HEALTHY')
                UNION ALL
                SELECT 
                    'Change Failure Rate',
                    (SELECT (countIf(payload LIKE '%bug%') * 100.0) / count() FROM github_analytics.events WHERE created_at >= now() - interval 1 day),
                    15,
                    if(current > 15, '🔴 UNHEALTHY', '🟢 HEALTHY')
            """,
            "format": "table"
        }],
        "gridPos": {"h": 6, "w": 24, "x": 0, "y": 12}
    })
    
    # Panel 8: Forecast vs Actual – using forecasts table
    dashboard["panels"].append({
        "id": 8,
        "title": "🔮 Forecast vs Actual",
        "type": "timeseries",
        "datasource": "ClickHouse",
        "targets": [
            {
                "rawSql": """
                    SELECT 
                        toDate(created_at) as time,
                        count() as actual
                    FROM github_analytics.events
                    WHERE repo_name IN ($repository)
                      AND created_at >= now() - interval 30 day
                    GROUP BY time
                    ORDER BY time
                """,
                "format": "time_series",
                "legendFormat": "Actual"
            },
            {
                "rawSql": """
                    SELECT 
                        forecast_date as time,
                        predicted_events as predicted,
                        lower_bound,
                        upper_bound
                    FROM github_analytics.forecasts
                    WHERE repository IN ($repository)
                      AND forecast_date >= now() - interval 30 day
                    ORDER BY time
                """,
                "format": "time_series",
                "legendFormat": "Predicted"
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
        "gridPos": {"h": 8, "w": 24, "x": 0, "y": 18}
    })
    
    return dashboard

def main():
    thresholds = load_thresholds()
    dashboard = generate_dashboard_json(thresholds)
    print(json.dumps(dashboard, indent=2))

if __name__ == '__main__':
    main()
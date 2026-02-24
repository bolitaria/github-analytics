#!/usr/bin/env python3
"""
Calcula umbrales dinámicos (media + 3σ) para eventos e issues.
Guarda los umbrales en scripts/thresholds.json.
"""
import sys
import os
import json
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.clickhouse import clickhouse_client
from src.utils.logger import logger

def calculate_thresholds():
    thresholds = {}
    try:
        # Umbral para eventos diarios (usamos stddevPop para población completa)
        result = clickhouse_client.execute_query("""
            SELECT avg(c) + 3 * stddevPop(c)
            FROM (
                SELECT count() as c
                FROM github_analytics.events
                WHERE created_at >= now() - interval 90 day
                GROUP BY toDate(created_at)
            )
        """)
        thresholds['events_per_day'] = float(result[0][0]) if result and result[0][0] else 100.0

        # Umbral para issues diarios
        result = clickhouse_client.execute_query("""
            SELECT avg(c) + 3 * stddevPop(c)
            FROM (
                SELECT count() as c
                FROM github_analytics.issues
                WHERE created_at >= now() - interval 90 day
                GROUP BY toDate(created_at)
            )
        """)
        thresholds['issues_per_day'] = float(result[0][0]) if result and result[0][0] else 10.0

        # Umbrales fijos para otras métricas (podrían calcularse dinámicamente si se desea)
        thresholds['cfr_threshold'] = 15.0
        thresholds['mttr_threshold'] = 72.0
        thresholds['lead_time_threshold'] = 72.0

        thresholds['last_updated'] = datetime.now(timezone.utc).isoformat()
        thresholds['method'] = 'mean + 3σ (normal distribution)'

        os.makedirs('scripts', exist_ok=True)
        with open('scripts/thresholds.json', 'w') as f:
            json.dump(thresholds, f, indent=2)

        logger.info(f"✅ Thresholds calculados: {thresholds}")

    except Exception as e:
        logger.error(f"❌ Error calculando thresholds: {e}")
        # Fallback a valores por defecto
        thresholds = {
            'events_per_day': 100.0,
            'issues_per_day': 10.0,
            'cfr_threshold': 15.0,
            'mttr_threshold': 72.0,
            'lead_time_threshold': 72.0,
            'last_updated': datetime.now(timezone.utc).isoformat(),
            'method': 'default fallback'
        }
        with open('scripts/thresholds.json', 'w') as f:
            json.dump(thresholds, f, indent=2)

if __name__ == '__main__':
    calculate_thresholds()
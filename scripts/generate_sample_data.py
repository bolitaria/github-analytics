#!/usr/bin/env python3

import sys
import os
import json
from datetime import datetime, timedelta
import random

# Añadir el directorio raíz al path para importar src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.clickhouse import clickhouse_client
from src.utils.logger import logger

def generate_sample_events():
    """Genera eventos de GitHub de ejemplo para demostración"""
    
    repos = [
        "ClickHouse/ClickHouse",
        "nodejs/node", 
        "microsoft/vscode",
        "facebook/react",
        "tensorflow/tensorflow"
    ]
    
    users = ["alice", "bob", "carol", "dave", "eve", "frank", "grace", "henry"]
    event_types = ["PushEvent", "PullRequestEvent", "IssuesEvent", "WatchEvent", "ForkEvent"]
    
    sample_events = []
    
    # Generar eventos de los últimos 30 días
    for i in range(500):  # 500 eventos de ejemplo
        days_ago = random.randint(0, 30)
        hours_ago = random.randint(0, 23)
        minutes_ago = random.randint(0, 59)
        
        # Usar datetime objects directamente - NO convertir a string
        event_time = datetime.utcnow() - timedelta(
            days=days_ago, 
            hours=hours_ago, 
            minutes=minutes_ago
        )
        
        event = {
            'id': f'sample_event_{i}',
            'type': random.choice(event_types),
            'actor_login': random.choice(users),
            'repo_name': random.choice(repos),
            'created_at': event_time,  # Mantener como objeto datetime
            'payload': json.dumps({
                'action': 'opened' if random.random() > 0.5 else 'closed',
                'size': random.randint(1, 10)
            }),
            'org_login': random.choice([None, 'microsoft', 'google', 'facebook'])
        }
        
        sample_events.append(event)
    
    # Insertar en ClickHouse
    if sample_events:
        clickhouse_client.insert_batch('github_analytics.events', sample_events)
        logger.info(f"Generated {len(sample_events)} sample events")
    
    return sample_events

if __name__ == '__main__':
    generate_sample_events()
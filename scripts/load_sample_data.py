#!/usr/bin/env python3

import json
from datetime import datetime, timedelta
from src.database.clickhouse import clickhouse_client
from src.utils.logger import logger

def load_sample_data():
    """Carga datos de ejemplo para desarrollo"""
    
    sample_events = [
        {
            'id': '123456',
            'type': 'PushEvent',
            'actor_login': 'developer1',
            'repo_name': 'example/repo1',
            'created_at': datetime.now() - timedelta(days=1),
            'payload': json.dumps({'push_id': 123, 'size': 2}),
            'org_login': None
        },
        {
            'id': '123457',
            'type': 'IssuesEvent',
            'actor_login': 'developer2',
            'repo_name': 'example/repo1',
            'created_at': datetime.now() - timedelta(hours=12),
            'payload': json.dumps({'action': 'opened'}),
            'org_login': 'example'
        },
        {
            'id': '123458',
            'type': 'WatchEvent',
            'actor_login': 'developer3',
            'repo_name': 'example/repo2',
            'created_at': datetime.now() - timedelta(hours=6),
            'payload': json.dumps({'action': 'started'}),
            'org_login': None
        }
    ]
    
    # Insertar datos de ejemplo
    clickhouse_client.insert_batch('events', sample_events)
    logger.info("Sample data loaded successfully")

if __name__ == '__main__':
    load_sample_data()
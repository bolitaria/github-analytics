#!/usr/bin/env python3
"""
Script para configurar dashboards de Grafana automáticamente
"""
import json
import requests
import time
import logging
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GrafanaDashboardSetup:
    def __init__(self, base_url: str = "http://localhost:3001", 
                 username: str = "admin", password: str = "admin"):
        self.base_url = base_url
        self.auth = (username, password)
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def test_connection(self) -> bool:
        """Verificar conexión con Grafana"""
        try:
            response = requests.get(
                f"{self.base_url}/api/health",
                auth=self.auth,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error conectando a Grafana: {e}")
            return False
    
    def create_dashboard(self, dashboard_config: Dict[str, Any]) -> bool:
        """Crear o actualizar dashboard en Grafana"""
        try:
            # Configurar el dashboard para sobrescribir si existe
            dashboard_config["overwrite"] = True
            
            response = requests.post(
                f"{self.base_url}/api/dashboards/db",
                auth=self.auth,
                headers=self.headers,
                json={"dashboard": dashboard_config},
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"Dashboard '{dashboard_config.get('title')}' creado exitosamente")
                return True
            else:
                logger.error(f"Error creando dashboard: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error creando dashboard: {e}")
            return False
    
    def setup_github_analytics_dashboard(self):
        """Configurar dashboard principal de analytics de GitHub"""
        dashboard = {
            "title": "GitHub Analytics Overview",
            "tags": ["github", "analytics"],
            "timezone": "browser",
            "panels": self._get_main_dashboard_panels(),
            "templating": {
                "list": [
                    {
                        "name": "repository",
                        "type": "query",
                        "dataSource": "ClickHouse",
                        "query": "SELECT DISTINCT repo_name FROM github_events ORDER BY repo_name",
                        "refresh": 1,
                        "includeAll": True,
                        "multi": True,
                        "sort": 1
                    },
                    {
                        "name": "event_type",
                        "type": "query",
                        "dataSource": "ClickHouse",
                        "query": "SELECT DISTINCT event_type FROM github_events ORDER BY event_type",
                        "refresh": 1,
                        "includeAll": True,
                        "multi": True,
                        "sort": 1
                    }
                ]
            },
            "time": {
                "from": "now-7d",
                "to": "now"
            },
            "refresh": "5m"
        }
        
        return self.create_dashboard(dashboard)
    
    def _get_main_dashboard_panels(self):
        """Definir paneles del dashboard principal"""
        return [
            # Panel 1: Eventos por tipo
            {
                "id": 1,
                "title": "Eventos por Tipo",
                "type": "piechart",
                "targets": [
                    {
                        "rawSql": "SELECT event_type, count(*) as count FROM github_events WHERE $__timeFilter(created_at) AND repo_name IN ($repository) GROUP BY event_type ORDER BY count DESC",
                        "format": "table",
                        "datasource": "ClickHouse"
                    }
                ],
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
            },
            # Panel 2: Actividad temporal
            {
                "id": 2,
                "title": "Actividad por Hora",
                "type": "graph",
                "targets": [
                    {
                        "rawSql": "SELECT toStartOfHour(created_at) as time, count(*) as events FROM github_events WHERE $__timeFilter(created_at) AND repo_name IN ($repository) GROUP BY time ORDER BY time",
                        "format": "time_series",
                        "datasource": "ClickHouse"
                    }
                ],
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
            },
            # Panel 3: Top repositorios
            {
                "id": 3,
                "title": "Top Repositorios por Actividad",
                "type": "bargauge",
                "targets": [
                    {
                        "rawSql": "SELECT repo_name, count(*) as events FROM github_events WHERE $__timeFilter(created_at) GROUP BY repo_name ORDER BY events DESC LIMIT 10",
                        "format": "table",
                        "datasource": "ClickHouse"
                    }
                ],
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8}
            },
            # Panel 4: Top contribuidores
            {
                "id": 4,
                "title": "Top Contribuidores",
                "type": "table",
                "targets": [
                    {
                        "rawSql": "SELECT actor_login, count(*) as events, count(DISTINCT repo_name) as repos FROM github_events WHERE $__timeFilter(created_at) AND repo_name IN ($repository) GROUP BY actor_login ORDER BY events DESC LIMIT 15",
                        "format": "table",
                        "datasource": "ClickHouse"
                    }
                ],
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8}
            }
        ]

def main():
    """Función principal"""
    logger.info("Iniciando configuración de dashboards de Grafana...")
    
    setup = GrafanaDashboardSetup()
    
    # Esperar a que Grafana esté listo
    logger.info("Esperando que Grafana esté disponible...")
    for i in range(30):
        if setup.test_connection():
            logger.info("Grafana está disponible")
            break
        time.sleep(2)
    else:
        logger.error("Grafana no está disponible después de 60 segundos")
        return
    
    # Configurar dashboards
    logger.info("Configurando dashboard principal...")
    if setup.setup_github_analytics_dashboard():
        logger.info("Dashboard principal configurado exitosamente")
    else:
        logger.error("Error configurando dashboard principal")

if __name__ == "__main__":
    main()
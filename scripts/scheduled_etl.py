#!/usr/bin/env python3
"""
Script para ejecución programada del ETL
"""
import schedule
import time
import logging
import sys
import os
from datetime import datetime

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.etl.github_etl import GitHubETL
from src.database.clickhouse_client import ClickHouseClient
from src.config.settings import GITHUB_TOKEN, REPOSITORIES

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/etl_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ETLScheduler:
    def __init__(self):
        self.clickhouse_client = ClickHouseClient()
        self.etl = GitHubETL(self.clickhouse_client, GITHUB_TOKEN)
        self.success_count = 0
        self.error_count = 0
    
    def run_etl_job(self):
        """Ejecutar job ETL para todos los repositorios"""
        logger.info(f"Iniciando job ETL programado - {datetime.now()}")
        
        try:
            for repo in REPOSITORIES:
                logger.info(f"Procesando repositorio: {repo}")
                try:
                    self.etl.process_repository(repo)
                    self.success_count += 1
                    logger.info(f"Repositorio {repo} procesado exitosamente")
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error procesando repositorio {repo}: {e}")
            
            logger.info(f"Job ETL completado. Exitosa: {self.success_count}, Errores: {self.error_count}")
            
        except Exception as e:
            logger.error(f"Error en job ETL: {e}")
    
    def run_once(self):
        """Ejecutar ETL una vez"""
        logger.info("Ejecutando ETL una vez...")
        self.run_etl_job()
    
    def start_scheduler(self):
        """Iniciar el scheduler programado"""
        logger.info("Iniciando scheduler ETL...")
        
        # Programar jobs
        schedule.every(1).hour.do(self.run_etl_job)  # Cada hora
        schedule.every().day.at("02:00").do(self.run_etl_job)  # Backup diario a las 2 AM
        
        # Ejecutar inmediatamente la primera vez
        self.run_etl_job()
        
        logger.info("Scheduler iniciado. Jobs programados:")
        for job in schedule.jobs:
            logger.info(f"  - {job}")
        
        # Mantener el scheduler corriendo
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Revisar cada minuto
            except KeyboardInterrupt:
                logger.info("Scheduler detenido por el usuario")
                break
            except Exception as e:
                logger.error(f"Error en scheduler: {e}")
                time.sleep(60)

def main():
    """Función principal"""
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        # Ejecutar una sola vez
        scheduler = ETLScheduler()
        scheduler.run_once()
    else:
        # Ejecutar en modo scheduler
        scheduler = ETLScheduler()
        scheduler.start_scheduler()

if __name__ == "__main__":
    main()
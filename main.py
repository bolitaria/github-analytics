#!/usr/bin/env python3
import os
os.environ['CLICKHOUSE_HOST'] = 'localhost'
os.environ['CLICKHOUSE_PORT'] = '9001'
from src.etl.github_etl import GitHubETL
from src.utils.logger import logger

# Lista de repositorios a analizar (propio + proyectos destacados)
repositories = [
    # Tu repositorio
    "bolitaria/github-analytics",
    # AI & ML de alto crecimiento
    "vllm-project/vllm",
    "infiniflow/ragflow",
    "sgl-project/sglang",
    # Comunidad masiva
    "home-assistant/core",
    # Datos y visualización
    "public-apis/public-apis",
    "ossu/computer-science",
    # Herramientas de desarrollo y aprendizaje
    "TheAlgorithms/Python",
    "freeCodeCamp/freeCodeCamp",
    "EbookFoundation/free-programming-books",
]

def run_etl_for_all():
    etl = GitHubETL()
    for repo in repositories:
        owner, repo_name = repo.split('/')
        logger.info(f"Procesando {owner}/{repo_name}...")
        etl.run_etl(owner, repo_name, days_back=30)  # Últimos 30 días

if __name__ == "__main__":
    run_etl_for_all()
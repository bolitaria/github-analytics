#!/usr/bin/env python3
import os
os.environ['CLICKHOUSE_HOST'] = 'localhost'
os.environ['CLICKHOUSE_PORT'] = '9001'
from src.etl.github_etl import GitHubETL
from src.utils.logger import logger

# Leer repositorios desde variable de entorno GITHUB_REPOS
# Formato: "owner1/repo1,owner2/repo2,..."
repos_env = os.getenv('GITHUB_REPOS', '').strip()
if repos_env:
    repositories = [r.strip() for r in repos_env.split(',') if r.strip()]
    logger.info(f"Usando repositorios desde GITHUB_REPOS: {repositories}")
else:
    # Lista por defecto (puedes modificarla)
    repositories = [
        "bolitaria/github-analytics",
        "vllm-project/vllm",
        "infiniflow/ragflow",
        "sgl-project/sglang",
        "home-assistant/core",
        "public-apis/public-apis",
        "ossu/computer-science",
        "TheAlgorithms/Python",
        "freeCodeCamp/freeCodeCamp",
        "EbookFoundation/free-programming-books",
    ]
    logger.info("Usando lista de repositorios por defecto (puedes sobreescribirla con GITHUB_REPOS en .env)")

def run_etl_for_all():
    etl = GitHubETL()
    for repo in repositories:
        owner, repo_name = repo.split('/')
        logger.info(f"Procesando {owner}/{repo_name}...")
        try:
            etl.run_etl(owner, repo_name, days_back=30)
        except Exception as e:
            logger.error(f"Error procesando {owner}/{repo_name}: {e}")
            # Continuar con el siguiente repo sin detener el proceso

if __name__ == "__main__":
    run_etl_for_all()

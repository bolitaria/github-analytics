#!/usr/bin/env python3

from src.etl.github_etl import GitHubETL
from src.utils.logger import logger

def main():
    etl = GitHubETL()
    
    # Repositories to monitor
    repositories = [
        ('ClickHouse', 'ClickHouse'),
        ('nodejs', 'node'),
        ('microsoft', 'vscode')
    ]
    
    for owner, repo in repositories:
        try:
            etl.run_etl(owner, repo, days_back=30)
            
            # Get and display stats
            stats = etl.get_repository_stats(f"{owner}/{repo}")
            logger.info(f"Stats for {owner}/{repo}: {stats}")
            
        except Exception as e:
            logger.error(f"Error processing {owner}/{repo}: {e}")

if __name__ == '__main__':
    main()
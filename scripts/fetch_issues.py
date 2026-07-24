#!/usr/bin/env python3
import requests, os, sys, time
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.clickhouse import clickhouse_client
from src.utils.logger import logger

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
HEADERS = {'Authorization': f'token {GITHUB_TOKEN}'} if GITHUB_TOKEN else {}

def fetch_issues(owner, repo, max_pages=10):
    issues = []
    page = 1
    while page <= max_pages:
        url = f'https://api.github.com/repos/{owner}/{repo}/issues'
        params = {'state': 'all', 'per_page': 100, 'page': page}
        resp = requests.get(url, headers=HEADERS, params=params)
        if resp.status_code != 200:
            logger.error(f"Error {resp.status_code}: {resp.text}")
            break
        data = resp.json()
        if not data:
            break
        data = [i for i in data if 'pull_request' not in i]
        for i in data:
            labels = [l['name'] for l in i.get('labels', [])]
            issues.append({
                'id': i['id'],
                'number': i['number'],
                'title': i['title'],
                'body': i.get('body', '') or '',
                'labels': labels,
                'state': i['state'],
                'created_at': i['created_at'],
                'closed_at': i.get('closed_at'),
                'user_login': i['user']['login'],
                'repo_name': f"{owner}/{repo}"
            })
        logger.info(f"Page {page}: {len(data)} issues")
        page += 1
        time.sleep(0.5)
    return issues

def save_issues(issues):
    if not issues:
        return
    query = """
    INSERT INTO github_analytics.issues
    (id, number, title, body, labels, state, created_at, closed_at, user_login, repo_name)
    VALUES
    """
    values = []
    for i in issues:
        values.append((
            i['id'], i['number'], i['title'], i['body'],
            i['labels'], i['state'],
            datetime.fromisoformat(i['created_at'].replace('Z', '+00:00')),
            datetime.fromisoformat(i['closed_at'].replace('Z', '+00:00')) if i['closed_at'] else None,
            i['user_login'], i['repo_name']
        ))
    clickhouse_client.client.execute(query, values)
    logger.info(f"Insertados {len(issues)} issues")

if __name__ == '__main__':
    repos_env = os.getenv('GITHUB_REPOS', '')
    if repos_env:
        repos = [r.strip().split('/') for r in repos_env.split(',') if r.strip()]
        repos = [(owner, repo) for owner, repo in repos]
    else:
        # Default hardcoded for standalone script
        repos = [('ClickHouse', 'ClickHouse'), ('nodejs', 'node'), ('microsoft', 'vscode')]
    for owner, repo in repos:
        logger.info(f"Obteniendo issues de {owner}/{repo}")
        issues = fetch_issues(owner, repo)
        save_issues(issues)

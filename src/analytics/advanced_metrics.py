"""
Módulo para métricas avanzadas y KPIs de GitHub
"""

import logging
from typing import Any, Dict, List

from src.database.clickhouse_client import ClickHouseClient

logger = logging.getLogger(__name__)


class AdvancedGitHubMetrics:
    def __init__(self, clickhouse_client: ClickHouseClient):
        self.client = clickhouse_client

    def get_developer_velocity_metrics(
        self, repo_name: str, days: int = 30
    ) -> Dict[str, Any]:
        """Calcular métricas de velocidad de desarrollo"""
        query = """
        SELECT
            countIf(event_type = 'PushEvent') as push_events,
            countIf(event_type = 'PullRequestEvent') as pr_events,
            countIf(event_type = 'IssuesEvent') as issue_events,
            countIf(event_type = 'WatchEvent') as watch_events,
            count(DISTINCT actor_login) as active_developers,
            count(DISTINCT toDate(created_at)) as active_days,
            round(count(*) / active_days, 2) as events_per_day
        FROM github_events
        WHERE repo_name = %(repo_name)s
          AND created_at >= now() - INTERVAL %(days)s DAY
        """

        result = self.client.execute_query(
            query, {"repo_name": repo_name, "days": days}
        )

        if result:
            return {
                "push_events": result[0][0],
                "pr_events": result[0][1],
                "issue_events": result[0][2],
                "watch_events": result[0][3],
                "active_developers": result[0][4],
                "active_days": result[0][5],
                "events_per_day": result[0][6],
                "velocity_score": self._calculate_velocity_score(result[0]),
            }
        return {}

    def _calculate_velocity_score(self, metrics_data) -> float:
        """Calcular score de velocidad basado en múltiples métricas"""
        push_weight = 0.3
        pr_weight = 0.4
        developer_weight = 0.2
        activity_weight = 0.1

        push_score = min(metrics_data[0] / 100, 1.0)  # Normalizar a max 100 pushes
        pr_score = min(metrics_data[1] / 50, 1.0)  # Normalizar a max 50 PRs
        developer_score = min(
            metrics_data[4] / 10, 1.0
        )  # Normalizar a max 10 developers
        activity_score = min(
            metrics_data[6] / 20, 1.0
        )  # Normalizar a max 20 eventos/día

        total_score = (
            push_score * push_weight
            + pr_score * pr_weight
            + developer_score * developer_weight
            + activity_score * activity_weight
        )

        return round(total_score * 100, 2)  # Convertir a porcentaje

    def get_community_health_metrics(self, repo_name: str) -> Dict[str, Any]:
        """Calcular métricas de salud de la comunidad"""
        query = """
        WITH repo_stats AS (
            SELECT
                count(*) as total_events,
                count(DISTINCT actor_login) as total_contributors,
                countIf(event_type = 'WatchEvent') as stars,
                countIf(event_type = 'ForkEvent') as forks,
                countIf(event_type = 'IssuesEvent') as total_issues,
                countIf(event_type = 'PullRequestEvent') as total_prs,
                min(created_at) as first_event_date
            FROM github_events
            WHERE repo_name = %(repo_name)s
        ),
        recent_contributors AS (
            SELECT count(DISTINCT actor_login) as recent_contributors
            FROM github_events
            WHERE repo_name = %(repo_name)s
              AND created_at >= now() - INTERVAL 90 DAY
        )
        SELECT
            rs.total_events,
            rs.total_contributors,
            rc.recent_contributors,
            rs.stars,
            rs.forks,
            rs.total_issues,
            rs.total_prs,
            rs.first_event_date,
            round(rc.recent_contributors * 100.0 / rs.total_contributors, 2) as contributor_retention_rate
        FROM repo_stats rs, recent_contributors rc
        """

        result = self.client.execute_query(query, {"repo_name": repo_name})

        if result:
            return {
                "total_events": result[0][0],
                "total_contributors": result[0][1],
                "recent_contributors": result[0][2],
                "stars": result[0][3],
                "forks": result[0][4],
                "total_issues": result[0][5],
                "total_prs": result[0][6],
                "first_event_date": (
                    result[0][7].strftime("%Y-%m-%d") if result[0][7] else None
                ),
                "contributor_retention_rate": result[0][8],
                "health_score": self._calculate_health_score(result[0]),
            }
        return {}

    def _calculate_health_score(self, metrics_data) -> float:
        """Calcular score de salud de la comunidad"""
        contributor_score = min(metrics_data[1] / 50, 1.0)  # Max 50 contributors
        retention_score = min(metrics_data[8] / 100, 1.0)  # Retention rate
        activity_score = min(metrics_data[0] / 1000, 1.0)  # Max 1000 eventos
        engagement_score = min(
            (metrics_data[3] + metrics_data[4]) / 100, 1.0
        )  # Stars + forks

        weights = [0.3, 0.3, 0.2, 0.2]  # Pesos para cada métrica
        scores = [contributor_score, retention_score, activity_score, engagement_score]

        total_score = sum(score * weight for score, weight in zip(scores, weights))
        return round(total_score * 100, 2)

    def get_trending_repositories(
        self, days: int = 7, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Obtener repositorios trending"""
        query = """
        SELECT
            repo_name,
            count(*) as event_count,
            count(DISTINCT actor_login) as contributor_count,
            countIf(event_type = 'WatchEvent') as new_stars,
            countIf(event_type = 'ForkEvent') as new_forks,
            round(event_count / %(days)s, 2) as daily_avg_events,
            round((new_stars * 3 + new_forks * 2 + contributor_count) / %(days)s, 2) as trend_score
        FROM github_events
        WHERE created_at >= now() - INTERVAL %(days)s DAY
        GROUP BY repo_name
        ORDER BY trend_score DESC
        LIMIT %(limit)s
        """

        results = self.client.execute_query(query, {"days": days, "limit": limit})

        trending_repos = []
        for row in results:
            trending_repos.append(
                {
                    "repository": row[0],
                    "event_count": row[1],
                    "contributor_count": row[2],
                    "new_stars": row[3],
                    "new_forks": row[4],
                    "daily_avg_events": row[5],
                    "trend_score": row[6],
                    "trend_level": self._get_trend_level(row[6]),
                }
            )

        return trending_repos

    def _get_trend_level(self, trend_score: float) -> str:
        """Determinar nivel de trending basado en el score"""
        if trend_score >= 20:
            return "high"
        elif trend_score >= 10:
            return "medium"
        elif trend_score >= 5:
            return "low"
        else:
            return "stable"

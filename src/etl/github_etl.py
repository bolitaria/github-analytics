import requests
import time
import random
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from src.config.settings import settings
from src.database.clickhouse import clickhouse_client
from src.models.github_models import GitHubEvent
from src.utils.logger import logger


class GitHubETL:
    def __init__(self):
        self.headers = {}
        if settings.has_github_token:
            self.headers = {
                "Authorization": f"token {settings.GITHUB_TOKEN}",
                "Accept": "application/vnd.github.v3+json",
            }
        self.base_url = settings.GITHUB_API_BASE_URL

    def fetch_events(
        self, owner: str, repo: str, since: Optional[datetime] = None
    ) -> List[dict]:
        """Fetch events from GitHub API or generate sample data"""

        # If no token, use demo data
        if not settings.has_github_token:
            logger.info("No GitHub token found. Using demo mode with sample data")
            return self._generate_demo_events(owner, repo, since)

        # Original code with real API
        url = f"{self.base_url}/repos/{owner}/{repo}/events"
        params = {}

        if since:
            params["since"] = since.isoformat()

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()

            time.sleep(settings.GITHUB_RATE_LIMIT_DELAY)
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error fetching events from GitHub API: {e}")
            return []

    def _generate_demo_events(
        self, owner: str, repo: str, since: Optional[datetime] = None
    ) -> List[dict]:
        """Generate demo events for development"""
        event_types = [
            "PushEvent",
            "PullRequestEvent",
            "IssuesEvent",
            "WatchEvent",
            "ForkEvent",
            "CreateEvent",
        ]
        users = [
            "alice-dev",
            "bob-contributor",
            "carol-maintainer",
            "dave-reviewer",
            "eve-bot",
        ]
        actions = ["opened", "closed", "created", "reopened", "merged"]

        demo_events = []
        num_events = random.randint(80, 200)

        base_date = since if since else datetime.now() - timedelta(days=30)

        for i in range(num_events):
            # Generate random timestamp within the range
            days_offset = random.randint(0, 30)
            hours_offset = random.randint(0, 23)
            minutes_offset = random.randint(0, 59)

            event_time = base_date + timedelta(
                days=days_offset, hours=hours_offset, minutes=minutes_offset
            )

            event_type = random.choice(event_types)

            # Create appropriate payload based on event type
            payload = {}
            if event_type == "PushEvent":
                payload = {
                    "push_id": random.randint(1000, 9999),
                    "size": random.randint(1, 10),
                    "distinct_size": random.randint(1, 8),
                }
            elif event_type in ["PullRequestEvent", "IssuesEvent"]:
                payload = {
                    "action": random.choice(actions),
                    "number": random.randint(1, 500),
                }
            elif event_type == "CreateEvent":
                payload = {
                    "ref": f"feature-{random.randint(1, 20)}",
                    "ref_type": random.choice(["branch", "tag"]),
                }
            else:
                payload = {"action": random.choice(actions)}

            event = {
                "id": f"demo_{owner}_{repo}_{i}_{random.randint(1000, 9999)}",
                "type": event_type,
                "actor": {"login": random.choice(users)},
                "repo": {"name": f"{owner}/{repo}"},
                "created_at": event_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "payload": payload,
                "org": {"login": owner} if random.random() > 0.7 else None,
            }

            demo_events.append(event)

        logger.info(f"Generated {len(demo_events)} demo events for {owner}/{repo}")
        return demo_events

    def transform_event(self, event_data: dict) -> GitHubEvent:
        """Transform raw event data to our model"""
        try:
            # Handle both API response and demo data format
            actor_login = (
                event_data["actor"]["login"]
                if isinstance(event_data["actor"], dict)
                else event_data["actor"]
            )
            repo_name = (
                event_data["repo"]["name"]
                if isinstance(event_data["repo"], dict)
                else event_data["repo"]
            )

            # Parse datetime - handle both string and datetime objects
            if isinstance(event_data["created_at"], str):
                created_at = datetime.strptime(
                    event_data["created_at"], "%Y-%m-%dT%H:%M:%SZ"
                )
            else:
                created_at = event_data["created_at"]

            org_login = None
            if event_data.get("org"):
                org_login = (
                    event_data["org"]["login"]
                    if isinstance(event_data["org"], dict)
                    else event_data["org"]
                )

            return GitHubEvent(
                id=event_data["id"],
                type=event_data["type"],
                actor_login=actor_login,
                repo_name=repo_name,
                created_at=created_at,
                payload=event_data.get("payload", {}),
                org_login=org_login,
            )
        except KeyError as e:
            logger.error(f"Error transforming event data: missing key {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error transforming event: {e}")
            raise

    def load_events(self, events: List[GitHubEvent]):
        """Load events into ClickHouse"""
        if not events:
            logger.warning("No events to load")
            return

        data = []
        for event in events:
            data.append(
                {
                    "id": event.id,
                    "type": event.type,
                    "actor_login": event.actor_login,
                    "repo_name": event.repo_name,
                    "created_at": event.created_at,
                    "payload": json.dumps(
                        event.payload
                    ),  # Convert dict to JSON string for storage
                    "org_login": event.org_login,
                }
            )

        try:
            clickhouse_client.insert_batch("github_analytics.events", data)
            logger.info(f"Successfully loaded {len(events)} events into ClickHouse")
        except Exception as e:
            logger.error(f"Error loading events into ClickHouse: {e}")
            raise

    def run_etl(self, owner: str, repo: str, days_back: int = 7):
        """Run complete ETL process"""
        since = datetime.now() - timedelta(days=days_back)

        logger.info(f"Starting ETL for {owner}/{repo} since {since}")

        try:
            raw_events = self.fetch_events(owner, repo, since)
            if not raw_events:
                logger.warning(f"No events found for {owner}/{repo}")
                return

            transformed_events = [self.transform_event(event) for event in raw_events]
            self.load_events(transformed_events)

            logger.info(
                f"ETL completed for {owner}/{repo}. Processed {len(transformed_events)} events"
            )

            # Show sample stats
            stats = self.get_repository_stats(f"{owner}/{repo}")
            logger.info(f"Repository stats: {stats}")

        except Exception as e:
            logger.error(f"ETL failed for {owner}/{repo}: {e}")
            raise

    def get_repository_stats(self, repo_name: str) -> Dict[str, Any]:
        """Get analytics for a repository"""
        query = """
            SELECT 
                count(*) as total_events,
                uniq(actor_login) as unique_contributors,
                max(created_at) as last_activity
            FROM github_analytics.events 
            WHERE repo_name = %(repo_name)s
        """

        try:
            result = clickhouse_client.execute_query(query, {"repo_name": repo_name})

            if result and result[0]:
                return {
                    "total_events": result[0][0],
                    "unique_contributors": result[0][1],
                    "last_activity": result[0][2],
                }
            return {}
        except Exception as e:
            logger.error(f"Error getting repository stats: {e}")
            return {}

    def generate_sample_data(self, count: int = 100):
        """Generate sample data for development (alternative method)"""
        logger.info(f"Generating {count} sample events using direct method")

        event_types = [
            "PushEvent",
            "IssuesEvent",
            "WatchEvent",
            "PullRequestEvent",
            "ForkEvent",
        ]
        repos = ["sample/repo1", "sample/repo2", "sample/repo3", "sample/repo4"]
        users = ["dev1", "dev2", "dev3", "dev4", "dev5"]
        orgs = ["sample-org", None, None, None]  # Mostly no org, sometimes has org

        sample_events = []
        for i in range(count):
            event = GitHubEvent(
                id=f"sample_direct_{i}_{random.randint(1000, 9999)}",
                type=random.choice(event_types),
                actor_login=random.choice(users),
                repo_name=random.choice(repos),
                created_at=datetime.now() - timedelta(days=random.randint(0, 365)),
                payload={
                    "sample": True,
                    "index": i,
                    "action": random.choice(["opened", "closed", "created"]),
                    "size": random.randint(1, 15),
                },
                org_login=random.choice(orgs),
            )
            sample_events.append(event)

        self.load_events(sample_events)
        logger.info(f"Generated {count} sample events using direct method")

        return sample_events

    def get_detailed_analytics(self, repo_name: str, days: int = 30) -> Dict[str, Any]:
        """Get detailed analytics for advanced reporting"""
        query = """
            SELECT 
                type as event_type,
                count(*) as event_count,
                uniq(actor_login) as unique_users,
                toDate(created_at) as date
            FROM github_analytics.events 
            WHERE repo_name = %(repo_name)s
              AND created_at >= now() - INTERVAL %(days)s DAY
            GROUP BY event_type, date
            ORDER BY date DESC, event_count DESC
        """

        try:
            result = clickhouse_client.execute_query(
                query, {"repo_name": repo_name, "days": days}
            )

            # Process result into structured format
            analytics = {
                "repo_name": repo_name,
                "period_days": days,
                "daily_breakdown": {},
                "event_type_summary": {},
            }

            for row in result:
                event_type, count, unique_users, date = row
                date_str = date.strftime("%Y-%m-%d")

                if date_str not in analytics["daily_breakdown"]:
                    analytics["daily_breakdown"][date_str] = {}

                analytics["daily_breakdown"][date_str][event_type] = {
                    "count": count,
                    "unique_users": unique_users,
                }

                if event_type not in analytics["event_type_summary"]:
                    analytics["event_type_summary"][event_type] = 0
                analytics["event_type_summary"][event_type] += count

            return analytics

        except Exception as e:
            logger.error(f"Error getting detailed analytics: {e}")
            return {}

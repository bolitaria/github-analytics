from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


class GitHubEvent(BaseModel):
    id: str
    type: str
    actor_login: str
    repo_name: str
    created_at: datetime
    payload: Dict[str, Any]
    org_login: Optional[str] = None


class RepositoryStats(BaseModel):
    repo_name: str
    total_events: int
    unique_contributors: int
    last_activity: datetime
    event_types: Dict[str, int]


class ContributorStats(BaseModel):
    username: str
    total_contributions: int
    first_contribution: datetime
    last_contribution: datetime
    contribution_types: Dict[str, int]

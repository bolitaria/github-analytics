import pytest
from src.etl.github_etl import GitHubETL
from src.models.github_models import GitHubEvent

def test_transform_event():
    etl = GitHubETL()
    sample_event = {
        'id': '123',
        'type': 'PushEvent',
        'actor': {'login': 'testuser'},
        'repo': {'name': 'test/repo'},
        'created_at': '2023-01-01T00:00:00Z',
        'payload': {'push_id': 123},
        'org': None
    }
    
    transformed = etl.transform_event(sample_event)
    assert transformed.id == '123'
    assert transformed.actor_login == 'testuser'
    assert transformed.repo_name == 'test/repo'
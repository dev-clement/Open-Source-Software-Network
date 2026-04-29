"""
Unit tests for get_contribution_service dependency in contributions/api.py.
"""
import pytest
from fastapi import Depends, HTTPException, status
from app.contributions.api import apply_to_project, ContributionCreate
from app.contributions.api import get_contribution_service

class DummySession:
    pass

class DummyService:
    def __init__(self):
        self.called = False
        self.args = None
        self.raise_exc = None
    async def apply_to_project(self, contribution_data):
        self.called = True
        self.args = contribution_data
        if self.raise_exc:
            raise self.raise_exc
        return 'contribution_result'

@pytest.mark.asyncio
async def test_apply_to_project_calls_service():
    service = DummyService()
    contribution = ContributionCreate(user_id=1, project_id=999)  # project_id will be overwritten
    project_id = 42
    result = await apply_to_project(project_id, contribution, service)
    assert service.called
    assert service.args.project_id == project_id
    assert result is None  # The endpoint does not return a value

@pytest.mark.asyncio
async def test_apply_to_project_raises_http_exception():
    service = DummyService()
    service.raise_exc = Exception('fail')
    contribution = ContributionCreate(user_id=1, project_id=999)
    project_id = 42
    with pytest.raises(HTTPException) as exc_info:
        await apply_to_project(project_id, contribution, service)
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert 'fail' in str(exc_info.value.detail)

def test_get_contribution_service_returns_service(monkeypatch):
    """
    Test that get_contribution_service returns a SqlContributionService
    with a SqlContributionRepository using the provided session.
    """
    dummy_session = DummySession()


    # Patch SqlContributionRepository and SqlContributionService in the api module
    created = {}
    def fake_repo(session):
        created['session'] = session
        return 'repo_instance'
    monkeypatch.setattr('app.contributions.api.SqlContributionRepository', fake_repo)

    def fake_service(repo):
        created['repo'] = repo
        return 'service_instance'
    monkeypatch.setattr('app.contributions.api.SqlContributionService', fake_service)

    # Call the dependency function
    result = get_contribution_service(dummy_session)

    assert result == 'service_instance'
    assert created['session'] is dummy_session
    assert created['repo'] == 'repo_instance'

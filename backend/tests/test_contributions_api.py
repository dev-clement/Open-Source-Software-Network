"""
Unit tests for get_contribution_service dependency in contributions/api.py.
"""
import pytest
from fastapi import Depends, HTTPException, status
from app.contributions.api import apply_to_project, ContributionCreate, list_my_contributions
from app.contributions.api import get_contribution_service, update_status
from app.contributions.exception import UserNotFound, ProjectNotFound
from app.domain.enums import ContributionStatus

import types
from app.auth.schemas import User
import asyncio

class DummySession:
    pass

class DummyService:
    def __init__(self):
        self.called = False
        self.args = None
        self.raise_exc = None
        self.list_by_user_called = False
        self.list_by_user_args = None
        self.list_by_user_return = None
    async def apply_to_project(self, contribution_data):
        self.called = True
        self.args = contribution_data
        if self.raise_exc:
            raise self.raise_exc
        return 'contribution_result'

    async def list_by_user(self, user_id):
        self.list_by_user_called = True
        self.list_by_user_args = user_id
        if self.raise_exc:
            raise self.raise_exc
        return self.list_by_user_return

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


# --- Tests for /me endpoint (list_my_contributions) ---

@pytest.mark.asyncio
async def test_list_my_contributions_valid_user():
    service = DummyService()
    user = User(id=123, username='bob', email='bob@example.com', created_at='2024-01-01T00:00:00', updated_at='2024-01-01T00:00:00')
    expected_contributions = ['contrib1', 'contrib2']
    service.list_by_user_return = expected_contributions
    result = await list_my_contributions(user, service)
    assert service.list_by_user_called
    assert service.list_by_user_args == user.id
    assert result == expected_contributions


# Test for UserNotFound exception handling (should return 404)
@pytest.mark.asyncio
async def test_list_my_contributions_user_not_found():
    service = DummyService()
    user = User(id=999, username='ghost', email='ghost@example.com', created_at='2024-01-01T00:00:00', updated_at='2024-01-01T00:00:00')
    service.raise_exc = UserNotFound(user.id)
    with pytest.raises(HTTPException) as exc_info:
        await list_my_contributions(user, service)
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert f"User with id {user.id} does not exist." in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_list_my_contributions_raises_http_exception():
    service = DummyService()
    user = User(id=1, username='alice', email='alice@example.com', created_at='2024-01-01T00:00:00', updated_at='2024-01-01T00:00:00')
    service.raise_exc = Exception('unexpected error')
    with pytest.raises(HTTPException) as exc_info:
        await list_my_contributions(user, service)
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert 'unexpected error' in str(exc_info.value.detail)

# --- Tests for update_status endpoint ---

class DummyServiceWithUpdate(DummyService):
    async def update_status(self, user_id, project_id, new_status):
        if self.raise_exc:
            raise self.raise_exc
        return f"updated:{user_id}:{project_id}:{new_status}"

def test_update_status_project_id_none():
    service = DummyServiceWithUpdate()
    with pytest.raises(HTTPException) as exc_info:
        # project_id is None
        asyncio.run(update_status(None, 1, ContributionStatus.INTERESTED, service))
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert "Project ID is required." in str(exc_info.value.detail)

def test_update_status_user_id_none():
    service = DummyServiceWithUpdate()
    with pytest.raises(HTTPException) as exc_info:
        # user_id is None
        asyncio.run(update_status(1, None, ContributionStatus.INTERESTED, service))
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert "User ID is required." in str(exc_info.value.detail)

def test_update_status_project_not_found():
    service = DummyServiceWithUpdate()
    service.raise_exc = ProjectNotFound(42)
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(update_status(1, 42, ContributionStatus.INTERESTED, service))
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "Project with id 42 does not exist." in str(exc_info.value.detail)

def test_update_status_user_not_found():
    service = DummyServiceWithUpdate()
    service.raise_exc = UserNotFound(99)
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(update_status(1, 2, ContributionStatus.INTERESTED, service))
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "User with id 99 does not exist." in str(exc_info.value.detail)

def test_update_status_generic_exception():
    service = DummyServiceWithUpdate()
    service.raise_exc = Exception("fail")
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(update_status(1, 2, ContributionStatus.INTERESTED, service))
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "fail" in str(exc_info.value.detail)

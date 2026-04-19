import os
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI
from fastapi.testclient import TestClient

os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_DB", "test")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5432")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-key-at-least-32-bytes")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("JWT_EXPIRATION_MINUTES", "30")

from app.projects import api as projects_api
from app.projects.schemas import Project, ProjectCreate
from app.projects.exception import CreateProjectError
from app.projects.exception import ProjectNotFoundError


NOW = datetime(2026, 4, 17, 10, 0, 0)

VALID_PAYLOAD = {
    "title": "My OSS Project",
    "description": "An open source project",
    "repository_url": "https://github.com/example/project",
    "help_wanted": False,
}


class FakeProjectService:
    def __init__(
        self,
        *,
        project_to_return: Optional[Project] = None,
        projects_to_return: Optional[List[Project]] = None,
        all_projects: Optional[List[Project]] = None,
        error_to_raise: Optional[Exception] = None,
    ):
        self.project_to_return = project_to_return
        self.projects_to_return = projects_to_return or []
        self.all_projects = all_projects
        self.error_to_raise = error_to_raise
        self.create_calls = 0
        self.list_calls = 0
        self.list_help_wanted_calls = 0
        self.get_by_id_calls = 0
        self.last_project_data: Optional[ProjectCreate] = None
        self.last_skip: Optional[int] = None
        self.last_limit: Optional[int] = None
        self.last_help_wanted_skip: Optional[int] = None
        self.last_help_wanted_limit: Optional[int] = None
        self.last_project_id: Optional[int] = None

    async def create(self, project_data: ProjectCreate) -> Project:
        self.create_calls += 1
        self.last_project_data = project_data
        if self.error_to_raise is not None:
            raise self.error_to_raise
        return self.project_to_return

    async def list(self, skip: int = 0, limit: int = 100) -> List[Project]:
        self.list_calls += 1
        self.last_skip = skip
        self.last_limit = limit
        if self.error_to_raise is not None:
            raise self.error_to_raise
        if self.all_projects is not None:
            return self.all_projects[skip:skip + limit]
        return self.projects_to_return

    async def get_by_id(self, project_id: int) -> Project:
        self.get_by_id_calls += 1
        self.last_project_id = project_id
        if self.error_to_raise is not None:
            raise self.error_to_raise
        return self.project_to_return

    async def list_help_wanted(self, skip: int = 0, limit: int = 100) -> List[Project]:
        self.list_help_wanted_calls += 1
        self.last_help_wanted_skip = skip
        self.last_help_wanted_limit = limit
        if self.error_to_raise is not None:
            raise self.error_to_raise
        if self.all_projects is not None:
            return [project for project in self.all_projects if project.help_wanted][skip:skip + limit]
        return [project for project in self.projects_to_return if project.help_wanted][skip:skip + limit]


def _build_project(
    *,
    project_id: int = 1,
    title: str = VALID_PAYLOAD["title"],
    description: str = VALID_PAYLOAD["description"],
    repository_url: str = VALID_PAYLOAD["repository_url"],
    help_wanted: bool = VALID_PAYLOAD["help_wanted"],
) -> Project:
    return Project(
        id=project_id,
        title=title,
        description=description,
        repository_url=repository_url,
        help_wanted=help_wanted,
        created_at=NOW,
        updated_at=NOW,
    )


def _build_client(
    fake_service: FakeProjectService,
    *,
    raise_server_exceptions: bool = True,
) -> TestClient:
    app = FastAPI()
    app.include_router(projects_api.router)
    app.dependency_overrides[projects_api.get_project_service] = lambda: fake_service
    return TestClient(app, raise_server_exceptions=raise_server_exceptions)


# ---------------------------------------------------------------------------
# Success path
# ---------------------------------------------------------------------------

def test_list_projects_returns_200_on_success():
    fake_service = FakeProjectService(projects_to_return=[_build_project()])
    client = _build_client(fake_service)

    response = client.get("/projects/")

    assert response.status_code == 200


def test_list_projects_returns_projects_from_service():
    fake_service = FakeProjectService(
        projects_to_return=[
            _build_project(project_id=1, title="Project One"),
            _build_project(project_id=2, title="Project Two"),
        ]
    )
    client = _build_client(fake_service)

    response = client.get("/projects/")

    assert [project["title"] for project in response.json()] == ["Project One", "Project Two"]


def test_list_projects_delegates_to_service_once():
    fake_service = FakeProjectService(projects_to_return=[])
    client = _build_client(fake_service)

    client.get("/projects/")

    assert fake_service.list_calls == 1


def test_list_projects_forwards_pagination_to_service():
    fake_service = FakeProjectService(projects_to_return=[])
    client = _build_client(fake_service)

    client.get("/projects/?skip=5&limit=20")

    assert fake_service.last_skip == 5
    assert fake_service.last_limit == 20


def test_list_projects_returns_paginated_subset_for_skip_and_limit():
    fake_service = FakeProjectService(
        all_projects=[
            _build_project(project_id=1, title="Project One"),
            _build_project(project_id=2, title="Project Two"),
            _build_project(project_id=3, title="Project Three"),
            _build_project(project_id=4, title="Project Four"),
        ]
    )
    client = _build_client(fake_service)

    response = client.get("/projects/?skip=1&limit=2")

    assert [project["id"] for project in response.json()] == [2, 3]


def test_list_projects_does_not_swallow_unexpected_errors():
    fake_service = FakeProjectService(error_to_raise=RuntimeError("unexpected"))
    client = _build_client(fake_service, raise_server_exceptions=False)

    response = client.get("/projects/")

    assert response.status_code == 500


def test_get_project_returns_200_on_success():
    fake_service = FakeProjectService(project_to_return=_build_project(project_id=7))
    client = _build_client(fake_service)

    response = client.get("/projects/7")

    assert response.status_code == 200


def test_get_project_returns_project_from_service():
    fake_service = FakeProjectService(project_to_return=_build_project(project_id=7, title="Project Seven"))
    client = _build_client(fake_service)

    response = client.get("/projects/7")

    assert response.json()["id"] == 7
    assert response.json()["title"] == "Project Seven"


def test_get_project_delegates_to_service_with_project_id():
    fake_service = FakeProjectService(project_to_return=_build_project(project_id=99))
    client = _build_client(fake_service)

    client.get("/projects/99")

    assert fake_service.get_by_id_calls == 1
    assert fake_service.last_project_id == 99


def test_get_project_returns_404_on_project_not_found_error():
    fake_service = FakeProjectService(error_to_raise=ProjectNotFoundError(404))
    client = _build_client(fake_service)

    response = client.get("/projects/404")

    assert response.status_code == 404
    assert response.json()["detail"] == "Project with id 404 not found"


def test_get_project_does_not_swallow_unexpected_errors():
    fake_service = FakeProjectService(error_to_raise=RuntimeError("unexpected"))
    client = _build_client(fake_service, raise_server_exceptions=False)

    response = client.get("/projects/1")

    assert response.status_code == 500


def test_list_help_wanted_projects_returns_200_on_success():
    fake_service = FakeProjectService(
        projects_to_return=[
            _build_project(project_id=1, title="Help One", help_wanted=True),
            _build_project(project_id=2, title="Help Two", help_wanted=True),
        ]
    )
    client = _build_client(fake_service)

    response = client.get("/projects/help-wanted")

    assert response.status_code == 200


def test_list_help_wanted_projects_returns_only_help_wanted_entries():
    fake_service = FakeProjectService(
        all_projects=[
            _build_project(project_id=1, title="Help One", help_wanted=True),
            _build_project(project_id=2, title="Closed", help_wanted=False),
            _build_project(project_id=3, title="Help Two", help_wanted=True),
        ]
    )
    client = _build_client(fake_service)

    response = client.get("/projects/help-wanted")

    assert [project["id"] for project in response.json()] == [1, 3]
    assert all(project["help_wanted"] for project in response.json())


def test_list_help_wanted_projects_delegates_to_service_once():
    fake_service = FakeProjectService(projects_to_return=[])
    client = _build_client(fake_service)

    client.get("/projects/help-wanted")

    assert fake_service.list_help_wanted_calls == 1


def test_list_help_wanted_projects_forwards_pagination_to_service():
    fake_service = FakeProjectService(projects_to_return=[])
    client = _build_client(fake_service)

    client.get("/projects/help-wanted?skip=3&limit=4")

    assert fake_service.last_help_wanted_skip == 3
    assert fake_service.last_help_wanted_limit == 4


def test_list_help_wanted_projects_does_not_swallow_unexpected_errors():
    fake_service = FakeProjectService(error_to_raise=RuntimeError("unexpected"))
    client = _build_client(fake_service, raise_server_exceptions=False)

    response = client.get("/projects/help-wanted")

    assert response.status_code == 500

def test_create_project_returns_201_on_success():
    fake_service = FakeProjectService(project_to_return=_build_project())
    client = _build_client(fake_service)

    response = client.post("/projects/", json=VALID_PAYLOAD)

    assert response.status_code == 201


def test_create_project_response_contains_project_id():
    fake_service = FakeProjectService(project_to_return=_build_project(project_id=42))
    client = _build_client(fake_service)

    response = client.post("/projects/", json=VALID_PAYLOAD)

    assert response.json()["id"] == 42


def test_create_project_response_contains_title():
    fake_service = FakeProjectService(project_to_return=_build_project())
    client = _build_client(fake_service)

    response = client.post("/projects/", json=VALID_PAYLOAD)

    assert response.json()["title"] == VALID_PAYLOAD["title"]


def test_create_project_response_contains_repository_url():
    fake_service = FakeProjectService(project_to_return=_build_project())
    client = _build_client(fake_service)

    response = client.post("/projects/", json=VALID_PAYLOAD)

    assert response.json()["repository_url"] == VALID_PAYLOAD["repository_url"]


def test_create_project_response_contains_help_wanted():
    fake_service = FakeProjectService(project_to_return=_build_project())
    client = _build_client(fake_service)

    response = client.post("/projects/", json=VALID_PAYLOAD)

    assert response.json()["help_wanted"] == VALID_PAYLOAD["help_wanted"]


def test_create_project_delegates_to_service():
    fake_service = FakeProjectService(project_to_return=_build_project())
    client = _build_client(fake_service)

    client.post("/projects/", json=VALID_PAYLOAD)

    assert fake_service.create_calls == 1


def test_create_project_forwards_title_to_service():
    fake_service = FakeProjectService(project_to_return=_build_project())
    client = _build_client(fake_service)

    client.post("/projects/", json=VALID_PAYLOAD)

    assert fake_service.last_project_data.title == VALID_PAYLOAD["title"]


def test_create_project_forwards_repository_url_to_service():
    fake_service = FakeProjectService(project_to_return=_build_project())
    client = _build_client(fake_service)

    client.post("/projects/", json=VALID_PAYLOAD)

    assert str(fake_service.last_project_data.repository_url) == VALID_PAYLOAD["repository_url"]


def test_create_project_forwards_help_wanted_to_service():
    fake_service = FakeProjectService(project_to_return=_build_project(help_wanted=True))
    client = _build_client(fake_service)

    payload = {**VALID_PAYLOAD, "help_wanted": True}
    client.post("/projects/", json=payload)

    assert fake_service.last_project_data.help_wanted is True


# ---------------------------------------------------------------------------
# Conflict path
# ---------------------------------------------------------------------------

def test_create_project_returns_409_on_create_project_error():
    fake_service = FakeProjectService(
        error_to_raise=CreateProjectError("A project with that URL already exists.")
    )
    client = _build_client(fake_service)

    response = client.post("/projects/", json=VALID_PAYLOAD)

    assert response.status_code == 409


def test_create_project_409_response_contains_error_detail():
    error_message = "A project with that URL already exists."
    fake_service = FakeProjectService(error_to_raise=CreateProjectError(error_message))
    client = _build_client(fake_service)

    response = client.post("/projects/", json=VALID_PAYLOAD)

    assert response.json()["detail"] == error_message


def test_create_project_does_not_swallow_unexpected_errors():
    fake_service = FakeProjectService(error_to_raise=RuntimeError("unexpected"))
    client = _build_client(fake_service, raise_server_exceptions=False)

    response = client.post("/projects/", json=VALID_PAYLOAD)

    assert response.status_code == 500


# ---------------------------------------------------------------------------
# Validation path
# ---------------------------------------------------------------------------

def test_create_project_returns_422_when_title_is_missing():
    fake_service = FakeProjectService(project_to_return=_build_project())
    client = _build_client(fake_service)

    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "title"}
    response = client.post("/projects/", json=payload)

    assert response.status_code == 422


def test_create_project_returns_422_when_repository_url_is_invalid():
    fake_service = FakeProjectService(project_to_return=_build_project())
    client = _build_client(fake_service)

    payload = {**VALID_PAYLOAD, "repository_url": "not-a-url"}
    response = client.post("/projects/", json=payload)

    assert response.status_code == 422


def test_create_project_returns_422_when_title_is_empty_string():
    fake_service = FakeProjectService(project_to_return=_build_project())
    client = _build_client(fake_service)

    payload = {**VALID_PAYLOAD, "title": ""}
    response = client.post("/projects/", json=payload)

    assert response.status_code == 422

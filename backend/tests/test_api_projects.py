import os
from datetime import datetime
from typing import Optional

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
        error_to_raise: Optional[Exception] = None,
    ):
        self.project_to_return = project_to_return
        self.error_to_raise = error_to_raise
        self.create_calls = 0
        self.last_project_data: Optional[ProjectCreate] = None

    async def create(self, project_data: ProjectCreate) -> Project:
        self.create_calls += 1
        self.last_project_data = project_data
        if self.error_to_raise is not None:
            raise self.error_to_raise
        return self.project_to_return


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

import asyncio
import os
from datetime import datetime
from typing import Optional

from fastapi import FastAPI
from fastapi.testclient import TestClient

# Ensure settings can be instantiated when importing app.auth.api.
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_DB", "test")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5432")

from app.auth import api as auth_api
from app.auth.schemas import User, UserCreate


NOW = datetime(2026, 4, 12, 10, 30, 0)


class FakeAuthService:
    def __init__(self, *, user_to_return: Optional[User] = None, error_to_raise: Optional[Exception] = None):
        """Initialize a configurable fake auth service for signup tests.

        :param user_to_return: User instance returned by ``register`` when no
            error is configured.
        :param error_to_raise: Exception raised by ``register`` to test error
            mapping behavior.
        :return: None.
        """
        self.user_to_return = user_to_return
        self.error_to_raise = error_to_raise
        self.register_calls = 0
        self.last_register_payload: Optional[UserCreate] = None

    async def register(self, user_data: UserCreate) -> User:
        """Simulate signup registration behavior for unit tests.

        The method records invocation metadata so tests can assert delegation
        behavior and payload forwarding from the API layer.

        :param user_data: Signup payload received by the fake service.
        :return: Preconfigured user instance when no error is configured.
        :raises Exception: Re-raises the configured ``error_to_raise`` when
            present.
        """
        self.register_calls += 1
        self.last_register_payload = user_data
        if self.error_to_raise is not None:
            raise self.error_to_raise
        return self.user_to_return


def _build_user(
    *,
    user_id: int = 1,
    username: str = "alice",
    email: str = "alice@example.com",
    github_page: Optional[str] = None,
    bio: Optional[str] = None,
) -> User:
    """Create a deterministic user fixture for signup endpoint tests.

    :param user_id: Identifier assigned to the returned user model.
    :param username: Username assigned to the returned user model.
    :param email: Email assigned to the returned user model.
    :param github_page: Optional GitHub profile URL assigned to the user.
    :param bio: Optional user biography text.
    :return: A fully populated ``User`` instance with stable timestamps.
    """
    return User(
        id=user_id,
        username=username,
        email=email,
        github_page=github_page,
        bio=bio,
        created_at=NOW,
        updated_at=NOW,
    )


def _build_client(
    fake_service: FakeAuthService,
    *,
    raise_server_exceptions: bool = True,
) -> TestClient:
    """Build a FastAPI test client with auth service dependency overridden.

    :param fake_service: Fake service injected into the auth router
        dependency graph.
    :return: Configured ``TestClient`` ready for signup endpoint tests.
    """
    app = FastAPI()
    app.include_router(auth_api.router)
    app.dependency_overrides[auth_api.get_auth_service] = lambda: fake_service
    return TestClient(app, raise_server_exceptions=raise_server_exceptions)


def test_signup_returns_201_on_success_with_required_fields_only():
    fake_service = FakeAuthService(user_to_return=_build_user())
    client = _build_client(fake_service)

    response = client.post(
        "/auth/signup",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "plain-password",
        },
    )

    assert response.status_code == 201
    assert response.json()["username"] == "alice"
    assert response.json()["email"] == "alice@example.com"


def test_signup_returns_201_on_success_with_optional_fields():
    fake_service = FakeAuthService(
        user_to_return=_build_user(
            github_page="https://github.com/alice",
            bio="Open-source contributor",
        )
    )
    client = _build_client(fake_service)

    response = client.post(
        "/auth/signup",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "plain-password",
            "github_page": "https://github.com/alice",
            "bio": "Open-source contributor",
        },
    )

    assert response.status_code == 201
    assert response.json()["bio"] == "Open-source contributor"
    assert response.json()["github_page"] == "https://github.com/alice"


def test_signup_response_does_not_expose_password_field():
    fake_service = FakeAuthService(user_to_return=_build_user())
    client = _build_client(fake_service)

    response = client.post(
        "/auth/signup",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "plain-password",
        },
    )

    assert response.status_code == 201
    assert "password" not in response.json()


def test_signup_calls_register_once_on_success():
    fake_service = FakeAuthService(user_to_return=_build_user())
    client = _build_client(fake_service)

    response = client.post(
        "/auth/signup",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "plain-password",
        },
    )

    assert response.status_code == 201
    assert fake_service.register_calls == 1


def test_signup_passes_expected_payload_to_service_register():
    fake_service = FakeAuthService(user_to_return=_build_user())
    client = _build_client(fake_service)

    request_payload = {
        "username": "alice",
        "email": "alice@example.com",
        "password": "plain-password",
        "github_page": "https://github.com/alice",
        "bio": "bio text",
    }
    response = client.post("/auth/signup", json=request_payload)

    assert response.status_code == 201
    assert fake_service.last_register_payload is not None
    assert fake_service.last_register_payload.username == "alice"
    assert str(fake_service.last_register_payload.email) == "alice@example.com"
    assert fake_service.last_register_payload.password == "plain-password"
    assert str(fake_service.last_register_payload.github_page) == "https://github.com/alice"
    assert fake_service.last_register_payload.bio == "bio text"


def test_signup_maps_duplicate_email_to_conflict_409():
    fake_service = FakeAuthService(error_to_raise=ValueError("Email already exists"))
    client = _build_client(fake_service)

    response = client.post(
        "/auth/signup",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "plain-password",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Email already exists"


def test_signup_preserves_value_error_message_in_response_detail():
    fake_service = FakeAuthService(error_to_raise=ValueError("Custom signup rule failed"))
    client = _build_client(fake_service)

    response = client.post(
        "/auth/signup",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "plain-password",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Custom signup rule failed"


def test_signup_returns_422_for_empty_json_body():
    fake_service = FakeAuthService(user_to_return=_build_user())
    client = _build_client(fake_service)

    response = client.post("/auth/signup", json={})

    assert response.status_code == 422


def test_signup_returns_422_when_username_is_missing():
    fake_service = FakeAuthService(user_to_return=_build_user())
    client = _build_client(fake_service)

    response = client.post(
        "/auth/signup",
        json={"email": "alice@example.com", "password": "plain-password"},
    )

    assert response.status_code == 422


def test_signup_returns_422_when_email_is_missing():
    fake_service = FakeAuthService(user_to_return=_build_user())
    client = _build_client(fake_service)

    response = client.post(
        "/auth/signup",
        json={"username": "alice", "password": "plain-password"},
    )

    assert response.status_code == 422


def test_signup_returns_422_when_password_is_missing():
    fake_service = FakeAuthService(user_to_return=_build_user())
    client = _build_client(fake_service)

    response = client.post(
        "/auth/signup",
        json={"username": "alice", "email": "alice@example.com"},
    )

    assert response.status_code == 422


def test_signup_returns_422_for_invalid_email_format():
    fake_service = FakeAuthService(user_to_return=_build_user())
    client = _build_client(fake_service)

    response = client.post(
        "/auth/signup",
        json={
            "username": "alice",
            "email": "invalid-email",
            "password": "plain-password",
        },
    )

    assert response.status_code == 422


def test_signup_returns_422_for_invalid_github_url():
    fake_service = FakeAuthService(user_to_return=_build_user())
    client = _build_client(fake_service)

    response = client.post(
        "/auth/signup",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "plain-password",
            "github_page": "not-a-url",
        },
    )

    assert response.status_code == 422


def test_signup_returns_422_for_empty_username():
    fake_service = FakeAuthService(user_to_return=_build_user())
    client = _build_client(fake_service)

    response = client.post(
        "/auth/signup",
        json={
            "username": "",
            "email": "alice@example.com",
            "password": "plain-password",
        },
    )

    assert response.status_code == 422


def test_signup_returns_422_for_username_longer_than_255():
    fake_service = FakeAuthService(user_to_return=_build_user())
    client = _build_client(fake_service)

    response = client.post(
        "/auth/signup",
        json={
            "username": "a" * 256,
            "email": "alice@example.com",
            "password": "plain-password",
        },
    )

    assert response.status_code == 422


def test_signup_returns_422_for_empty_password():
    fake_service = FakeAuthService(user_to_return=_build_user())
    client = _build_client(fake_service)

    response = client.post(
        "/auth/signup",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "",
        },
    )

    assert response.status_code == 422


def test_signup_returns_422_for_password_longer_than_255():
    fake_service = FakeAuthService(user_to_return=_build_user())
    client = _build_client(fake_service)

    response = client.post(
        "/auth/signup",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "p" * 256,
        },
    )

    assert response.status_code == 422


def test_signup_returns_created_user_identifier_and_timestamps():
    fake_service = FakeAuthService(user_to_return=_build_user(user_id=42))
    client = _build_client(fake_service)

    response = client.post(
        "/auth/signup",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "plain-password",
        },
    )

    body = response.json()
    assert response.status_code == 201
    assert body["id"] == 42
    assert body["created_at"].startswith("2026-04-12T10:30:00")
    assert body["updated_at"].startswith("2026-04-12T10:30:00")


def test_signup_route_function_returns_user_object_on_success():
    async def run_test():
        fake_service = FakeAuthService(user_to_return=_build_user(user_id=7))
        payload = UserCreate(
            username="alice",
            email="alice@example.com",
            password="plain-password",
        )

        result = await auth_api.signup(payload, fake_service)

        assert result.id == 7
        assert result.email == "alice@example.com"

    asyncio.run(run_test())


def test_signup_route_function_raises_http_409_for_value_error():
    async def run_test():
        fake_service = FakeAuthService(error_to_raise=ValueError("Email already exists"))
        payload = UserCreate(
            username="alice",
            email="alice@example.com",
            password="plain-password",
        )

        try:
            await auth_api.signup(payload, fake_service)
            raise AssertionError("Expected HTTPException for duplicate email")
        except Exception as exc:  # noqa: BLE001 - explicit behavior assertion.
            assert exc.status_code == 409
            assert exc.detail == "Email already exists"

    asyncio.run(run_test())


def test_signup_does_not_map_unexpected_service_error_to_409():
    fake_service = FakeAuthService(error_to_raise=RuntimeError("unexpected failure"))
    client = _build_client(fake_service, raise_server_exceptions=False)

    response = client.post(
        "/auth/signup",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "plain-password",
        },
    )

    assert response.status_code == 500


def test_signup_validation_error_short_circuits_service_register_call():
    fake_service = FakeAuthService(user_to_return=_build_user())
    client = _build_client(fake_service)

    response = client.post(
        "/auth/signup",
        json={
            "username": "",
            "email": "alice@example.com",
            "password": "plain-password",
        },
    )

    assert response.status_code == 422
    assert fake_service.register_calls == 0


def test_signup_returns_500_when_service_returns_invalid_response_model():
    fake_service = FakeAuthService(user_to_return=None)
    client = _build_client(fake_service, raise_server_exceptions=False)

    response = client.post(
        "/auth/signup",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "plain-password",
        },
    )

    assert response.status_code == 500


def test_signup_returns_422_for_malformed_json_body():
    fake_service = FakeAuthService(user_to_return=_build_user())
    client = _build_client(fake_service)

    response = client.post(
        "/auth/signup",
        content='{"username": "alice", "email": "alice@example.com",',
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 422
    assert fake_service.register_calls == 0


def test_signup_ignores_extra_input_fields_by_contract():
    fake_service = FakeAuthService(user_to_return=_build_user())
    client = _build_client(fake_service)

    response = client.post(
        "/auth/signup",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "plain-password",
            "unexpected_field": "should be ignored",
        },
    )

    assert response.status_code == 201
    assert fake_service.last_register_payload is not None
    assert "unexpected_field" not in fake_service.last_register_payload.model_dump()
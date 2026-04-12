import asyncio
import os
from datetime import datetime
from typing import Optional

import jwt
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Ensure settings can be instantiated when importing app.auth.api.
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_DB", "test")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5432")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-key-at-least-32-bytes")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("JWT_EXPIRATION_MINUTES", "30")

from app.auth import api as auth_api
from app.auth.schemas import LoginRequest, TokenResponse, User


NOW = datetime(2026, 4, 12, 10, 30, 0)

TEST_JWT_ALGORITHM = os.environ["JWT_ALGORITHM"]
TEST_JWT_SECRET_KEY = os.environ["JWT_SECRET_KEY"]
TEST_JWT_EXPIRATION_MINUTES = int(os.environ["JWT_EXPIRATION_MINUTES"])


class FakeAuthService:
    def __init__(
        self,
        *,
        user_to_return: Optional[User] = None,
        error_to_raise: Optional[Exception] = None,
    ):
        """Initialize a configurable fake auth service for login tests.

        :param user_to_return: User instance returned by ``authenticate`` when
            authentication succeeds. Pass ``None`` to simulate invalid
            credentials.
        :param error_to_raise: Exception raised by ``authenticate`` to test
            unexpected error propagation.
        :return: None.
        """
        self.user_to_return = user_to_return
        self.error_to_raise = error_to_raise
        self.authenticate_calls = 0
        self.last_email: Optional[str] = None
        self.last_password: Optional[str] = None

    async def authenticate(self, email: str, password: str) -> Optional[User]:
        """Simulate credential verification for login unit tests.

        The method records invocation metadata so tests can assert delegation
        behavior and credential forwarding from the API layer.

        :param email: Email address received by the fake service.
        :param password: Plain-text password received by the fake service.
        :return: Preconfigured user instance when no error is configured, or
            ``None`` to simulate invalid credentials.
        :raises Exception: Re-raises the configured ``error_to_raise`` when
            present.
        """
        self.authenticate_calls += 1
        self.last_email = email
        self.last_password = password
        if self.error_to_raise is not None:
            raise self.error_to_raise
        return self.user_to_return


def _build_user(
    *,
    user_id: int = 1,
    username: str = "alice",
    email: str = "alice@example.com",
) -> User:
    """Create a deterministic user fixture for login endpoint tests.

    :param user_id: Identifier assigned to the returned user model.
    :param username: Username assigned to the returned user model.
    :param email: Email assigned to the returned user model.
    :return: A fully populated ``User`` instance with stable timestamps.
    """
    return User(
        id=user_id,
        username=username,
        email=email,
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
    :param raise_server_exceptions: When ``False``, server-side errors are
        returned as 500 responses instead of being re-raised in the test
        process.
    :return: Configured ``TestClient`` ready for login endpoint tests.
    """
    app = FastAPI()
    app.include_router(auth_api.router)
    app.dependency_overrides[auth_api.get_auth_service] = lambda: fake_service
    return TestClient(app, raise_server_exceptions=raise_server_exceptions)


def _decode_token(token: str) -> dict:
    """Decode a JWT using the test secret without verifying expiry.

    :param token: Encoded JWT string to decode.
    :return: Decoded payload as a dictionary.
    """
    return jwt.decode(
        token,
        options={"verify_signature": False},
        algorithms=[TEST_JWT_ALGORITHM],
    )


# ---------------------------------------------------------------------------
# Success path
# ---------------------------------------------------------------------------

def test_login_returns_200_on_valid_credentials():
    fake_service = FakeAuthService(user_to_return=_build_user())
    client = _build_client(fake_service)

    response = client.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": "plain-password"},
    )

    assert response.status_code == 200


def test_login_response_contains_access_token_field():
    fake_service = FakeAuthService(user_to_return=_build_user())
    client = _build_client(fake_service)

    response = client.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": "plain-password"},
    )

    assert "access_token" in response.json()


def test_login_response_token_type_is_bearer():
    fake_service = FakeAuthService(user_to_return=_build_user())
    client = _build_client(fake_service)

    response = client.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": "plain-password"},
    )

    assert response.json()["token_type"] == "bearer"


def test_login_access_token_is_non_empty_string():
    fake_service = FakeAuthService(user_to_return=_build_user())
    client = _build_client(fake_service)

    response = client.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": "plain-password"},
    )

    token = response.json()["access_token"]
    assert isinstance(token, str)
    assert len(token) > 0


def test_login_access_token_has_three_jwt_parts():
    fake_service = FakeAuthService(user_to_return=_build_user())
    client = _build_client(fake_service)

    response = client.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": "plain-password"},
    )

    token = response.json()["access_token"]
    parts = token.split(".")
    assert len(parts) == 3


def test_login_response_does_not_expose_password():
    fake_service = FakeAuthService(user_to_return=_build_user())
    client = _build_client(fake_service)

    response = client.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": "plain-password"},
    )

    assert "password" not in response.json()


# ---------------------------------------------------------------------------
# Service delegation
# ---------------------------------------------------------------------------

def test_login_calls_authenticate_once_on_success():
    fake_service = FakeAuthService(user_to_return=_build_user())
    client = _build_client(fake_service)

    response = client.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": "plain-password"},
    )

    assert response.status_code == 200
    assert fake_service.authenticate_calls == 1


def test_login_passes_email_to_service_authenticate():
    fake_service = FakeAuthService(user_to_return=_build_user())
    client = _build_client(fake_service)

    client.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": "plain-password"},
    )

    assert fake_service.last_email == "alice@example.com"


def test_login_passes_password_to_service_authenticate():
    fake_service = FakeAuthService(user_to_return=_build_user())
    client = _build_client(fake_service)

    client.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": "plain-password"},
    )

    assert fake_service.last_password == "plain-password"


# ---------------------------------------------------------------------------
# JWT payload
# ---------------------------------------------------------------------------

def test_login_token_sub_claim_matches_user_id():
    fake_service = FakeAuthService(user_to_return=_build_user(user_id=42))
    client = _build_client(fake_service)

    response = client.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": "plain-password"},
    )

    token = response.json()["access_token"]
    payload = _decode_token(token)
    assert payload["sub"] == "42"


def test_login_token_contains_exp_claim():
    fake_service = FakeAuthService(user_to_return=_build_user())
    client = _build_client(fake_service)

    response = client.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": "plain-password"},
    )

    token = response.json()["access_token"]
    payload = _decode_token(token)
    assert "exp" in payload


def test_login_token_contains_iat_claim():
    fake_service = FakeAuthService(user_to_return=_build_user())
    client = _build_client(fake_service)

    response = client.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": "plain-password"},
    )

    token = response.json()["access_token"]
    payload = _decode_token(token)
    assert "iat" in payload


# ---------------------------------------------------------------------------
# 401 Unauthorized
# ---------------------------------------------------------------------------

def test_login_returns_401_when_service_returns_none():
    fake_service = FakeAuthService(user_to_return=None)
    client = _build_client(fake_service)

    response = client.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401


def test_login_401_detail_message_is_explicit():
    fake_service = FakeAuthService(user_to_return=None)
    client = _build_client(fake_service)

    response = client.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": "wrong-password"},
    )

    assert response.json()["detail"] == "Invalid email or password"


def test_login_401_includes_www_authenticate_header():
    fake_service = FakeAuthService(user_to_return=None)
    client = _build_client(fake_service)

    response = client.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": "wrong-password"},
    )

    assert response.headers.get("www-authenticate") == "Bearer"


# ---------------------------------------------------------------------------
# Request validation (422)
# ---------------------------------------------------------------------------

def test_login_returns_422_for_empty_body():
    fake_service = FakeAuthService(user_to_return=_build_user())
    client = _build_client(fake_service)

    response = client.post("/auth/login", json={})

    assert response.status_code == 422


def test_login_returns_422_when_email_is_missing():
    fake_service = FakeAuthService(user_to_return=_build_user())
    client = _build_client(fake_service)

    response = client.post("/auth/login", json={"password": "plain-password"})

    assert response.status_code == 422


def test_login_returns_422_when_password_is_missing():
    fake_service = FakeAuthService(user_to_return=_build_user())
    client = _build_client(fake_service)

    response = client.post("/auth/login", json={"email": "alice@example.com"})

    assert response.status_code == 422


def test_login_returns_422_for_invalid_email_format():
    fake_service = FakeAuthService(user_to_return=_build_user())
    client = _build_client(fake_service)

    response = client.post(
        "/auth/login",
        json={"email": "not-an-email", "password": "plain-password"},
    )

    assert response.status_code == 422


def test_login_returns_422_for_empty_password():
    fake_service = FakeAuthService(user_to_return=_build_user())
    client = _build_client(fake_service)

    response = client.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": ""},
    )

    assert response.status_code == 422


def test_login_returns_422_for_password_longer_than_255():
    fake_service = FakeAuthService(user_to_return=_build_user())
    client = _build_client(fake_service)

    response = client.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": "p" * 256},
    )

    assert response.status_code == 422


def test_login_validation_short_circuits_service_call():
    fake_service = FakeAuthService(user_to_return=_build_user())
    client = _build_client(fake_service)

    response = client.post(
        "/auth/login",
        json={"email": "not-an-email", "password": "plain-password"},
    )

    assert response.status_code == 422
    assert fake_service.authenticate_calls == 0


def test_login_returns_422_for_malformed_json_body():
    fake_service = FakeAuthService(user_to_return=_build_user())
    client = _build_client(fake_service)

    response = client.post(
        "/auth/login",
        content='{"email": "alice@example.com",',
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 422
    assert fake_service.authenticate_calls == 0


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_login_does_not_map_unexpected_service_error_to_401():
    fake_service = FakeAuthService(error_to_raise=RuntimeError("unexpected failure"))
    client = _build_client(fake_service, raise_server_exceptions=False)

    response = client.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": "plain-password"},
    )

    assert response.status_code == 500


def test_login_ignores_extra_input_fields_by_contract():
    fake_service = FakeAuthService(user_to_return=_build_user())
    client = _build_client(fake_service)

    response = client.post(
        "/auth/login",
        json={
            "email": "alice@example.com",
            "password": "plain-password",
            "unexpected_field": "should be ignored",
        },
    )

    assert response.status_code == 200


# ---------------------------------------------------------------------------
# Direct route function tests
# ---------------------------------------------------------------------------

def test_login_route_function_returns_token_response_on_success():
    async def run_test():
        fake_service = FakeAuthService(user_to_return=_build_user(user_id=7))
        credentials = LoginRequest(
            email="alice@example.com",
            password="plain-password",
        )

        result = await auth_api.login(credentials, fake_service)

        assert isinstance(result, TokenResponse)
        assert result.token_type == "bearer"
        assert len(result.access_token) > 0

    asyncio.run(run_test())


def test_login_route_function_raises_http_401_when_service_returns_none():
    async def run_test():
        fake_service = FakeAuthService(user_to_return=None)
        credentials = LoginRequest(
            email="alice@example.com",
            password="wrong-password",
        )

        try:
            await auth_api.login(credentials, fake_service)
            raise AssertionError("Expected HTTPException for invalid credentials")
        except Exception as exc:  # noqa: BLE001 - explicit behavior assertion.
            assert exc.status_code == 401
            assert exc.detail == "Invalid email or password"

    asyncio.run(run_test())

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import fastapi
import jwt
import pytest
from fastapi import FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient

# Ensure settings can be instantiated when importing app.auth.api.
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_DB", "test")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5432")
os.environ.setdefault(
    "JWT_CURRENT_SECRET",
    "test-jwt-current-secret-key-at-least-32-bytes",
)
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("JWT_EXPIRATION_MINUTES", "30")

from app.auth import api as auth_api
from app.auth.helper import create_access_token, revoke_access_token
from app.auth.schemas import User
from app.core.settings import settings


NOW = datetime(2026, 4, 12, 10, 30, 0)


class FakeAuthService:
    def __init__(self, *, user_to_return: Optional[User] = None):
        """Initialize a fake service used by /me endpoint tests.

        :param user_to_return: User object returned by ``get_user_by_id``.
        :return: None.
        """
        self.user_to_return = user_to_return
        self.get_user_by_id_calls = 0
        self.last_user_id: Optional[int] = None

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Simulate user profile lookup for the /me endpoint.

        :param user_id: Identifier extracted from token subject claim.
        :return: Configured user object or ``None`` when missing.
        """
        self.get_user_by_id_calls += 1
        self.last_user_id = user_id
        return self.user_to_return



def _build_user(*, user_id: int = 1) -> User:
    """Create a deterministic user fixture.

    :param user_id: Identifier assigned to the user fixture.
    :return: A ``User`` schema instance.
    """
    return User(
        id=user_id,
        username=f"user-{user_id}",
        email=f"user-{user_id}@example.com",
        created_at=NOW,
        updated_at=NOW,
    )



def _build_client(fake_service: FakeAuthService) -> TestClient:
    """Build a test client with auth service override.

    :param fake_service: Fake auth service used by dependency override.
    :return: Configured ``TestClient``.
    """
    app = FastAPI()
    app.include_router(auth_api.router)
    app.dependency_overrides[auth_api.get_auth_service] = lambda: fake_service
    return TestClient(app)



def _encode_payload(payload: dict) -> str:
    """Encode a token payload using current app settings.

    :param payload: JWT payload dictionary.
    :return: Encoded JWT string.
    """
    return jwt.encode(payload, settings.JWT_CURRENT_SECRET, algorithm=settings.JWT_ALGORITHM)



def test_me_returns_200_for_valid_token_and_existing_user():
    fake_service = FakeAuthService(user_to_return=_build_user(user_id=7))
    client = _build_client(fake_service)
    token = create_access_token(user_id=7)

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200



def test_me_returns_user_profile_payload():
    fake_service = FakeAuthService(user_to_return=_build_user(user_id=7))
    client = _build_client(fake_service)
    token = create_access_token(user_id=7)

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    body = response.json()
    assert body["id"] == 7
    assert body["username"] == "user-7"
    assert body["email"] == "user-7@example.com"



def test_me_calls_get_user_by_id_once_for_valid_token():
    fake_service = FakeAuthService(user_to_return=_build_user(user_id=2))
    client = _build_client(fake_service)
    token = create_access_token(user_id=2)

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert fake_service.get_user_by_id_calls == 1



def test_me_passes_subject_as_integer_to_service_lookup():
    fake_service = FakeAuthService(user_to_return=_build_user(user_id=13))
    client = _build_client(fake_service)
    token = create_access_token(user_id=13)

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert fake_service.last_user_id == 13



def test_me_returns_401_when_authorization_header_is_missing():
    fake_service = FakeAuthService(user_to_return=_build_user(user_id=1))
    client = _build_client(fake_service)

    response = client.get("/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"



def test_me_returns_401_with_www_authenticate_when_header_missing():
    fake_service = FakeAuthService(user_to_return=_build_user(user_id=1))
    client = _build_client(fake_service)

    response = client.get("/auth/me")

    assert response.headers.get("www-authenticate") == "Bearer"



@pytest.mark.parametrize(
    "auth_header",
    [
        "Basic abc",
        "Digest abc",
        "Token abc",
        "",
        "bearer",  # missing token value
    ],
)
def test_me_returns_401_for_invalid_auth_scheme(auth_header: str):
    fake_service = FakeAuthService(user_to_return=_build_user(user_id=1))
    client = _build_client(fake_service)

    response = client.get("/auth/me", headers={"Authorization": auth_header})

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"



@pytest.mark.parametrize(
    "token",
    [
        "not-a-jwt",
        "onepart",
        "part1.part2",
        "abc.def.ghi",
        "....",
        "eyJhbGciOiJIUzI1NiJ9.invalid.signature",
        "eyJhbGciOiJIUzI1NiJ9..sig",
        "123.456.789",
    ],
)
def test_me_returns_401_for_malformed_or_invalid_token_strings(token: str):
    fake_service = FakeAuthService(user_to_return=_build_user(user_id=1))
    client = _build_client(fake_service)

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid access token"



def test_me_returns_401_for_expired_token():
    fake_service = FakeAuthService(user_to_return=_build_user(user_id=1))
    client = _build_client(fake_service)

    expired_payload = {
        "sub": "1",
        "jti": "expired-jti-1",
        "iat": 1,
        "exp": 2,
    }
    expired_token = _encode_payload(expired_payload)

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {expired_token}"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid access token"



def test_me_returns_401_for_revoked_token():
    fake_service = FakeAuthService(user_to_return=_build_user(user_id=1))
    client = _build_client(fake_service)
    token = create_access_token(user_id=1)
    revoke_access_token(token)

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid access token"



def test_me_returns_401_for_token_missing_sub_claim():
    fake_service = FakeAuthService(user_to_return=_build_user(user_id=1))
    client = _build_client(fake_service)
    payload = {
        "jti": "no-sub-jti",
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "exp": int((datetime.now(timezone.utc) + timedelta(minutes=5)).timestamp()),
    }
    token = _encode_payload(payload)

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401



def test_me_returns_401_for_token_missing_jti_claim():
    fake_service = FakeAuthService(user_to_return=_build_user(user_id=1))
    client = _build_client(fake_service)
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "1",
        "iat": now,
        "exp": now + timedelta(minutes=5),
    }
    token = _encode_payload(payload)

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid access token"



@pytest.mark.parametrize("jti_value", ["", None])
def test_me_returns_401_for_token_with_invalid_jti(jti_value):
    fake_service = FakeAuthService(user_to_return=_build_user(user_id=1))
    client = _build_client(fake_service)
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "1",
        "jti": jti_value,
        "iat": now,
        "exp": now + timedelta(minutes=5),
    }
    token = _encode_payload(payload)

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid access token"



@pytest.mark.parametrize("sub_value", ["abc", "1.2", "", " ", "none"])
def test_me_returns_401_for_non_integer_subject(sub_value: str):
    fake_service = FakeAuthService(user_to_return=_build_user(user_id=1))
    client = _build_client(fake_service)
    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub_value,
        "jti": f"sub-invalid-{sub_value!r}",
        "iat": now,
        "exp": now + timedelta(minutes=10),
    }
    token = _encode_payload(payload)

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid access token"



@pytest.mark.parametrize("sub_value", ["0", "-1", "-99"])
def test_me_returns_401_for_non_positive_subject(sub_value: str):
    fake_service = FakeAuthService(user_to_return=_build_user(user_id=1))
    client = _build_client(fake_service)
    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub_value,
        "jti": f"sub-non-positive-{sub_value}",
        "iat": now,
        "exp": now + timedelta(minutes=10),
    }
    token = _encode_payload(payload)

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401



def test_me_returns_404_when_user_does_not_exist():
    fake_service = FakeAuthService(user_to_return=None)
    client = _build_client(fake_service)
    token = create_access_token(user_id=404)

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"



def test_me_does_not_call_service_when_token_is_invalid():
    fake_service = FakeAuthService(user_to_return=_build_user(user_id=1))
    client = _build_client(fake_service)

    response = client.get("/auth/me", headers={"Authorization": "Bearer invalid"})

    assert response.status_code == 401
    assert fake_service.get_user_by_id_calls == 0



def test_me_does_not_call_service_when_token_is_revoked():
    fake_service = FakeAuthService(user_to_return=_build_user(user_id=1))
    client = _build_client(fake_service)
    token = create_access_token(user_id=1)
    revoke_access_token(token)

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert fake_service.get_user_by_id_calls == 0



def test_get_current_user_route_function_returns_user_on_success():
    async def run_test():
        fake_service = FakeAuthService(user_to_return=_build_user(user_id=5))
        token = create_access_token(user_id=5)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        user = await auth_api.get_current_user(credentials, fake_service)

        assert user.id == 5
        assert user.email == "user-5@example.com"

    import asyncio

    asyncio.run(run_test())



def test_get_current_user_route_function_raises_401_for_invalid_token():
    async def run_test():
        fake_service = FakeAuthService(user_to_return=_build_user(user_id=5))
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid")

        with pytest.raises(HTTPException) as exc_info:
            await auth_api.get_current_user(credentials, fake_service)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid access token"

    import asyncio

    asyncio.run(run_test())


def test_me_response_includes_created_at_field():
    fake_service = FakeAuthService(user_to_return=_build_user(user_id=8))
    client = _build_client(fake_service)
    token = create_access_token(user_id=8)

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert "created_at" in response.json()


def test_me_response_includes_updated_at_field():
    fake_service = FakeAuthService(user_to_return=_build_user(user_id=8))
    client = _build_client(fake_service)
    token = create_access_token(user_id=8)

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert "updated_at" in response.json()


def test_me_response_does_not_include_password_field():
    fake_service = FakeAuthService(user_to_return=_build_user(user_id=8))
    client = _build_client(fake_service)
    token = create_access_token(user_id=8)

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert "password" not in response.json()


def test_me_returns_401_with_www_authenticate_for_invalid_token():
    fake_service = FakeAuthService(user_to_return=_build_user(user_id=1))
    client = _build_client(fake_service)

    response = client.get("/auth/me", headers={"Authorization": "Bearer invalid"})

    assert response.status_code == 401
    assert response.headers.get("www-authenticate") == "Bearer"


def test_me_returns_401_with_www_authenticate_for_revoked_token():
    fake_service = FakeAuthService(user_to_return=_build_user(user_id=1))
    client = _build_client(fake_service)
    token = create_access_token(user_id=1)
    revoke_access_token(token)

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert response.headers.get("www-authenticate") == "Bearer"


def test_me_supports_uppercase_bearer_scheme():
    fake_service = FakeAuthService(user_to_return=_build_user(user_id=21))
    client = _build_client(fake_service)
    token = create_access_token(user_id=21)

    response = client.get("/auth/me", headers={"Authorization": f"BEARER {token}"})

    assert response.status_code == 200
    assert response.json()["id"] == 21


def test_me_accepts_very_large_positive_subject_id():
    large_id = 9_223_372_036_854_775_807
    fake_service = FakeAuthService(user_to_return=_build_user(user_id=large_id))
    client = _build_client(fake_service)
    token = create_access_token(user_id=large_id)

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["id"] == large_id


def test_me_accepts_subject_with_leading_whitespace():
    fake_service = FakeAuthService(user_to_return=_build_user(user_id=1))
    client = _build_client(fake_service)
    now = datetime.now(timezone.utc)
    token = _encode_payload(
        {
            "sub": " 1",
            "jti": "sub-leading-space",
            "iat": now,
            "exp": now + timedelta(minutes=10),
        }
    )

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["id"] == 1


def test_me_accepts_subject_with_trailing_whitespace():
    fake_service = FakeAuthService(user_to_return=_build_user(user_id=1))
    client = _build_client(fake_service)
    now = datetime.now(timezone.utc)
    token = _encode_payload(
        {
            "sub": "1 ",
            "jti": "sub-trailing-space",
            "iat": now,
            "exp": now + timedelta(minutes=10),
        }
    )

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["id"] == 1


def test_get_current_user_route_function_raises_401_when_credentials_missing():
    async def run_test():
        fake_service = FakeAuthService(user_to_return=_build_user(user_id=2))

        with pytest.raises(HTTPException) as exc_info:
            await auth_api.get_current_user(None, fake_service)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Not authenticated"

    import asyncio

    asyncio.run(run_test())


def test_get_current_user_route_function_raises_401_for_wrong_scheme():
    async def run_test():
        fake_service = FakeAuthService(user_to_return=_build_user(user_id=2))
        credentials = HTTPAuthorizationCredentials(scheme="Basic", credentials="abc")

        with pytest.raises(HTTPException) as exc_info:
            await auth_api.get_current_user(credentials, fake_service)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Not authenticated"

    import asyncio

    asyncio.run(run_test())


def test_get_current_user_route_function_raises_404_when_user_missing():
    async def run_test():
        fake_service = FakeAuthService(user_to_return=None)
        token = create_access_token(user_id=404)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        with pytest.raises(HTTPException) as exc_info:
            await auth_api.get_current_user(credentials, fake_service)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "User not found"

    import asyncio

    asyncio.run(run_test())

import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
import pytest
from fastapi import FastAPI
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
from app.auth.helper import (
    create_access_token,
    decode_access_token,
    is_access_token_revoked,
)
from app.core.settings import settings


def _build_client() -> TestClient:
    """Build a FastAPI test client with the auth router mounted.

    :return: Configured ``TestClient`` for auth endpoint tests.
    """
    app = FastAPI()
    app.include_router(auth_api.router)
    return TestClient(app)


def _jwt_secret() -> str:
    """Return the JWT secret used by tests.

    :return: JWT secret string.
    """
    return settings.JWT_CURRENT_SECRET


def _jwt_algorithm() -> str:
    """Return the JWT algorithm used by tests.

    :return: JWT algorithm string.
    """
    return settings.JWT_ALGORITHM


def _encode_payload(payload: dict) -> str:
    """Encode a payload with the current test JWT secret.

    :param payload: JWT payload to encode.
    :return: Encoded JWT string.
    """
    return jwt.encode(payload, _jwt_secret(), algorithm=_jwt_algorithm())


def _valid_payload(*, sub: str = "1") -> dict:
    """Build a valid JWT payload for logout tests.

    :param sub: Subject claim value.
    :return: Payload dictionary containing sub, jti, iat, exp.
    """
    now = datetime.now(timezone.utc)
    return {
        "sub": sub,
        "jti": str(uuid4()),
        "iat": now,
        "exp": now + timedelta(minutes=30),
    }


def test_logout_returns_401_when_authorization_header_is_missing():
    client = _build_client()

    response = client.post("/auth/logout")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.parametrize(
    "authorization_value",
    [
        "Basic abcdef",
        "Digest abcdef",
        "Token abcdef",
        "ApiKey abcdef",
        "Negotiate abcdef",
        "OAuth abcdef",
        "Bearer",
        "",
        "UnknownScheme token",
        "bearer",
        "Basic",
        "Custom verycustomtoken",
    ],
)
def test_logout_rejects_invalid_authorization_schemes(authorization_value: str):
    client = _build_client()

    response = client.post(
        "/auth/logout",
        headers={"Authorization": authorization_value},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
    assert response.headers.get("www-authenticate") == "Bearer"


def test_logout_returns_401_when_bearer_scheme_is_not_used():
    client = _build_client()

    response = client.post(
        "/auth/logout",
        headers={"Authorization": "Basic abcdef"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.parametrize(
    "token",
    [
        "not-a-jwt",
        "abc",
        "abc.def",
        "abc.def.ghi",
        "....",
        "###",
        "123.456.789",
        "BearerInsideToken",
        "eyJhbGciOiJIUzI1NiJ9.badpayload.signature",
        "eyJhbGciOiJIUzI1NiJ9..signature",
        "only-one-part",
        "two.parts",
    ],
)
def test_logout_returns_401_for_invalid_token_string(token: str):
    client = _build_client()

    response = client.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid access token"
    assert response.headers.get("www-authenticate") == "Bearer"


def test_logout_returns_401_with_www_authenticate_header_for_missing_token():
    client = _build_client()

    response = client.post("/auth/logout")

    assert response.headers.get("www-authenticate") == "Bearer"


def test_logout_returns_401_with_www_authenticate_header_for_invalid_token():
    client = _build_client()

    response = client.post(
        "/auth/logout",
        headers={"Authorization": "Bearer not-a-jwt"},
    )

    assert response.headers.get("www-authenticate") == "Bearer"


@pytest.mark.parametrize("user_id", [1, 2, 3, 7, 11, 42, 99, 123, 1000, 9999])
def test_logout_returns_200_for_valid_token(user_id: int):
    client = _build_client()
    token = create_access_token(user_id=user_id)

    response = client.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200


def test_logout_returns_success_message_for_valid_token():
    client = _build_client()
    token = create_access_token(user_id=1)

    response = client.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.json()["detail"] == "Logged out successfully"


def test_logout_marks_token_as_revoked_after_success():
    client = _build_client()
    token = create_access_token(user_id=1)

    before = is_access_token_revoked(token)
    response = client.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )
    after = is_access_token_revoked(token)

    assert before is False
    assert response.status_code == 200
    assert after is True


@pytest.mark.parametrize("user_id", [1, 2, 3, 4, 5])
def test_logout_is_idempotent_for_same_token(user_id: int):
    client = _build_client()
    token = create_access_token(user_id=user_id)

    first = client.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )
    second = client.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert first.status_code == 200
    assert second.status_code == 200


def test_logout_only_revokes_provided_token_not_another_token():
    client = _build_client()
    token_one = create_access_token(user_id=1)
    token_two = create_access_token(user_id=1)

    client.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {token_one}"},
    )

    assert is_access_token_revoked(token_one) is True
    assert is_access_token_revoked(token_two) is False


@pytest.mark.parametrize("pair", [(1, 2), (5, 6), (10, 11)])
def test_logout_revocation_is_isolated_between_multiple_tokens(pair: tuple[int, int]):
    client = _build_client()
    first_id, second_id = pair
    token_one = create_access_token(user_id=first_id)
    token_two = create_access_token(user_id=second_id)

    client.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {token_two}"},
    )

    assert is_access_token_revoked(token_two) is True
    assert is_access_token_revoked(token_one) is False


def test_logout_accepts_token_encoded_with_current_secret():
    payload = _valid_payload(sub="7")
    token = _encode_payload(payload)
    client = _build_client()
    response = client.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200


@pytest.mark.parametrize(
    "payload",
    [
        {"sub": "1", "iat": 1_700_000_000, "exp": 2_000_000_000},
        {"sub": "1", "jti": "", "iat": 1_700_000_000, "exp": 2_000_000_000},
        {"sub": "1", "jti": None, "iat": 1_700_000_000, "exp": 2_000_000_000},
    ],
)
def test_logout_rejects_token_with_missing_or_invalid_jti_claim(payload: dict):
    token = _encode_payload(payload)
    client = _build_client()

    response = client.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid access token"


@pytest.mark.parametrize(
    "payload",
    [
        {"sub": "1", "jti": "abc", "iat": 1_700_000_000},
        {"sub": "1", "jti": "abc", "iat": 1_700_000_000, "exp": "tomorrow"},
        {"sub": "1", "jti": "abc", "iat": 1_700_000_000, "exp": 1.25},
        {"sub": "1", "jti": "abc", "iat": 1_700_000_000, "exp": None},
        {"sub": "1", "jti": "abc", "iat": 1_700_000_000, "exp": []},
        {"sub": "1", "jti": "abc", "iat": 1_700_000_000, "exp": {}},
    ],
)
def test_logout_rejects_token_with_missing_or_invalid_exp_claim(payload: dict):
    token = _encode_payload(payload)
    client = _build_client()

    response = client.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid access token"


@pytest.mark.parametrize("verify_exp", [True, False])
def test_decode_access_token_returns_payload_for_valid_token(verify_exp: bool):
    token = create_access_token(user_id=33)

    payload = decode_access_token(token, verify_exp=verify_exp)
    assert payload["sub"] == "33"
    assert "jti" in payload
    assert "exp" in payload


def test_decode_access_token_raises_for_expired_token_when_verify_exp_true():
    expired_payload = {
        "sub": "1",
        "jti": str(uuid4()),
        "iat": 1,
        "exp": 2,
    }
    expired_token = _encode_payload(expired_payload)

    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(expired_token, verify_exp=True)


def test_decode_access_token_without_exp_verification_allows_expired_token():
    expired_payload = {
        "sub": "1",
        "jti": str(uuid4()),
        "iat": 1,
        "exp": 2,
    }
    expired_token = _encode_payload(expired_payload)

    decoded = decode_access_token(expired_token, verify_exp=False)
    assert decoded["jti"] == expired_payload["jti"]


@pytest.mark.parametrize("iterations", [1, 2, 3, 5])
def test_logout_multiple_tokens_for_same_user_are_independently_revoked(iterations: int):
    client = _build_client()
    tokens = [create_access_token(user_id=5) for _ in range(iterations)]

    for token in tokens:
        response = client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    for token in tokens:
        assert is_access_token_revoked(token) is True

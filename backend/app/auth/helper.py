from datetime import datetime, timedelta, timezone
from uuid import uuid4
from typing import Iterable

import jwt
from jwt import InvalidTokenError

from app.core.settings import settings


# In-memory token denylist keyed by JWT `jti` with expiration timestamp.
# This is suitable for single-process development and tests only.
_REVOKED_JTIS: dict[str, int] = {}

def _previous_jwt_secrets() -> list[str]:
    """Parse previous JWT secrets from settings.

    :return: A list of previous JWT secret keys for token verification.
    """
    secrets_str = settings.JWT_PREVIOUS_SECRETS
    if not secrets_str:
        return []
    return [s.strip() for s in secrets_str.split(",") if s.strip()]

def create_access_token(user_id: int) -> str:
    """Create a JWT access token for the given user ID.

    :param user_id: The ID of the user for whom to create the token.
    :return: A signed JWT access token string.
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "jti": str(uuid4()),
        "iat": now,
        "exp": now + timedelta(minutes=settings.JWT_EXPIRATION_MINUTES),
    }
    return jwt.encode(
        payload,
        settings.JWT_CURRENT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )

def _candidate_secrets() -> Iterable[str]:
    """Generate candidate secrets for JWT verification.

    This includes the current secret and any previous secrets configured in
    settings, allowing for seamless secret rotation without invalidating tokens.

    :return: An iterable of candidate secret keys to try for token verification.
    """
    yield settings.JWT_CURRENT_SECRET
    yield from _previous_jwt_secrets()

def decode_access_token(token: str, *, verify_exp: bool = True) -> dict:
    """Decode and verify a JWT access token against candidate secrets.

    This function attempts to decode the token using the current secret and
    any previous secrets configured in settings. If decoding succeeds with any
    of the secrets, the decoded payload is returned. If all attempts fail,
    an InvalidTokenError is raised.

    :param token: The JWT access token string to decode and verify.
    :param verify_exp: Whether to enforce expiration claim validation.
    :return: The decoded token payload if verification succeeds.
    :raises InvalidTokenError: If the token cannot be verified with any candidate secret.
    """
    last_exception = None
    for secret in _candidate_secrets():
        try:
            return jwt.decode(
                token,
                secret,
                algorithms=[settings.JWT_ALGORITHM],
                options={"verify_exp": verify_exp},
            )
        except InvalidTokenError as exc:
            last_exception = exc
            continue

    raise InvalidTokenError("Token verification failed with all candidate secrets") from last_exception


def _cleanup_revoked_jtis(now_ts: int) -> None:
    """Remove expired entries from the in-memory JWT denylist.

    :param now_ts: Current UTC timestamp used to evict stale entries.
    :return: None.
    """
    expired = [jti for jti, exp_ts in _REVOKED_JTIS.items() if exp_ts <= now_ts]
    for jti in expired:
        _REVOKED_JTIS.pop(jti, None)


def revoke_access_token(token: str) -> None:
    """Revoke an access token by storing its JTI until expiration.

    :param token: Encoded JWT access token to revoke.
    :return: None.
    :raises InvalidTokenError: Raised when token decoding fails or required
        claims are missing.
    """
    payload = decode_access_token(token, verify_exp=False)
    token_jti = payload.get("jti")
    token_exp = payload.get("exp")
    if not isinstance(token_jti, str) or not token_jti:
        raise InvalidTokenError("Missing or invalid jti claim")
    if not isinstance(token_exp, int):
        raise InvalidTokenError("Missing or invalid exp claim")

    now_ts = int(datetime.now(timezone.utc).timestamp())
    _cleanup_revoked_jtis(now_ts)
    _REVOKED_JTIS[token_jti] = token_exp


def is_access_token_revoked(token: str) -> bool:
    """Check whether an access token has been revoked.

    :param token: Encoded JWT access token to inspect.
    :return: ``True`` when the token JTI exists in the denylist,
        otherwise ``False``.
    """
    payload = decode_access_token(token, verify_exp=False)
    token_jti = payload.get("jti")
    if not isinstance(token_jti, str) or not token_jti:
        return False

    now_ts = int(datetime.now(timezone.utc).timestamp())
    _cleanup_revoked_jtis(now_ts)
    return token_jti in _REVOKED_JTIS
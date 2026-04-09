# Signout Decision Table

## Purpose
Define deterministic signout outcomes so API behavior, security expectations, and test scenarios remain consistent.

## Decision Table

| Entry | Condition | Action | Result |
|---|---|---|---|
| Signout request | Missing authentication token | Reject request | `401 Unauthorized` |
| Signout request | Token invalid or expired | Reject request | `401 Unauthorized` |
| Signout request | Token valid and revocation succeeds | Revoke current token/session and clear server-side auth state | `200 OK` |
| Signout request | Token valid but already revoked | Return idempotent signout response | `200 OK` |
| Signout request | Revocation store temporarily unavailable | Return retryable error | `503 Service Unavailable` |

## Rules
- Signout must require authentication context from a valid token/session.
- Signout should be idempotent: repeating the same request should not fail if session is already revoked.
- Local signout revokes OSSN authentication only; provider-side global logout is optional and separate.
- After successful signout, previously revoked token/session must no longer authorize protected routes.
- Client should clear local auth artifacts (token, profile cache, session flags) after success.

## Suggested Service Mapping

| Step | Service Method |
|---|---|
| Parse and validate auth token | `SecurityService.decode_access_token(token)` |
| Check token status | `AuthRepository.is_token_revoked(jti)` |
| Revoke token/session | `AuthRepository.revoke_token(jti, user_id)` |
| Clear refresh/session link | `AuthRepository.revoke_refresh_tokens(user_id)` |
| Build success response | `AuthService.signout_response()` |

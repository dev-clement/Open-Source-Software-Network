# Signin Decision Table

## Purpose
Provide a deterministic decision matrix for signin outcomes so API behavior, implementation, and tests remain consistent.

## Decision Table

| Entry | Condition | Action | Result |
|---|---|---|---|
| Local signin | Email not found | Reject authentication | `401 Unauthorized` |
| Local signin | Email found, password invalid | Reject authentication | `401 Unauthorized` |
| Local signin | Email found, password valid | Issue JWT and return profile | `200 OK` + token + profile |
| OAuth callback | Invalid state, PKCE, code, or token exchange failure | Abort signin | `400 Bad Request` or `401 Unauthorized` |
| OAuth callback | Provider subject linked to user | Issue JWT and return profile | `200 OK` + token + profile |
| OAuth callback | Provider subject not linked but matching account exists and auto-link enabled | Link provider then issue JWT | `200 OK` + token + profile |
| OAuth callback | Provider subject not linked and confirmation required | Return link-required response | `202 Accepted` or `409 Conflict` |
| OAuth callback | Missing or unverified provider email when policy requires verified email | Reject signin | `422 Unprocessable Entity` |

## Rules
- Local signin validates credentials by email lookup and password hash verification.
- OAuth signin should first resolve identity through `provider + provider_user_id`.
- Email-based linking is allowed only for verified provider email and explicit policy.
- Do not reveal whether email exists via different error messages on signin.
- JWT is returned only after successful authentication.

## Suggested Service Mapping

| Step | Service Method |
|---|---|
| Validate input | `backend/app/auth/schemas.py` request schema for signin (replace with the concrete schema name defined there) |
| Get user by email | `UserRepository.get_by_email(email)` |
| Verify password | `SecurityService.verify_password(plain, hashed)` |
| Exchange OAuth code | `OAuthService.exchange_code(provider, code)` |
| Fetch provider profile | `OAuthService.get_profile(provider, token)` |
| Find provider link | `OAuthRepository.get_by_provider_subject(provider, provider_user_id)` |
| Link provider to user | `OAuthRepository.create_link(user_id, provider, provider_user_id)` |
| Generate JWT | `SecurityService.create_access_token(user_id)` |

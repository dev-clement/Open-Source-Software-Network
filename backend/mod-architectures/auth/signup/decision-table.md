# Signup Decision Table

## Purpose
Define deterministic outcomes for signup and OAuth callback branches so implementation and tests stay aligned.

## Decision Table

| Entry | Condition | Action | Result |
|---|---|---|---|
| Normal signup | Email not found | Hash password, create user, issue JWT | `201 Created` + profile + token |
| Normal signup | Email already exists | Reject creation | `409 Conflict` |
| OAuth callback | Provider account already linked | Issue JWT | `200 OK` + profile + token |
| OAuth callback | Provider not linked, verified email matches existing account, auto-link enabled | Link provider to existing user, issue JWT | `200 OK` + profile + token |
| OAuth callback | Provider not linked, verified email matches existing account, confirmation required | Return pending-link state for explicit confirmation | `202 Accepted` (or `409 Conflict` with `link_required`) |
| OAuth callback | Provider not linked, no matching account | Create user (no local password), store provider link, issue JWT | `201 Created` + profile + token |
| OAuth callback | Email missing or unverified and policy requires verified email | Reject callback | `422 Unprocessable Entity` |
| OAuth callback | Invalid state, PKCE, code, or token exchange failure | Abort flow | `400 Bad Request` or `401 Unauthorized` |

## Rules
- Do not check email plus password for signup uniqueness; uniqueness check is by email only.
- For local signup, hash password before persistence.
- For OAuth signup, use `provider + provider_user_id` as the primary identity key.
- Use provider email only when the provider marks it as verified.
- If an OAuth email collides with an existing account, follow explicit linking policy (`auto-link` or `confirm-link`).

## Suggested Service Mapping
<<<<<<< HEAD
Note: in `backend/app/auth` today, only `AuthService` and `UserRepository` are present. The `SecurityService`, `OAuthService`, and `OAuthRepository` references below are planned abstractions for a future refactor, not current modules.

| Step | Service Method | Status / Notes |
|---|---|---|
| Check local email uniqueness | `UserRepository.get_by_email(email)` | Current repository |
| Hash password (local only) | `SecurityService.hash_password(password)` | Planned component; currently handled within existing auth flow |
| Exchange OAuth code | `OAuthService.exchange_code(provider, code)` | Planned component |
| Fetch OAuth identity/profile | `OAuthService.get_profile(provider, token)` | Planned component |
| Lookup provider identity link | `OAuthRepository.get_by_provider_subject(provider, provider_user_id)` | Planned component |
| Link provider to existing user | `OAuthRepository.create_link(user_id, provider, provider_user_id)` | Planned component |
| Create user | `UserRepository.create(user_data)` | Current repository |
| Generate JWT | `SecurityService.create_access_token(user_id)` | Planned component; currently handled within existing auth flow |
=======
| Step | Service Method |
|---|---|
| Check local email uniqueness | `UserRepository.get_by_email(email)` |
| Hash password (local only) | `SecurityService.hash_password(password)` |
| Exchange OAuth code | `OAuthService.exchange_code(provider, code)` |
| Fetch OAuth identity/profile | `OAuthService.get_profile(provider, token)` |
| Lookup provider identity link | `OAuthRepository.get_by_provider_subject(provider, provider_user_id)` |
| Link provider to existing user | `OAuthRepository.create_link(user_id, provider, provider_user_id)` |
| Create user | `UserRepository.create(user_data)` |
| Generate JWT | `SecurityService.create_access_token(user_id)` |
>>>>>>> a3bcc91 (docs(auth): add consolidated auth architecture documentation)

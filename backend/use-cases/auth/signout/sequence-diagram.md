# Signout Sequence Diagram

## Purpose
Describe the interaction steps required to terminate an authenticated OSSN session safely and predictably.

## Mermaid Sequence Diagram

```mermaid
sequenceDiagram
    actor User
    participant Client as App UI
    participant Auth as Auth API
    participant Security as Security Service
    participant Repo as Auth Repository

    User->>Client: Click signout
    Client->>Auth: POST /auth/logout (Bearer token)
    Auth->>Security: decode_access_token(token)
    alt Invalid or expired token
        Security-->>Auth: token invalid
        Auth-->>Client: 401 Unauthorized
    else Valid token
        Security-->>Auth: user_id, jti
        Auth->>Repo: is_token_revoked(jti)
        alt Already revoked
            Repo-->>Auth: true
            Auth-->>Client: 200 OK (idempotent signout)
        else Active token
            Repo-->>Auth: false
            Auth->>Repo: revoke_token(jti, user_id)
            Repo-->>Auth: revoked
            Auth->>Repo: revoke_refresh_tokens(user_id)
            Repo-->>Auth: refresh/session cleared
            Auth-->>Client: 200 OK
        end
    end
    Client-->>User: Clear local auth data and redirect to signin
```

## Related Documents
- [Signout Use-Case](README.md)
- [Signout Decision Table](decision-table.md)

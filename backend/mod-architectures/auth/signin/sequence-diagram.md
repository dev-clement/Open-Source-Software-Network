# Signin Sequence Diagram

## Purpose
Provide a concise interaction view of signin behavior for both local credentials and OAuth providers.

## Mermaid Sequence Diagram

```mermaid
sequenceDiagram
    actor User
    participant Client as Signin UI
    participant Auth as Auth API
    participant Provider as OAuth Provider
    participant Repo as User Repository
    participant Token as JWT Service

    alt Local signin (email/password)
        User->>Client: Submit email and password
        Client->>Auth: POST /auth/login
        Auth->>Auth: Validate request
        Auth->>Repo: get_by_email(email)
        Repo-->>Auth: User record
        Auth->>Auth: verify_password(input, stored_hash)
        alt Invalid credentials
            Auth-->>Client: 401 Unauthorized
        else Valid credentials
            Auth->>Token: create_access_token(user_id)
            Token-->>Auth: JWT access token
            Auth-->>Client: 200 OK + token + profile
        end
        Client-->>User: Signin result
    else OAuth signin
        User->>Client: Choose GitHub, GitLab, or Bitbucket
        Client-)Provider: Redirect for authorization
        Provider--)Client: Callback with authorization code
        Client->>Auth: GET /auth/oauth/{provider}/callback?code=...
        Auth->>Auth: Validate state and PKCE
        Auth->>Provider: Exchange code for provider token
        Provider-->>Auth: Provider access token
        Auth->>Provider: Fetch provider identity and email
        Provider-->>Auth: provider_user_id, verified email
        Auth->>Repo: get_by_provider_subject(provider, provider_user_id)
        alt Linked account found
            Repo-->>Auth: User found
            Auth->>Token: create_access_token(user_id)
            Token-->>Auth: JWT access token
            Auth-->>Client: 200 OK + token + profile
        else No link found
            Repo-->>Auth: No user link
            Auth-->>Client: 401 Unauthorized or 202 link-required
        end
        Client-->>User: Signin result
    end
```

## Related Documents
- [Signin Use-Case](README.md)
- [Signin Decision Table](design-table.md)

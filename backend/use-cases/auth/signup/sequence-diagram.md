# Signup Sequence Diagram

## Purpose
Provide a focused sequence view of the signup flow for both local credentials and OAuth providers.

## Mermaid Sequence Diagram

```mermaid
sequenceDiagram
    actor Visitor
    participant Client as Signup UI
    participant Auth as Auth API
    participant Provider as OAuth Provider
    participant Repo as User Repository
    participant Token as JWT Service

    alt Email and password signup
        Visitor->>Client: Submit username, email, password
        Client->>Auth: POST /auth/signup
        Auth->>Auth: Validate input
        Auth->>Repo: get_by_email(email)
        Repo-->>Auth: User not found
        Auth->>Auth: Hash password
        Auth->>Repo: create(local user)
        Repo-->>Auth: User created
        Auth->>Token: create_access_token(user_id)
        Token-->>Auth: JWT access token
        Auth-->>Client: 201 Created + token + profile
        Client-->>Visitor: Signup success
    else OAuth provider signup
        Visitor->>Client: Choose GitHub, GitLab, or Bitbucket
        Client-)Provider: Redirect for authorization
        Provider--)Client: Callback with authorization code
        Client->>Auth: GET /auth/oauth/{provider}/callback?code=...
        Auth->>Auth: Validate state and PKCE
        Auth->>Provider: Exchange code for access token
        Provider-->>Auth: Provider access token
        Auth->>Provider: Fetch provider profile and email
        Provider-->>Auth: provider_user_id, username, verified email
        Auth->>Repo: get_by_provider_subject(provider, provider_user_id)
        alt Provider account already linked
            Repo-->>Auth: Linked user found
            Auth->>Token: create_access_token(user_id)
            Token-->>Auth: JWT access token
            Auth-->>Client: 200 OK + token + profile
        else Provider account not linked
            Repo-->>Auth: No linked user
            Auth->>Repo: get_by_email(verified_email)
            alt Verified email already exists
                Repo-->>Auth: Existing user found
                Auth-->>Client: 409 Conflict or 202 Accepted for account linking
            else No matching account
                Repo-->>Auth: No user found
                Auth->>Repo: create(oauth user without password)
                Repo-->>Auth: User created
                Auth->>Repo: create provider link
                Repo-->>Auth: Link created
                Auth->>Token: create_access_token(user_id)
                Token-->>Auth: JWT access token
                Auth-->>Client: 201 Created + token + profile
            end
        end
        Client-->>Visitor: Signup result
    end
```

## Related Documents
- [Signup Use-Case](README.md)
- [Signup Decision Table](decision-table.md)
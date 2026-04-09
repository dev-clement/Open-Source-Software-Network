# Use-Case: Signin

## Actor
**User** — a registered OSSN user who wants to access their account.

## Goal
Authenticate an existing user using local credentials or an OAuth provider, then return an access token and user profile.

## Preconditions
- The user already has an account in OSSN.
- For local signin, the user knows their email and password.
- For OAuth signin, the user can authenticate with GitHub, GitLab, or Bitbucket.

## Supported Login Methods
| Method | Authentication mechanism |
|---|---|
| Email/Password | Credential verification against stored password hash |
| GitHub | OAuth 2.0 authorization code flow |
| GitLab | OAuth 2.0 authorization code flow |
| Bitbucket | OAuth 2.0 authorization code flow |

## Main Flow

```mermaid
flowchart TD
    A([User lands on signin page]) --> B{Choose signin method}

    B -->|Email / Password| C[Submit email and password]
    B -->|GitHub| D[Redirect to GitHub OAuth]
    B -->|GitLab| E[Redirect to GitLab OAuth]
    B -->|Bitbucket| F[Redirect to Bitbucket OAuth]

    C --> G[Validate input fields]
    G --> H{Validation passes?}
    H -->|No| I[Return validation error]
    H -->|Yes| J[Fetch user by email]
    J --> K{User exists?}
    K -->|No| L[Return unauthorized]
    K -->|Yes| M[Verify password hash]
    M --> N{Password valid?}
    N -->|No| L
    N -->|Yes| O[Generate JWT access token]
    O --> P([Return token + user profile])

    D --> Q[Provider returns authorization code]
    E --> Q
    F --> Q
    Q --> R[Exchange code for provider token]
    R --> S[Fetch provider identity and verified email]
    S --> T[Find user by provider subject]
    T --> U{Provider link exists?}
    U -->|No| V[Return unauthorized or link-required]
    U -->|Yes| O
```

## Related Documents
- [Signin Decision Table](design-table.md)
- [Signin Sequence Diagram](sequence-diagram.md)

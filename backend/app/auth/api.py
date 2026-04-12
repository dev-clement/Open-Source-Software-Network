"""
Auth API routes: signup, login, logout.

All routes delegate to AuthService for business logic.
"""

from typing import AsyncGenerator
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import jwt

from app.auth.auth_local_service import AuthLocalService
from app.auth.service import AuthService
from app.auth.sql_repository import SqlUserRepository
from app.auth.schemas import LoginRequest, TokenResponse, UserCreate, User
from app.auth.helper import create_access_token
from app.core.settings import settings
from app.db.session import DatabaseEngine


router = APIRouter(prefix="/auth", tags=["auth"])


db_engine = DatabaseEngine(database_url=settings.db_url)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session for auth route dependencies.

    :return: An async generator yielding an active SQLAlchemy session.
    """
    async with db_engine.async_session() as session:
        yield session


def get_auth_service(session: AsyncSession = Depends(get_db_session)) -> AuthService:
    """Build the auth service used by route handlers.

    :param session: Request-scoped asynchronous database session.
    :return: A concrete auth service implementation for local auth.
    """
    repository = SqlUserRepository(session)
    return AuthLocalService(repository)


@router.post("/signup", status_code=status.HTTP_201_CREATED, response_model=User)
async def signup(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    """
    Register a new local-auth user account.

    This endpoint validates incoming user data, delegates account creation to
    the auth service, and returns the created public user profile.

    :param user_data: Signup payload containing username, email, plain-text
        password, and optional profile metadata.
    :param auth_service: Authentication service responsible for applying
        registration business rules such as duplicate-email checks and
        password hashing.
    :return: The newly created user profile serialized with the response
        schema.
    :raises HTTPException: Returns ``409 Conflict`` when a user with the same
        email already exists.
    """
    try:
        return await auth_service.register(user_data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """
    Authenticate user and return JWT access token.

    The endpoint verifies the supplied credentials against the local-auth
    backend and, on success, issues a signed JWT access token the client
    can use for subsequent authenticated requests.

    :param credentials: Login payload containing the user's email address
        and plain-text password.
    :param auth_service: Authentication service responsible for verifying
        credentials against the stored password hash.
    :return: A bearer token response containing the signed JWT access token
        and its type.
    :raises HTTPException: Returns ``401 Unauthorized`` when the supplied
        credentials are invalid or the email does not exist.
    """
    user = await auth_service.authenticate(credentials.email, credentials.password)
    access_token = create_access_token(user.id) if user else None
    if access_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenResponse(access_token=access_token)


@router.post("/logout")
async def logout():
    """
    Logout (stateless: client discards token).
    
    For stateful logout with token blacklist, further implementation needed.
    """
    raise NotImplementedError


@router.get("/me", response_model=User)
async def get_current_user():
    """Get the currently authenticated user's profile."""
    raise NotImplementedError

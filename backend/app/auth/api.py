"""
Auth API routes: signup, login, logout.

All routes delegate to AuthService for business logic.
"""

from fastapi import APIRouter, HTTPException

from app.auth.schemas import UserCreate, User


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=User)
async def signup(user_data: UserCreate):
    """
    Register a new user.
    
    - **username**: Unique username (1-255 chars)
    - **email**: Valid email address
    - **password**: Password (1-255 chars, will be hashed)
    - **github_page**: Optional GitHub profile URL
    - **bio**: Optional bio text
    """
    raise NotImplementedError


@router.post("/login")
async def login(email: str, password: str):
    """
    Authenticate user and return JWT access token.
    
    Returns:
    - **access_token**: JWT token valid for subsequent requests
    - **token_type**: "bearer"
    """
    raise NotImplementedError


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

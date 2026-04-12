from __future__ import annotations

from abc import ABC, abstractmethod
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def _get_default_env_file() -> Path:
    """Resolve the backend `.env` file for core settings.

    The function searches the current module directory and parent folders so
    configuration works whether `.env` is located in `app/core` or at the
    backend root.

    :return: The resolved `.env` path to use for settings loading.
    """
    current = Path(__file__).resolve()
    candidates = [
        current.parent / ".env",
        current.parents[1] / ".env",
        current.parents[2] / ".env",
        current.parents[3] / ".env",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[2]


class DBSettings(BaseSettings, ABC):
    """Abstract base class for database configuration.

    Inheriting from `BaseSettings` provides Pydantic environment loading,
    parsing, validation, and the ability to freeze instances.
    Inheriting from `ABC` allows this class to declare abstract methods and
    properties, creating a formal interface for concrete database settings.
    """

    APP_NAME: str = "OSSN Backend"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    model_config = SettingsConfigDict(
        env_file=_get_default_env_file(),
        env_file_encoding="utf-8",
        frozen=True,
        extra="ignore",
    )

    @property
    @abstractmethod
    def db_url(self) -> str:
        """Return the database connection URL for this settings model.

        :return: A SQLAlchemy-compatible database URL string.
        """
        raise NotImplementedError("Subclasses must implement db_url")


class PSQLSettings(DBSettings):
    """PostgreSQL-specific settings implementation.

    This concrete subclass defines the Postgres connection fields and builds
    a SQLAlchemy-compatible `postgresql+asyncpg://` URL.
    """

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    JWT_CURRENT_SECRET: str = "changeme-replace-this-key-in-production-env"
    JWT_PREVIOUS_SECRETS: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 30

    @property
    def db_url(self) -> str:
        """Build and return the PostgreSQL connection URL.

        :return: A SQLAlchemy-compatible PostgreSQL connection URL.
        """
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


@lru_cache(maxsize=1)
def get_psql_settings() -> PSQLSettings:
    """Create and cache the singleton Postgres settings instance.

    `lru_cache(maxsize=1)` is used as a lightweight lazy singleton so the same
    immutable settings object is shared across the application.

    :return: The cached `PSQLSettings` instance.
    """
    return PSQLSettings()


settings = get_psql_settings()

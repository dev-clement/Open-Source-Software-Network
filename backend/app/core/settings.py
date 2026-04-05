from __future__ import annotations

from abc import ABC, abstractmethod
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def _get_default_env_file() -> Path:
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
        raise NotImplementedError("Subclasses must implement db_url")


class PSQLSettings(DBSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    @property
    def db_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


@lru_cache(maxsize=1)
def get_psql_settings() -> PSQLSettings:
    return PSQLSettings()


settings = get_psql_settings()

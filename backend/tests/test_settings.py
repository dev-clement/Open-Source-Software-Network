import pytest
from pydantic import ValidationError

from app.core.settings import DBSettings, PSQLSettings, get_psql_settings, settings


def test_settings_singleton_instance():
    settings_one = get_psql_settings()
    settings_two = get_psql_settings()

    assert settings_one is settings_two
    assert settings is settings_one
    assert isinstance(settings, PSQLSettings)
    assert issubclass(type(settings), DBSettings)


def test_settings_builds_database_url_from_env_values():
    config = PSQLSettings(
        POSTGRES_USER="user",
        POSTGRES_PASSWORD="pass",
        POSTGRES_DB="db",
        POSTGRES_HOST="dbhost",
        POSTGRES_PORT=5432,
    )

    assert (
        config.db_url
        == "postgresql+asyncpg://user:pass@dbhost:5432/db"
    )


def test_settings_is_immutable():
    config = PSQLSettings(
        POSTGRES_USER="user",
        POSTGRES_PASSWORD="pass",
        POSTGRES_DB="db",
    )

    with pytest.raises(ValidationError):
        config.POSTGRES_DB = "other"

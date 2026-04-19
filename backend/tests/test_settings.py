import pytest
from pydantic import ValidationError

from app.core.settings import (
    DBSettings,
    PSQLSettings,
    _get_default_env_file,
    get_psql_settings,
    settings,
)


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


def test_settings_default_host_and_port_are_applied():
    config = PSQLSettings(
        POSTGRES_USER="user",
        POSTGRES_PASSWORD="pass",
        POSTGRES_DB="db",
    )

    assert config.POSTGRES_HOST == "localhost"
    assert config.POSTGRES_PORT == 5432


def test_settings_app_defaults_are_present():
    config = PSQLSettings(
        POSTGRES_USER="user",
        POSTGRES_PASSWORD="pass",
        POSTGRES_DB="db",
    )

    assert config.APP_NAME == "OSSN Backend"
    assert config.ENVIRONMENT == "development"
    assert config.DEBUG is False


def test_settings_jwt_defaults_are_present(monkeypatch):
    monkeypatch.delenv("JWT_CURRENT_SECRET", raising=False)
    monkeypatch.delenv("JWT_PREVIOUS_SECRETS", raising=False)
    monkeypatch.delenv("JWT_ALGORITHM", raising=False)
    monkeypatch.delenv("JWT_EXPIRATION_MINUTES", raising=False)

    config = PSQLSettings(
        _env_file=None,
        POSTGRES_USER="user",
        POSTGRES_PASSWORD="pass",
        POSTGRES_DB="db",
    )

    assert config.JWT_CURRENT_SECRET == "changeme-replace-this-key-in-production-env"
    assert config.JWT_PREVIOUS_SECRETS == ""
    assert config.JWT_ALGORITHM == "HS256"
    assert config.JWT_EXPIRATION_MINUTES == 30


def test_settings_accepts_custom_jwt_values():
    config = PSQLSettings(
        POSTGRES_USER="user",
        POSTGRES_PASSWORD="pass",
        POSTGRES_DB="db",
        JWT_CURRENT_SECRET="current-secret",
        JWT_PREVIOUS_SECRETS="old1,old2",
        JWT_ALGORITHM="HS512",
        JWT_EXPIRATION_MINUTES=90,
    )

    assert config.JWT_CURRENT_SECRET == "current-secret"
    assert config.JWT_PREVIOUS_SECRETS == "old1,old2"
    assert config.JWT_ALGORITHM == "HS512"
    assert config.JWT_EXPIRATION_MINUTES == 90


def test_settings_ignores_unknown_fields():
    config = PSQLSettings(
        POSTGRES_USER="user",
        POSTGRES_PASSWORD="pass",
        POSTGRES_DB="db",
        UNKNOWN_KEY="ignored",
    )

    assert not hasattr(config, "UNKNOWN_KEY")


@pytest.mark.parametrize(
    "host,port,expected",
    [
        ("localhost", 5432, "postgresql+asyncpg://user:pass@localhost:5432/db"),
        ("db", 5433, "postgresql+asyncpg://user:pass@db:5433/db"),
        ("127.0.0.1", 6543, "postgresql+asyncpg://user:pass@127.0.0.1:6543/db"),
        ("postgres.internal", 9999, "postgresql+asyncpg://user:pass@postgres.internal:9999/db"),
    ],
)
def test_db_url_varies_with_host_and_port(host, port, expected):
    config = PSQLSettings(
        POSTGRES_USER="user",
        POSTGRES_PASSWORD="pass",
        POSTGRES_DB="db",
        POSTGRES_HOST=host,
        POSTGRES_PORT=port,
    )

    assert config.db_url == expected


@pytest.mark.parametrize("port", [1, 5432, 65535, "5434"])
def test_settings_accepts_valid_postgres_port_values(port):
    config = PSQLSettings(
        POSTGRES_USER="user",
        POSTGRES_PASSWORD="pass",
        POSTGRES_DB="db",
        POSTGRES_PORT=port,
    )

    assert isinstance(config.POSTGRES_PORT, int)


@pytest.mark.parametrize("bad_port", ["not-an-int", "", None])
def test_settings_rejects_invalid_postgres_port_values(bad_port):
    with pytest.raises(ValidationError):
        PSQLSettings(
            POSTGRES_USER="user",
            POSTGRES_PASSWORD="pass",
            POSTGRES_DB="db",
            POSTGRES_PORT=bad_port,
        )


@pytest.mark.parametrize("minutes", [1, 30, 120, "45"])
def test_settings_accepts_valid_jwt_expiration_values(minutes):
    config = PSQLSettings(
        POSTGRES_USER="user",
        POSTGRES_PASSWORD="pass",
        POSTGRES_DB="db",
        JWT_EXPIRATION_MINUTES=minutes,
    )

    assert isinstance(config.JWT_EXPIRATION_MINUTES, int)


@pytest.mark.parametrize("bad_minutes", ["soon", "", None])
def test_settings_rejects_invalid_jwt_expiration_values(bad_minutes):
    with pytest.raises(ValidationError):
        PSQLSettings(
            POSTGRES_USER="user",
            POSTGRES_PASSWORD="pass",
            POSTGRES_DB="db",
            JWT_EXPIRATION_MINUTES=bad_minutes,
        )


@pytest.mark.parametrize("algo", ["HS256", "HS384", "HS512"])
def test_settings_accepts_jwt_algorithm_strings(algo):
    config = PSQLSettings(
        POSTGRES_USER="user",
        POSTGRES_PASSWORD="pass",
        POSTGRES_DB="db",
        JWT_ALGORITHM=algo,
    )

    assert config.JWT_ALGORITHM == algo


@pytest.mark.parametrize(
    "field, value",
    [
        ("POSTGRES_USER", None),
        ("POSTGRES_PASSWORD", None),
        ("POSTGRES_DB", None),
    ],
)
def test_settings_requires_mandatory_postgres_fields(field, value):
    kwargs = {
        "POSTGRES_USER": "user",
        "POSTGRES_PASSWORD": "pass",
        "POSTGRES_DB": "db",
    }
    kwargs[field] = value

    with pytest.raises(ValidationError):
        PSQLSettings(**kwargs)


def test_default_env_file_path_points_to_dotenv_name():
    env_path = _get_default_env_file()

    assert env_path.name == ".env"


def test_get_psql_settings_returns_psql_settings_instance(monkeypatch):
    get_psql_settings.cache_clear()
    monkeypatch.setenv("POSTGRES_USER", "env_user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "env_pass")
    monkeypatch.setenv("POSTGRES_DB", "env_db")
    monkeypatch.setenv("POSTGRES_HOST", "env_host")
    monkeypatch.setenv("POSTGRES_PORT", "5544")

    instance = get_psql_settings()

    assert isinstance(instance, PSQLSettings)
    get_psql_settings.cache_clear()


def test_get_psql_settings_uses_environment_values(monkeypatch):
    get_psql_settings.cache_clear()
    monkeypatch.setenv("POSTGRES_USER", "env_user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "env_pass")
    monkeypatch.setenv("POSTGRES_DB", "env_db")
    monkeypatch.setenv("POSTGRES_HOST", "env_host")
    monkeypatch.setenv("POSTGRES_PORT", "7777")

    instance = get_psql_settings()

    assert instance.POSTGRES_USER == "env_user"
    assert instance.POSTGRES_PASSWORD == "env_pass"
    assert instance.POSTGRES_DB == "env_db"
    assert instance.POSTGRES_HOST == "env_host"
    assert instance.POSTGRES_PORT == 7777
    get_psql_settings.cache_clear()


def test_get_psql_settings_cache_does_not_refresh_without_cache_clear(monkeypatch):
    get_psql_settings.cache_clear()
    monkeypatch.setenv("POSTGRES_USER", "first_user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "first_pass")
    monkeypatch.setenv("POSTGRES_DB", "first_db")
    first = get_psql_settings()

    monkeypatch.setenv("POSTGRES_USER", "second_user")
    second = get_psql_settings()

    assert first is second
    assert second.POSTGRES_USER == "first_user"
    get_psql_settings.cache_clear()


def test_get_psql_settings_cache_refreshes_after_cache_clear(monkeypatch):
    get_psql_settings.cache_clear()
    monkeypatch.setenv("POSTGRES_USER", "first_user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "first_pass")
    monkeypatch.setenv("POSTGRES_DB", "first_db")
    first = get_psql_settings()

    get_psql_settings.cache_clear()
    monkeypatch.setenv("POSTGRES_USER", "second_user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "second_pass")
    monkeypatch.setenv("POSTGRES_DB", "second_db")
    second = get_psql_settings()

    assert first is not second
    assert second.POSTGRES_USER == "second_user"
    get_psql_settings.cache_clear()


def test_db_url_contains_database_name_component():
    config = PSQLSettings(
        POSTGRES_USER="user",
        POSTGRES_PASSWORD="pass",
        POSTGRES_DB="my_database",
    )

    assert config.db_url.endswith("/my_database")


def test_db_url_includes_credentials_and_host_information():
    config = PSQLSettings(
        POSTGRES_USER="alice",
        POSTGRES_PASSWORD="secret",
        POSTGRES_DB="work",
        POSTGRES_HOST="postgres",
        POSTGRES_PORT=5435,
    )

    assert "alice:secret@postgres:5435" in config.db_url


def test_settings_supports_empty_previous_jwt_secrets():
    config = PSQLSettings(
        POSTGRES_USER="user",
        POSTGRES_PASSWORD="pass",
        POSTGRES_DB="db",
        JWT_PREVIOUS_SECRETS="",
    )

    assert config.JWT_PREVIOUS_SECRETS == ""


def test_settings_supports_non_empty_previous_jwt_secrets():
    config = PSQLSettings(
        POSTGRES_USER="user",
        POSTGRES_PASSWORD="pass",
        POSTGRES_DB="db",
        JWT_PREVIOUS_SECRETS="k1,k2,k3",
    )

    assert config.JWT_PREVIOUS_SECRETS == "k1,k2,k3"

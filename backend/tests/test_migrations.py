from pathlib import Path
import sqlite3

from alembic import command
from alembic.config import Config


BACKEND_ROOT = Path(__file__).resolve().parents[1]
ALEMBIC_INI = BACKEND_ROOT / "alembic.ini"
MIGRATIONS_DIR = BACKEND_ROOT / "migrations"
MIGRATIONS_ENV = MIGRATIONS_DIR / "env.py"
MIGRATIONS_SCRIPT_TEMPLATE = MIGRATIONS_DIR / "script.py.mako"
MIGRATIONS_VERSIONS_DIR = MIGRATIONS_DIR / "versions"


def _build_alembic_config() -> Config:
    cfg = Config(str(ALEMBIC_INI))
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    return cfg


def test_alembic_ini_exists_and_points_to_migrations_dir():
    assert ALEMBIC_INI.exists(), "Expected Alembic config file at backend/alembic.ini"

    content = ALEMBIC_INI.read_text(encoding="utf-8")
    assert "[alembic]" in content
    assert "script_location = %(here)s/migrations" in content
    assert "sqlalchemy.url" in content


def test_migrations_folder_contains_required_files():
    assert MIGRATIONS_DIR.exists(), "Expected migrations directory to exist"
    assert MIGRATIONS_ENV.exists(), "Expected migrations/env.py to exist"
    assert MIGRATIONS_SCRIPT_TEMPLATE.exists(), "Expected migrations/script.py.mako to exist"
    assert MIGRATIONS_VERSIONS_DIR.exists(), "Expected migrations/versions directory to exist"
    assert MIGRATIONS_VERSIONS_DIR.is_dir(), "Expected migrations/versions to be a directory"


def test_env_py_is_wired_to_project_settings_and_metadata():
    content = MIGRATIONS_ENV.read_text(encoding="utf-8")

    # Ensure Alembic env loads application settings and SQLModel metadata.
    assert "from app.core.settings import settings" in content
    assert "from sqlmodel import SQLModel" in content
    assert "import app.db.models" in content
    assert "target_metadata = SQLModel.metadata" in content
    assert "config.set_main_option(\"sqlalchemy.url\", _sync_url)" in content
    assert "ALEMBIC_DATABASE_URL" in content


def test_alembic_upgrade_head_creates_expected_tables(monkeypatch, tmp_path):
    assert any(MIGRATIONS_VERSIONS_DIR.glob("*.py")), (
        "Expected at least one migration revision under migrations/versions"
    )

    db_file = tmp_path / "migrations_test.sqlite"
    db_url = f"sqlite:///{db_file.as_posix()}"
    monkeypatch.setenv("ALEMBIC_DATABASE_URL", db_url)

    cfg = _build_alembic_config()
    command.upgrade(cfg, "head")

    with sqlite3.connect(db_file) as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()

    table_names = {name for (name,) in rows}
    assert "projects" in table_names
    assert "user" in table_names
    assert "contributions" in table_names


def test_alembic_downgrade_base_removes_app_tables(monkeypatch, tmp_path):
    db_file = tmp_path / "migrations_test.sqlite"
    db_url = f"sqlite:///{db_file.as_posix()}"
    monkeypatch.setenv("ALEMBIC_DATABASE_URL", db_url)

    cfg = _build_alembic_config()
    command.upgrade(cfg, "head")
    command.downgrade(cfg, "base")

    with sqlite3.connect(db_file) as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()

    table_names = {name for (name,) in rows}
    assert "projects" not in table_names
    assert "user" not in table_names
    assert "contributions" not in table_names

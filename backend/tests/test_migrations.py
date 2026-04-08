from pathlib import Path
import sqlite3

import pytest
from alembic import command
from alembic.config import Config


BACKEND_ROOT = Path(__file__).resolve().parents[1]
ALEMBIC_INI = BACKEND_ROOT / "alembic.ini"
MIGRATIONS_DIR = BACKEND_ROOT / "migrations"
MIGRATIONS_ENV = MIGRATIONS_DIR / "env.py"
MIGRATIONS_SCRIPT_TEMPLATE = MIGRATIONS_DIR / "script.py.mako"
MIGRATIONS_VERSIONS_DIR = MIGRATIONS_DIR / "versions"

# Revision ID of the single migration currently in the project.
INITIAL_REVISION_ID = "f39922f06319"


def _build_alembic_config() -> Config:
    cfg = Config(str(ALEMBIC_INI))
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    return cfg


def _migrated_db(monkeypatch, tmp_path, name: str = "test.sqlite") -> Path:
    """Upgrade to head against an isolated SQLite file and return its path."""
    db_file = tmp_path / name
    monkeypatch.setenv("ALEMBIC_DATABASE_URL", f"sqlite:///{db_file.as_posix()}")
    command.upgrade(_build_alembic_config(), "head")
    return db_file


# ===========================================================================
# 1. Scaffold & configuration
# ===========================================================================

class TestAlembicScaffold:

    def test_alembic_ini_exists_and_points_to_migrations_dir(self):
        assert ALEMBIC_INI.exists(), "Expected Alembic config file at backend/alembic.ini"

        content = ALEMBIC_INI.read_text(encoding="utf-8")
        assert "[alembic]" in content
        assert "script_location = %(here)s/migrations" in content
        assert "sqlalchemy.url" in content

    def test_migrations_folder_contains_required_files(self):
        assert MIGRATIONS_DIR.exists(), "Expected migrations directory to exist"
        assert MIGRATIONS_ENV.exists(), "Expected migrations/env.py to exist"
        assert MIGRATIONS_SCRIPT_TEMPLATE.exists(), "Expected migrations/script.py.mako to exist"
        assert MIGRATIONS_VERSIONS_DIR.exists(), "Expected migrations/versions directory to exist"
        assert MIGRATIONS_VERSIONS_DIR.is_dir(), "Expected migrations/versions to be a directory"

    def test_env_py_reads_alembic_database_url_env_var(self):
        content = MIGRATIONS_ENV.read_text(encoding="utf-8")
        assert "ALEMBIC_DATABASE_URL" in content

    def test_env_py_targets_sqlmodel_metadata(self):
        content = MIGRATIONS_ENV.read_text(encoding="utf-8")
        assert "SQLModel.metadata" in content

    def test_env_py_imports_app_db_models(self):
        content = MIGRATIONS_ENV.read_text(encoding="utf-8")
        assert "import app.db.models" in content


# ===========================================================================
# 2. Revision files
# ===========================================================================

class TestAlembicVersionFiles:

    def test_at_least_one_revision_file_exists(self):
        revision_files = list(MIGRATIONS_VERSIONS_DIR.glob("*.py"))
        assert len(revision_files) >= 1, (
            "Expected at least one revision file under migrations/versions"
        )

    def test_initial_revision_has_no_parent(self):
        revision_files = list(MIGRATIONS_VERSIONS_DIR.glob("*.py"))
        assert revision_files, "No revision files found"
        content = revision_files[0].read_text(encoding="utf-8")
        assert any(
            "down_revision" in line and "= None" in line
            for line in content.splitlines()
        ), "Expected the initial revision to declare down_revision = None"

    def test_initial_revision_id_matches_filename(self):
        revision_files = list(MIGRATIONS_VERSIONS_DIR.glob("*.py"))
        assert revision_files, "No revision files found"
        rev_file = revision_files[0]
        rev_id = rev_file.stem.split("_")[0]
        content = rev_file.read_text(encoding="utf-8")
        assert f"revision: str = '{rev_id}'" in content, (
            f"Expected revision ID '{rev_id}' to be declared in {rev_file.name}"
        )

    def test_initial_revision_defines_upgrade_function(self):
        revision_files = list(MIGRATIONS_VERSIONS_DIR.glob("*.py"))
        assert revision_files, "No revision files found"
        content = revision_files[0].read_text(encoding="utf-8")
        assert "def upgrade(" in content

    def test_initial_revision_defines_downgrade_function(self):
        revision_files = list(MIGRATIONS_VERSIONS_DIR.glob("*.py"))
        assert revision_files, "No revision files found"
        content = revision_files[0].read_text(encoding="utf-8")
        assert "def downgrade(" in content


# ===========================================================================
# 3. Migration execution
# ===========================================================================

class TestAlembicMigrations:

    def test_env_py_honors_alembic_database_url(self, monkeypatch, tmp_path):
        db_file = _migrated_db(monkeypatch, tmp_path, "env_override.sqlite")
        assert db_file.exists(), "Expected Alembic to use ALEMBIC_DATABASE_URL for migrations"

        with sqlite3.connect(db_file) as conn:
            rows = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()

        assert "alembic_version" in {name for (name,) in rows}

    def test_upgrade_head_creates_expected_tables(self, monkeypatch, tmp_path):
        assert any(MIGRATIONS_VERSIONS_DIR.glob("*.py")), (
            "Expected at least one migration revision under migrations/versions"
        )

        db_file = _migrated_db(monkeypatch, tmp_path)

        with sqlite3.connect(db_file) as conn:
            rows = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()

        table_names = {name for (name,) in rows}
        assert "projects" in table_names
        assert "user" in table_names
        assert "contributions" in table_names

    def test_upgrade_head_records_revision_in_alembic_version(self, monkeypatch, tmp_path):
        db_file = _migrated_db(monkeypatch, tmp_path)

        with sqlite3.connect(db_file) as conn:
            rows = conn.execute("SELECT version_num FROM alembic_version").fetchall()

        assert INITIAL_REVISION_ID in {row[0] for row in rows}

    def test_downgrade_base_removes_app_tables(self, monkeypatch, tmp_path):
        db_file = _migrated_db(monkeypatch, tmp_path)
        command.downgrade(_build_alembic_config(), "base")

        with sqlite3.connect(db_file) as conn:
            rows = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()

        table_names = {name for (name,) in rows}
        assert "projects" not in table_names
        assert "user" not in table_names
        assert "contributions" not in table_names

    def test_downgrade_base_clears_alembic_version_table(self, monkeypatch, tmp_path):
        db_file = _migrated_db(monkeypatch, tmp_path)
        command.downgrade(_build_alembic_config(), "base")

        with sqlite3.connect(db_file) as conn:
            rows = conn.execute("SELECT * FROM alembic_version").fetchall()

        assert len(rows) == 0, "Expected alembic_version to be empty after downgrade base"

    def test_projects_table_has_expected_columns(self, monkeypatch, tmp_path):
        db_file = _migrated_db(monkeypatch, tmp_path)

        with sqlite3.connect(db_file) as conn:
            rows = conn.execute("PRAGMA table_info(projects)").fetchall()

        column_names = {row[1] for row in rows}
        assert "id" in column_names
        assert "title" in column_names
        assert "description" in column_names
        assert "repository_url" in column_names
        assert "help_wanted" in column_names
        assert "created_at" in column_names
        assert "updated_at" in column_names

    def test_user_table_has_expected_columns(self, monkeypatch, tmp_path):
        db_file = _migrated_db(monkeypatch, tmp_path)

        with sqlite3.connect(db_file) as conn:
            rows = conn.execute("PRAGMA table_info(user)").fetchall()

        column_names = {row[1] for row in rows}
        assert "id" in column_names
        assert "username" in column_names
        assert "email" in column_names
        assert "password" in column_names
        assert "github_page" in column_names
        assert "bio" in column_names
        assert "created_at" in column_names
        assert "updated_at" in column_names

    def test_contributions_table_has_expected_columns(self, monkeypatch, tmp_path):
        db_file = _migrated_db(monkeypatch, tmp_path)

        with sqlite3.connect(db_file) as conn:
            rows = conn.execute("PRAGMA table_info(contributions)").fetchall()

        column_names = {row[1] for row in rows}
        assert "id" in column_names
        assert "fk_user_id" in column_names
        assert "fk_project_id" in column_names
        assert "status" in column_names
        assert "applied_at" in column_names
        assert "updated_at" in column_names

    def test_contributions_status_defaults_to_interested(self, monkeypatch, tmp_path):
        db_file = _migrated_db(monkeypatch, tmp_path)

        # sa.Identity(always=True) is PostgreSQL-specific; SQLite requires an explicit id.
        with sqlite3.connect(db_file) as conn:
            conn.execute(
                "INSERT INTO contributions (id, fk_user_id, fk_project_id) VALUES (?, ?, ?)",
                (1, 99, 99),
            )
            row = conn.execute(
                "SELECT status FROM contributions WHERE id = ?", (1,)
            ).fetchone()

        assert row is not None
        assert row[0] == "interested"

    def test_projects_repository_url_is_unique(self, monkeypatch, tmp_path):
        db_file = _migrated_db(monkeypatch, tmp_path)

        # sa.Identity(always=True) is PostgreSQL-specific; SQLite requires an explicit id.
        with sqlite3.connect(db_file) as conn:
            conn.execute(
                "INSERT INTO projects (id, title, repository_url, help_wanted) VALUES (?, ?, ?, ?)",
                (1, "A", "https://example.com", 0),
            )

        with sqlite3.connect(db_file) as conn:
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO projects (id, title, repository_url, help_wanted) VALUES (?, ?, ?, ?)",
                    (2, "B", "https://example.com", 0),
                )
                conn.commit()

    def test_user_email_is_unique(self, monkeypatch, tmp_path):
        db_file = _migrated_db(monkeypatch, tmp_path)

        # sa.Identity(always=True) is PostgreSQL-specific; SQLite requires an explicit id.
        with sqlite3.connect(db_file) as conn:
            conn.execute(
                "INSERT INTO user (id, username, email, password) VALUES (?, ?, ?, ?)",
                (1, "alice", "dup@example.com", "secret"),
            )

        with sqlite3.connect(db_file) as conn:
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO user (id, username, email, password) VALUES (?, ?, ?, ?)",
                    (2, "bob", "dup@example.com", "secret"),
                )
                conn.commit()

    def test_contributions_foreign_keys_reference_correct_tables(self, monkeypatch, tmp_path):
        db_file = _migrated_db(monkeypatch, tmp_path)

        with sqlite3.connect(db_file) as conn:
            rows = conn.execute("PRAGMA foreign_key_list(contributions)").fetchall()

        # PRAGMA foreign_key_list columns: id, seq, table, from, to, on_update, on_delete, match
        fk_map = {row[3]: row[2] for row in rows}  # from_column -> referenced_table
        assert fk_map.get("fk_user_id") == "user"
        assert fk_map.get("fk_project_id") == "projects"

    def test_upgrade_downgrade_upgrade_is_idempotent(self, monkeypatch, tmp_path):
        db_file = _migrated_db(monkeypatch, tmp_path)
        cfg = _build_alembic_config()
        command.downgrade(cfg, "base")
        command.upgrade(cfg, "head")

        with sqlite3.connect(db_file) as conn:
            rows = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()

        table_names = {name for (name,) in rows}
        assert "projects" in table_names
        assert "user" in table_names
        assert "contributions" in table_names

import sys
from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas.user import User, UserBase, UserCreate, UserUpdate
from app.schemas.project import Project, ProjectBase, ProjectCreate, ProjectUpdate
from app.schemas.contribution import (
    Contribution,
    ContributionBase,
    ContributionCreate,
    ContributionUpdate,
)

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------
VALID_EMAIL = "test@example.com"
NOW = datetime(2026, 4, 7, 12, 0, 0)

# DB column limits from backend/app/db/models.py:
#   username / email / password / github_page / title / repository_url → String(255)
#   status → String(20)
#   id / fk_user_id / fk_project_id → BigInteger
STR_AT_DB_LIMIT = "a" * 255
STR_OVER_DB_LIMIT = "a" * 256   # Schema has no max_length: Pydantic accepts this,
                                 # but the DB would reject it at persist time.
STATUS_AT_DB_LIMIT = "s" * 20
STATUS_OVER_DB_LIMIT = "s" * 21

MIN_POSITIVE_INT = 1
MAX_BIGINT = 9_223_372_036_854_775_807


# ===========================================================================
# 1. Import / class existence
# ===========================================================================

def test_user_schema_classes_are_importable():
    assert UserBase is not None
    assert UserCreate is not None
    assert UserUpdate is not None
    assert User is not None


def test_project_schema_classes_are_importable():
    assert ProjectBase is not None
    assert ProjectCreate is not None
    assert ProjectUpdate is not None
    assert Project is not None


def test_contribution_schema_classes_are_importable():
    assert ContributionBase is not None
    assert ContributionCreate is not None
    assert ContributionUpdate is not None
    assert Contribution is not None


# ===========================================================================
# 2. UserBase
# ===========================================================================

class TestUserBase:

    def test_valid_minimal(self):
        u = UserBase(username="alice", email=VALID_EMAIL)
        assert u.username == "alice"
        assert u.email == VALID_EMAIL

    def test_valid_full(self):
        u = UserBase(
            username="alice",
            email=VALID_EMAIL,
            github_page="https://github.com/alice",
            bio="OSS contributor",
        )
        assert str(u.github_page) == "https://github.com/alice"
        assert u.bio == "OSS contributor"

    def test_optional_fields_default_to_none(self):
        u = UserBase(username="alice", email=VALID_EMAIL)
        assert u.github_page is None
        assert u.bio is None

    def test_username_is_str_type(self):
        u = UserBase(username="alice", email=VALID_EMAIL)
        assert isinstance(u.username, str)

    def test_email_is_str_type(self):
        u = UserBase(username="alice", email=VALID_EMAIL)
        assert isinstance(str(u.email), str)

    def test_missing_username_raises(self):
        with pytest.raises(ValidationError):
            UserBase(email=VALID_EMAIL)

    def test_missing_email_raises(self):
        with pytest.raises(ValidationError):
            UserBase(username="alice")

    def test_invalid_email_format_raises(self):
        with pytest.raises(ValidationError):
            UserBase(username="alice", email="not-an-email")

    # --- string min / max ---
    def test_username_single_char(self):
        u = UserBase(username="a", email=VALID_EMAIL)
        assert len(u.username) == 1

    def test_username_at_db_limit_255(self):
        u = UserBase(username=STR_AT_DB_LIMIT, email=VALID_EMAIL)
        assert len(u.username) == 255

    def test_username_over_db_limit_accepted_by_schema(self):
        with pytest.raises(ValidationError):
            UserBase(username=STR_OVER_DB_LIMIT, email=VALID_EMAIL)


# ===========================================================================
# 3. UserCreate
# ===========================================================================

class TestUserCreate:

    def test_valid(self):
        u = UserCreate(username="alice", email=VALID_EMAIL, password="s3cr3t")
        assert u.password == "s3cr3t"

    def test_missing_password_raises(self):
        with pytest.raises(ValidationError):
            UserCreate(username="alice", email=VALID_EMAIL)

    def test_password_is_str_type(self):
        u = UserCreate(username="alice", email=VALID_EMAIL, password="s3cr3t")
        assert isinstance(u.password, str)

    # --- password min / max ---
    def test_password_single_char(self):
        u = UserCreate(username="alice", email=VALID_EMAIL, password="x")
        assert len(u.password) == 1

    def test_password_at_db_limit_255(self):
        u = UserCreate(username="alice", email=VALID_EMAIL, password="p" * 255)
        assert len(u.password) == 255

    def test_password_over_db_limit_accepted_by_schema(self):
        with pytest.raises(ValidationError):
            UserCreate(username="alice", email=VALID_EMAIL, password="p" * 256)


# ===========================================================================
# 4. UserUpdate
# ===========================================================================

class TestUserUpdate:

    def test_all_fields_optional(self):
        u = UserUpdate()
        assert u.username is None
        assert u.email is None
        assert u.password is None
        assert u.github_page is None
        assert u.bio is None

    def test_partial_update(self):
        u = UserUpdate(username="bob")
        assert u.username == "bob"
        assert u.email is None

    def test_invalid_email_raises(self):
        with pytest.raises(ValidationError):
            UserUpdate(email="bad-email")


# ===========================================================================
# 5. User (read schema)
# ===========================================================================

class TestUser:

    def test_valid(self):
        u = User(id=1, username="alice", email=VALID_EMAIL, created_at=NOW, updated_at=NOW)
        assert u.id == 1

    def test_missing_id_raises(self):
        with pytest.raises(ValidationError):
            User(username="alice", email=VALID_EMAIL, created_at=NOW, updated_at=NOW)

    def test_missing_created_at_raises(self):
        with pytest.raises(ValidationError):
            User(id=1, username="alice", email=VALID_EMAIL, updated_at=NOW)

    def test_missing_updated_at_raises(self):
        with pytest.raises(ValidationError):
            User(id=1, username="alice", email=VALID_EMAIL, created_at=NOW)

    def test_id_is_int_type(self):
        u = User(id=1, username="alice", email=VALID_EMAIL, created_at=NOW, updated_at=NOW)
        assert isinstance(u.id, int)

    def test_created_at_is_datetime_type(self):
        u = User(id=1, username="alice", email=VALID_EMAIL, created_at=NOW, updated_at=NOW)
        assert isinstance(u.created_at, datetime)

    def test_updated_at_is_datetime_type(self):
        u = User(id=1, username="alice", email=VALID_EMAIL, created_at=NOW, updated_at=NOW)
        assert isinstance(u.updated_at, datetime)

    def test_from_attributes_enabled(self):
        assert User.model_config.get("from_attributes") is True

    def test_id_invalid_string_raises(self):
        with pytest.raises(ValidationError):
            User(id="abc", username="alice", email=VALID_EMAIL, created_at=NOW, updated_at=NOW)

    # --- id min / max ---
    def test_id_min_positive(self):
        u = User(id=MIN_POSITIVE_INT, username="a", email=VALID_EMAIL, created_at=NOW, updated_at=NOW)
        assert u.id == MIN_POSITIVE_INT

    def test_id_max_biginteger(self):
        u = User(id=MAX_BIGINT, username="a", email=VALID_EMAIL, created_at=NOW, updated_at=NOW)
        assert u.id == MAX_BIGINT


# ===========================================================================
# 6. ProjectBase
# ===========================================================================

class TestProjectBase:

    def test_valid_minimal(self):
        p = ProjectBase(title="OSS Tool", repository_url="https://github.com/org/repo")
        assert p.title == "OSS Tool"

    def test_help_wanted_defaults_to_false(self):
        p = ProjectBase(title="OSS Tool", repository_url="https://github.com/org/repo")
        assert p.help_wanted is False

    def test_description_defaults_to_none(self):
        p = ProjectBase(title="OSS Tool", repository_url="https://github.com/org/repo")
        assert p.description is None

    def test_missing_title_raises(self):
        with pytest.raises(ValidationError):
            ProjectBase(repository_url="https://github.com/org/repo")

    def test_missing_repository_url_raises(self):
        with pytest.raises(ValidationError):
            ProjectBase(title="OSS Tool")

    def test_title_is_str_type(self):
        p = ProjectBase(title="OSS Tool", repository_url="https://github.com/org/repo")
        assert isinstance(p.title, str)

    def test_repository_url_is_str_type(self):
        p = ProjectBase(title="OSS Tool", repository_url="https://github.com/org/repo")
        assert str(p.repository_url) == "https://github.com/org/repo"

    def test_repository_url_non_http_https_raises(self):
        with pytest.raises(ValidationError):
            ProjectBase(title="OSS Tool", repository_url="ftp://example.com/repo")

    def test_help_wanted_is_bool_type(self):
        p = ProjectBase(title="OSS Tool", repository_url="https://github.com/org/repo", help_wanted=True)
        assert isinstance(p.help_wanted, bool)

    def test_invalid_help_wanted_type_raises(self):
        with pytest.raises(ValidationError):
            ProjectBase(
                title="OSS Tool",
                repository_url="https://github.com/org/repo",
                help_wanted="invalid-bool",
            )

    # --- title min / max ---
    def test_title_single_char(self):
        p = ProjectBase(title="X", repository_url="https://github.com/org/repo")
        assert len(p.title) == 1

    def test_title_at_db_limit_255(self):
        p = ProjectBase(title=STR_AT_DB_LIMIT, repository_url="https://github.com/org/repo")
        assert len(p.title) == 255

    def test_title_over_db_limit_accepted_by_schema(self):
        with pytest.raises(ValidationError):
            ProjectBase(title=STR_OVER_DB_LIMIT, repository_url="https://github.com/org/repo")


# ===========================================================================
# 7. ProjectCreate
# ===========================================================================

class TestProjectCreate:

    def test_valid(self):
        p = ProjectCreate(title="OSS Tool", repository_url="https://github.com/org/repo")
        assert p.title == "OSS Tool"
        assert p.help_wanted is False


# ===========================================================================
# 8. ProjectUpdate
# ===========================================================================

class TestProjectUpdate:

    def test_all_fields_optional(self):
        p = ProjectUpdate()
        assert p.title is None
        assert p.description is None
        assert p.repository_url is None
        assert p.help_wanted is None

    def test_partial_update(self):
        p = ProjectUpdate(help_wanted=True)
        assert p.help_wanted is True
        assert p.title is None


# ===========================================================================
# 9. Project (read schema)
# ===========================================================================

class TestProject:

    def test_valid(self):
        p = Project(
            id=1,
            title="OSS Tool",
            repository_url="https://github.com/org/repo",
            created_at=NOW,
            updated_at=NOW,
        )
        assert p.id == 1

    def test_missing_id_raises(self):
        with pytest.raises(ValidationError):
            Project(
                title="OSS Tool",
                repository_url="https://github.com/org/repo",
                created_at=NOW,
                updated_at=NOW,
            )

    def test_id_is_int_type(self):
        p = Project(id=1, title="X", repository_url="https://github.com/o/r", created_at=NOW, updated_at=NOW)
        assert isinstance(p.id, int)

    def test_timestamps_are_datetime_type(self):
        p = Project(id=1, title="X", repository_url="https://github.com/o/r", created_at=NOW, updated_at=NOW)
        assert isinstance(p.created_at, datetime)
        assert isinstance(p.updated_at, datetime)

    def test_from_attributes_enabled(self):
        assert Project.model_config.get("from_attributes") is True

    def test_id_invalid_string_raises(self):
        with pytest.raises(ValidationError):
            Project(id="NaN", title="X", repository_url="https://github.com/o/r", created_at=NOW, updated_at=NOW)

    # --- id min / max ---
    def test_id_min_positive(self):
        p = Project(id=MIN_POSITIVE_INT, title="X", repository_url="https://github.com/o/r", created_at=NOW, updated_at=NOW)
        assert p.id == MIN_POSITIVE_INT

    def test_id_max_biginteger(self):
        p = Project(id=MAX_BIGINT, title="X", repository_url="https://github.com/o/r", created_at=NOW, updated_at=NOW)
        assert p.id == MAX_BIGINT


# ===========================================================================
# 10. ContributionBase
# ===========================================================================

class TestContributionBase:

    def test_valid(self):
        c = ContributionBase(fk_user_id=1, fk_project_id=2)
        assert c.fk_user_id == 1
        assert c.fk_project_id == 2

    def test_status_defaults_to_interested(self):
        c = ContributionBase(fk_user_id=1, fk_project_id=1)
        assert c.status == "interested"

    def test_status_is_str_type(self):
        c = ContributionBase(fk_user_id=1, fk_project_id=1)
        assert isinstance(c.status, str)

    def test_fk_user_id_is_int_type(self):
        c = ContributionBase(fk_user_id=1, fk_project_id=1)
        assert isinstance(c.fk_user_id, int)

    def test_fk_project_id_is_int_type(self):
        c = ContributionBase(fk_user_id=1, fk_project_id=1)
        assert isinstance(c.fk_project_id, int)

    def test_missing_fk_user_id_raises(self):
        with pytest.raises(ValidationError):
            ContributionBase(fk_project_id=1)

    def test_missing_fk_project_id_raises(self):
        with pytest.raises(ValidationError):
            ContributionBase(fk_user_id=1)

    def test_fk_user_id_invalid_string_raises(self):
        with pytest.raises(ValidationError):
            ContributionBase(fk_user_id="abc", fk_project_id=1)

    def test_fk_project_id_invalid_string_raises(self):
        with pytest.raises(ValidationError):
            ContributionBase(fk_user_id=1, fk_project_id="abc")

    # --- int min / max ---
    def test_fk_user_id_min_positive(self):
        c = ContributionBase(fk_user_id=MIN_POSITIVE_INT, fk_project_id=1)
        assert c.fk_user_id == MIN_POSITIVE_INT

    def test_fk_project_id_min_positive(self):
        c = ContributionBase(fk_user_id=1, fk_project_id=MIN_POSITIVE_INT)
        assert c.fk_project_id == MIN_POSITIVE_INT

    def test_fk_user_id_max_biginteger(self):
        c = ContributionBase(fk_user_id=MAX_BIGINT, fk_project_id=1)
        assert c.fk_user_id == MAX_BIGINT

    def test_fk_project_id_max_biginteger(self):
        c = ContributionBase(fk_user_id=1, fk_project_id=MAX_BIGINT)
        assert c.fk_project_id == MAX_BIGINT

    # --- status string min / max ---
    def test_status_at_db_limit_20(self):
        c = ContributionBase(fk_user_id=1, fk_project_id=1, status=STATUS_AT_DB_LIMIT)
        assert len(c.status) == 20

    def test_status_over_db_limit_accepted_by_schema(self):
        with pytest.raises(ValidationError):
            ContributionBase(fk_user_id=1, fk_project_id=1, status=STATUS_OVER_DB_LIMIT)


# ===========================================================================
# 11. ContributionCreate
# ===========================================================================

class TestContributionCreate:

    def test_valid(self):
        c = ContributionCreate(fk_user_id=1, fk_project_id=2)
        assert c.status == "interested"


# ===========================================================================
# 12. ContributionUpdate
# ===========================================================================

class TestContributionUpdate:

    def test_all_fields_optional(self):
        c = ContributionUpdate()
        assert c.status is None

    def test_partial_update(self):
        c = ContributionUpdate(status="contributed")
        assert c.status == "contributed"


# ===========================================================================
# 13. Contribution (read schema)
# ===========================================================================

class TestContribution:

    def test_valid(self):
        c = Contribution(
            id=1,
            fk_user_id=1,
            fk_project_id=2,
            applied_at=NOW,
            updated_at=NOW,
        )
        assert c.id == 1

    def test_missing_id_raises(self):
        with pytest.raises(ValidationError):
            Contribution(fk_user_id=1, fk_project_id=2, applied_at=NOW, updated_at=NOW)

    def test_missing_applied_at_raises(self):
        with pytest.raises(ValidationError):
            Contribution(id=1, fk_user_id=1, fk_project_id=2, updated_at=NOW)

    def test_missing_updated_at_raises(self):
        with pytest.raises(ValidationError):
            Contribution(id=1, fk_user_id=1, fk_project_id=2, applied_at=NOW)

    def test_id_is_int_type(self):
        c = Contribution(id=1, fk_user_id=1, fk_project_id=2, applied_at=NOW, updated_at=NOW)
        assert isinstance(c.id, int)

    def test_applied_at_is_datetime_type(self):
        c = Contribution(id=1, fk_user_id=1, fk_project_id=2, applied_at=NOW, updated_at=NOW)
        assert isinstance(c.applied_at, datetime)

    def test_updated_at_is_datetime_type(self):
        c = Contribution(id=1, fk_user_id=1, fk_project_id=2, applied_at=NOW, updated_at=NOW)
        assert isinstance(c.updated_at, datetime)

    def test_from_attributes_enabled(self):
        assert Contribution.model_config.get("from_attributes") is True

    def test_id_invalid_string_raises(self):
        with pytest.raises(ValidationError):
            Contribution(id="bad", fk_user_id=1, fk_project_id=1, applied_at=NOW, updated_at=NOW)

    # --- id min / max ---
    def test_id_min_positive(self):
        c = Contribution(id=MIN_POSITIVE_INT, fk_user_id=1, fk_project_id=1, applied_at=NOW, updated_at=NOW)
        assert c.id == MIN_POSITIVE_INT

    def test_id_max_biginteger(self):
        c = Contribution(id=MAX_BIGINT, fk_user_id=1, fk_project_id=1, applied_at=NOW, updated_at=NOW)
        assert c.id == MAX_BIGINT

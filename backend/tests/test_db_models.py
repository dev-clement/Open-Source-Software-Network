from app.domain.enums import ContributionStatus
from app.db.models import Contribution, Project, User
from sqlmodel import SQLModel


def test_models_registered_in_metadata():
    tables = SQLModel.metadata.tables

    assert "user" in tables
    assert "projects" in tables
    assert "contributions" in tables

    assert User.__tablename__ == "user"
    assert Project.__tablename__ == "projects"
    assert Contribution.__tablename__ == "contributions"

    assert tables["user"].c["id"].primary_key
    assert tables["projects"].c["repository_url"].unique
    assert tables["contributions"].c["fk_user_id"].foreign_keys


def test_user_table_has_expected_columns():
    columns = set(SQLModel.metadata.tables["user"].c.keys())

    assert columns == {
        "id",
        "username",
        "email",
        "password",
        "github_page",
        "bio",
        "created_at",
        "updated_at",
    }


def test_project_table_has_expected_columns():
    columns = set(SQLModel.metadata.tables["projects"].c.keys())

    assert columns == {
        "id",
        "title",
        "description",
        "repository_url",
        "help_wanted",
        "created_at",
        "updated_at",
        "owner_id",
    }


def test_contribution_table_has_expected_columns():
    columns = set(SQLModel.metadata.tables["contributions"].c.keys())

    assert columns == {
        "id",
        "fk_user_id",
        "fk_project_id",
        "status",
        "applied_at",
        "updated_at",
    }


def test_user_primary_key_is_id():
    user_table = SQLModel.metadata.tables["user"]

    assert user_table.c["id"].primary_key is True


def test_project_primary_key_is_id():
    project_table = SQLModel.metadata.tables["projects"]

    assert project_table.c["id"].primary_key is True


def test_contribution_primary_key_is_id():
    contribution_table = SQLModel.metadata.tables["contributions"]

    assert contribution_table.c["id"].primary_key is True


def test_user_email_is_unique_and_not_nullable():
    email_column = SQLModel.metadata.tables["user"].c["email"]

    assert email_column.unique is True
    assert email_column.nullable is False


def test_project_repository_url_is_unique_and_not_nullable():
    repository_url_column = SQLModel.metadata.tables["projects"].c["repository_url"]

    assert repository_url_column.unique is True
    assert repository_url_column.nullable is False


def test_help_wanted_is_boolean_not_nullable_column():
    help_wanted_column = SQLModel.metadata.tables["projects"].c["help_wanted"]

    assert help_wanted_column.nullable is False
    assert help_wanted_column.type.python_type is bool


def test_contribution_foreign_keys_target_user_and_project_tables():
    contribution_table = SQLModel.metadata.tables["contributions"]
    user_fk = next(iter(contribution_table.c["fk_user_id"].foreign_keys))
    project_fk = next(iter(contribution_table.c["fk_project_id"].foreign_keys))

    assert user_fk.target_fullname == "user.id"
    assert project_fk.target_fullname == "projects.id"


def test_contribution_foreign_keys_use_cascade_delete():
    contribution_table = SQLModel.metadata.tables["contributions"]
    user_fk = next(iter(contribution_table.c["fk_user_id"].foreign_keys))
    project_fk = next(iter(contribution_table.c["fk_project_id"].foreign_keys))

    assert user_fk.ondelete == "CASCADE"
    assert project_fk.ondelete == "CASCADE"


def test_user_timestamp_columns_have_server_defaults():
    user_table = SQLModel.metadata.tables["user"]

    assert user_table.c["created_at"].server_default is not None
    assert user_table.c["updated_at"].server_default is not None


def test_project_timestamp_columns_have_server_defaults():
    project_table = SQLModel.metadata.tables["projects"]

    assert project_table.c["created_at"].server_default is not None
    assert project_table.c["updated_at"].server_default is not None


def test_contribution_timestamp_columns_have_server_defaults():
    contribution_table = SQLModel.metadata.tables["contributions"]

    assert contribution_table.c["applied_at"].server_default is not None
    assert contribution_table.c["updated_at"].server_default is not None


def test_updated_at_columns_have_onupdate_callbacks():
    user_updated = SQLModel.metadata.tables["user"].c["updated_at"]
    project_updated = SQLModel.metadata.tables["projects"].c["updated_at"]
    contribution_updated = SQLModel.metadata.tables["contributions"].c["updated_at"]

    assert user_updated.onupdate is not None
    assert project_updated.onupdate is not None
    assert contribution_updated.onupdate is not None


def test_contribution_status_has_interested_server_default():
    status_column = SQLModel.metadata.tables["contributions"].c["status"]
    default_sql = str(status_column.server_default.arg).lower()

    assert status_column.nullable is False
    assert ContributionStatus.INTERESTED.value in default_sql


def test_user_contributions_relationship_back_populates_user():
    relationship = User.contributions.property

    assert relationship.back_populates == "user"


def test_project_contributions_relationship_back_populates_project():
    relationship = Project.contributions.property

    assert relationship.back_populates == "project"


def test_contribution_user_relationship_back_populates_contributions():
    relationship = Contribution.user.property

    assert relationship.back_populates == "contributions"


def test_contribution_project_relationship_back_populates_contributions():
    relationship = Contribution.project.property

    assert relationship.back_populates == "contributions"


def test_user_model_instantiation_sets_required_fields():
    user = User(username="alice", email="alice@example.com", password="secret")

    assert user.username == "alice"
    assert user.email == "alice@example.com"
    assert user.password == "secret"


def test_project_model_instantiation_defaults_help_wanted_to_false():
    project = Project(title="OSS", repository_url="https://github.com/example/oss")

    assert project.help_wanted is False


def test_contribution_model_instantiation_defaults_status_to_interested():
    contribution = Contribution(fk_user_id=1, fk_project_id=1)

    assert contribution.status == ContributionStatus.INTERESTED

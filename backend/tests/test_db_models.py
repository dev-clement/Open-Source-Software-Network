from sqlmodel import SQLModel

from app.db.models import Contribution, Project, User


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

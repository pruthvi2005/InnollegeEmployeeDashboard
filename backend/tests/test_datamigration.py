import pytest
from sqlalchemy import Column, ForeignKey, Integer, MetaData, String, Table, create_engine, select
from sqlalchemy.engine import URL

from datamigration import MigrationError, transfer_data


def _database_url(path):
    return URL.create(
        "sqlite+pysqlite",
        database=path.as_posix(),
    ).render_as_string(hide_password=False)


def _create_schema(url):
    engine = create_engine(url)
    metadata = MetaData()
    users = Table(
        "users",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("email", String, nullable=False),
    )
    tasks = Table(
        "tasks",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
        Column("title", String, nullable=False),
    )
    metadata.create_all(engine)
    return engine, users, tasks


def test_transfer_data_dry_run_and_apply_preserve_source(tmp_path):
    source_url = _database_url(tmp_path / "source.db")
    target_url = _database_url(tmp_path / "target.db")
    source_engine, source_users, source_tasks = _create_schema(source_url)
    target_engine, target_users, target_tasks = _create_schema(target_url)

    with source_engine.begin() as connection:
        connection.execute(source_users.insert(), [{"id": 1, "email": "founder@example.test"}])
        connection.execute(
            source_tasks.insert(),
            [{"id": 1, "user_id": 1, "title": "Initial task"}],
        )

    assert transfer_data(source_url, target_url) == {"users": 1, "tasks": 1}
    with target_engine.connect() as connection:
        assert connection.execute(select(target_users)).all() == []
        assert connection.execute(select(target_tasks)).all() == []

    assert transfer_data(source_url, target_url, apply=True) == {"users": 1, "tasks": 1}
    with target_engine.connect() as connection:
        assert len(connection.execute(select(target_users)).all()) == 1
        assert len(connection.execute(select(target_tasks)).all()) == 1
    with source_engine.connect() as connection:
        assert len(connection.execute(select(source_users)).all()) == 1
        assert len(connection.execute(select(source_tasks)).all()) == 1

    source_engine.dispose()
    target_engine.dispose()


def test_transfer_data_refuses_a_populated_destination(tmp_path):
    source_url = _database_url(tmp_path / "source.db")
    target_url = _database_url(tmp_path / "target.db")
    source_engine, source_users, _ = _create_schema(source_url)
    target_engine, target_users, _ = _create_schema(target_url)

    with source_engine.begin() as connection:
        connection.execute(source_users.insert(), [{"id": 1, "email": "founder@example.test"}])
    with target_engine.begin() as connection:
        connection.execute(target_users.insert(), [{"id": 2, "email": "existing@example.test"}])

    with pytest.raises(MigrationError, match="Destination is not empty"):
        transfer_data(source_url, target_url, apply=True)

    with target_engine.connect() as connection:
        assert connection.execute(select(target_users)).all() == [
            (2, "existing@example.test")
        ]

    source_engine.dispose()
    target_engine.dispose()

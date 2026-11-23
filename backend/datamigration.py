"""Copy application data from the local SQLite database to a configured target."""

import argparse
import os
from pathlib import Path
from typing import Dict

from sqlalchemy import MetaData, create_engine, func, select
from sqlalchemy.engine import URL
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings

BATCH_SIZE = 500
EXCLUDED_TABLES = {"alembic_version"}


class MigrationError(Exception):
    """Raised when source and destination are not safe to migrate."""


def default_source_url() -> str:
    source_path = Path(__file__).resolve().parents[1] / "jyohar.db"
    return URL.create(
        "sqlite+pysqlite",
        database=source_path.as_posix(),
    ).render_as_string(hide_password=False)


def transfer_data(source_url: str, target_url: str, apply: bool = False) -> Dict[str, int]:
    """Copy all rows after verifying compatible schemas and an empty destination."""
    source_engine = create_engine(source_url)
    target_engine = create_engine(target_url, pool_pre_ping=True)

    try:
        if source_engine.url == target_engine.url:
            raise MigrationError("Source and destination must be different databases.")

        with source_engine.connect() as source, target_engine.begin() as target:
            source_metadata = MetaData()
            target_metadata = MetaData()
            source_metadata.reflect(bind=source)
            target_metadata.reflect(bind=target)

            source_tables = set(source_metadata.tables) - EXCLUDED_TABLES
            target_tables = set(target_metadata.tables) - EXCLUDED_TABLES
            if source_tables != target_tables:
                missing = sorted(source_tables - target_tables)
                extra = sorted(target_tables - source_tables)
                raise MigrationError(
                    "Source and target schemas differ. "
                    f"Missing target tables: {missing}; extra target tables: {extra}. "
                    "Apply the Alembic schema to MySQL before migrating data."
                )

            for table_name in source_tables:
                source_columns = set(source_metadata.tables[table_name].columns.keys())
                target_columns = set(target_metadata.tables[table_name].columns.keys())
                if source_columns != target_columns:
                    raise MigrationError(
                        f"Column definitions differ for table '{table_name}'. "
                        "Update the target schema before migrating data."
                    )

            target_counts = {
                table_name: target.execute(
                    select(func.count()).select_from(target_metadata.tables[table_name])
                ).scalar_one()
                for table_name in target_tables
            }
            populated_tables = sorted(
                name for name, row_count in target_counts.items() if row_count
            )
            if populated_tables:
                raise MigrationError(
                    "Destination is not empty; refusing to duplicate or overwrite data. "
                    f"Populated tables: {populated_tables}"
                )

            source_counts = {
                table_name: source.execute(
                    select(func.count()).select_from(source_metadata.tables[table_name])
                ).scalar_one()
                for table_name in source_tables
            }

            if apply:
                for target_table in target_metadata.sorted_tables:
                    table_name = target_table.name
                    if table_name in EXCLUDED_TABLES:
                        continue

                    source_table = source_metadata.tables[table_name]
                    rows = source.execute(select(source_table))
                    while batch := rows.mappings().fetchmany(BATCH_SIZE):
                        target.execute(
                            target_table.insert(),
                            [dict(row) for row in batch],
                        )

            return source_counts
    finally:
        source_engine.dispose()
        target_engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Copy all rows from jyohar.db into an empty MySQL database."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="perform the copy; without this flag, only validate and report row counts",
    )
    args = parser.parse_args()

    source_url = os.getenv("SOURCE_DATABASE_URL", default_source_url())
    target_url = os.getenv("TARGET_DATABASE_URL", settings.DATABASE_URL)

    try:
        counts = transfer_data(source_url, target_url, apply=args.apply)
    except MigrationError as exc:
        parser.exit(2, f"Migration stopped safely: {exc}\n")
    except SQLAlchemyError as exc:
        parser.exit(
            2,
            "Database migration failed "
            f"({type(exc).__name__}). Check database connectivity, schema, and credentials.\n",
        )

    action = "Copied" if args.apply else "Validated (dry run)"
    print(f"{action} row counts:")
    for table_name, row_count in sorted(counts.items()):
        print(f"  {table_name}: {row_count}")
    if not args.apply:
        print("No data was written. Re-run with --apply to perform the copy.")


if __name__ == "__main__":
    main()

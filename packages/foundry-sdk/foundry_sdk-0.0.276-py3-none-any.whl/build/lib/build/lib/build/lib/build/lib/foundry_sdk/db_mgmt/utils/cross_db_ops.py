"""Cross-database utility functions for multi-database operations."""

import typing as t

from foundry_sdk.db_mgmt.sql_db_alchemy import SQLAlchemyDatabase


def is_table_empty(db: SQLAlchemyDatabase, table_class: t.Any) -> bool:
    """
    Check if a table is empty.

    Args:
        db: Database connection instance
        table_class: SQLAlchemy model class (e.g., Regions, Companies)

    Returns:
        True if table is empty, False otherwise

    """
    from sqlalchemy import select

    with db.get_session() as session:
        stmt = select(table_class).limit(1)
        row = session.execute(stmt).first()
        return row is None


def copy_table_data(
    source_db: SQLAlchemyDatabase,
    target_db: SQLAlchemyDatabase,
    source_table_class: t.Any,
    target_table_class: t.Any,
    columns: list[str] | None = None,
) -> None:
    """
    Copy data from one database table to another.

    Args:
        source_db: Source database connection
        target_db: Target database connection
        source_table_class: Source SQLAlchemy model class
        target_table_class: Target SQLAlchemy model class
        columns: Optional list of columns to copy (copies all if None)

    """
    # Get column definitions from both tables
    source_columns = {col.name: col.type for col in source_table_class.__table__.columns}
    target_columns = {col.name: col.type for col in target_table_class.__table__.columns}

    # Determine columns to copy
    if columns is None:
        # Find common columns between source and target
        common_columns = set(source_columns.keys()) & set(target_columns.keys())
        columns = list(common_columns)
    else:
        # Validate that specified columns exist in both tables
        missing_source = set(columns) - set(source_columns.keys())
        missing_target = set(columns) - set(target_columns.keys())

        if missing_source:
            raise ValueError(f"Columns not found in source table: {missing_source}")
        if missing_target:
            raise ValueError(f"Columns not found in target table: {missing_target}")

    if not columns:
        raise ValueError("No common columns found between source and target tables")

    # Read data from source database
    with source_db.get_session() as source_session:
        source_data = source_session.query(source_table_class).all()

        # Convert to list of dictionaries with only the specified columns
        data_list = []
        for row in source_data:
            row_dict = {}
            for col in columns:
                row_dict[col] = getattr(row, col)
            data_list.append(row_dict)

    # Write to target database
    if data_list:
        import polars as pl

        data_df = pl.DataFrame(data_list)

        target_db.handle_insertion_multi_line(
            model_class=target_table_class,
            data=data_df,
            mode="IGNORE",
            returning_id=False,
        )


def get_company_id(db: SQLAlchemyDatabase, company_name: str) -> int | None:
    """
    Get company ID by name.

    Args:
        db: Database connection instance
        company_name: Name of the company

    Returns:
        Company ID if found, None otherwise

    """
    from sqlalchemy import select

    from foundry_sdk.db_mgmt.tables_ts import Companies

    with db.get_session() as session:
        stmt = select(Companies.company_id).where(Companies.company_name == company_name)
        result = session.execute(stmt).scalar_one_or_none()
        return result

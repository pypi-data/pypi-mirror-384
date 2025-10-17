import io
import logging
import multiprocessing as mp
import time
import typing as t
from contextlib import contextmanager
from functools import partial
from pathlib import Path
from types import TracebackType

import polars as pl
from kedro.config import OmegaConfigLoader
from kedro.framework.project import settings
from sqlalchemy import Column, MetaData, Table, create_engine, text, tuple_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.pool import QueuePool
from sqlalchemy.sql import bindparam
from tqdm import tqdm

from .dtype_mappings import sa_column_to_polars_dtype

logger = logging.getLogger(__name__)


def _quote_ident(name: str) -> str:
    """Double-quote an identifier for PostgreSQL, escaping internal quotes."""
    return '"' + name.replace('"', '""') + '"'


def _full_table_name(sa_table: Table) -> str:
    """Schema-qualify and quote a SQLAlchemy table name for PostgreSQL."""
    if sa_table.schema:
        return f"{_quote_ident(sa_table.schema)}.{_quote_ident(sa_table.name)}"
    return _quote_ident(sa_table.name)


class SQLAlchemyDatabase:
    """
    SQLAlchemy-based database management class to replace the legacy psycopg2 implementation.
    Provides three ways to configure database credentials and modern session management.
    """

    def __init__(
        self,
        *,
        autocommit: bool = False,
        pool_size: int = 10,
        max_overflow: int = 20,
        pool_timeout: int = 30,
        pool_recycle: int = 3600,
        echo: bool = False,
        connect_args: dict | None = None,
    ) -> None:
        self.engine: Engine | None = None
        self.SessionLocal: t.Callable[[], Session] | None = None
        self.autocommit = autocommit
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.pool_recycle = pool_recycle
        self.echo = echo
        self.connect_args = connect_args or {}

    def _create_engine(self, connection_string: str) -> Engine:
        return create_engine(
            connection_string,
            poolclass=QueuePool,
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
            pool_timeout=self.pool_timeout,
            pool_recycle=self.pool_recycle,
            pool_pre_ping=True,
            echo=self.echo,
            connect_args=self.connect_args,
            pool_reset_on_return="commit",
            execution_options={"isolation_level": "READ_COMMITTED"},
        )

    @classmethod
    def from_kedro(cls, credentials_name: str = "postgres", **kwargs) -> "SQLAlchemyDatabase":
        conf_path = str(Path(settings.CONF_SOURCE))
        conf_loader = OmegaConfigLoader(conf_source=conf_path)

        db_credentials = conf_loader["credentials"][credentials_name]
        connection_string = db_credentials["con"]
        instance = cls(**kwargs)
        instance.engine = instance._create_engine(connection_string)
        instance.SessionLocal = sessionmaker(
            bind=instance.engine,
            autocommit=instance.autocommit,
            autoflush=not instance.autocommit,
        )
        return instance

    @classmethod
    def from_connection_string(
        cls,
        connection_string: str,
        **kwargs,
    ) -> "SQLAlchemyDatabase":
        instance = cls(**kwargs)
        instance.engine = instance._create_engine(connection_string)
        instance.SessionLocal = sessionmaker(
            bind=instance.engine,
            autocommit=instance.autocommit,
            autoflush=not instance.autocommit,
        )
        return instance

    @classmethod
    def from_parameters(
        cls,
        host: str,
        port: int,
        database: str,
        user: str,
        password: str,
        **kwargs,
    ) -> "SQLAlchemyDatabase":
        connection_params = {}
        instance_params = {}

        for key, value in kwargs.items():
            if key in ["sslmode", "application_name", "connect_timeout", "sslcert", "sslkey"]:
                connection_params[key] = value
            else:
                instance_params[key] = value

        connection_string = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        if connection_params:
            params = "&".join([f"{k}={v}" for k, v in connection_params.items()])
            connection_string += f"?{params}"

        instance = cls(**instance_params)
        instance.engine = instance._create_engine(connection_string)
        instance.SessionLocal = sessionmaker(
            bind=instance.engine,
            autocommit=instance.autocommit,
            autoflush=not instance.autocommit,
        )
        return instance

    @contextmanager
    def get_session(self, *, read_only: bool = False) -> t.Generator[Session, None, None]:
        if not self.SessionLocal:
            raise RuntimeError(
                "Database not configured. Call one of the factory methods "
                "(from_kedro, from_connection_string, from_parameters) first.",
            )

        session = self.SessionLocal()

        try:
            if read_only:
                session.execute(text("SET TRANSACTION READ ONLY"))
            yield session
            if not self.autocommit and not read_only:
                session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def test_connection(self) -> bool:
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
        except SQLAlchemyError:
            logger.exception("[DB Test Failed]")
            return False
        else:
            return True

    def health_check(self) -> dict[str, t.Any]:
        try:
            start_time = time.time()

            with self.get_session() as session:
                session.execute(text("SELECT 1"))
                result = session.execute(text("SELECT current_timestamp, version()")).fetchone()
                db_time = result[0] if result else None
                db_version = result[1] if result else None

            response_time = time.time() - start_time
            pool_status = {}
            if self.engine and hasattr(self.engine, "pool"):
                pool = self.engine.pool
                pool_status = {
                    "pool_size": pool.size(),
                    "checked_out_connections": pool.checkedout(),
                    "overflow_connections": pool.overflow(),
                    "invalid_connections": pool.invalidated(),
                }

            return {
                "status": "healthy",
                "response_time_ms": round(response_time * 1000, 2),
                "database_time": str(db_time) if db_time else None,
                "database_version": db_version.split("\n")[0] if db_version else None,
                "pool_status": pool_status,
                "autocommit_mode": self.autocommit,
                "timestamp": time.time(),
            }

        except SQLAlchemyError as e:
            return {
                "status": "unhealthy",
                "error": f"Database error: {e!s}",
                "timestamp": time.time(),
            }

    def get_primary_unique_constraint(self, model_class: DeclarativeMeta) -> list[str]:
        if hasattr(model_class, "__unique_keys__"):
            return model_class.__unique_keys__
        msg = f"Model class {model_class.__name__} does not define __unique_keys__ attribute."
        raise ValueError(msg)

    def copy_read_table(
        self,
        model: type[DeclarativeMeta],
        *,
        null_tokens: tuple[str, ...] = ("", "NULL", "null"),
    ) -> pl.DataFrame:
        """Read an entire model table into a Polars DataFrame via PostgreSQL COPY."""
        if not hasattr(model, "__table__"):
            msg = "Model must define a __table__ attribute."
            raise TypeError(msg)

        sa_table: Table = model.__table__
        cols = [col.name for col in sa_table.columns]

        select_cols = ", ".join(_quote_ident(col_name) for col_name in cols)
        table_name = _full_table_name(sa_table)

        select_sql = f"SELECT {select_cols} FROM {table_name}"

        buf = io.StringIO()

        with self.get_session(read_only=True) as session:
            raw_conn = session.connection().connection
            with raw_conn.cursor() as cursor:
                cursor.copy_expert(
                    f"COPY ({select_sql}) TO STDOUT WITH (FORMAT CSV, HEADER, ENCODING 'UTF8')",
                    buf,
                )

        buf.seek(0)

        schema_overrides = {col.name: sa_column_to_polars_dtype(col) for col in sa_table.columns}

        return pl.read_csv(
            buf,
            dtypes=schema_overrides,
            infer_schema_length=0,
            null_values=list(null_tokens),
        )

    def get_primary_key_columns(self, model_class: DeclarativeMeta) -> list[str]:
        """
        Get the primary key column names for a model class.

        Args:
            model_class: SQLAlchemy model class

        Returns:
            list[str]: List of primary key column names

        """
        return [col.name for col in model_class.__table__.primary_key.columns]

    def get_single_primary_key_column(self, model_class: DeclarativeMeta) -> str:
        """
        Get the single primary key column name for a model class.
        Raises an error if there are multiple primary key columns.

        Args:
            model_class: SQLAlchemy model class

        Returns:
            str: Primary key column name

        Raises:
            ValueError: If the model has a composite primary key

        """
        pk_columns = self.get_primary_key_columns(model_class)
        if len(pk_columns) != 1:
            msg = f"Model {model_class.__name__} has {len(pk_columns)} primary key columns, expected exactly 1"
            raise ValueError(msg)
        return pk_columns[0]

    def _validate_single_line_input(
        self,
        model_class: DeclarativeMeta,
        data: dict[str, t.Any],
    ) -> None:
        """Validate the input data is a dict representing a single row."""
        if not isinstance(data, dict):
            raise TypeError("`data` must be a dict of column names to values.")
        table = model_class.__table__
        model_columns = {col.name for col in table.columns}
        extra_keys = set(data.keys()) - model_columns
        if extra_keys:
            msg = f"Unexpected columns in data: {extra_keys}"
            raise ValueError(msg)

    def handle_insertion_single_line(
        self,
        model_class: DeclarativeMeta,
        data: dict[str, t.Any],
        mode: t.Literal["RAISE", "IGNORE", "UPDATE"],
        *,
        returning_id: bool = False,
    ) -> int | dict[str, t.Any] | None:
        """
        Unified single-call insert/upsert with explicit modes.
         - RAISE:   plain INSERT, error on conflict
         - IGNORE:  INSERT ... ON CONFLICT DO NOTHING
         - UPDATE:  INSERT ... ON CONFLICT DO UPDATE (excluding PK cols).

        Conflict logic targets the model's primary key columns.

        Args:
            model_class: SQLAlchemy model class
            data: Dictionary of column names to values
            mode: Conflict resolution strategy ("RAISE", "IGNORE", "UPDATE")
            returning_id: If True, returns the record ID(s); if False, returns None

        Returns:
            int: the primary key (id) of the processed record if returning_id=True and single PK
            dict: all primary key columns if returning_id=True and composite PK
            None: if returning_id=False

        """
        # validate that data keys match the model
        self._validate_single_line_input(model_class, data)
        self.check_mode(mode)

        p_unique_key_columns = self.get_primary_unique_constraint(model_class)

        # build base INSERT statement
        stmt = insert(model_class).values(**data)

        # Get primary key column(s) for returning ID
        if returning_id:
            pk_columns = self.get_primary_key_columns(model_class)
            pk_attrs = [self.get_column_attr_by_db_name(model_class, col) for col in pk_columns]

        # apply conflict clause per mode
        if mode == "IGNORE":
            stmt = stmt.on_conflict_do_nothing(index_elements=p_unique_key_columns)
            with self.get_session() as session:
                if returning_id:
                    stmt_ret = stmt.returning(*pk_attrs)
                    result = session.execute(stmt_ret).fetchone()
                    if result is None:
                        # Find existing record that caused the conflict
                        pk_filter = {pk: data[pk] for pk in p_unique_key_columns if pk in data}
                        query_result = session.query(*pk_attrs).filter_by(**pk_filter).first()
                        if query_result is None:
                            raise RuntimeError("Record not found after conflict - possible race condition")
                        result = query_result

                    # Return single value for single PK, dict for composite PK
                    if len(pk_columns) == 1:
                        return result[0] if hasattr(result, "__getitem__") else result
                    return dict(zip(pk_columns, result, strict=True))
                session.execute(stmt)
                return None
        elif mode == "UPDATE":
            update_data = {k: getattr(stmt.excluded, k) for k in data if k not in p_unique_key_columns}
            if not update_data:  # All columns are primary keys
                # Convert to IGNORE behavior since nothing to update
                stmt = stmt.on_conflict_do_nothing(index_elements=p_unique_key_columns)
            else:
                stmt = stmt.on_conflict_do_update(
                    index_elements=p_unique_key_columns,
                    set_=update_data,
                )
        elif mode == "RAISE":
            # no ON CONFLICT clause; let DB raise on duplicates
            pass
        else:
            msg = f"Unsupported insertion mode: '{mode}'"
            raise ValueError(msg)

        # UPDATE or RAISE paths: execute and optionally fetch the ID
        with self.get_session() as session:
            if returning_id:
                stmt = stmt.returning(*pk_attrs)
                result = session.execute(stmt).fetchone()
                # Return single value for single PK, dict for composite PK
                if len(pk_columns) == 1:
                    return result[0] if hasattr(result, "__getitem__") else result
                return dict(zip(pk_columns, result, strict=True))
            session.execute(stmt)
            return None

    def handle_insertion_multi_line(
        self,
        model_class: DeclarativeMeta,
        data: pl.DataFrame,
        mode: t.Literal["RAISE", "IGNORE", "UPDATE"],
        *,
        threshold_for_copy: int = 1_000_001,
        returning_id: bool = False,
        parallel_workers: int = 1,
    ) -> pl.DataFrame | None:
        """
        Validate a Polars DataFrame against the model schema, then delegate
        to the bulk-insert implementation.
        """
        self.check_mode(mode)
        # 1. Basic type & column-name checks
        if not isinstance(data, pl.DataFrame):
            raise TypeError("`data` must be a Polars DataFrame.")

        if len(data) == 0:
            logger.warning("Empty DataFrame provided, nothing to insert.")
            return None

        if len(data) >= threshold_for_copy:
            if parallel_workers > 1:
                return self.handle_insertion_multi_line_copy_parallel(
                    model_class,
                    data,
                    mode,
                    returning_id=returning_id,
                    num_workers=parallel_workers,
                )
            return self.handle_insertion_multi_line_copy(
                model_class,
                data,
                mode,
                returning_id=returning_id,
            )

        return self.handle_insertion_multi_line_bulk(
            model_class,
            data,
            mode,
            returning_id=returning_id,
        )

    def handle_insertion_multi_line_bulk(
        self,
        model_class: DeclarativeMeta,
        data: pl.DataFrame,
        mode: t.Literal["RAISE", "IGNORE", "UPDATE"],
        *,
        chunk_size: int = 10000,
        returning_id: bool = False,
    ) -> pl.DataFrame | None:
        """
        Perform bulk upserts in chunks of `chunk_size` rows using SQLAlchemy Core.

        Writes data first, then—if `returning_id=True`—fetches all primary keys
        for the provided unique-key combinations in one go.
        Returns a DataFrame of unique-key columns plus "ID" if requested,
        otherwise returns None.
        """
        # Determine unique-key columns
        p_unique_key_columns = self.get_primary_unique_constraint(model_class)
        logger.info(
            "Starting bulk insert of %d rows in %d chunks of size %d",
            data.height,
            (data.height + chunk_size - 1) // chunk_size,
            chunk_size,
        )
        table_name = model_class.__table__.name
        self._write_chunks(
            model_class,
            data,
            mode,
            chunk_size,
            p_unique_key_columns,
            table_name,
        )

        if returning_id:
            logger.info("Fetching IDs for unique keys: %s", p_unique_key_columns)
            return self._fetch_ids_chunks(
                model_class,
                data,
                chunk_size,
                p_unique_key_columns,
            )

        return None

    def _write_chunks(
        self,
        model_class: DeclarativeMeta,
        data: pl.DataFrame,
        mode: t.Literal["RAISE", "IGNORE", "UPDATE"],
        chunk_size: int,
        p_unique_key_columns: list[str],
        table_name: str,
    ) -> None:
        """Helper to write data into the database in chunks."""
        total_rows = data.height
        total_chunks = (total_rows + chunk_size - 1) // chunk_size
        row_iter = range(0, total_rows, chunk_size)
        show_progress = total_chunks > 1
        progress_bar = (
            tqdm(
                row_iter,
                total=total_rows,
                desc=f"Bulk writing to table: {table_name}",
                unit="rows",
                dynamic_ncols=True,
            )
            if show_progress
            else row_iter
        )
        columns = data.columns
        stmt = insert(model_class.__table__).values({col: bindparam(col) for col in columns})
        if mode == "IGNORE":
            stmt = stmt.on_conflict_do_nothing(index_elements=p_unique_key_columns)
        elif mode == "UPDATE":
            update_cols = [c for c in columns if c not in p_unique_key_columns]
            if update_cols:
                stmt = stmt.on_conflict_do_update(
                    index_elements=p_unique_key_columns, set_={col: stmt.excluded[col] for col in update_cols}
                )
            else:
                stmt = stmt.on_conflict_do_nothing(index_elements=p_unique_key_columns)
        elif mode == "RAISE":
            pass  # No ON CONFLICT clause needed

        with self.get_session() as session:
            for offset in row_iter:
                chunk_df = data.slice(offset, chunk_size)
                records = chunk_df.to_dicts()
                session.execute(stmt, records)
                # Manually update progress bar to show correct number of rows processed
                if show_progress:
                    progress_bar.update(len(records))

    def _fetch_ids_chunks(
        self,
        model_class: DeclarativeMeta,
        data: pl.DataFrame,
        chunk_size: int,
        p_unique_key_columns: list[str],
        use_temp_table: int = 10,
    ) -> pl.DataFrame:
        """Helper to fetch IDs in chunks after writing data. Uses temp table for large chunks."""
        key_df = data.select(*p_unique_key_columns)
        total_keys = key_df.height
        total_chunks = (total_keys + chunk_size - 1) // chunk_size
        row_iter = range(0, total_keys, chunk_size)
        show_progress = total_chunks > 1
        progress_bar = (
            tqdm(
                row_iter,
                total=total_keys,
                desc=f"Fetching IDs from table: {model_class.__table__.name}",
                unit="rows",
                dynamic_ncols=True,
            )
            if show_progress
            else row_iter
        )
        unique_key_attrs = [self.get_column_attr_by_db_name(model_class, col) for col in p_unique_key_columns]
        use_temp = chunk_size > use_temp_table
        if use_temp:
            ids = self._fetch_ids_chunks_temp_table(
                model_class,
                key_df,
                chunk_size,
                p_unique_key_columns,
                progress_bar,
            )
        else:
            ids = self._fetch_ids_chunks_in_clause(
                model_class,
                key_df,
                chunk_size,
                p_unique_key_columns,
                unique_key_attrs,
                progress_bar,
            )
        ids_df = pl.DataFrame(ids)
        return ids_df

    def _fetch_ids_chunks_in_clause(
        self,
        model_class: DeclarativeMeta,
        key_df: pl.DataFrame,
        chunk_size: int,
        p_unique_key_columns: list[str],
        unique_key_attrs: list[InstrumentedAttribute],
        progress_bar: tqdm,
    ) -> list[dict[str, t.Any]]:
        """Fetch IDs using IN clause for each chunk."""
        ids = []
        with self.get_session() as session:
            pk_columns = self.get_primary_key_columns(model_class)
            pk_attrs = [self.get_column_attr_by_db_name(model_class, col) for col in pk_columns]

            for offset in progress_bar:
                chunk_keys = key_df.slice(offset, chunk_size)
                key_rows = chunk_keys.rows()
                if not key_rows:
                    continue
                key_tuples = [tuple(row) for row in key_rows]
                query = session.query(*unique_key_attrs, *pk_attrs)
                if len(p_unique_key_columns) == 1:
                    col_attr = unique_key_attrs[0]
                    query = query.filter(col_attr.in_(key_tuples))
                else:
                    query = query.filter(tuple_(*unique_key_attrs).in_(key_tuples))
                results = query.all()
                for row in results:
                    row_dict = dict(zip([*p_unique_key_columns, *pk_columns], row, strict=True))
                    # For composite primary keys, create ID as a tuple or keep individual columns
                    if len(pk_columns) == 1:
                        row_dict["ID"] = row_dict.pop(pk_columns[0])
                    else:
                        # Keep all PK columns in the result for composite keys
                        pass
                    ids.append(row_dict)
                if hasattr(progress_bar, "update"):
                    progress_bar.update(len(key_rows))
        return ids

    def _fetch_ids_chunks_temp_table(
        self,
        model_class: DeclarativeMeta,
        key_df: pl.DataFrame,
        chunk_size: int,
        p_unique_key_columns: list[str],
        progress_bar: tqdm,
    ) -> list[dict[str, t.Any]]:
        """Fetch IDs using a temporary table for each chunk."""
        ids = []
        with self.get_session() as session:
            pk_columns = self.get_primary_key_columns(model_class)
            metadata = MetaData()
            # Precompute column definitions, join conditions, and select columns
            col_defs = []
            for col in p_unique_key_columns:
                col_obj = model_class.__table__.columns[col]
                col_type = col_obj.type.compile(dialect=session.bind.dialect)
                col_defs.append(f'"{col}" {col_type}')
            col_defs_sql = ", ".join(col_defs)
            join_conds = " AND ".join(f'main."{col}" = temp."{col}"' for col in p_unique_key_columns)
            select_cols = ", ".join(
                [f'main."{col}"' for col in p_unique_key_columns] + [f'main."{col}"' for col in pk_columns]
            )

            for i, offset in enumerate(progress_bar):
                chunk_keys = key_df.slice(offset, chunk_size)
                key_rows = chunk_keys.rows()
                if not key_rows:
                    continue
                temp_table_name = f"temp_keys_{i}"
                # session.execute(text(f'DROP TABLE IF EXISTS "{temp_table_name}"'))
                session.execute(text(f'CREATE TEMP TABLE "{temp_table_name}" ({col_defs_sql}) ON COMMIT DROP'))
                col_objs = []
                for col in p_unique_key_columns:
                    col_obj = model_class.__table__.columns[col]
                    col_objs.append(Column(col, col_obj.type))
                temp_table = Table(temp_table_name, metadata, *col_objs)
                param_dicts = [dict(zip(p_unique_key_columns, row, strict=True)) for row in key_rows]
                if param_dicts:
                    session.execute(insert(temp_table), param_dicts)
                    join_sql = f'SELECT {select_cols} FROM "{model_class.__table__.name}" AS main JOIN "{temp_table_name}" AS temp ON {join_conds}'  # noqa: S608
                    results = session.execute(text(join_sql)).fetchall()
                else:
                    results = []
                session.execute(text(f'DROP TABLE IF EXISTS "{temp_table_name}"'))
                for row in results:
                    row_dict = dict(zip([*p_unique_key_columns, *pk_columns], row, strict=True))
                    # For composite primary keys, create ID as a tuple or keep individual columns
                    if len(pk_columns) == 1:
                        row_dict["ID"] = row_dict.pop(pk_columns[0])
                    else:
                        # Keep all PK columns in the result for composite keys
                        pass
                    ids.append(row_dict)
                if hasattr(progress_bar, "update"):
                    progress_bar.update(len(key_rows))

                # Commit every 100 iterations to avoid hitting connection limits
                if (i + 1) % 100 == 0:
                    session.commit()

            # Final commit for any remaining uncommitted work
            session.commit()
        return ids

    def handle_insertion_multi_line_copy(
        self,
        model_class: DeclarativeMeta,
        data: pl.DataFrame,
        mode: t.Literal["RAISE", "IGNORE", "UPDATE"],
        *,
        chunk_size: int = 1_000_000,
        returning_id: bool = False,
    ) -> pl.DataFrame | None:
        """
        Bulk-load via PostgreSQL COPY into a temp table, then upsert from that staging table.

        - Splits the Polars DataFrame into batches of `chunk_size` rows.
        - For each batch:
            1. Creates a TEMP TABLE LIKE the target table (no indexes/constraints)
            2. COPYs the batch into the temp table (CSV via STDIN)
            3. INSERTs from temp into real table with ON CONFLICT configured by `mode`
            4. If `returning_id=True`, SELECTs back all {pk_cols..., id} by joining real+temp
        - Commits each batch independently, returning a combined DataFrame of IDs if requested.
        """
        # Primary-key columns used for conflict detection
        pks = self.get_primary_unique_constraint(model_class)
        pk_columns = self.get_primary_key_columns(model_class)
        table = model_class.__table__.name
        cols = data.columns

        # Prepare batching
        total_batches = (data.height + chunk_size - 1) // chunk_size
        show_progress = total_batches > 1

        logger.info(
            "Starting COPY insert of %d rows in %d chunks of size %d",
            data.height,
            (data.height + chunk_size - 1) // chunk_size,
            chunk_size,
        )
        if show_progress:
            progress_bar = tqdm(
                total=data.height,
                desc=f"COPY writing to table: {table}",
                unit="rows",
                dynamic_ncols=True,
            )

        all_id_maps: list[pl.DataFrame] = []

        # Performance tracking
        total_times = {"csv_gen": 0, "copy_data": 0, "insert": 0, "fetch_ids": 0, "truncate": 0}
        batch_count = 0

        # Use single connection for all batches
        raw_conn = self.engine.raw_connection()
        cursor = raw_conn.cursor()

        try:
            # Connection tuning for bulk operations
            cursor.execute("SET synchronous_commit = OFF")

            # Precompute conflict handling strategy based on mode
            conflict_cols = ", ".join(f'"{c}"' for c in pks)

            # For UPDATE mode, we'll use optimized ON CONFLICT instead of DELETE + INSERT
            if mode == "RAISE":
                use_on_conflict = True
                on_conflict = ""
            elif mode == "IGNORE":
                use_on_conflict = True
                on_conflict = f"ON CONFLICT ({conflict_cols}) DO NOTHING"
            else:  # UPDATE mode - use optimized ON CONFLICT
                use_on_conflict = True
                non_pk_cols = [c for c in cols if c not in pks]
                if non_pk_cols:
                    set_clause = ", ".join(f'"{c}" = EXCLUDED."{c}"' for c in non_pk_cols)
                    on_conflict = f"ON CONFLICT ({conflict_cols}) DO UPDATE SET {set_clause}"
                else:
                    on_conflict = f"ON CONFLICT ({conflict_cols}) DO NOTHING"

            # Create single temp table outside loop
            temp_table = f"temp_{table}_copy"
            # Exclude all primary key columns from temp table for composite keys
            non_pk_cols_for_temp = [c for c in cols if c not in pk_columns]
            non_pk_col_list = ", ".join(f'"{c}"' for c in non_pk_cols_for_temp)

            cursor.execute(f'CREATE TEMP TABLE "{temp_table}" AS SELECT {non_pk_col_list} FROM "{table}" WHERE FALSE')

            # Process each batch
            for offset in range(0, data.height, chunk_size):
                batch = data.slice(offset, chunk_size)
                if batch.height == 0:
                    continue

                batch_count += 1

                # 1) Time truncate operation
                start = time.time()
                cursor.execute(f'TRUNCATE "{temp_table}"')
                total_times["truncate"] += time.time() - start

                # 2) Time CSV generation
                start = time.time()
                buf = io.StringIO()
                batch.write_csv(buf)
                buf.seek(0)
                total_times["csv_gen"] += time.time() - start

                # 3) Time COPY operation
                start = time.time()
                cursor.copy_expert(f'COPY "{temp_table}" ({non_pk_col_list}) FROM STDIN WITH CSV HEADER', buf)
                total_times["copy_data"] += time.time() - start

                # 4) Time INSERT/UPDATE operation
                start = time.time()

                # Use optimized ON CONFLICT approach for all modes
                insert_sql = (
                    f'INSERT INTO "{table}" ({non_pk_col_list}) SELECT {non_pk_col_list} FROM "{temp_table}" '
                    + on_conflict
                )
                cursor.execute(insert_sql)

                total_times["insert"] += time.time() - start

                # 5) Time ID fetching
                if returning_id:
                    start = time.time()
                    buf_out = io.StringIO()
                    # Build SELECT clause with all primary key columns
                    if len(pk_columns) == 1:
                        # Single primary key - keep backward compatibility with "ID" alias
                        select_list = ", ".join([f'r."{pk_columns[0]}" AS "ID"', *[f't."{c}" AS "{c}"' for c in pks]])
                    else:
                        # Composite primary key - include all PK columns by name
                        select_list = ", ".join(
                            [*[f'r."{col}" AS "{col}"' for col in pk_columns], *[f't."{c}" AS "{c}"' for c in pks]]
                        )

                    copy_sql = f'COPY (SELECT {select_list} FROM "{table}" AS r JOIN "{temp_table}" AS t USING ({conflict_cols})) TO STDOUT WITH CSV HEADER'  # noqa: S608
                    cursor.copy_expert(copy_sql, buf_out)
                    buf_out.seek(0)
                    df_ids = pl.read_csv(buf_out)
                    all_id_maps.append(df_ids)
                    total_times["fetch_ids"] += time.time() - start

                # Update progress bar with number of rows processed
                if show_progress:
                    progress_bar.update(batch.height)

            # Final commit for all batches
            raw_conn.commit()

        finally:
            cursor.close()
            raw_conn.close()

        # Log performance breakdown
        total_time = sum(total_times.values())
        total_rows = data.height
        print(
            f"COPY Performance Breakdown for {total_rows:,} rows in {batch_count} batches:\n"
            f"  CSV generation: {total_times['csv_gen']:.3f}s ({total_times['csv_gen'] / total_time * 100:.1f}%)\n"
            f"  COPY to temp:   {total_times['copy_data']:.3f}s ({total_times['copy_data'] / total_time * 100:.1f}%)\n"
            f"  INSERT upsert:  {total_times['insert']:.3f}s ({total_times['insert'] / total_time * 100:.1f}%)\n"
            f"  Fetch IDs:      {total_times['fetch_ids']:.3f}s ({total_times['fetch_ids'] / total_time * 100:.1f}%)\n"
            f"  Truncate:       {total_times['truncate']:.3f}s ({total_times['truncate'] / total_time * 100:.1f}%)\n"
            f"  Total time:     {total_time:.3f}s\n"
            f"  Overall rate:   {total_rows / total_time:.0f} rows/sec"
        )

        if returning_id:
            all_dfs = pl.concat(all_id_maps)
            return all_dfs
        return None

    def handle_insertion_multi_line_copy_parallel(
        self,
        model_class: DeclarativeMeta,
        data: pl.DataFrame,
        mode: t.Literal["RAISE", "IGNORE", "UPDATE"],
        *,
        chunk_size: int = 1_000_000,
        num_workers: int = 2,
        returning_id: bool = False,
    ) -> pl.DataFrame | None:
        """
        Parallel bulk-load via PostgreSQL COPY using multiprocessing workers.

        - Splits the data into chunks and distributes them across `num_workers` processes
        - Each worker creates its own database connection and processes its assigned chunks
        - For returning_id=True, collects results from all workers and combines them

        """
        # Primary-key columns used for conflict detection
        pks = self.get_primary_unique_constraint(model_class)
        table = model_class.__table__.name
        cols = data.columns

        # Prepare batching
        total_batches = (data.height + chunk_size - 1) // chunk_size
        show_progress = total_batches > 1

        logger.info(
            "Starting parallel COPY insert of %d rows in %d chunks of size %d using %d workers",
            data.height,
            total_batches,
            chunk_size,
            num_workers,
        )

        # Split data into chunks for workers
        chunks = []
        for offset in range(0, data.height, chunk_size):
            chunk = data.slice(offset, chunk_size)
            if chunk.height > 0:
                chunks.append((offset, chunk))

        if not chunks:
            return None

        logger.info(f"Created {len(chunks)} chunks for processing")

        # Test multiprocessing capability first
        try:
            mp.set_start_method("spawn", force=True)  # Force spawn method for better compatibility
            logger.info(f"Multiprocessing start method set to: {mp.get_start_method()}")
        except Exception as e:
            logger.warning(f"Could not set multiprocessing start method: {e}")

        # Get connection parameters for workers to recreate engines
        # Need to extract full connection info including password
        engine_url = self.engine.url
        connection_params = {
            "host": engine_url.host,
            "port": engine_url.port,
            "database": engine_url.database,
            "username": engine_url.username,
            "password": engine_url.password,  # This will be None if not set
        }

        # If password is None, try to get the full URL with credentials
        if connection_params["password"] is None:
            # Try to get the URL with render_as_string to include password
            connection_url = engine_url.render_as_string(hide_password=False)
        else:
            # Reconstruct connection URL with all parameters
            connection_url = f"postgresql://{connection_params['username']}:{connection_params['password']}@{connection_params['host']}:{connection_params['port']}/{connection_params['database']}"

        # Create worker function with connection string instead of engine
        worker_func = partial(
            _copy_worker_static,
            connection_url=connection_url,
            mode=mode,
            pks=pks,
            table=table,
            cols=cols,
            returning_id=returning_id,
        )

        # Process chunks in parallel
        if show_progress:
            progress_bar = tqdm(
                total=data.height,
                desc=f"Parallel COPY writing to table: {table}",
                unit="rows",
                dynamic_ncols=True,
            )

        all_id_maps = []

        # Use multiprocessing Pool with imap_unordered for real-time updates
        with mp.Pool(processes=num_workers) as pool:
            # Submit all chunks to workers and process results as they complete
            for result in pool.imap_unordered(worker_func, chunks):
                batch_size, id_df = result
                if show_progress:
                    progress_bar.update(batch_size)
                if returning_id and id_df is not None:
                    all_id_maps.append(id_df)

        if show_progress:
            progress_bar.close()

        if returning_id and all_id_maps:
            return pl.concat(all_id_maps)
        return None

    @staticmethod
    def get_column_attr_by_db_name(model_class: DeclarativeMeta, db_col_name: str) -> InstrumentedAttribute:
        """
        Map database column name to SQLAlchemy model attribute.

        This function resolves the mapping between database column names (e.g., "ID", "companyID", "regionID")
        and their corresponding SQLAlchemy model attributes (e.g., model.id, model.company_id, model.region_id).
        This is necessary because SQLAlchemy models often use Python naming conventions for attributes
        while maintaining the original database column names.

        Args:
            model_class: SQLAlchemy declarative model class
            db_col_name: Database column name as stored in the database schema

        Returns:
            SQLAlchemy InstrumentedAttribute that can be used in queries

        Raises:
            AttributeError: If no matching attribute is found for the given database column name

        Example:
            >>> # For a model with: id = Column("ID", Integer, primary_key=True)
            >>> attr = get_column_attr_by_db_name(MyModel, "ID")
            >>> # Returns MyModel.id (InstrumentedAttribute)
            >>> query = session.query(attr)  # Can be used in queries

        """
        # Check all columns in the model's table to find the matching attribute
        for attr_name in dir(model_class):
            attr = getattr(model_class, attr_name)
            if (
                hasattr(attr, "property")
                and hasattr(attr.property, "columns")
                and attr.property.columns[0].name == db_col_name
            ):
                # This is a SQLAlchemy column that matches the database column name
                return attr
        msg = f"No attribute found for database column '{db_col_name}' in {model_class.__name__}"
        raise AttributeError(msg)

    @staticmethod
    def check_mode(mode: t.Literal["RAISE", "IGNORE", "UPDATE"]) -> None:
        """
        Validate the insertion mode is one of the supported types.
        Raises ValueError if unsupported mode is provided.
        """
        if mode not in {"RAISE", "IGNORE", "UPDATE"}:
            msg = f"Unsupported insertion mode: '{mode}'"
            raise ValueError(msg)

    def close(self) -> None:
        if self.engine:
            self.engine.dispose()
            self.engine = None
            self.SessionLocal = None

    def __enter__(self) -> None:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()


def _copy_worker_static(
    chunk_data: tuple[int, pl.DataFrame],
    *,
    connection_url: str,
    mode: str,
    pks: list[str],
    table: str,
    cols: list[str],
    returning_id: bool,
) -> tuple[int, pl.DataFrame | None]:
    """
    Static worker function for parallel COPY operations with pre-filtering optimization.
    This function recreates its own database connection from the connection URL.

    Pre-filters existing data to reduce conflict resolution overhead and improve performance.

    Returns:
        tuple: (batch_size, id_dataframe_or_none)

    """
    offset, batch = chunk_data
    batch_size = batch.height

    # Create new engine and connection for this worker
    worker_engine = create_engine(connection_url)
    raw_conn = worker_engine.raw_connection()
    cursor = raw_conn.cursor()

    try:
        # Connection tuning for bulk operations
        cursor.execute("SET synchronous_commit = OFF")

        # Create temp tables for this worker
        temp_table = f"temp_{table}_worker_{offset}"
        existing_keys_table = f"temp_existing_keys_worker_{offset}"
        non_id_cols = [c for c in cols if c.upper() != "ID"]
        non_id_col_list = ", ".join(f'"{c}"' for c in non_id_cols)
        pk_col_list = ", ".join(f'"{c}"' for c in pks)

        # Create staging table for new data
        cursor.execute(
            f'CREATE TEMP TABLE "{temp_table}" AS SELECT {non_id_col_list} FROM "{table}" WHERE FALSE'  # noqa: S608
        )

        # 1) COPY data into staging
        buf = io.StringIO()
        batch.write_csv(buf)
        buf.seek(0)
        cursor.copy_expert(f'COPY "{temp_table}" ({non_id_col_list}) FROM STDIN WITH CSV HEADER', buf)

        # 2) Pre-filter: Find which key combinations already exist
        cursor.execute(
            f'CREATE TEMP TABLE "{existing_keys_table}" AS '  # noqa: S608
            f'SELECT {pk_col_list} FROM "{table}" AS r '
            f'WHERE EXISTS (SELECT 1 FROM "{temp_table}" AS t WHERE {" AND ".join(f'r."{c}" = t."{c}"' for c in pks)})'
        )

        # 3) Split data into NEW and EXISTING sets
        if mode == "RAISE":
            # For RAISE mode, only insert truly new records
            insert_sql = (
                f'INSERT INTO "{table}" ({non_id_col_list}) '  # noqa: S608
                f'SELECT {non_id_col_list} FROM "{temp_table}" AS t '
                f'WHERE NOT EXISTS (SELECT 1 FROM "{existing_keys_table}" AS e WHERE {" AND ".join(f't."{c}" = e."{c}"' for c in pks)})'
            )
            cursor.execute(insert_sql)

        elif mode == "IGNORE":
            # For IGNORE mode, only insert new records (skip existing)
            insert_sql = (
                f'INSERT INTO "{table}" ({non_id_col_list}) '  # noqa: S608
                f'SELECT {non_id_col_list} FROM "{temp_table}" AS t '
                f'WHERE NOT EXISTS (SELECT 1 FROM "{existing_keys_table}" AS e WHERE {" AND ".join(f't."{c}" = e."{c}"' for c in pks)})'
            )
            cursor.execute(insert_sql)

        else:  # UPDATE mode - Use optimized staging table approach
            # Strategy: Use a single INSERT ... ON CONFLICT DO UPDATE with better performance
            # This avoids both slow UPDATEs and slow DELETEs

            # First insert new records
            insert_sql = (
                f'INSERT INTO "{table}" ({non_id_col_list}) '  # noqa: S608
                f'SELECT {non_id_col_list} FROM "{temp_table}" AS t '
                f'WHERE NOT EXISTS (SELECT 1 FROM "{existing_keys_table}" AS e WHERE {" AND ".join(f't."{c}" = e."{c}"' for c in pks)})'
            )
            cursor.execute(insert_sql)

            # For existing records: Use optimized batch UPSERT
            non_pk_cols = [c for c in cols if c not in pks]
            if non_pk_cols:
                # Create properly qualified column lists
                qualified_non_id_cols = ", ".join(f't."{c}"' for c in non_id_cols)
                update_set_clause = ", ".join(f'"{c}" = EXCLUDED."{c}"' for c in non_pk_cols)

                # Create a direct INSERT ... ON CONFLICT for existing records only
                # This is faster than UPDATE because it only processes records that need updating
                existing_records_sql = (
                    f'INSERT INTO "{table}" ({non_id_col_list}) '  # noqa: S608
                    f'SELECT {qualified_non_id_cols} FROM "{temp_table}" t '
                    f'WHERE EXISTS (SELECT 1 FROM "{existing_keys_table}" e WHERE {" AND ".join(f't."{c}" = e."{c}"' for c in pks)}) '
                    f"ON CONFLICT ({pk_col_list}) DO UPDATE SET {update_set_clause}"
                )
                cursor.execute(existing_records_sql)

        # 4) Optionally retrieve IDs
        id_df = None
        if returning_id:
            buf_out = io.StringIO()
            # Build SELECT clause with explicit aliases
            select_list = ", ".join(['r."ID" AS "ID"', *[f't."{c}" AS "{c}"' for c in pks]])
            copy_sql = f'COPY (SELECT {select_list} FROM "{table}" AS r JOIN "{temp_table}" AS t USING ({pk_col_list})) TO STDOUT WITH CSV HEADER'  # noqa: S608
            cursor.copy_expert(copy_sql, buf_out)
            buf_out.seek(0)
            id_df = pl.read_csv(buf_out)

        # 5) Clean up temp tables
        cursor.execute(f'DROP TABLE IF EXISTS "{temp_table}"')
        cursor.execute(f'DROP TABLE IF EXISTS "{existing_keys_table}"')

        # Commit this worker's transaction
        raw_conn.commit()

    except Exception:
        raw_conn.rollback()
        raise
    else:
        return (batch_size, id_df)
    finally:
        cursor.close()
        raw_conn.close()
        worker_engine.dispose()

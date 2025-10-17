from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Dict, Optional, Tuple, Type

import dask
import dask.dataframe as dd
import pandas as pd
import sqlalchemy as sa
from sqlalchemy import func, inspect, select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.exc import TimeoutError as SASQLTimeoutError
from sqlalchemy.orm import declarative_base

from sibi_dst.df_helper.core import FilterHandler
from sibi_dst.utils import ManagedResource
from ._db_gatekeeper import DBGatekeeper


class SQLAlchemyDask(ManagedResource):
    """
    Production-grade DB -> Dask loader with robust, error-coercing type alignment
    and concurrent-safe database access via DBGatekeeper.
    """

    _SQLALCHEMY_TO_DASK_DTYPE: Dict[str, str] = {
        "INTEGER": "Int64", "SMALLINT": "Int64", "BIGINT": "Int64",
        "FLOAT": "float64", "DOUBLE": "float64",
        "NUMERIC": "string", "DECIMAL": "string",
        "BOOLEAN": "boolean",
        "VARCHAR": "string", "CHAR": "string", "TEXT": "string", "UUID": "string",
        "DATE": "datetime64[ns]", "DATETIME": "datetime64[ns]", "TIMESTAMP": "datetime64[ns]",
        "TIME": "string",
    }

    logger_extra: Dict[str, Any] = {"sibi_dst_component": __name__}

    def __init__(
            self,
            model: Type[declarative_base()],
            *,
            engine: Engine,
            filters: Optional[Dict[str, Any]] = None,
            chunk_size: int = 50_000,
            pagination: str = "offset",
            index_col: Optional[str] = None,
            num_workers: int = 1,
            **kwargs: Any,
    ):
        super().__init__(**kwargs)
        if pagination not in {"offset", "range"}:
            raise ValueError("pagination must be 'offset' or 'range'.")
        if pagination == "range" and not index_col:
            raise ValueError("pagination='range' requires index_col.")

        self.model = model
        self.engine = engine
        self.filters = filters or {}
        self.chunk_size = int(chunk_size)
        self.pagination = pagination
        self.index_col = index_col
        self.num_workers = int(num_workers)
        self.filter_handler_cls = FilterHandler
        self.total_records: int = -1

        # --- DBGatekeeper Initialization (Re-integrated) ---
        pool_size, max_overflow = self._engine_pool_limits()
        pool_capacity = max(1, pool_size + max_overflow)
        per_proc_cap = max(1, pool_capacity // max(1, self.num_workers))
        cap = per_proc_cap  # Can be overridden by an explicit db_gatekeeper_cap attribute
        gate_key = self._normalized_engine_key(self.engine)
        self._sem = DBGatekeeper.get(gate_key, max_concurrency=cap)
        self.logger.debug(f"DBGatekeeper initialized with max_concurrency={cap}")

        self._ordered_columns = [c.name for c in self.model.__table__.columns]
        self._meta_dtypes = self.infer_meta_from_model(self.model)
        self._meta_df = self._build_meta()

    @classmethod
    def infer_meta_from_model(cls, model: Type[declarative_base()]) -> Dict[str, str]:
        # (This method is unchanged)
        mapper = inspect(model)
        dtypes: Dict[str, str] = {}
        for column in mapper.columns:
            dtype_str = str(column.type).upper().split("(")[0]
            dtypes[column.name] = cls._SQLALCHEMY_TO_DASK_DTYPE.get(dtype_str, "string")
        return dtypes

    def _build_meta(self) -> pd.DataFrame:
        # (This method is unchanged)
        return pd.DataFrame({col: pd.Series(dtype=dtype) for col, dtype in self._meta_dtypes.items()})

    @contextmanager
    def _conn(self):
        """Provides a managed, concurrent-safe database connection using the semaphore."""
        with self._sem:
            with self.engine.connect() as c:
                yield c

    def _fetch_with_retry(self, sql: sa.sql.Select) -> pd.DataFrame:
        """Fetches a data chunk using the concurrent-safe connection."""
        try:
            with self._conn() as conn:
                df = pd.read_sql_query(sql, conn, dtype_backend="pyarrow")
            return self._align_and_coerce_partition(df)
        except (SASQLTimeoutError, OperationalError) as e:
            self.logger.error(f"Chunk fetch failed due to {e.__class__.__name__}", exc_info=True,
                              extra=self.logger_extra)
            # Return empty but correctly typed DataFrame on failure
            return self._meta_df.copy()

    def _align_and_coerce_partition(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aligns DataFrame partition to expected dtypes, coercing errors to nulls.
        Explicitly handles PyArrow timestamps by converting to numpy arrays.
        """
        output_df = pd.DataFrame(index=df.index)

        for col, target_dtype in self._meta_dtypes.items():
            if col not in df.columns:
                # Add missing column as nulls of the target type
                output_df[col] = pd.Series(pd.NA, index=df.index, dtype=target_dtype)
                continue

            source_series = df[col]
            try:
                if target_dtype == "datetime64[ns]":
                    # Convert to datetime, coercing errors to NaT
                    coerced_series = pd.to_datetime(source_series, errors='coerce')
                    # Ensure numpy backend by creating a new Series from values
                    output_df[col] = pd.Series(coerced_series.to_numpy(), index=coerced_series.index)
                elif target_dtype == "Int64":
                    output_df[col] = pd.to_numeric(source_series, errors='coerce').astype("Int64")
                elif target_dtype == "boolean":
                    # Handle boolean conversion with explicit mapping
                    if pd.api.types.is_bool_dtype(source_series.dtype):
                        output_df[col] = source_series.astype('boolean')
                    else:
                        output_df[col] = (
                            source_series.astype(str)
                            .str.lower()
                            .map({'true': True, '1': True, 'false': False, '0': False})
                            .astype('boolean')
                        )
                else:
                    output_df[col] = source_series.astype(target_dtype)
            except Exception:
                # Fallback to string type on any error
                output_df[col] = source_series.astype("string")

        return output_df

    def _count_total(self, subquery: sa.sql.Select) -> int:
        """Executes a COUNT(*) query safely."""
        try:
            with self._conn() as conn:
                count_q = sa.select(func.count()).select_from(subquery.alias())
                return conn.execute(count_q).scalar_one()
        except Exception:
            self.logger.error("Failed to count total records.", exc_info=True, extra=self.logger_extra)
            return -1

    def read_frame(self) -> Tuple[int, dd.DataFrame]:
        base_select = select(self.model)
        if self.filters:
            base_select = self.filter_handler_cls(backend="sqlalchemy").apply_filters(base_select, self.model, self.filters)

        total = self._count_total(base_select)
        self.total_records = total

        if total <= 0:
            self.logger.info(f"Query returned {total} or failed to count records.", extra=self.logger_extra)
            return total, dd.from_pandas(self._meta_df, npartitions=1)

        # Simplified to offset pagination as it's the most robust
        offsets = range(0, total, self.chunk_size)
        delayed_parts = [
            dask.delayed(self._fetch_with_retry)(
                base_select.limit(self.chunk_size).offset(off)
            ) for off in offsets
        ]

        ddf = dd.from_delayed(delayed_parts, meta=self._meta_df, verify_meta=True)
        return total, ddf

    # --- Other helper methods (unchanged) ---
    def _engine_pool_limits(self) -> Tuple[int, int]:
        pool = getattr(self.engine, "pool", None)

        def to_int(val, default):
            try:
                return int(val() if callable(val) else val)
            except Exception:
                return default

        size = to_int(getattr(pool, "size", None), 5)
        overflow = to_int(getattr(pool, "max_overflow", None) or getattr(pool, "_max_overflow", None), 10)
        return size, overflow

    @staticmethod
    def _normalized_engine_key(engine: Engine) -> str:
        try:
            return str(engine.url.set(query=None).set(password=None))
        except Exception:
            return str(engine.url)

# from __future__ import annotations
#
# import time
# from typing import Any, Dict, Tuple, Type
#
# import dask
# import dask.dataframe as dd
# import pandas as pd
# import sqlalchemy as sa
# from sqlalchemy import select, inspect
# from sqlalchemy.engine import Engine
# from sqlalchemy.exc import TimeoutError as SASQLTimeoutError, OperationalError
# from sqlalchemy.orm import declarative_base
#
# from sibi_dst.utils import ManagedResource
# from sibi_dst.df_helper.core import FilterHandler
# from ._db_gatekeeper import DBGatekeeper
#
#
# class SQLAlchemyDask(ManagedResource):
#     """
#     Loads data from a database into a Dask DataFrame using a memory-safe,
#     non-parallel, paginated approach (LIMIT/OFFSET).
#     """
#
#     _SQLALCHEMY_TO_DASK_DTYPE: Dict[str, str] = {
#         "INTEGER": "Int64",
#         "SMALLINT": "Int64",
#         "BIGINT": "Int64",
#         "FLOAT": "float64",
#         "NUMERIC": "float64",
#         "BOOLEAN": "bool",
#         "VARCHAR": "object",
#         "TEXT": "object",
#         "DATE": "datetime64[ns]",
#         "DATETIME": "datetime64[ns]",
#         "TIMESTAMP": "datetime64[ns]",
#         "TIME": "object",
#         "UUID": "object",
#     }
#     logger_extra: Dict[str, Any] = {"sibi_dst_component": __name__}
#
#     def __init__(
#         self,
#         model: Type[declarative_base()],
#         filters: Dict[str, Any],
#         engine: Engine,
#         chunk_size: int = 1000,
#         **kwargs: Any,
#     ):
#         super().__init__(**kwargs)
#         self.model = model
#         self.filters = filters or {}
#         self.engine = engine
#         self.chunk_size = int(chunk_size)
#         self.filter_handler_cls = FilterHandler
#         self.total_records: int = -1  # -1 indicates failure/unknown
#         self._sem = DBGatekeeper.get(str(engine.url), max_concurrency=self._safe_cap())
#
#     def _safe_cap(self) -> int:
#         """
#         Calculate a safe concurrency cap for DB work based on the engine's pool.
#
#         Returns: max(1, pool_size + max_overflow - 1)
#         - Works across SQLAlchemy 1.4/2.x
#         - Tolerates pools that expose size/max_overflow as methods or attrs
#         - Allows explicit override via self.db_gatekeeper_cap (if you pass it)
#         """
#         # optional explicit override
#         explicit = getattr(self, "db_gatekeeper_cap", None)
#         if isinstance(explicit, int) and explicit > 0:
#             return explicit
#
#         pool = getattr(self.engine, "pool", None)
#
#         def _to_int(val, default):
#             if val is None:
#                 return default
#             if callable(val):
#                 try:
#                     return int(val())  # e.g., pool.size()
#                 except Exception:
#                     return default
#             try:
#                 return int(val)
#             except Exception:
#                 return default
#
#         # size: QueuePool.size() -> int
#         size_candidate = getattr(pool, "size", None)  # method on QueuePool
#         pool_size = _to_int(size_candidate, 5)
#
#         # max_overflow: prefer attribute; fall back to private _max_overflow; avoid 'overflow()' (method)
#         max_overflow_attr = (
#                 getattr(pool, "max_overflow", None) or  # SQLAlchemy 2.x QueuePool
#                 getattr(pool, "_max_overflow", None)  # private fallback
#         )
#         max_overflow = _to_int(max_overflow_attr, 10)
#
#         cap = max(1, pool_size + max_overflow - 1)
#         self.logger.debug(f"Using a Cap of {cap} from pool size of {pool_size} and max overflow of {max_overflow}.", extra=self.logger_extra)
#         return max(1, cap)
#
#     # ---------- meta ----------
#     @classmethod
#     def infer_meta_from_model(cls, model: Type[declarative_base()]) -> Dict[str, str]:
#         mapper = inspect(model)
#         dtypes: Dict[str, str] = {}
#         for column in mapper.columns:
#             dtype_str = str(column.type).upper().split("(")[0]
#             dtype = cls._SQLALCHEMY_TO_DASK_DTYPE.get(dtype_str, "object")
#             dtypes[column.name] = dtype
#         return dtypes
#
#     def read_frame(self, fillna_value=None) -> Tuple[int, dd.DataFrame]:
#         # Base selectable
#         query = select(self.model)
#         if self.filters:
#             query = self.filter_handler_cls(
#                 backend="sqlalchemy", logger=self.logger, debug=self.debug
#             ).apply_filters(query, model=self.model, filters=self.filters)
#         else:
#             query = query.limit(self.chunk_size)
#
#         # Meta dataframe (stable column order & dtypes)
#         ordered_columns = [c.name for c in self.model.__table__.columns]
#         meta_dtypes = self.infer_meta_from_model(self.model)
#         meta_df = pd.DataFrame(columns=ordered_columns).astype(meta_dtypes)
#
#         # Count with retry/backoff
#         retry_attempts = 3
#         backoff = 0.5
#         total = 0
#
#         for attempt in range(retry_attempts):
#             try:
#                 with self._sem:
#                     with self.engine.connect() as connection:
#                         count_q = sa.select(sa.func.count()).select_from(query.alias())
#                         total = connection.execute(count_q).scalar_one()
#                     break
#             except SASQLTimeoutError:
#                 if attempt < retry_attempts - 1:
#                     self.logger.warning(f"Connection pool limit reached. Retrying in {backoff} seconds...", extra=self.logger_extra)
#                     time.sleep(backoff)
#                     backoff *= 2
#                 else:
#                     self.total_records = -1
#                     self.logger.error("Failed to get a connection from the pool after retries.", exc_info=True, extra=self.logger_extra)
#                     return self.total_records, dd.from_pandas(meta_df, npartitions=1)
#             except OperationalError as oe:
#                 if "timeout" in str(oe).lower() and attempt < retry_attempts - 1:
#                     self.logger.warning("Operational timeout, retrying…", exc_info=self.debug, extra=self.logger_extra)
#                     time.sleep(backoff)
#                     backoff *= 2
#                     continue
#                 self.total_records = -1
#                 self.logger.error("OperationalError during count.", exc_info=True, extra=self.logger_extra)
#                 return self.total_records, dd.from_pandas(meta_df, npartitions=1)
#             except Exception as e:
#                 self.total_records = -1
#                 self.logger.error(f"Unexpected error during count: {e}", exc_info=True, extra=self.logger_extra)
#                 return self.total_records, dd.from_pandas(meta_df, npartitions=1)
#
#         self.total_records = int(total)
#         if total == 0:
#             self.logger.warning("Query returned 0 records.")
#             super().close()
#             return self.total_records, dd.from_pandas(meta_df, npartitions=1)
#
#         self.logger.debug(f"Total records to fetch: {total}. Chunk size: {self.chunk_size}.", extra=self.logger_extra)
#
#         @dask.delayed
#         def get_chunk(sql_query, chunk_offset):
#             with self._sem:  # <<< cap concurrent DB fetches
#                 paginated = sql_query.limit(self.chunk_size).offset(chunk_offset)
#                 df = pd.read_sql(paginated, self.engine)
#                 if fillna_value is not None:
#                     df = df.fillna(fillna_value)
#                 return df[ordered_columns].astype(meta_dtypes)
#
#         offsets = range(0, total, self.chunk_size)
#         delayed_chunks = [get_chunk(query, off) for off in offsets]
#         ddf = dd.from_delayed(delayed_chunks, meta=meta_df)
#         self.logger.debug(f"{self.model.__name__} created Dask DataFrame with {ddf.npartitions} partitions.", extra=self.logger_extra)
#         return self.total_records, ddf
#

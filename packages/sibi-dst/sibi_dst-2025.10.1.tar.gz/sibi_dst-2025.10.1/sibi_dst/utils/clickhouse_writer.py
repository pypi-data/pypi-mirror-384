from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import ClassVar, Dict, Optional, Any, Iterable, Tuple

import pandas as pd
import dask.dataframe as dd
import clickhouse_connect
import numpy as np

from . import ManagedResource

def _to_bool(val: Any) -> bool:
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return bool(val)
    if isinstance(val, str):
        return val.strip().lower() in ("1", "true", "yes", "on")
    return False

class ClickHouseWriter(ManagedResource):
    """
    Write a Dask DataFrame to ClickHouse with:
      - Safe Dask checks (no df.empty)
      - Nullable dtype mapping
      - Optional overwrite (drop + recreate)
      - Partitioned, batched inserts
      - Per-thread clients to avoid session conflicts
      - Proper PyArrow dtype handling
    """

    # Default dtype mapping (pandas/dask → ClickHouse)
    DTYPE_MAP: ClassVar[Dict[str, str]] = {
        "int64": "Int64",
        "Int64": "Int64",  # pandas nullable Int64
        "int32": "Int32",
        "Int32": "Int32",
        "float64": "Float64",
        "Float64": "Float64",
        "float32": "Float32",
        "bool": "UInt8",
        "boolean": "UInt8",
        "object": "String",
        "string": "String",
        "category": "String",
        "datetime64[ns]": "DateTime",
        "datetime64[ns, UTC]": "DateTime",
    }

    def __init__(
        self,
        *,
        host: str = "localhost",
        port: int = 8123,
        database: str = "sibi_data",
        user: str = "default",
        password: str = "",
        secure: bool = False,
        verify: bool = False,
        ca_cert: str = "",
        client_cert: str = "",
        compression: str = "",
        table: str = "test_sibi_table",
        order_by: str = "id",
        engine: Optional[str] = None,  # e.g. "ENGINE MergeTree ORDER BY (`id`)"
        max_workers: int = 4,
        insert_chunksize: int = 50_000,
        overwrite: bool = False,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.host = host
        self.port = int(port)
        self.database = database
        self.user = user
        self.password = password
        self.secure = _to_bool(secure)
        self.verify = _to_bool(verify)
        self.ca_cert = ca_cert
        self.client_cert = client_cert
        self.compression = compression  # e.g. 'lz4', 'zstd',
        self.table = table
        self.order_by = order_by
        self.engine = engine  # if None → default MergeTree ORDER BY
        self.max_workers = int(max_workers)
        self.insert_chunksize = int(insert_chunksize)
        self.overwrite = bool(overwrite)

        # one client per thread to avoid session contention
        self._tlocal = threading.local()
        ow = self.overwrite
        if ow:
            self._command(f"DROP TABLE IF EXISTS {self._ident(self.table)}")
            self.logger.info(f"Dropped table {self.table} (overwrite=True)")

    # ------------- public -------------

    def save_to_clickhouse(self, df: dd.DataFrame) -> None:
        """
        Persist a Dask DataFrame into ClickHouse.

        Args:
            df: Dask DataFrame
            overwrite: Optional override for dropping/recreating table
        """
        if not isinstance(df, dd.DataFrame):
            raise TypeError("ClickHouseWriter.save_to_clickhouse expects a dask.dataframe.DataFrame.")

        # small, cheap check: head(1) to detect empty
        head = df.head(1, npartitions=-1, compute=True)
        if head.empty:
            self.logger.info("Dask DataFrame appears empty (head(1) returned 0 rows). Nothing to write.")
            return

        # lazily fill missing values per-partition (no global compute)
        # Use the new method that ensures correct types for ClickHouse
        df = df.map_partitions(
            type(self)._process_partition_for_clickhouse_compatible,
            meta=df._meta
        )

        # (re)create table
        dtypes = df._meta_nonempty.dtypes  # metadata-only types (no compute)
        schema_sql = self._generate_clickhouse_schema(dtypes)
        engine_sql = self._default_engine_sql() if not self.engine else self.engine

        create_sql = f"CREATE TABLE IF NOT EXISTS {self._ident(self.table)} ({schema_sql}) {engine_sql}"
        self._command(create_sql)
        self.logger.info(f"Ensured table {self.table} exists")

        # write partitions concurrently
        parts = list(df.to_delayed())
        if not parts:
            self.logger.info("No partitions to write.")
            return

        self.logger.info(f"Writing {len(parts)} partitions to ClickHouse (max_workers={self.max_workers})")
        with ThreadPoolExecutor(max_workers=self.max_workers) as ex:
            futures = {ex.submit(self._write_one_partition, part, idx): idx for idx, part in enumerate(parts)}
            for fut in as_completed(futures):
                idx = futures[fut]
                try:
                    fut.result()
                except Exception as e:
                    self.logger.error(f"Partition {idx} failed: {e}", exc_info=self.debug)
                    raise

        self.logger.info(f"Completed writing {len(parts)} partitions to {self.table}")

    # ------------- schema & types -------------

    def _generate_clickhouse_schema(self, dask_dtypes: pd.Series) -> str:
        cols: Iterable[Tuple[str, Any]] = dask_dtypes.items()
        pieces = []
        for col, dtype in cols:
            ch_type = self._map_dtype(dtype)
            # Use Nullable for non-numeric/string columns that may carry NaN/None,
            # and for datetimes to be safe with missing values.
            if self._should_mark_nullable(dtype):
                ch_type = f"Nullable({ch_type})"
            pieces.append(f"{self._ident(col)} {ch_type}")
        return ", ".join(pieces)

    def _map_dtype(self, dtype: Any) -> str:
        dtype_str = str(dtype).lower()
        # Handle PyArrow dtypes
        if "[pyarrow]" in dtype_str:
            if "int64" in dtype_str:
                return "Int64"
            elif "int32" in dtype_str:
                return "Int32"
            elif "float64" in dtype_str or "double" in dtype_str:
                return "Float64"
            elif "float32" in dtype_str:
                return "Float32"
            elif "bool" in dtype_str:
                return "UInt8"
            elif "timestamp" in dtype_str: # PyArrow timestamp
                return "DateTime"
            elif "string" in dtype_str: # PyArrow string
                return "String"
            else:
                return "String" # fallback

        # Handle pandas extension dtypes explicitly
        if isinstance(dtype, pd.Int64Dtype):
            return "Int64"
        if isinstance(dtype, pd.Int32Dtype):
            return "Int32"
        if isinstance(dtype, pd.BooleanDtype):
            return "UInt8"
        if isinstance(dtype, pd.Float64Dtype):
            return "Float64"
        if isinstance(dtype, pd.StringDtype):
            return "String"
        if "datetime64" in dtype_str:
            return "DateTime"

        return self.DTYPE_MAP.get(str(dtype), "String")

    def _should_mark_nullable(self, dtype: Any) -> bool:
        dtype_str = str(dtype).lower()
        # PyArrow types are generally nullable, but let's be specific
        if "[pyarrow]" in dtype_str:
             # For PyArrow, make strings and timestamps nullable, numbers usually not unless data has nulls
             base_type = dtype_str.replace("[pyarrow]", "")
             if base_type in ["string", "large_string"] or "timestamp" in base_type:
                 return True
             # For numeric PyArrow, check if the actual data contains nulls (hard to do here)
             # Let's default to not nullable for numeric unless explicitly needed
             return False # Conservative for PyArrow numerics

        if isinstance(dtype, (pd.StringDtype, pd.BooleanDtype, pd.Int64Dtype, pd.Int32Dtype, pd.Float64Dtype)):
            return True
        if "datetime64" in dtype_str:
            return True
        # object/category almost always nullable
        if dtype_str in ("object", "category", "string"):
            return True
        return False

    def _default_engine_sql(self) -> str:
        # minimal MergeTree clause; quote order_by safely
        ob = self.order_by if self.order_by.startswith("(") else f"(`{self.order_by}`)"
        return f"ENGINE = MergeTree ORDER BY {ob} SETTINGS allow_nullable_key = 1"

    # ------------- partition write -------------

    def _write_one_partition(self, part, index: int) -> None:
        # Compute partition → pandas
        pdf: pd.DataFrame = part.compute()
        if pdf.empty:
            self.logger.debug(f"Partition {index} empty; skipping")
            return

        # Ensure column ordering is stable
        cols = list(pdf.columns)

        # --- CRITICAL FIX: Ensure datetime columns are compatible BEFORE insertion ---
        # This is the key step to prevent the numpy.datetime64 error
        pdf = self._ensure_clickhouse_compatible_datetime_types(pdf)

        # Split into batches (to avoid giant single insert)
        for start in range(0, len(pdf), self.insert_chunksize):
            batch = pdf.iloc[start:start + self.insert_chunksize]
            if batch.empty:
                continue
            self._insert_df(cols, batch)

        self.logger.debug(f"Partition {index} inserted ({len(pdf)} rows)")

    def _insert_df(self, cols: Iterable[str], df: pd.DataFrame) -> None:
        client = self._get_client()
        # clickhouse-connect supports insert_df
        # The df passed here should now have compatible datetime types
        client.insert_df(self.table, df[cols], settings={"async_insert": 1, "wait_end_of_query": 1})

    # ------------- missing values & type conversion (lazy) -------------

    @staticmethod
    def _process_partition_for_clickhouse_compatible(pdf: pd.DataFrame) -> pd.DataFrame:
        """
        Process a partition to fill missing values and ensure initial data types are consistent.
        This is the first step of data preparation.
        """
        pdf = pdf.copy() # Avoid modifying original

        for col in pdf.columns:
            s = pdf[col]
            dtype_str = str(s.dtype).lower()

            # --- Handle PyArrow dtypes ---
            if "[pyarrow]" in dtype_str:
                try:
                    if "string" in dtype_str:
                        # Convert PyArrow string to object, fillna with empty string
                        pdf[col] = s.astype('object').fillna("")
                    elif "timestamp" in dtype_str:
                        # Convert PyArrow timestamp to pandas datetime, NaT for nulls
                        pdf[col] = pd.to_datetime(s, errors='coerce') # errors='coerce' handles conversion issues
                    elif "int" in dtype_str:
                        # Convert PyArrow int to pandas int, fillna with 0 for non-nullable
                        pdf[col] = s.fillna(0)
                    elif "float" in dtype_str or "double" in dtype_str:
                        pdf[col] = s.fillna(0.0)
                    elif "bool" in dtype_str:
                         pdf[col] = s.fillna(False) # Or pd.NA if you prefer
                    else:
                        # Fallback: convert to object and then to string
                        pdf[col] = s.astype('object').astype(str).fillna("")
                except Exception as e:
                    # If conversion fails, fall back to object and string
                    pdf[col] = s.astype('object').astype(str).fillna("")

            # --- Handle standard pandas dtypes ---
            elif pd.api.types.is_integer_dtype(s.dtype):
                if pd.api.types.is_extension_array_dtype(s.dtype):
                    pdf[col] = s.fillna(pd.NA)
                else:
                    pdf[col] = s.fillna(0)
            elif pd.api.types.is_bool_dtype(s.dtype):
                pdf[col] = s.fillna(pd.NA) # Or False
            elif pd.api.types.is_float_dtype(s.dtype):
                pdf[col] = s.fillna(0.0)
            elif pd.api.types.is_datetime64_any_dtype(s.dtype):
                # Datetimes - leave as is for now, will be handled in final step
                pass
            else:
                # For object/string/category columns, ensure they're strings
                pdf[col] = s.astype(str).fillna("")

        return pdf

    def _ensure_clickhouse_compatible_datetime_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Final conversion step: Ensure datetime columns are in a format compatible
        with clickhouse-connect driver. Specifically, convert numpy.datetime64 to
        pandas.Timestamp or Python datetime objects.
        This is called just before insertion.
        """
        df = df.copy()
        for col in df.columns:
            s = df[col]
            # Check if the column is datetime-like
            if pd.api.types.is_datetime64_any_dtype(s.dtype):
                # --- Robust conversion to ensure compatibility ---
                # 1. Convert to pandas datetime explicitly
                df[col] = pd.to_datetime(s, utc=True) # Ensures timezone handling

                # 2. Replace NaT with None for nullable columns (clickhouse-connect handles this)
                #    This is often sufficient, but let's be extra sure about the object type
                # 3. Ensure the underlying objects are pandas.Timestamp (which have .timestamp())
                #    The pd.to_datetime should handle this, but accessing .dt accessor reinforces it.
                #    If there are still issues, we can force object conversion:
                # df[col] = df[col].dt.to_pydatetime() # Converts to numpy array of datetime64 or None
                # But pd.Timestamp is better. Let's try accessing .dt to ensure it's proper:
                try:
                    _ = df[col].dt # Accessing .dt confirms it's datetime-like
                except:
                    # If .dt fails, it means conversion wasn't clean, force it
                    self.logger.debug(f"Forcing datetime conversion for column {col}")
                    df[col] = pd.to_datetime(df[col].astype('object'), utc=True)

                # --- Final check and explicit conversion if needed ---
                # If the error persists, we might need to explicitly convert the array elements.
                # Let's add a check for the first non-null element in a sample:
                sample_series = df[col].dropna()
                if len(sample_series) > 0:
                    first_val = sample_series.iloc[0]
                    if isinstance(first_val, np.datetime64):
                        self.logger.warning(f"Column {col} still contains numpy.datetime64 after conversion. Forcing object conversion.")
                        # Force conversion to object array of pandas.Timestamp or None
                        def convert_val(v):
                            if pd.isna(v):
                                return None
                            if isinstance(v, np.datetime64):
                                # Convert numpy.datetime64 to pandas.Timestamp
                                return pd.Timestamp(v)
                            return v
                        df[col] = df[col].apply(convert_val)

        return df


    # ------------- low-level helpers -------------

    def _get_client(self):
        cli = getattr(self._tlocal, "client", None)
        if cli is not None:
            return cli
        cli = clickhouse_connect.get_client(
            host=self.host,
            port=self.port,
            database=self.database,
            username=self.user,  # clickhouse-connect uses 'username'
            password=self.password,
            secure=self.secure,
            verify=self.verify,
            ca_cert=self.ca_cert or None,
            client_cert=self.client_cert or None,
            compression=self.compression or None,
        )
        self._tlocal.client = cli
        return cli

    def _command(self, sql: str) -> None:
        client = self._get_client()
        client.command(sql)

    @staticmethod
    def _ident(name: str) -> str:
        # minimal identifier quoting
        if name.startswith("`") and name.endswith("`"):
            return name
        return f"`{name}`"

    # ------------- context cleanup -------------

    def _cleanup(self):
        # close client in this thread (the manager calls _cleanup in the owning thread)
        cli = getattr(self._tlocal, "client", None)
        try:
            if cli is not None:
                cli.close()
        except Exception:
            pass
        finally:
            if hasattr(self._tlocal, "client"):
                delattr(self._tlocal, "client")

import datetime as dt
import posixpath
from pathlib import Path
from typing import Optional, List

import dask.dataframe as dd
import fsspec
import pandas as pd
from pydantic import BaseModel, ConfigDict, model_validator

from sibi_dst.df_helper.core import FilterHandler
from sibi_dst.utils import FilePathGenerator
from sibi_dst.utils import Logger


class ParquetConfig(BaseModel):
    """
    Configuration and helpers for reading Parquet datasets with fsspec + Dask.

    Heavy I/O (exists/size/listing) is deferred to explicit methods.
    The validator only normalizes and validates inputs.
    """

    # ---- Inputs / knobs ----
    parquet_storage_path: Optional[str] = None
    parquet_filename: Optional[str] = None
    parquet_start_date: Optional[str] = None   # YYYY-MM-DD
    parquet_end_date: Optional[str] = None     # YYYY-MM-DD
    parquet_max_age_minutes: int = 0           # 0 => no recency limit
    fs: Optional[fsspec.spec.AbstractFileSystem] = None
    logger: Optional[Logger] = None
    debug: bool = False
    partition_on: Optional[list[str]] = None          # column name for partitioned datasets

    # ---- Derived / runtime fields (lazy) ----
    parquet_full_path: Optional[str] = None      # file or directory
    parquet_folder_list: Optional[List[str]] = None
    parquet_is_recent: bool = False
    parquet_size_bytes: int = 0
    load_parquet: bool = False                   # computed when loading

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # ------------------------- validation -------------------------

    @model_validator(mode="after")
    def _normalize_and_validate(self):
        # logger
        if self.logger is None:
            self.logger = Logger.default_logger(logger_name=self.__class__.__name__)
        import logging as _logging
        self.logger.set_level(_logging.DEBUG if self.debug else _logging.INFO)

        # fs
        if self.fs is None:
            raise ValueError("File system (fs) must be specified")

        # base path
        if not self.parquet_storage_path:
            raise ValueError("Parquet storage path must be specified")
        self.parquet_storage_path = self.parquet_storage_path.rstrip("/")

        # dates: both or none
        if self.parquet_start_date and not self.parquet_end_date:
            raise ValueError("Parquet end date must be specified if start date is provided")
        if self.parquet_end_date and not self.parquet_start_date:
            raise ValueError("Parquet start date must be specified if end date is provided")

        # date ordering
        if self.parquet_start_date and self.parquet_end_date:
            start = dt.datetime.strptime(self.parquet_start_date, "%Y-%m-%d").date()
            end = dt.datetime.strptime(self.parquet_end_date, "%Y-%m-%d").date()
            if end < start:
                raise ValueError("Parquet end date must be greater than start date")

            # generate day-wise folders (no I/O)
            fpg = FilePathGenerator(str(self.parquet_storage_path), fs=self.fs, logger=self.logger)
            self.parquet_folder_list = fpg.generate_file_paths(
                dt.datetime.combine(start, dt.time.min),
                dt.datetime.combine(end, dt.time.min),
            )

        # file vs dataset-at-root
        if self.parquet_filename and self.partition_on is None:
            self.parquet_full_path = self.ensure_file_extension(
                posixpath.join(str(self.parquet_storage_path), str(self.parquet_filename)),
                "parquet",
            )
        else:
            # treat storage path as a directory dataset
            self.parquet_full_path = self.parquet_storage_path

        return self

    # ------------------------- public helpers -------------------------

    def determine_recency(self) -> bool:
        """
        Returns True if parquet_full_path exists and is within parquet_max_age_minutes.
        File recency applies only when full_path points to a file.
        """
        path = self.parquet_full_path
        if not path:
            return False

        # If path is a directory dataset, skip recency check
        if not path.endswith(".parquet"):
            self.parquet_is_recent = True
            return True

        if not self._exists(path):
            self.parquet_is_recent = False
            return False

        if self.parquet_max_age_minutes == 0:
            self.parquet_is_recent = True
            return True

        mdt = self._get_mtime(path)
        if not mdt:
            self.parquet_is_recent = False
            return False

        now = dt.datetime.now(dt.timezone.utc)
        if mdt.tzinfo is None:
            mdt = mdt.replace(tzinfo=dt.timezone.utc)
        self.parquet_is_recent = (now - mdt) <= dt.timedelta(minutes=self.parquet_max_age_minutes)
        return self.parquet_is_recent

    def compute_parquet_size_bytes(self) -> int:
        """
        Computes total size of *.parquet files under parquet_folder_list.
        No-op if folder list is missing.
        """
        if not self.parquet_folder_list:
            self.parquet_size_bytes = 0
            return 0

        total = 0
        for folder in self.parquet_folder_list:
            try:
                # Preferred: find (recursive)
                for path in self.fs.find(folder):
                    if path.endswith(".parquet"):
                        info = self.fs.info(path)
                        total += int(info.get("size", 0))
            except Exception:
                # Fallback: glob recursive
                for path in self.fs.glob(f"{folder}/**/*.parquet"):
                    info = self.fs.info(path)
                    total += int(info.get("size", 0))

        self.parquet_size_bytes = total
        return total

    def load_files(self, **filters) -> dd.DataFrame:
        """
        Load Parquet as a Dask DataFrame with optional pushdown + residual filtering.
        Decides paths lazily. Avoids heavy work in validators.
        """
        paths_to_load = self._resolve_paths_for_read()
        if not paths_to_load:
            self.logger.warning("No valid parquet paths resolved. Returning empty DataFrame.")
            return self._empty_ddf()

        # Determine if loading is allowed
        # If a single file was specified, honor recency; for directories or date ranges, load.
        if self.parquet_folder_list:
            self.load_parquet = True
        else:
            # single file or dataset-at-root
            if self.parquet_full_path and self.parquet_full_path.endswith(".parquet"):
                self.load_parquet = self.determine_recency()
            else:
                self.load_parquet = True

        if not self.load_parquet:
            self.logger.info("Parquet loading disabled by recency policy. Returning empty DataFrame.")
            return self._empty_ddf()

        # Compile filters
        fh = None
        pq_filters = None
        residual_expr = None
        if filters:
            fh = FilterHandler(backend="dask", debug=self.debug, logger=self.logger)
            if hasattr(fh, "split_pushdown_and_residual"):
                pq_filters, residual_filters = fh.split_pushdown_and_residual(filters)
                if residual_filters:
                    residual_expr = fh.compile_filters(residual_filters)
            else:
                residual_expr = fh.compile_filters(filters)
                if hasattr(residual_expr, "to_parquet_filters"):
                    pq_filters = residual_expr.to_parquet_filters()

        # Read parquet
        try:
            self.logger.debug(f"Reading parquet from: {paths_to_load}")
            if pq_filters:
                self.logger.debug(f"Applying pushdown filters: {pq_filters}")

            dd_result = dd.read_parquet(
                paths_to_load,
                engine="pyarrow",
                filesystem=self.fs,
                filters=pq_filters,
                # Toggle based on file count; False is safer for many tiny files.
                aggregate_files=True,
                split_row_groups=True,
                gather_statistics=False,
                ignore_metadata_file=True,
            )

            if residual_expr is not None:
                dd_result = dd_result[residual_expr.mask(dd_result)]

            return dd_result

        except FileNotFoundError as e:
            self.logger.debug(f"Parquet not found at {paths_to_load}: {e}")
            return self._empty_ddf()
        except Exception as e:
            self.logger.debug(f"Parquet load failed for {paths_to_load}: {e}")
            return self._empty_ddf()

    # ------------------------- internals -------------------------


    def _resolve_paths_for_read(self) -> List[str]:
        """
        Builds a list of path patterns for dask.read_parquet.
        Respects partition_on + start/end date if given.
        """
        self.logger.debug(f"_resolve_paths_for_read: {self.partition_on}")
        # Partitioned dataset by column
        if self.partition_on and self.parquet_start_date and self.parquet_end_date:
            if not isinstance(self.partition_on, (list, tuple)):
                parts = [self.partition_on]
            else:
                parts = self.partition_on

            start = dt.datetime.strptime(self.parquet_start_date, "%Y-%m-%d").date()
            end = dt.datetime.strptime(self.parquet_end_date, "%Y-%m-%d").date()
            days = pd.date_range(start=start, end=end, freq="D").date

            base = self.parquet_storage_path.rstrip("/")
            result= [
                f"{base}/{parts[0]}={d.isoformat()}/*.parquet"
                for d in days
            ]
            return result

        # Date-ranged folders (non-partitioned, using FilePathGenerator)
        if self.parquet_folder_list:
            dirs = {self._dirname(p) for p in self.parquet_folder_list}
            return [d.rstrip("/") + "/*.parquet" for d in sorted(dirs)]

        # Single file or dataset root
        if not self.parquet_full_path:
            return []

        if self.parquet_full_path.endswith(".parquet"):
            return [self.parquet_full_path]

        # Directory dataset
        return [self.parquet_full_path.rstrip("/") + "/*.parquet"]

    def _get_mtime(self, path: str) -> Optional[dt.datetime]:
        """
        Returns a timezone-aware datetime for the path's modification time if available.
        """
        try:
            info = self.fs.info(path)
        except Exception:
            return None

        mtime = info.get("mtime") or info.get("last_modified") or info.get("LastModified")
        if isinstance(mtime, (int, float)):
            return dt.datetime.fromtimestamp(mtime, tz=dt.timezone.utc)
        if isinstance(mtime, str):
            # ISO 8601 or RFC 3339 common form
            try:
                return dt.datetime.fromisoformat(mtime.replace("Z", "+00:00"))
            except ValueError:
                return None
        if hasattr(mtime, "tzinfo"):
            return mtime
        return None

    def _exists(self, path: str) -> bool:
        try:
            return self.fs.exists(path)
        except Exception:
            return False

    @staticmethod
    def _dirname(p: str) -> str:
        # Keep URL semantics stable (S3/HTTP/…)
        return posixpath.dirname(p.rstrip("/"))

    @staticmethod
    def _empty_ddf() -> dd.DataFrame:
        return dd.from_pandas(pd.DataFrame(), npartitions=1)

    @staticmethod
    def ensure_file_extension(filepath: str, extension: str) -> str:
        path = Path(filepath)
        return str(path.with_suffix(f".{extension}")) if path.suffix != f".{extension}" else filepath


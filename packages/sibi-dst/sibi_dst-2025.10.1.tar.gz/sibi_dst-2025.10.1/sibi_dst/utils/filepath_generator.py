import datetime as dt
import re
from pathlib import PurePosixPath
from typing import Iterable, List, Optional

import fsspec
from fsspec.utils import infer_storage_options

from .log_utils import Logger


class FilePathGenerator:
    """
    Scans date-partitioned directories base/YYYY/MM/DD and returns paths for pandas or Dask.
    Works with any fsspec filesystem.
    """

    def __init__(
        self,
        base_path: str = "",
        *,
        fs=None,
        logger: Optional[Logger] = None,
        debug: bool = False,
        storage_options: Optional[dict] = None,
        exclude_patterns: Optional[Iterable[str]] = None,
        file_extension: str = "parquet",
    ):
        self.logger = logger or Logger.default_logger(logger_name=self.__class__.__name__)
        self.debug = debug
        self.storage_options = storage_options or {}
        self.file_extension = file_extension.lstrip(".")
        self._compiled_exclusions = [re.compile(p) for p in (exclude_patterns or [])]

        # Normalize base path & derive protocol + root path
        opts = infer_storage_options(base_path or ".")
        proto = opts.get("protocol") or "file"
        root = opts.get("path") or ""  # protocol-stripped

        # If no fs given, make one from base_path
        if fs is None:
            self.fs, resolved_root = fsspec.core.url_to_fs(base_path or ".", **self.storage_options)
            # Prefer resolved_root (already stripped and normalized by fsspec)
            root = resolved_root or root
        else:
            self.fs = fs

        self._protocol = proto if isinstance(proto, str) else (proto[0] if proto else "file")
        self._root = self._ensure_no_trailing_slash(self._to_posix(root))

        if self.debug:
            self.logger.debug(
                f"FilePathGenerator init: protocol={self._protocol!r}, root={self._root!r}, fs={type(self.fs).__name__}"
            )

    # ------------------------- public API -------------------------

    def generate_file_paths(self, start_date, end_date, engine: str = "dask") -> List[str]:
        """
        Return a list of file (engine='dask') or dataset directory (engine='pandas') paths
        for all dates in [start_date, end_date].
        """
        sd = self._to_date(start_date)
        ed = self._to_date(end_date)
        if sd > ed:
            sd, ed = ed, sd  # be forgiving on reversed dates

        paths: List[str] = []
        current = sd
        while current <= ed:
            y, m, d = current.year, current.month, current.day
            paths.extend(self._collect_paths_for_day(y, m, d, engine))
            current += dt.timedelta(days=1)

        if self.debug:
            self.logger.debug(f"Generated {len(paths)} path(s) for {sd}..{ed} (engine={engine})")
        return paths

    # ------------------------- internals -------------------------

    def _collect_paths_for_day(self, year: int, month: int, day: int, engine: str) -> List[str]:
        # IMPORTANT: use protocol-stripped paths with fs methods
        day_dir = self._join(self._root, f"{year:04d}", f"{month:02d}", f"{day:02d}")

        if not self.fs.exists(day_dir):
            if self.debug:
                self.logger.debug(f"Directory does not exist: {day_dir}")
            return []

        if engine == "dask":
            # Try recursive glob first
            pattern = self._join(day_dir, "**", f"*.{self.file_extension}")
            all_paths = self.fs.glob(pattern) or []

            # Some filesystems don’t support recursive glob well; fallback to find()
            if not all_paths:
                try:
                    found = self.fs.find(day_dir)  # recursive listing
                except Exception:
                    found = []
                all_paths = [p for p in found if p.endswith(f".{self.file_extension}")]

            # Filter out dirs & excluded patterns
            file_paths = [
                p for p in all_paths
                if not self._is_dir(p) and not self._is_excluded(p)
            ]

        elif engine == "pandas":
            # For pandas, return the dataset directory for the day (if not excluded)
            file_paths = [day_dir] if self._is_dir(day_dir) and not self._is_excluded(day_dir) else []
        else:
            raise ValueError("engine must be 'pandas' or 'dask'.")

        # Reattach protocol ONLY for returned paths
        return [self._with_protocol(p) for p in file_paths]

    def _is_dir(self, path: str) -> bool:
        try:
            return bool(self.fs.isdir(path))
        except Exception:
            # Robust fallback via info()
            try:
                return (self.fs.info(path).get("type") == "directory")
            except Exception:
                return False

    def _is_excluded(self, path: str) -> bool:
        return any(pat.search(path) for pat in self._compiled_exclusions)

    # ------------------------- helpers -------------------------

    @staticmethod
    def _to_date(x) -> dt.date:
        if isinstance(x, dt.datetime):
            return x.date()
        if isinstance(x, dt.date):
            return x
        return dt.datetime.strptime(str(x), "%Y-%m-%d").date()

    @staticmethod
    def _to_posix(path: str) -> str:
        return PurePosixPath(path).as_posix()

    @staticmethod
    def _ensure_no_trailing_slash(path: str) -> str:
        return path[:-1] if path.endswith("/") else path

    @staticmethod
    def _join(*parts: str) -> str:
        p = PurePosixPath(parts[0])
        for part in parts[1:]:
            p = p / part
        return p.as_posix()

    def _with_protocol(self, path: str) -> str:
        # If path already has a scheme, leave it
        if "://" in path:
            return path
        # For local file, return absolute-like path without scheme or keep 'file://'? Keep scheme for consistency.
        return f"{self._protocol}://{path}"


# """
# Usage:
# # Initialize the generator
# generator = FilePathGenerator(
#     base_path='/Users/lvalverdeb/TeamDev/sibi-dst/IbisDataWH/logistics_storage/products/tracking',
#     debug=True
# )
#
# # Generate dataset paths for Dask
# dataset_paths = generator.generate_file_paths('2024-01-01', '2024-01-05', engine='dask')
#
# # Read data with Dask
# import dask.dataframe as dd
#
# df = dd.read_parquet(dataset_paths)
#
# # Now you can use df as a Dask DataFrame
# print(df.head())
#
# # Generate file paths for pandas
# file_paths = generator.generate_file_paths('2024-01-01', '2024-01-05', engine='pandas')
#
# # Read data with pandas
# import pandas as pd
#
# dataframes = []
# for fp in file_paths:
#     df = pd.read_parquet(fp)
#     dataframes.append(df)
#
# df_pandas = pd.concat(dataframes, ignore_index=True)
# print(df_pandas.head())
# """

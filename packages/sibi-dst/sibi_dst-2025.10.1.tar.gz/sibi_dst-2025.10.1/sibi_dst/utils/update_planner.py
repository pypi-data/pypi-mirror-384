from __future__ import annotations

import datetime as dt
import re
from concurrent.futures import ThreadPoolExecutor, wait
from typing import List, Optional, Dict, Union, Tuple, Set, Iterator, ClassVar, Any, Callable

import pandas as pd

from sibi_dst.utils import ManagedResource
from . import FileAgeChecker


class UpdatePlanner(ManagedResource):
    """
    Update planner for datasets organized either as:

    - Legacy layout: /YYYY/MM/DD/file.parquet
    - Hive layout:   /partition_date=YYYY-MM-DD/[other=val]/file.parquet

    Public API is unchanged (`generate_plan`, `show_update_plan`, etc.).
    """

    DEFAULT_PRIORITY_MAP: ClassVar[Dict[str, int]] = {
        "file_is_recent": 0,
        "missing_ignored": 0,
        "overwrite_forced": 1,
        "incomplete": 1,
        "create_missing": 2,
        "missing_in_history": 3,
        "stale_in_history": 4,
        "future": 99,
    }

    DEFAULT_MAX_AGE_MINUTES: int = 1440
    DEFAULT_HISTORY_DAYS_THRESHOLD: int = 30

    DATA_FILE_PATTERNS: ClassVar[Tuple[str, ...]] = (".parquet", ".orc", ".csv", ".json")
    CONTROL_BASENAMES: ClassVar[Set[str]] = {"_SUCCESS", "_metadata", "_common_metadata"}

    HIVE_PARTITION_RE: ClassVar[re.Pattern] = re.compile(r"([^/=]+)=([^/]+)")

    logger_extra = {"sibi_dst_component": __name__}

    def __init__(
        self,
        parquet_storage_path: str,
        *,
        partition_on: Optional[List[str]] = None,
        description: str = "Update Planner",
        reference_date: Union[str, dt.date, None] = None,
        history_days_threshold: int = DEFAULT_HISTORY_DAYS_THRESHOLD,
        max_age_minutes: int = DEFAULT_MAX_AGE_MINUTES,
        overwrite: bool = False,
        ignore_missing: bool = False,
        custom_priority_map: Optional[Dict[str, int]] = None,
        reverse_order: bool = False,
        show_progress: bool = False,
        hive_style: bool = False,
        skipped: Optional[List[Union[str, dt.date]]] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)

        # ---- core config ----
        self.data_path: str = self._ensure_trailing_slash(parquet_storage_path)
        self.description: str = description
        self.reverse_order: bool = reverse_order
        self.show_progress: bool = show_progress
        self.overwrite: bool = overwrite
        self.ignore_missing: bool = ignore_missing
        self.history_days_threshold: int = history_days_threshold
        self.max_age_minutes: int = max_age_minutes
        self.priority_map: Dict[str, int] = dict(custom_priority_map) if custom_priority_map else dict(self.DEFAULT_PRIORITY_MAP)

        # ---- NEW: Hive partition support ----
        self.hive_style: bool = hive_style
        self.partition_on: List[str] = list(partition_on or ["partition_date"] if self.hive_style else ["year", "month", "day"])

        # ---- execution knobs ----
        self.max_threads: int = int(kwargs.get("max_threads", 3))
        self.timeout: float = float(kwargs.get("timeout", 30.0))
        self.list_timeout: float = float(kwargs.get("list_timeout", self.timeout))
        self.total_timeout: float = float(kwargs.get("total_timeout", self.timeout))

        # ---- date window ----
        self.start_date = kwargs.get("parquet_start_date")
        self.end_date = kwargs.get("parquet_end_date")

        # ---- reference date ----
        if reference_date is not None:
            self.reference_date: dt.date = pd.to_datetime(reference_date).date()
        else:
            self.reference_date: dt.date = dt.date.today()

        # ---- completeness/heuristics ----
        self.check_completeness: bool = bool(kwargs.get("check_completeness", False))
        self.require_success_marker: bool = bool(kwargs.get("require_success_marker", False))
        self.list_granularity: str = str(kwargs.get("list_granularity", "month"))
        self.data_file_suffixes: Tuple[str, ...] = tuple(kwargs.get("data_file_suffixes", self.DATA_FILE_PATTERNS))

        # ---- clock for tests ----
        self._utcnow: Callable[[], dt.datetime] = kwargs.get("utcnow_func", None) or (lambda: dt.datetime.utcnow())

        # ---- skipped (back-compat) ----
        self.skipped = list(skipped or kwargs.get("skipped", []) or [])
        self.skipped_paths: Set[str] = {p.rstrip("/") + "/" for p in self.skipped if isinstance(p, str)}
        self.skipped_dates: Set[dt.date] = {p for p in self.skipped if isinstance(p, dt.date)}

        if not getattr(self, "fs", None):
            raise ValueError("UpdatePlanner requires a valid fsspec filesystem (fs).")

        # ---- state ----
        self.age_checker = FileAgeChecker(debug=self.debug, logger=self.logger)
        self.plan: pd.DataFrame = pd.DataFrame()
        self.df_req: pd.DataFrame = pd.DataFrame()
        self._printed_this_run: bool = False

    # --------------------- Back-compat property bridge ---------------------
    @property
    def skipped(self) -> List[Union[str, dt.date]]:
        return [*sorted(self.skipped_paths), *sorted(self.skipped_dates)]

    @skipped.setter
    def skipped(self, value: List[Union[str, dt.date]]) -> None:
        self.skipped_paths = {p.rstrip("/") + "/" for p in value if isinstance(p, str)}
        self.skipped_dates = {p for p in value if isinstance(p, dt.date)}

    # --------------------- Public API ---------------------
    def generate_plan(
        self,
        start: Union[str, dt.date, None] = None,
        end: Union[str, dt.date, None] = None,
        freq: str = "D",
    ) -> pd.DataFrame:
        start = start or self.start_date
        end = end or self.end_date
        if start is None or end is None:
            raise ValueError("start and end must be provided (or set via parquet_* kwargs).")

        sd = pd.to_datetime(start).date()
        ed = pd.to_datetime(end).date()
        if sd > ed:
            raise ValueError(f"Start date ({sd}) must be on or before end date ({ed}).")

        self.logger.info(f"Generating update plan for {self.description} from {sd} to {ed}", extra=self._log_extra())
        self._generate_plan(sd, ed, freq=freq)
        return self.df_req

    def show_update_plan(self) -> None:
        if not self.has_plan() or self._printed_this_run:
            return
        try:
            from rich.console import Console
            from rich.table import Table
            console = Console()
            table = Table(
                title=f"Update Plan for {self.data_path} [{'Hive' if 'partition_date' in self.partition_on else 'Legacy'}]",
                show_header=True, header_style="bold magenta", expand=True, pad_edge=False,
            )
            for col in self.plan.columns:
                table.add_column(col, justify="left", overflow="fold")
            for _, row in self.plan.iterrows():
                table.add_row(*(str(row[c]) for c in self.plan.columns))
            console.print(table)
        except Exception:
            self.logger.info(f"Update Plan:\n{self.plan.head(50)}", extra=self._log_extra())
        self._printed_this_run = True

    def get_tasks_by_priority(self) -> Iterator[Tuple[int, List[dt.date]]]:
        if not self.has_plan():
            return
        req = self.plan[self.plan["update_required"]]
        for priority in sorted(req["update_priority"].unique()):
            dates = req[req["update_priority"] == priority].sort_values(
                by="date", ascending=not self.reverse_order
            )["date"].tolist()
            if dates:
                yield int(priority), dates

    def has_plan(self) -> bool:
        return not self.plan.empty

    def required_count(self) -> int:
        return len(self.df_req)

    # --------------------- Internals ---------------------
    def _generate_plan(self, start: dt.date, end: dt.date, freq: str = "D") -> None:
        dates: List[dt.date] = pd.date_range(start=start, end=end, freq=freq).date.tolist()
        history_start = self.reference_date - dt.timedelta(days=self.history_days_threshold)
        rows: List[Dict[str, Any]] = []

        if "partition_date" in self.partition_on:
            caches: Dict[dt.date, Dict[str, Any]] = self._list_prefix(self.data_path)
        else:
            caches: Dict[dt.date, Dict[str, Any]] = {}
            months = list(self._iter_month_starts(self._month_floor(start), self._month_floor(end)))
            with ThreadPoolExecutor(max_workers=max(1, self.max_threads)) as ex:
                future_to_unit = {ex.submit(self._list_prefix, self._month_prefix(m)): m for m in months}
                done, _ = wait(future_to_unit.keys(), timeout=self.total_timeout or None)
                for fut in done:
                    m = future_to_unit[fut]
                    try:
                        caches[m] = fut.result(timeout=self.list_timeout or None)
                    except Exception:
                        caches[m] = {}

        for d in dates:
            if d > self.reference_date:
                rows.append(self._row_future(d))
                continue
            if self._is_skipped(d):
                rows.append(self._make_row(d, history_start, False, None))
                continue

            cache = caches if "partition_date" in self.partition_on else caches.get(d.replace(day=1), {})
            exists, age_min, incomplete = self._summarize_partition(d, cache)
            if incomplete and not self.overwrite:
                rows.append(self._row_incomplete(d, age_min))
            else:
                rows.append(self._make_row(d, history_start, exists, age_min))

        df = pd.DataFrame.from_records(rows)
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"]).dt.date
            df["update_priority"] = df["update_priority"].astype(int)
        self.plan = df.sort_values(
            by=["update_priority", "date"],
            ascending=[True, not self.reverse_order],
            kind="mergesort",
        ).reset_index(drop=True)
        self.df_req = self.plan[self.plan["update_required"]].copy()

    def _list_prefix(self, prefix: str) -> Dict[dt.date, Dict[str, Any]]:
        try:
            items: Dict[str, Any] = self.fs.find(prefix, withdirs=False, detail=True)
        except Exception:
            return {}

        out: Dict[dt.date, Dict[str, Any]] = {}
        for path, info in items.items():
            d: Optional[dt.date] = None
            if "partition_date" in self.partition_on:
                parts = self._extract_partitions(path)
                if "partition_date" in parts:
                    try:
                        d = dt.date.fromisoformat(parts["partition_date"])
                    except Exception:
                        continue
            else:
                segs = path.strip("/").split("/")
                if len(segs) >= 3:
                    try:
                        y, m, dd = int(segs[-3]), int(segs[-2]), int(segs[-1])
                        d = dt.date(y, m, dd)
                    except Exception:
                        continue
            if d is None:
                continue

            rec = out.setdefault(d, {"files": [], "has_success": False, "newest_ts": None})
            base = path.rsplit("/", 1)[-1]
            if base == "_SUCCESS":
                rec["has_success"] = True
            if self._is_data_file(path):
                rec["files"].append(path)
                ts = self._extract_mtime(info)
                if ts and (rec["newest_ts"] is None or ts > rec["newest_ts"]):
                    rec["newest_ts"] = ts
        return out

    def _extract_partitions(self, path: str) -> Dict[str, str]:
        out: Dict[str, str] = {}
        for seg in path.strip("/").split("/"):
            m = self.HIVE_PARTITION_RE.match(seg)
            if m:
                out[m.group(1)] = m.group(2)
        return out

    def _summarize_partition(self, d: dt.date, cache: Dict[dt.date, Dict[str, Any]]) -> Tuple[bool, Optional[float], bool]:
        rec = cache.get(d, {})
        files = rec.get("files", [])
        exists = bool(files)
        if not exists:
            return False, None, False
        has_success = rec.get("has_success", False)
        newest_ts = rec.get("newest_ts")
        age_min = None
        if newest_ts:
            now = self._utcnow().replace(tzinfo=None)
            ts = newest_ts.replace(tzinfo=None) if newest_ts.tzinfo else newest_ts
            age_min = max(0.0, (now - ts).total_seconds() / 60.0)
        incomplete = self.check_completeness and self.require_success_marker and not has_success
        return exists, age_min, incomplete

    def _make_row(self, d: dt.date, history_start: dt.date, exists: bool, age_min: Optional[float]) -> Dict[str, Any]:
        within_history = history_start <= d <= self.reference_date
        category, update_required = "unknown", False
        if self.overwrite:
            category, update_required = "overwrite_forced", True
        elif within_history:
            if not exists:
                category, update_required = "missing_in_history", True
            elif age_min is not None and age_min > self.max_age_minutes:
                category, update_required = "stale_in_history", True
            else:
                category = "file_is_recent"
        elif not exists and not self.ignore_missing:
            category, update_required = "create_missing", True
        else:
            category = "missing_ignored" if not exists else "file_is_recent"
        return {
            "date": d,
            "file_exists": exists,
            "file_age_minutes": age_min,
            "update_category": category,
            "update_priority": self.priority_map.get(category, 99),
            "update_required": update_required,
            "description": self.description,
        }

    def _row_future(self, d: dt.date) -> Dict[str, Any]:
        return {
            "date": d, "file_exists": False, "file_age_minutes": None,
            "update_category": "future", "update_priority": self.priority_map.get("future", 99),
            "update_required": False, "description": self.description,
        }

    def _row_incomplete(self, d: dt.date, age_min: Optional[float]) -> Dict[str, Any]:
        return {
            "date": d, "file_exists": True, "file_age_minutes": age_min,
            "update_category": "incomplete", "update_priority": self.priority_map.get("incomplete", 1),
            "update_required": True, "description": self.description,
        }

    # --------------------- Utilities ---------------------
    @staticmethod
    def _ensure_trailing_slash(path: str) -> str:
        return path.rstrip("/") + "/"

    @staticmethod
    def _month_floor(d: dt.date) -> dt.date:
        return d.replace(day=1)

    @staticmethod
    def _iter_month_starts(start: dt.date, end: dt.date) -> Iterator[dt.date]:
        cur = start.replace(day=1)
        while cur <= end:
            yield cur
            y, m = cur.year, cur.month
            cur = dt.date(y + 1, 1, 1) if m == 12 else dt.date(y, m + 1, 1)

    def _month_prefix(self, month_start: dt.date) -> str:
        return f"{self.data_path}{month_start.year}/{month_start.month:02d}/"

    def _is_data_file(self, path: str) -> bool:
        base = path.rsplit("/", 1)[-1]
        if not base or base.startswith(".") or base in self.CONTROL_BASENAMES:
            return False
        return any(base.lower().endswith(suf) for suf in self.data_file_suffixes)

    @staticmethod
    def _extract_mtime(info: Dict[str, Any]) -> Optional[dt.datetime]:
        mtime = info.get("mtime") or info.get("LastModified") or info.get("last_modified")
        if isinstance(mtime, (int, float)):
            return dt.datetime.utcfromtimestamp(mtime)
        if isinstance(mtime, str):
            try:
                return pd.to_datetime(mtime, utc=True).to_pydatetime()
            except Exception:
                return None
        if isinstance(mtime, dt.datetime):
            return mtime if mtime.tzinfo else mtime.replace(tzinfo=dt.timezone.utc)
        return None

    def _is_skipped(self, d: dt.date) -> bool:
        if "partition_date" in self.partition_on:
            canonical_path = f"{self.data_path}partition_date={d.isoformat()}/"
        else:
            canonical_path = f"{self.data_path}{d.year}/{d.month:02d}/{d.day:02d}/"
        return (d in self.skipped_dates) or (canonical_path in self.skipped_paths)

    def _log_extra(self, **overrides) -> Dict[str, Any]:
        base = {
            "sibi_dst_component": self.logger_extra.get("sibi_dst_component", "warehouse.update_planner"),
            "date_of_update": self.reference_date.strftime("%Y-%m-%d"),
            "dataclass": self.description,
            "action_module_name": "update_plan",
        }
        base.update(overrides)
        return base
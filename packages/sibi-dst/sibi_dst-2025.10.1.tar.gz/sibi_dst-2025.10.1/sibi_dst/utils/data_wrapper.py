# data_wrapper.py
from __future__ import annotations

import datetime
import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from typing import Type, Any, Dict, Optional, Union, List, ClassVar, Callable

import pandas as pd
from tqdm import tqdm

from . import ManagedResource
from .parquet_saver import ParquetSaver


class DataWrapper(ManagedResource):
    """
    Manages the concurrent processing of data for multiple dates based on an update plan.
    Orchestrates loading data via a dataclass, processing it, and saving it to Parquet.
    """
    DEFAULT_PRIORITY_MAP: ClassVar[Dict[str, int]] = {
        "overwrite": 1,
        "missing_in_history": 2,
        "existing_but_stale": 3,
        "missing_outside_history": 4,
        "file_is_recent": 0,
    }
    DEFAULT_MAX_AGE_MINUTES: int = 1440
    DEFAULT_HISTORY_DAYS_THRESHOLD: int = 30

    logger_extra = {"sibi_dst_component": "warehouse.data_wrapper"}

    def __init__(
        self,
        dataclass: Type,
        date_field: str,
        data_path: str,
        class_params: Optional[Dict] = None,
        load_params: Optional[Dict] = None,
        show_progress: bool = False,
        timeout: float = 30,
        max_threads: int = 3,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        # ---- Core Configuration ----
        self.dataclass: Type = dataclass
        self.date_field: str = date_field
        self.data_path: str = self._ensure_forward_slash(data_path)
        self.partition_on_date: bool = True # Assume Hive-style date partitioning by default

        if self.fs is None:
            raise ValueError("DataWrapper requires a File system (fs) to be provided.")

        # ---- Execution Parameters ----
        self.show_progress: bool = show_progress
        self.timeout: float = timeout
        self.max_threads: int = max_threads

        # ---- Parameters for Dataclass Instantiation ----
        self.class_params: Dict[str, Any] = class_params or {
            "debug": self.debug,
            "logger": self.logger,
            "fs": self.fs,
            "verbose": self.verbose,
        }
        self.load_params: Dict[str, Any] = load_params or {}

        # ---- Internal State & Coordination ----
        self._lock = threading.Lock()
        self.processed_dates: List[datetime.date] = []
        self.benchmarks: Dict[datetime.date, Dict[str, float]] = {}

        # ---- External Dependencies ----
        self.mmanifest = kwargs.get("mmanifest", None)
        self.update_planner = kwargs.get("update_planner", None)

        # ---- Shutdown Coordination ----
        # Stop gate to block further scheduling/retries during cleanup/interrupt
        self._stop_event = threading.Event()

        # Update logger extra with specific context
        self.logger_extra.update({
            "action_module_name": "data_wrapper",
            "dataclass": self.dataclass.__name__
        })

    # --------------------- Cleanup ---------------------
    def _cleanup(self) -> None:
        """Signal shutdown during class-specific cleanup."""
        self._stop_event.set()

    # --------------------- Utilities ---------------------
    @staticmethod
    def _convert_to_date(date: Union[datetime.date, str]) -> datetime.date:
        """Convert a string or date object to a datetime.date."""
        if isinstance(date, datetime.date):
            return date
        try:
            return pd.to_datetime(date).date()
        except ValueError as e:
            raise ValueError(f"Error converting {date} to datetime: {e}") from e

    @staticmethod
    def _ensure_forward_slash(path: str) -> str:
        """Ensure the path ends with a forward slash."""
        return path.rstrip("/") + "/"

    def _log_extra(self, **overrides) -> Dict[str, Any]:
        """Generate consistent logger extra context."""
        base = self.logger_extra.copy()
        base.update(overrides)
        return base

    # --------------------- Core Public API ---------------------
    def process(
        self,
        max_retries: int = 3,
        backoff_base: float = 2.0,
        backoff_jitter: float = 0.1,
        backoff_max: float = 60.0,
    ):
        """
        Execute the update plan with concurrency, retries, and exponential backoff.
        Stops scheduling immediately if closed or interrupted (Ctrl-C).
        """
        overall_start = time.perf_counter()
        tasks = list(self.update_planner.get_tasks_by_priority()) if self.update_planner else []
        if not tasks:
            self.logger.info("No updates required based on the current plan.", extra=self.logger_extra)
            return

        if self.update_planner and self.update_planner.show_progress:
            self.update_planner.show_update_plan()

        try:
            for priority, dates in tasks:
                if self._stop_event.is_set():
                    self.logger.info("Stop event set, halting processing of remaining task batches.", extra=self.logger_extra)
                    break
                self._execute_task_batch(priority, dates, max_retries, backoff_base, backoff_jitter, backoff_max)
        except KeyboardInterrupt:
            self.logger.warning("KeyboardInterrupt received — stopping scheduling and shutting down.", extra=self.logger_extra)
            self._stop_event.set()
            raise
        finally:
            total_time = time.perf_counter() - overall_start
            if self.processed_dates:
                count = len(self.processed_dates)
                avg_time = total_time / count if count > 0 else 0
                self.logger.info(
                    f"Processed {count} dates in {total_time:.1f}s (avg {avg_time:.1f}s/date)",
                    extra=self.logger_extra
                )
                if self.update_planner and self.update_planner.show_progress:
                    self.show_benchmark_summary()

    # --------------------- Task Execution ---------------------
    def _execute_task_batch(
        self,
        priority: int,
        dates: List[datetime.date],
        max_retries: int,
        backoff_base: float,
        backoff_jitter: float,
        backoff_max: float,
    ):
        """Execute a batch of tasks (dates) with a given priority concurrently."""
        desc = f"Processing {self.dataclass.__name__}, priority: {priority}"
        max_thr = min(len(dates), self.max_threads)
        self.logger.info(
            f"Executing {len(dates)} tasks with priority {priority} using {max_thr} threads.",
            extra=self.logger_extra
        )

        # Use explicit try/finally for executor shutdown control
        executor = ThreadPoolExecutor(max_workers=max_thr, thread_name_prefix="datawrapper")
        try:
            futures_to_dates: Dict[Future, datetime.date] = {}
            submitted_count = 0

            for date in dates:
                if self._stop_event.is_set():
                    self.logger.debug(f"Stop event set, halting submission of new tasks in batch {priority}.", extra=self.logger_extra)
                    break
                try:
                    future = executor.submit(
                        self._process_date_with_retry,
                        date,
                        max_retries,
                        backoff_base,
                        backoff_jitter,
                        backoff_max
                    )
                    futures_to_dates[future] = date
                    submitted_count += 1
                except RuntimeError as e:
                    # Tolerate race: executor shutting down
                    if "cannot schedule new futures after shutdown" in str(e).lower():
                        self.logger.warning(
                            "Executor is shutting down; halting new submissions for this batch.",
                            extra=self.logger_extra
                        )
                        break
                    else:
                        # Re-raise unexpected RuntimeErrors
                        raise

            self.logger.debug(f"Submitted {submitted_count} tasks for priority {priority}.", extra=self.logger_extra)

            # Use as_completed for processing results as they finish
            iterator = as_completed(futures_to_dates)
            if self.show_progress:
                iterator = tqdm(iterator, total=len(futures_to_dates), desc=desc, leave=False)

            for future in iterator:
                date = futures_to_dates[future]
                try:
                    # Get the result, respecting the overall timeout
                    future.result(timeout=self.timeout)
                except Exception as e:
                    # Log errors for individual date processing failures
                    self.logger.error(f"Permanent failure for {date}: {e}", extra=self.logger_extra)
        finally:
            # Python 3.9+: cancel_futures prevents queued tasks from starting
            # Tasks already running will still complete.
            # shutdown(wait=True) ensures running tasks finish before returning.
            executor.shutdown(wait=True, cancel_futures=True)
            self.logger.debug(f"Executor for priority {priority} shut down.", extra=self.logger_extra)

    # --------------------- Date Processing ---------------------
    def _process_date_with_retry(
        self,
        date: datetime.date,
        max_retries: int,
        backoff_base: float,
        backoff_jitter: float,
        backoff_max: float,
    ):
        """Process a single date with retry logic and exponential backoff."""
        for attempt in range(max_retries):
            # Bail out quickly if shutdown/interrupt began
            if self._stop_event.is_set():
                self.logger.debug(f"Stop event set, aborting retries for {date} (attempt {attempt + 1}).", extra=self.logger_extra)
                raise RuntimeError("shutting_down")

            try:
                self._process_single_date(date)
                return # Success, exit retry loop
            except Exception as e:
                if attempt < max_retries - 1 and not self._stop_event.is_set():
                    # Calculate delay with exponential backoff and jitter
                    base_delay = min(backoff_base ** attempt, backoff_max)
                    jitter_amount = random.uniform(0.0, max(0.0, backoff_jitter))
                    delay = base_delay * (1 + jitter_amount)
                    self.logger.warning(
                        f"Retry {attempt + 1}/{max_retries} for {date}: {e} (sleep {delay:.2f}s)",
                        extra=self.logger_extra
                    )
                    # Respect stop event even during sleep
                    if self._stop_event.wait(timeout=delay):
                        self.logger.debug(f"Stop event set during retry sleep for {date}.", extra=self.logger_extra)
                        raise RuntimeError("shutting_down") from e
                else:
                    self.logger.error(f"Failed processing {date} after {max_retries} attempts.", extra=self.logger_extra)
                    raise # Re-raise the last exception after max retries

    def _process_single_date(self, date: datetime.date):
        """Process a single date: load, save to Parquet."""
        # --- 1. Setup paths and logging ---
        path = self.data_path.rstrip("/")+"/"
        if not self.partition_on_date:
            # not a Hive-style partitioned path
            path = f"{self.data_path}{date.year}/{date.month:02d}/{date.day:02d}/"
            log_extra = self._log_extra(date_context=date.isoformat())
            self.logger.debug(f"Processing date {date.isoformat()} for legacy {path}", extra=log_extra)
        else :
            # Hive-style partitioned path
            log_extra = self._log_extra(date_context=date.isoformat(), partition_on=self.date_field)
            self.logger.debug(f"Processing date {date.isoformat()} for partitioned {self.data_path} with hive-style partitions", extra=log_extra)
        # --- 2. Check if date/path should be skipped ---
        if (self.update_planner and path in self.update_planner.skipped and
                getattr(self.update_planner, 'ignore_missing', False)):
            self.logger.debug(f"Skipping {date} as it exists in the skipped list", extra=log_extra)
            return

        self.logger.debug(f"Processing date {date.isoformat()} for {path}", extra=log_extra)

        # --- 3. Timing ---
        overall_start = time.perf_counter()

        try:
            # --- 4. Load Data ---
            load_start = time.perf_counter()
            date_filter = {f"{self.date_field}__date": date.isoformat()}
            self.logger.debug(f"{self.dataclass.__name__} is loading data for {date} with filter: {date_filter}", extra=log_extra)

            # Prepare load parameters
            local_load_params = self.load_params.copy()
            local_load_params.update(date_filter)

            # Instantiate and use the dataclass (e.g., Etl...Dc) within a context manager
            with self.dataclass(**self.class_params) as local_class_instance:
                df = local_class_instance.load(**local_load_params)  # Expected to return Dask DataFrame

                load_time = time.perf_counter() - load_start
                self.logger.debug(f"{self.dataclass.__name__} data loading for {date} completed in {load_time:.2f}s", extra=log_extra)

                # --- 5. Handle Record Count ---
                total_records = -1
                if hasattr(local_class_instance, "total_records"):
                    total_records = int(getattr(local_class_instance, "total_records", -1))
                    self.logger.debug(f"{self.dataclass.__name__} total records loaded: {total_records}", extra=log_extra)

                    if total_records == 0:
                        # No data found, log to manifest if available
                        if self.mmanifest:
                            try:
                                self.mmanifest.record(full_path=path)
                            except Exception as e:
                                self.logger.error(f"Failed to record missing path {path}: {e}", extra=log_extra)
                        self.logger.info(f"No data found for {path}. Logged to missing manifest.", extra=log_extra)
                        return # Done for this date

                    if total_records < 0:
                        self.logger.warning(f"Negative record count ({total_records}) for {path}. Proceeding.", extra=log_extra)
                        # Continue processing even with negative count

                    # --- 6. Save to Parquet ---
                    save_start = time.perf_counter()


                    parquet_params = {
                        "df_result": df,
                        "parquet_storage_path": path,
                        "fs": self.fs,
                        "logger": self.logger,
                        "debug": self.debug,
                        "verbose": self.verbose,
                    }
                    if self.partition_on_date:
                        df["partition_date"] = df[self.date_field].dt.date.astype(str)
                        parquet_params["partition_on"] = ["partition_date"]
                    self.logger.debug(f"{self.dataclass.__name__} saving to parquet started...", extra=log_extra)
                    with ParquetSaver(**parquet_params) as ps:
                        ps.save_to_parquet()
                    save_time = time.perf_counter() - save_start
                    self.logger.debug(f"Parquet saving for {date} completed in {save_time:.2f}s", extra=log_extra)

                    # --- 7. Benchmarking ---
                    total_time = time.perf_counter() - overall_start
                    self.benchmarks[date] = {
                        "load_duration": load_time,
                        "save_duration": save_time,
                        "total_duration": total_time,
                    }

                    # --- 8. Log Success ---
                    self._log_success(date, total_time, path)

        except Exception as e:
            # --- 9. Handle Errors ---
            self._log_failure(date, e)
            raise # Re-raise to trigger retry logic

    # --------------------- Logging / Benchmarking ---------------------
    def _log_success(self, date: datetime.date, duration: float, path: str):
        """Log a successful date processing."""
        self.logger.info(f"Completed {date} in {duration:.1f}s | Saved to {path}", extra=self.logger_extra)
        with self._lock: # Protect the shared list
            self.processed_dates.append(date)

    def _log_failure(self, date: datetime.date, error: Exception):
        """Log a failed date processing."""
        self.logger.error(f"Failed processing {date}: {error}", extra=self.logger_extra)

    def show_benchmark_summary(self):
        """Display a summary of processing times."""
        if not self.benchmarks:
            self.logger.info("No benchmarking data to show", extra=self.logger_extra)
            return

        try:
            df_bench = pd.DataFrame.from_records(
                [{"date": d, **m} for d, m in self.benchmarks.items()]
            )
            if not df_bench.empty:
                df_bench = df_bench.set_index("date").sort_index(
                    ascending=not (self.update_planner.reverse_order if self.update_planner else False)
                )
                summary_str = df_bench.to_string()
                self.logger.info(f"Benchmark Summary:\n {self.dataclass.__name__}\n{summary_str}", extra=self.logger_extra)
            else:
                self.logger.info("Benchmark DataFrame is empty.", extra=self.logger_extra)
        except Exception as e:
            self.logger.error(f"Error generating benchmark summary: {e}", extra=self.logger_extra)


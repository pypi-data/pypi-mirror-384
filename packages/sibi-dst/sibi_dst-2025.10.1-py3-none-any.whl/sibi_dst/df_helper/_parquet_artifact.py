# parquet_artifact.py
from __future__ import annotations

import datetime as dt
import threading
from functools import cached_property
from typing import Any, Dict, Type, TypeVar, Optional, Set

from sibi_dst.utils import DataWrapper, DateUtils, UpdatePlanner, ManagedResource
from sibi_dst.utils import MissingManifestManager

# Type variable for potential future use with specific DataWrapper subclasses
T = TypeVar("T")


class ParquetArtifact(ManagedResource):
    """
    Orchestrates the generation of a single date-partitioned Parquet dataset.
      - Manages a MissingManifestManager for tracking missing data.
      - Uses an UpdatePlanner to determine which dates need processing.
      - Delegates execution to a DataWrapper for concurrent date processing.
      - Prevents duplicate concurrent runs for the same dataset.
      - Forwards retry/backoff configuration to the DataWrapper.
    """

    # --- Class-level state for concurrency control ---
    _global_lock = threading.RLock()
    _active_runs: Set[tuple[str, str]] = set()
    logger_extra = {"sibi_dst_component": __name__}

    def __init__(self, **kwargs: Any):
        """
        Initializes the ParquetArtifact.

        Args:
            **kwargs: Configuration parameters including:
                - parquet_storage_path (str): The base S3/path for the dataset.
                - parquet_filename (str): The name of the Parquet file within each date partition.
                - data_wrapper_class (Type): The class (e.g., Etl...Dc) used to load/process data for a date.
                - fs (fsspec.AbstractFileSystem): The filesystem object.
                - logger (Logger): Logger instance.
                - debug (bool): Enable debug logging.
                - verbose (bool): Enable verbose logging.
                - Plus other parameters passed to UpdatePlanner, DataWrapper, etc.
        """
        # Merge defaults from ManagedResource and caller kwargs
        self.all_kwargs: Dict[str, Any] = dict(kwargs) # Shallow copy
        super().__init__(**self.all_kwargs)

        # --- Instance-level coordination lock ---
        self._lock = threading.RLock()

        # --- Core Configuration (validated/accessed frequently) ---
        if "parquet_storage_path" not in self.all_kwargs:
             raise ValueError("Required argument 'parquet_storage_path' is missing.")
        if "parquet_filename" not in self.all_kwargs:
             raise ValueError("Required argument 'parquet_filename' is missing.")

        self._storage_path: str = self.all_kwargs["parquet_storage_path"]
        #self._parquet_filename: str = self.all_kwargs["parquet_filename"]
        self._data_wrapper_class: Optional[Type] = self.all_kwargs.get("data_wrapper_class")

        # Update logger extra with specific context
        self.logger_extra.update({
            "artifact_storage_path": self._storage_path,
            #"artifact_filename": self._parquet_filename
        })

    # --------------------- Helpers ---------------------
    def _invalidate_cached(self, *names: str) -> None:
        """Invalidate cached properties by name."""
        for name in names:
            self.__dict__.pop(name, None)

    def _build_manifest_path(self) -> str:
        """Construct the path for the missing manifest file."""
        base = self._storage_path.rstrip("/") + "/"
        return f"{base}_manifests/missing.parquet"

    # --------------------- Lazy Members (Cached Properties) ---------------------
    @cached_property
    def mmanifest(self) -> MissingManifestManager:
        """Lazily initialize and return the MissingManifestManager."""
        self.logger.info("Initializing MissingManifestManager...", extra=self.logger_extra)
        manifest_path = self._build_manifest_path()

        # Ensure the manifest directory exists
        manifest_dir = manifest_path.rsplit("/", 1)[0] if "/" in manifest_path else manifest_path
        self.ensure_directory_exists(manifest_dir)

        mgr = MissingManifestManager(
            fs=self.fs,
            manifest_path=manifest_path,
            clear_existing=self.all_kwargs.get("overwrite", False),
            debug=self.debug,
            logger=self.logger,
            overwrite=self.all_kwargs.get("overwrite", False),
        )

        if not mgr._safe_exists(mgr.manifest_path):
            self.logger.info(f"Creating new manifest at {mgr.manifest_path}", extra=self.logger_extra)
            try:
                mgr.save()
            except Exception as e:
                self.logger.error(f"Failed to create initial manifest: {e}", extra=self.logger_extra)
                raise
        else:
            self.logger.info(f"Manifest already exists at {mgr.manifest_path}", extra=self.logger_extra)

        return mgr

    @cached_property
    def update_planner(self) -> UpdatePlanner:
        """Lazily initialize and return the UpdatePlanner."""
        self.logger.info("Initializing UpdatePlanner...", extra=self.logger_extra)
        skipped_files = self.mmanifest.load_existing() or []

        # Prepare configuration for the UpdatePlanner
        cfg = {
            **self.all_kwargs,
            "fs": self.fs,
            "debug": self.debug,
            "logger": self.logger,
            "description": getattr(self._data_wrapper_class, "__name__", "DataWrapper"),
            "skipped": list(skipped_files),
            "mmanifest": self.mmanifest, # Pass the instance
            "partition_on": self.all_kwargs.get("partition_on", ["partition_date"]),
            "hive_style": self.all_kwargs.get("hive_style", True),
        }
        return UpdatePlanner(**cfg)

    @cached_property
    def data_wrapper(self) -> DataWrapper:
        """Lazily initialize and return the DataWrapper."""
        self.logger.info("Initializing DataWrapper...", extra=self.logger_extra)

        # Ensure the planner has generated its plan (accessing the property triggers generation if needed)
        # The planner itself checks if a plan already exists.
        _ = self.update_planner.plan # Access plan property

        # Prepare parameters for the data wrapper class instantiation (passed to Etl...Dc)
        class_params = {
            "debug": self.debug,
            "logger": self.logger,
            "fs": self.fs,
            "verbose": self.verbose,
        }

        # Prepare configuration for the DataWrapper
        cfg = {
            "data_path": self._storage_path,
            "fs": self.fs,
            "debug": self.debug,
            "logger": self.logger,
            "verbose": self.verbose,
            "dataclass": self._data_wrapper_class,
            "class_params": class_params,
            "load_params": self.all_kwargs.get("load_params", {}) or {},
            "mmanifest": self.mmanifest, # Pass the instance
            "update_planner": self.update_planner, # Pass the instance
            "date_field": self.all_kwargs.get("date_field"),
            # Pipeline execution knobs
            "show_progress": bool(self.all_kwargs.get("show_progress", False)),
            "timeout": float(self.all_kwargs.get("timeout", 30.0)),
            "max_threads": int(self.all_kwargs.get("max_threads", 3)),
        }
        return DataWrapper(**cfg)

    # --------------------- Public API ---------------------
    def load(self, **kwargs: Any):
        """
        Directly load data using the configured data_wrapper_class.
        This bypasses the planning/manifest process.

        Args:
            **kwargs: Arguments passed to the dataclass's load method.

        Returns:
            The result of the dataclass's load method (expected to be a DataFrame).
        """
        self.logger.info(f"Directly loading data using {self._data_wrapper_class}", extra=self.logger_extra)

        if not self._data_wrapper_class:
            raise ValueError("data_wrapper_class is not configured.")

        # Prepare parameters for direct loading (typically using Parquet backend)
        params = {
            "backend": "parquet", # Usually implies loading from existing Parquet
            "fs": self.fs,
            "logger": self.logger,
            "debug": self.debug,
            "parquet_storage_path": self._storage_path,
            "parquet_start_date": self.all_kwargs.get("parquet_start_date"),
            "parquet_end_date": self.all_kwargs.get("parquet_end_date"),
            "partition_on": self.all_kwargs.get("partition_on", ["partition_date"]),
            **(self.all_kwargs.get("class_params") or {}),
        }

        cls = self._data_wrapper_class
        # Use context manager to ensure proper setup/teardown of the dataclass instance
        with cls(**params) as instance:
            return instance.load(**kwargs)

    def generate_parquet(self, **kwargs: Any) -> None:
        """
        Generate or update the Parquet dataset according to the plan.
        - Merges runtime kwargs.
        - Invalidates dependent cached properties.
        - Guards against duplicate concurrent runs.
        - Forwards retry/backoff settings to DataWrapper.process().
        """
        # --- 1. Merge runtime configuration ---
        self.all_kwargs.update(kwargs)

        # --- 2. Invalidate caches that depend on runtime changes ---
        # These need to be recreated if their dependencies change
        self._invalidate_cached("update_planner", "data_wrapper")
        if "overwrite" in kwargs:
            self._invalidate_cached("mmanifest") # Overwrite affects manifest creation

        # --- 3. Global concurrency control ---
        key = self._storage_path
        with ParquetArtifact._global_lock:
            if key in ParquetArtifact._active_runs:
                self.logger.info(
                    f"Run already in progress for {key}; skipping this invocation.", extra=self.logger_extra
                )
                return # Exit early if another run is active
            ParquetArtifact._active_runs.add(key)
            self.logger.debug(f"Acquired lock for run {key}.", extra=self.logger_extra)

        try:
            # --- 4. Ensure base storage directory exists ---
            self.ensure_directory_exists(self._storage_path)

            # --- 5. Generate update plan ---
            self.logger.debug("Generating update plan...", extra=self.logger_extra)
            self.update_planner.generate_plan()
            plan = getattr(self.update_planner, "plan", None)

            # --- 6. Check if any updates are required ---
            if plan is None or (hasattr(plan, "empty") and plan.empty):
                # Planning uses Pandas; checking .empty is safe.
                self.logger.info("No updates needed based on the plan. Skipping Parquet generation.", extra=self.logger_extra)
                return

            # --- 7. (Optional) Display the plan ---
            if (
                getattr(self.update_planner, "show_progress", False) and
                not getattr(self.update_planner, "_printed_this_run", False)
            ):
                try:
                    self.update_planner.show_update_plan()
                except Exception as e:
                    self.logger.warning(f"Failed to display update plan: {e}", extra=self.logger_extra)
                # Mark as printed to avoid repeated display if generate_parquet is called again
                setattr(self.update_planner, "_printed_this_run", True)

            # --- 8. Prepare retry/backoff configuration for DataWrapper ---
            dw_retry_kwargs = {
                k: self.all_kwargs[k]
                for k in ("max_retries", "backoff_base", "backoff_jitter", "backoff_max")
                if k in self.all_kwargs
            }

            # --- 9. Execute processing via DataWrapper ---
            with self._lock: # Instance-level lock for accessing cached_property
                dw = self.data_wrapper  # Access the cached property (triggers initialization if needed)
                if hasattr(dw, "process"):
                    self.logger.info("Starting DataWrapper processing...", extra=self.logger_extra)
                    dw.process(**dw_retry_kwargs) # This is where the concurrent date processing happens
                    self.logger.info("DataWrapper processing completed.", extra=self.logger_extra)

                    # --- 10. (Optional) Show benchmark summary ---
                    if getattr(self.update_planner, "show_progress", False) and hasattr(dw, "show_benchmark_summary"):
                        try:
                            dw.show_benchmark_summary()
                        except Exception as e:
                            self.logger.warning(f"Failed to show benchmark summary: {e}", extra=self.logger_extra)

        finally:
            # --- 11. Release global concurrency lock ---
            with ParquetArtifact._global_lock:
                ParquetArtifact._active_runs.discard(key)
                self.logger.debug(f"Released lock for run {key}.", extra=self.logger_extra)

    def update_parquet(self, period: str = "today", **kwargs: Any) -> None:
        """
        High-level entry point to update Parquet for a standard or custom period.

        Args:
            period (str): The period to update. Options:
                - Standard periods: 'today', 'yesterday', 'last_7_days', etc. (via DateUtils.parse_period)
                - 'ytd': Year-to-date.
                - 'itd': Inception-to-date (requires 'history_begins_on' in kwargs).
                - 'custom': Requires 'start_on' and 'end_on' (aliases 'start_date'/'start', 'end_date'/'end' supported).
            **kwargs: Additional arguments passed to generate_parquet, including retry/backoff settings.
        """
        final_kwargs = {**self.all_kwargs, **kwargs}
        period_params: Dict[str, dt.date] = {}

        # --- Determine date range based on period ---
        if period == "itd":
            start_date_str = final_kwargs.get("history_begins_on")
            if not start_date_str:
                raise ValueError("For period 'itd', 'history_begins_on' must be configured.")
            try:
                start_date = dt.datetime.strptime(start_date_str, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError(f"Invalid date format for 'history_begins_on': {start_date_str}. Expected YYYY-MM-DD.")
            period_params = {
                "parquet_start_date": start_date,
                "parquet_end_date": dt.date.today(),
            }

        elif period == "ytd":
            period_params = {
                "parquet_start_date": dt.date(dt.date.today().year, 1, 1),
                "parquet_end_date": dt.date.today(),
            }

        elif period == "custom":
            # --- Handle 'custom' period with alias normalization ---
            alias_map = {
                "start_on": ["start_date", "start"],
                "end_on": ["end_date", "end"],
            }
            normalized_kwargs: Dict[str, Any] = dict(kwargs) # Shallow copy

            for target_key, aliases in alias_map.items():
                if target_key not in normalized_kwargs:
                    for alias in aliases:
                        if alias in normalized_kwargs:
                            normalized_kwargs[target_key] = normalized_kwargs[alias]
                            break # Use the first alias found

            # --- Validate required keys for 'custom' ---
            missing_keys = [k for k in ("start_on", "end_on") if k not in normalized_kwargs]
            if missing_keys:
                raise ValueError(
                    f"For period 'custom', the following required parameters are missing: {', '.join(missing_keys)}"
                )

            # --- Parse and validate custom dates ---
            try:
                start_date_custom = dt.datetime.strptime(str(normalized_kwargs["start_on"]), "%Y-%m-%d").date()
                end_date_custom = dt.datetime.strptime(str(normalized_kwargs["end_on"]), "%Y-%m-%d").date()
                if start_date_custom > end_date_custom:
                     raise ValueError(f"Start date {start_date_custom} cannot be after end date {end_date_custom}.")
            except ValueError as e:
                 raise ValueError(f"Invalid date format or range for 'custom' period: {e}")

            period_params = {
                "parquet_start_date": start_date_custom,
                "parquet_end_date": end_date_custom,
            }

        else:
            # --- Handle standard periods via DateUtils ---
            try:
                start_date_std, end_date_std = DateUtils.parse_period(period=period)
                period_params = {
                    "parquet_start_date": start_date_std,
                    "parquet_end_date": end_date_std,
                }
            except Exception as e:
                raise ValueError(f"Failed to parse period '{period}': {e}") from e

        # --- Merge period parameters and log ---
        final_kwargs.update(period_params)
        self.logger.debug(
            f"Parameters for update_parquet/generate_parquet (period '{period}'): {final_kwargs}",
            extra=self.logger_extra
        )

        # --- Delegate to the core generation logic ---
        self.generate_parquet(**final_kwargs)

    # --------------------- Utilities ---------------------
    def ensure_directory_exists(self, path: str) -> None:
        """Ensure the directory exists, handling potential backend quirks."""
        with self._lock:
            if not self.fs.exists(path):
                self.logger.info(f"Creating directory: {path}", extra=self.logger_extra)
                try:
                    # Try with exist_ok first (standard approach)
                    self.fs.makedirs(path, exist_ok=True)
                except TypeError:
                    # Fallback for backends that don't support exist_ok
                    try:
                        self.fs.makedirs(path)
                    except FileExistsError:
                        # Handle race condition where dir was created between checks
                        pass
                except Exception as e:
                    # Catch other potential errors during directory creation
                    self.logger.error(f"Failed to create directory {path}: {e}", extra=self.logger_extra)
                    raise # Re-raise to prevent proceeding with a missing directory

    # --------------------- Cleanup ---------------------
    def _cleanup(self) -> None:
        """Clean up resources upon instance closure."""
        try:
            # Save manifest if it was modified and has new records
            if (
                "mmanifest" in self.__dict__ and
                hasattr(self.mmanifest, '_new_records') and
                self.mmanifest._new_records
            ):
                self.logger.debug("Saving updated manifest during cleanup.", extra=self.logger_extra)
                self.mmanifest.save()

            # Close the DataWrapper if it was initialized
            if "data_wrapper" in self.__dict__ and hasattr(self.data_wrapper, "close"):
                self.logger.debug("Closing DataWrapper during cleanup.", extra=self.logger_extra)
                self.data_wrapper.close()

        except Exception as e:
            self.logger.warning(f"Error during ParquetArtifact resource cleanup: {e}", extra=self.logger_extra)



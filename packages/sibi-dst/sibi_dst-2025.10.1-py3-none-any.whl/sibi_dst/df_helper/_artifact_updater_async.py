from __future__ import annotations

import asyncio
import datetime
import random
import time
import pickle
from contextlib import ExitStack, suppress
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Sequence, Type

from sibi_dst.utils import ManagedResource, Logger


@dataclass(slots=True)
class _RetryCfg:
    """Retry and backoff configuration."""
    attempts: int = 3
    backoff_base: float = 2.0
    backoff_max: float = 60.0
    jitter: float = 0.15


def run_artifact_update(
    cls: Type,
    artifact_class_kwargs: Dict[str, Any],
    retry: _RetryCfg,
    period: str,
    artifact_kwargs: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Executed inside Dask worker.
    Instantiates artifact and runs update_parquet() with retry logic.
    Reconstructs logger and filesystem if not provided (worker isolation safe).
    """
    import logging
    import fsspec
    from sibi_dst.utils import Logger

    # ---- Reinitialize a lightweight logger for the worker
    worker_logger = Logger.default_logger(logger_name=cls.__name__) if hasattr(Logger, "default_logger") else logging.getLogger(cls.__name__)
    worker_logger.set_level(logging.INFO)

    # ---- Ensure fs is recreated if missing
    fs = artifact_class_kwargs.get("fs")
    if fs is None or isinstance(fs, str):
        try:
            fs_protocol = fs if isinstance(fs, str) else "file"
            fs = fsspec.filesystem(fs_protocol)
        except Exception:
            fs = fsspec.filesystem("file")

    # ---- Merge reconstructed environment into kwargs
    artifact_kwargs_final = {
        **artifact_class_kwargs,
        "logger": worker_logger,
        "fs": fs,
    }

    start_time = datetime.datetime.now()
    success, error_msg, attempts = False, None, 0

    for attempt in range(1, retry.attempts + 1):
        attempts = attempt
        try:
            with ExitStack() as stack:
                inst = cls(**artifact_kwargs_final)
                inst = stack.enter_context(inst)
                inst.update_parquet(period=period, **artifact_kwargs)
            success = True
            break
        except Exception as e:
            error_msg = str(e)
            if attempt < retry.attempts:
                delay = min(retry.backoff_base ** (attempt - 1), retry.backoff_max)
                delay *= 1 + random.uniform(0, retry.jitter)
                time.sleep(delay)

    duration = (datetime.datetime.now() - start_time).total_seconds()
    status = "😀" if success else "😩"
    worker_logger.info(
        f"{status} {cls.__name__} [{period}] finished in {duration:.2f}s ({attempts} attempt(s))"
    )

    return {
        "artifact": cls.__name__,
        "period": period,
        "success": success,
        "error": error_msg,
        "attempts": attempts,
        "duration_seconds": duration,
        "started_at": start_time.isoformat(),
        "ended_at": datetime.datetime.now().isoformat(),
    }


# ---------------- Async Orchestrator ----------------
class ArtifactUpdaterMultiWrapperAsync(ManagedResource):
    """
    Async orchestrator for concurrent artifact updates.

    • Uses Dask client (via DaskClientMixin) or local threads.
    • Automatically sanitizes non-picklable arguments (e.g., loggers, fs).
    • Provides structured retries, async orchestration, and safe cleanup.
    """

    def __init__(
        self,
        wrapped_classes: Dict[str, Sequence[Type]],
        *,
        logger: Logger,
        fs,
        max_workers: int = 3,
        retry_attempts: int = 3,
        update_timeout_seconds: int = 600,
        backoff_base: float = 2.0,
        backoff_max: float = 60.0,
        backoff_jitter: float = 0.15,
        priority_fn: Optional[Callable[[Type], int]] = None,
        artifact_class_kwargs: Optional[Dict[str, Any]] = None,
        use_dask: bool = True,
        dask_client: Optional[Any] = None,
        debug: bool = False,
        verbose: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(logger=logger, fs=fs, debug=debug, verbose=verbose)

        # ---- Core configuration
        self.wrapped_classes = wrapped_classes
        self.max_workers = max_workers
        self.priority_fn = priority_fn
        self.update_timeout_seconds = update_timeout_seconds
        # ---- Client lifecycle management
        self.dask_client = dask_client
        self.use_dask = self.dask_client is not None

        # ---- Retry configuration
        self._retry = _RetryCfg(
            attempts=retry_attempts,
            backoff_base=backoff_base,
            backoff_max=backoff_max,
            jitter=backoff_jitter,
        )

        # ---- Artifact instantiation arguments
        self.artifact_class_kwargs = {
            "logger": logger,
            "fs": fs,
            "debug": debug,
            "verbose": verbose,
            **(artifact_class_kwargs or {}),
        }

        # ---- Runtime tracking
        self.completion_secs: Dict[str, float] = {}
        self.failed: List[str] = []
        self._stop_event = asyncio.Event()

        self.logger_extra = {"sibi_dst_component": self.__class__.__name__}

        if self.use_dask:
            self.logger.debug(f"Initialized with Dask client: {self.dask_client}")
        else:
            self.logger.debug(f"Running in local thread-based mode.")

    async def update_data(self, period: str, **kwargs: Any) -> List[Dict[str, Any]]:
        """Runs updates for all artifacts in a given period."""
        self.completion_secs.clear()
        self.failed.clear()
        classes = self._classes_for(period)

        self.logger.info(
            f"Starting artifact updates for period '{period}' ({len(classes)} artifacts).",
            extra=self.logger_extra,
        )

        try:
            if self.use_dask:
                futures = [self._submit_one_dask(cls, period, kwargs) for cls in classes]
                results = await asyncio.to_thread(lambda: self.dask_client.gather(futures))
            else:
                sem = asyncio.Semaphore(self.max_workers)
                tasks = [self._run_one_async(cls, period, sem, kwargs) for cls in classes]
                results = await asyncio.gather(*tasks)

            self.logger.info(
                f"Completed {len(results)} artifact updates for period '{period}'.",
                extra=self.logger_extra,
            )
            return results

        finally:
            # Always cleanup if we own the client
            if getattr(self, "own_dask_client", False):
                self._close_dask_client()

    def _sanitize_kwargs_for_dask(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Removes non-picklable runtime objects (e.g., loggers, fs) before sending to Dask.
        """
        clean: Dict[str, Any] = {}
        for k, v in kwargs.items():
            try:
                pickle.dumps(v)
                clean[k] = v
            except Exception:
                self.logger.debug(f"Skipping non-picklable key '{k}' for Dask worker.")
        return clean

    def _submit_one_dask(self, cls: Type, period: str, artifact_kwargs: Dict[str, Any]):
        """Submit one artifact job to Dask."""
        safe_kwargs = self._sanitize_kwargs_for_dask(self.artifact_class_kwargs)
        return self.dask_client.submit(
            run_artifact_update,
            cls,
            safe_kwargs,
            self._retry,
            period,
            artifact_kwargs,
            pure=False,
        )

    def _classes_for(self, period: str) -> List[Type]:
        """Selects artifact classes for the given period."""
        try:
            classes = list(self.wrapped_classes[period])
        except KeyError:
            raise ValueError(f"No artifacts configured for period '{period}'.")
        if not classes:
            raise ValueError(f"No artifact classes found for '{period}'.")

        if self.priority_fn:
            with suppress(Exception):
                classes.sort(key=self.priority_fn)
        return classes

    async def _run_one_async(
        self,
        cls: Type,
        period: str,
        sem: asyncio.Semaphore,
        artifact_kwargs: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Fallback local async execution (no Dask)."""
        name = cls.__name__
        start_time = datetime.datetime.now()

        async with sem:
            for attempt in range(1, self._retry.attempts + 1):
                try:
                    def _sync_block():
                        with ExitStack() as stack:
                            inst = cls(**self.artifact_class_kwargs)
                            inst = stack.enter_context(inst)
                            inst.update_parquet(period=period, **artifact_kwargs)

                    await asyncio.wait_for(
                        asyncio.to_thread(_sync_block),
                        timeout=self.update_timeout_seconds,
                    )
                    duration = (datetime.datetime.now() - start_time).total_seconds()
                    self.completion_secs[name] = duration
                    self.logger.info(f"✅ {name} completed in {duration:.2f}s")
                    return {
                        "artifact": name,
                        "period": period,
                        "success": True,
                        "attempts": attempt,
                        "duration_seconds": duration,
                    }

                except Exception as e:
                    if attempt < self._retry.attempts:
                        delay = min(self._retry.backoff_base ** attempt, self._retry.backoff_max)
                        delay *= 1 + random.uniform(0, self._retry.jitter)
                        self.logger.warning(f"Retry {attempt}/{self._retry.attempts} for {name}: {e}")
                        await asyncio.sleep(delay)
                    else:
                        duration = (datetime.datetime.now() - start_time).total_seconds()
                        self.failed.append(name)
                        self.logger.error(f"❌ {name} failed after {attempt} attempts: {e}")
                        return {
                            "artifact": name,
                            "period": period,
                            "success": False,
                            "attempts": attempt,
                            "error": str(e),
                            "duration_seconds": duration,
                        }

    def get_update_status(self) -> Dict[str, Any]:
        """Returns summary of completed, failed, and pending artifacts."""
        done = set(self.completion_secs)
        fail = set(self.failed)
        all_names = {cls.__name__ for v in self.wrapped_classes.values() for cls in v}
        return {
            "total": len(all_names),
            "completed": sorted(done),
            "failed": sorted(fail),
            "pending": sorted(all_names - done - fail),
            "completion_times": self.completion_secs,
        }

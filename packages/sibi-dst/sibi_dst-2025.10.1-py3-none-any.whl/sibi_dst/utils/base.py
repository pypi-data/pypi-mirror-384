from __future__ import annotations

import abc
import asyncio
import contextlib
import json
import threading
import weakref
from typing import Any, Awaitable, Callable, Dict, Optional, Self, final

import fsspec
from sibi_dst.utils import Logger


# --------- Minimal built-in SSE sink (used when auto_sse=True) ----------
class _QueueSSE:
    __slots__ = ("q", "_closed")

    def __init__(self) -> None:
        self.q: asyncio.Queue = asyncio.Queue()
        self._closed = False

    async def send(self, event: str, data: Dict[str, Any]) -> None:
        await self.q.put({"event": event, "data": json.dumps(data)})

    async def put(self, item: Dict[str, Any]) -> None:
        await self.q.put(item)

    async def aclose(self) -> None:
        if not self._closed:
            self._closed = True
            await self.q.put({"event": "__close__", "data": ""})

    def close(self) -> None:
        self._closed = True

    async def __aiter__(self):
        while True:
            item = await self.q.get()
            if item.get("event") == "__close__":
                break
            yield item


# ------------------------------ Base class ------------------------------
class ManagedResource(abc.ABC):
    __slots__ = (
        "verbose", "debug", "_log_cleanup_errors",
        "logger", "_owns_logger",
        "fs", "_fs_factory", "_owns_fs",
        "_sse", "_sse_factory", "_owns_sse",
        "_emitter", "_auto_sse",
        "_is_closed", "_closing",
        "_close_lock", "_aclose_lock",
        "_finalizer",
    )

    def __init__(
        self,
        *,
        verbose: bool = False,
        debug: bool = False,
        log_cleanup_errors: bool = True,
        logger: Optional[Logger] = None,
        fs: Optional[fsspec.AbstractFileSystem] = None,
        fs_factory: Optional[Callable[[], fsspec.AbstractFileSystem]] = None,
        emitter: Optional[Callable[[str, Dict[str, Any]], Awaitable[None]]] = None,
        emitter_factory: Optional[Callable[[], Callable[[str, Dict[str, Any]], Awaitable[None]]]] = None,
        sse: Optional[object] = None,
        sse_factory: Optional[Callable[[], object]] = None,
        auto_sse: bool = False,
        **_: object,
    ) -> None:
        self.verbose = verbose
        self.debug = debug
        self._log_cleanup_errors = log_cleanup_errors

        self._is_closed = False
        self._closing = False
        self._close_lock = threading.RLock()
        self._aclose_lock = asyncio.Lock()

        # ---------- Logger ----------
        if logger is None:
            self.logger = Logger.default_logger(logger_name=self.__class__.__name__)
            self._owns_logger = True
            level = Logger.DEBUG if self.debug else (Logger.INFO if self.verbose else Logger.WARNING)
            self.logger.set_level(level)
        else:
            self.logger = logger
            self._owns_logger = False

        # ---------- FS ----------
        self.fs: Optional[fsspec.AbstractFileSystem] = None
        self._fs_factory = None
        self._owns_fs = False
        if fs is not None:
            if not isinstance(fs, fsspec.AbstractFileSystem):
                raise TypeError(f"fs must be an fsspec.AbstractFileSystem, got {type(fs)!r}")
            self.fs = fs
        elif fs_factory is not None:
            if not callable(fs_factory):
                raise TypeError("fs_factory must be callable")
            self._fs_factory = fs_factory
            self._owns_fs = True

        # ---------- SSE ----------
        self._sse: Optional[object] = None
        self._sse_factory: Optional[Callable[[], object]] = None
        self._owns_sse = False
        self._auto_sse = auto_sse

        self._emitter: Optional[Callable[[str, Dict[str, Any]], Awaitable[None]]] = None
        if emitter is not None:
            self._emitter = emitter
        elif emitter_factory is not None:
            self._emitter = emitter_factory()

        if sse is not None:
            self._sse = sse
            self._emitter = self._emitter or self._build_emitter(sse)
        elif sse_factory is not None:
            if not callable(sse_factory):
                raise TypeError("sse_factory must be callable")
            self._sse_factory = sse_factory
            self._owns_sse = True

        if self._auto_sse and self._sse is None and self._emitter is None and self._sse_factory is None:
            self._create_auto_sse()

        # ---------- Finalizer ----------
        self._finalizer = weakref.finalize(self, self._finalize_static, weakref.ref(self))

        if self.debug:
            with contextlib.suppress(Exception):
                self.logger.debug("Initialized %s %s", self.__class__.__name__, repr(self))

    # ---------- Properties ----------
    @property
    def closed(self) -> bool:
        return self._is_closed

    @property
    def has_fs(self) -> bool:
        return self.fs is not None or self._fs_factory is not None

    @property
    def has_sse(self) -> bool:
        return (self._emitter is not None) or (self._sse is not None)

    def __repr__(self) -> str:
        def _status(current: bool, factory: bool, owned: bool) -> str:
            if current:
                return "own" if owned else "external"
            if factory:
                return "own(lazy)"
            return "none"

        fs_status = _status(self.fs is not None, self._fs_factory is not None, self._owns_fs)
        sse_status = _status(self._sse is not None or self._emitter is not None,
                             self._sse_factory is not None or self._auto_sse, self._owns_sse)
        return (f"<{self.__class__.__name__} debug={self.debug} verbose={self.verbose} "
                f"log_cleanup_errors={self._log_cleanup_errors} fs={fs_status} sse={sse_status}>")

    # ---------- Hooks ----------
    def _cleanup(self) -> None:
        return

    async def _acleanup(self) -> None:
        return

    def _assert_open(self) -> None:
        if self._is_closed or self._closing:
            raise RuntimeError(f"{self.__class__.__name__} is closed")

    # ---------- FS ----------
    def set_fs_factory(self, factory: Optional[Callable[[], fsspec.AbstractFileSystem]]) -> None:
        with self._close_lock:
            self._assert_open()
            if self.fs is not None:
                return
            if factory is not None and not callable(factory):
                raise TypeError("fs_factory must be callable")
            self._fs_factory = factory
            self._owns_fs = factory is not None

    def _ensure_fs(self) -> Optional[fsspec.AbstractFileSystem]:
        with self._close_lock:
            self._assert_open()
            if self.fs is not None:
                return self.fs
            if self._fs_factory is None:
                return None
            fs_new = self._fs_factory()
            if not isinstance(fs_new, fsspec.AbstractFileSystem):
                raise TypeError(f"fs_factory() must return fsspec.AbstractFileSystem, got {type(fs_new)!r}")
            self.fs = fs_new
            return self.fs

    def require_fs(self) -> fsspec.AbstractFileSystem:
        fs = self._ensure_fs()
        if fs is None:
            raise RuntimeError(f"{self.__class__.__name__}: filesystem is required but not configured")
        return fs

    # ---------- SSE ----------
    def _create_auto_sse(self) -> None:
        sink = _QueueSSE()
        self._sse = sink
        we_own = True
        self._owns_sse = we_own
        self._emitter = self._build_emitter(sink)

    def set_sse_factory(self, factory: Optional[Callable[[], object]]) -> None:
        with self._close_lock:
            self._assert_open()
            if self._sse is not None or self._emitter is not None:
                return
            if factory is not None and not callable(factory):
                raise TypeError("sse_factory must be callable")
            self._sse_factory = factory
            self._owns_sse = factory is not None

    def _ensure_sse(self) -> Optional[object]:
        with self._close_lock:
            if self._sse is not None:
                return self._sse
            self._assert_open()
            if self._sse_factory is not None:
                sink = self._sse_factory()
                self._sse = sink
                self._owns_sse = True
                if self._emitter is None:
                    self._emitter = self._build_emitter(sink)
                return self._sse
            if self._auto_sse and self._emitter is None:
                self._create_auto_sse()
                return self._sse
            return None

    def get_sse(self) -> Optional[object]:
        return self._ensure_sse()

    def _build_emitter(self, sink: object) -> Callable[[str, Dict[str, Any]], Awaitable[None]]:
        send = getattr(sink, "send", None)
        put = getattr(sink, "put", None)

        if callable(send) and asyncio.iscoroutinefunction(send):
            async def _emit(event: str, payload: Dict[str, Any]) -> None:
                await send(event, payload)
            return _emit

        if callable(put) and asyncio.iscoroutinefunction(put):
            async def _emit(event: str, payload: Dict[str, Any]) -> None:
                await put({"event": event, "data": json.dumps(payload)})
            return _emit

        if callable(send) and not asyncio.iscoroutinefunction(send):
            async def _emit(event: str, payload: Dict[str, Any]) -> None:
                await asyncio.to_thread(send, event, payload)
            return _emit

        if callable(put) and not asyncio.iscoroutinefunction(put):
            async def _emit(event: str, payload: Dict[str, Any]) -> None:
                await asyncio.to_thread(put, {"event": event, "data": json.dumps(payload)})
            return _emit

        raise TypeError(f"{self.__class__.__name__}: SSE sink must expose send(event, data) or put(item)")

    async def emit(self, event: str, **data: Any) -> None:
        if self._is_closed or self._closing:
            return
        if self._emitter is None:
            self._ensure_sse()
        emitter = self._emitter
        if emitter is None:
            return
        try:
            await emitter(event, data)
        except Exception:
            if self._log_cleanup_errors:
                with contextlib.suppress(Exception):
                    self.logger.error("Error emitting SSE event %r", event, exc_info=self.debug)

    # ---------- Shutdown helpers ----------
    def _release_owned_fs(self) -> None:
        if self._owns_fs and self.fs is not None:
            close = getattr(self.fs, "close", None)
            with contextlib.suppress(Exception):
                if callable(close):
                    close()
            self.fs = None

    async def _aclose_obj(self, obj: object, timeout: float = 1.0) -> None:
        aclose = getattr(obj, "aclose", None)
        if callable(aclose):
            with contextlib.suppress(Exception):
                await asyncio.wait_for(aclose(), timeout=timeout)
        close = getattr(obj, "close", None)
        if callable(close):
            with contextlib.suppress(Exception):
                await asyncio.to_thread(close)

    def _shutdown_logger(self) -> None:
        if self._owns_logger:
            with contextlib.suppress(Exception):
                shutdown = getattr(self.logger, "shutdown", None)
                if callable(shutdown):
                    shutdown()
                else:
                    close_handlers = getattr(self.logger, "close_handlers", None)
                    if callable(close_handlers):
                        close_handlers()

    def _shutdown_owned_resources_sync(self) -> None:
        self._release_owned_fs()
        if self._owns_sse and self._sse is not None:
            with contextlib.suppress(Exception):
                close = getattr(self._sse, "close", None)
                if callable(close):
                    close()
        self._sse = None
        self._emitter = None
        self._shutdown_logger()

    async def _shutdown_owned_resources_async(self) -> None:
        self._release_owned_fs()
        if self._owns_sse and self._sse is not None:
            await self._aclose_obj(self._sse)
        self._sse = None
        self._emitter = None
        self._shutdown_logger()

    # ---------- Public lifecycle ----------
    @final
    def close(self, *, suppress_errors: bool = False) -> None:
        with self._close_lock:
            if self._is_closed or self._closing:
                return
            self._closing = True
            # optional subclass hook
            maybe_close = getattr(self, "_close_obj", None)
            if callable(maybe_close):
                try:
                    maybe_close()
                except Exception:
                    if not suppress_errors:
                        raise

        try:
            self._cleanup()
        except Exception:
            if self._log_cleanup_errors:
                with contextlib.suppress(Exception):
                    self.logger.error("Error during %s._cleanup()", self.__class__.__name__, exc_info=self.debug)
            if not suppress_errors:
                raise
        finally:
            with self._close_lock:
                self._is_closed = True
                self._closing = False
            self._shutdown_owned_resources_sync()
            if self.debug:
                with contextlib.suppress(Exception):
                    self.logger.debug("Component %s closed.", self.__class__.__name__)

    @final
    async def aclose(
        self,
        *,
        suppress_errors: bool = False,
        run_sync_cleanup_if_missing: bool = False,
    ) -> None:
        async with self._aclose_lock:
            with self._close_lock:
                if self._is_closed or self._closing:
                    return
                self._closing = True

            try:
                # optional subclass hook with distinct name to avoid clashing with helper
                maybe_async_close = getattr(self, "_custom_aclose_obj", None)
                if asyncio.iscoroutinefunction(maybe_async_close):
                    await maybe_async_close()
                elif callable(maybe_async_close):
                    await asyncio.to_thread(maybe_async_close)

                if run_sync_cleanup_if_missing and (type(self)._acleanup is ManagedResource._acleanup):
                    await asyncio.to_thread(self._cleanup)
                else:
                    await self._acleanup()
            except Exception:
                if self._log_cleanup_errors:
                    with contextlib.suppress(Exception):
                        self.logger.error(
                            "Error during %s._acleanup()", self.__class__.__name__, exc_info=self.debug
                        )
                if not suppress_errors:
                    raise
            finally:
                with self._close_lock:
                    self._is_closed = True
                    self._closing = False
                await self._shutdown_owned_resources_async()
                if self.debug:
                    with contextlib.suppress(Exception):
                        self.logger.debug("Async component %s closed.", self.__class__.__name__)

    # ---------- Context managers ----------
    @final
    def __enter__(self) -> Self:
        return self

    @final
    def __exit__(self, exc_type, exc, tb) -> bool:
        self.close()
        return False

    @final
    async def __aenter__(self) -> Self:
        return self

    @final
    async def __aexit__(self, exc_type, exc, tb) -> bool:
        await self.aclose()
        return False

    # ---------- Finalizer ----------
    @staticmethod
    def _finalize_static(ref: "weakref.ReferenceType[ManagedResource]") -> None:
        obj = ref()
        if obj is None:
            return
        try:
            if not obj._is_closed:
                with contextlib.suppress(Exception):
                    obj._cleanup()
                obj._is_closed = True
                with contextlib.suppress(Exception):
                    obj._shutdown_owned_resources_sync()
        except Exception:
            pass
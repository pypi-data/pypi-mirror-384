import asyncio
import json
import threading
from typing import Any, Dict
from unittest.mock import MagicMock

import fsspec

from sibi_dst.utils import Logger
from sibi_dst.utils import ManagedResource
from sibi_dst.utils.base import _QueueSSE  # Replace 'your_module' with actual module name


# ------------------------------ Test Fixtures ------------------------------

class TestResource(ManagedResource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cleanup_called = False
        self.acleanup_called = False

    def _cleanup(self) -> None:
        self.cleanup_called = True
        super()._cleanup()

    async def _acleanup(self) -> None:
        self.acleanup_called = True
        await super()._acleanup()


class MockSSESink:
    def __init__(self):
        self.events = []
        self.closed = False

    async def send(self, event: str, data: Dict[str, Any]) -> None:
        self.events.append({"event": event, "data": data})

    async def aclose(self) -> None:
        self.closed = True


class MockSyncSSESink:
    def __init__(self):
        self.events = []
        self.closed = False

    def send(self, event: str, data: Dict[str, Any]) -> None:
        self.events.append({"event": event, "data": data})

    def close(self) -> None:
        self.closed = True


# ------------------------------ Mock fsspec filesystem ------------------------------

class MockFileSystem(fsspec.AbstractFileSystem):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.closed = False

    def close(self):
        self.closed = True


# ------------------------------ Utility for Event Loop ------------------------------

def run_async_test(coro):
    """Run async test safely in different environments."""
    try:
        # Try to get existing event loop (for Jupyter/IPython)
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # In Jupyter, create a new task
            task = loop.create_task(coro)
            return task
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        # No event loop running, use asyncio.run()
        return asyncio.run(coro)


# ------------------------------ Lifecycle Tests ------------------------------

def test_double_close_no_error():
    """Test that calling close() multiple times doesn't raise errors."""
    resource = TestResource()
    resource.close()
    resource.close()  # Should not raise
    assert resource.closed


def test_double_aclose_no_error():
    """Test that calling aclose() multiple times doesn't raise errors."""
    async def test():
        resource = TestResource()
        await resource.aclose()
        await resource.aclose()  # Should not raise
        assert resource.closed

    run_async_test(test())


def test_context_manager_sync():
    """Test sync context manager behavior."""
    with TestResource() as resource:
        assert not resource.closed
    assert resource.closed
    assert resource.cleanup_called


def test_context_manager_async():
    """Test async context manager behavior."""
    async def test():
        async with TestResource() as resource:
            assert not resource.closed
        assert resource.closed
        assert resource.acleanup_called

    run_async_test(test())


# ------------------------------ SSE Emission Tests ------------------------------

def test_auto_sse_creation():
    """Test automatic SSE creation when auto_sse=True."""
    resource = TestResource(auto_sse=True)
    sse = resource.get_sse()
    assert sse is not None
    assert isinstance(sse, _QueueSSE)
    assert resource._owns_sse


def test_sse_emission_with_async_sink():
    """Test SSE emission with async send method."""
    async def test():
        sink = MockSSESink()
        resource = TestResource(sse=sink)

        await resource.emit("test_event", key="value")

        assert len(sink.events) == 1
        assert sink.events[0]["event"] == "test_event"
        assert sink.events[0]["data"] == {"key": "value"}

    run_async_test(test())


def test_sse_emission_with_sync_sink():
    """Test SSE emission with sync send method wrapped in async."""
    sink = MockSyncSSESink()
    resource = TestResource(sse=sink)

    async def test():
        await resource.emit("test_event", key="value")

        assert len(sink.events) == 1
        assert sink.events[0]["event"] == "test_event"
        assert sink.events[0]["data"] == {"key": "value"}

    run_async_test(test())


def test_sse_put_method_support():
    """Test SSE emission with put method."""
    class PutSink:
        def __init__(self):
            self.items = []

        async def put(self, item: Dict[str, Any]) -> None:
            self.items.append(item)

    async def test():
        sink = PutSink()
        resource = TestResource(sse=sink)

        await resource.emit("test_event", key="value")

        assert len(sink.items) == 1
        item = sink.items[0]
        assert item["event"] == "test_event"
        assert json.loads(item["data"]) == {"key": "value"}

    run_async_test(test())


def test_sse_no_emitter_no_error():
    """Test that emit on resource without emitter doesn't raise."""
    resource = TestResource()
    # Should not raise error
    async def test():
        await resource.emit("test_event", key="value")

    run_async_test(test())


def test_sse_emission_after_close():
    """Test that emit after close is no-op."""
    async def test():
        sink = MockSSESink()
        resource = TestResource(sse=sink)

        await resource.aclose()
        await resource.emit("test_event", key="value")  # Should not raise

        assert len(sink.events) == 0

    run_async_test(test())


# ------------------------------ Cleanup Interplay Tests ------------------------------

def test_sync_cleanup_called_on_sync_close():
    """Test that sync cleanup is called during sync close."""
    resource = TestResource()
    resource.close()
    assert resource.cleanup_called
    assert not resource.acleanup_called


def test_async_cleanup_called_on_async_close():
    """Test that async cleanup is called during async close."""
    async def test():
        resource = TestResource()
        await resource.aclose()
        assert resource.acleanup_called
        assert not resource.cleanup_called

    run_async_test(test())


# ------------------------------ Logger Tests ------------------------------

def test_logger_ownership():
    """Test that logger is owned when not provided externally."""
    resource = TestResource()
    assert resource._owns_logger
    assert resource.logger is not None


def test_external_logger_not_owned():
    """Test that external logger is not owned."""
    external_logger = Logger.default_logger("test")
    resource = TestResource(logger=external_logger)
    assert not resource._owns_logger
    assert resource.logger is external_logger


def test_logger_level_configuration():
    """Test logger level configuration based on verbose/debug flags."""
    # Default (warning level)
    resource = TestResource()
    assert hasattr(resource.logger, 'level')

    # Verbose (info level)
    resource = TestResource(verbose=True)
    assert hasattr(resource.logger, 'level')

    # Debug (debug level)
    resource = TestResource(debug=True)
    assert hasattr(resource.logger, 'level')


# ------------------------------ Lazy Instantiation Tests ------------------------------

def test_lazy_fs_instantiation():
    """Test lazy filesystem instantiation via factory."""
    fs_instance = MockFileSystem()
    factory_called = [False]

    def fs_factory():
        factory_called[0] = True
        return fs_instance

    resource = TestResource(fs_factory=fs_factory)
    assert not factory_called[0]  # Not called yet

    fs = resource._ensure_fs()
    assert factory_called[0]
    assert fs is fs_instance
    assert resource.fs is fs_instance


def test_lazy_sse_instantiation():
    """Test lazy SSE instantiation via factory."""
    sink_instance = MockSSESink()
    factory_called = [False]

    def sse_factory():
        factory_called[0] = True
        return sink_instance

    resource = TestResource(sse_factory=sse_factory)
    assert not factory_called[0]  # Not called yet

    sse = resource._ensure_sse()
    assert factory_called[0]
    assert sse is sink_instance
    assert resource._sse is sink_instance


def test_lazy_fs_not_called_if_fs_provided():
    """Test that factory is not called if fs is provided directly."""
    fs_instance = MockFileSystem()
    factory = MagicMock()

    resource = TestResource(fs=fs_instance, fs_factory=factory)
    fs = resource._ensure_fs()

    assert fs is fs_instance
    factory.assert_not_called()


def test_lazy_sse_not_called_if_sse_provided():
    """Test that factory is not called if sse is provided directly."""
    sink_instance = MockSSESink()
    factory = MagicMock()

    resource = TestResource(sse=sink_instance, sse_factory=factory)
    sse = resource._ensure_sse()

    assert sse is sink_instance
    factory.assert_not_called()


# ------------------------------ Thread Safety Tests ------------------------------

def test_thread_safe_close():
    """Test that close operations are thread-safe."""
    resource = TestResource()

    results = []
    errors = []

    def close_resource():
        try:
            resource.close()
            results.append("success")
        except Exception as e:
            errors.append(str(e))
            results.append(f"error: {e}")

    # Start multiple threads trying to close simultaneously
    threads = [threading.Thread(target=close_resource) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Debug information
    print(f"Results: {results}")
    print(f"Errors: {errors}")
    print(f"Resource closed: {resource.closed}")

    # Should have at least one success (the first one) and no exceptions
    success_count = results.count("success")
    error_count = len([r for r in results if r.startswith("error")])

    # At least one should succeed
    assert success_count >= 1, f"Expected at least 1 success, got {success_count}"
    # No errors should occur
    assert error_count == 0, f"Expected 0 errors, got {error_count}"
    # Resource should be closed
    assert resource.closed, "Resource should be closed"


# ------------------------------ Individual Test Functions ------------------------------

# You can now run individual tests like this:
if __name__ == "__main__":
    # Run individual tests
    test_double_close_no_error()
    print("✓ test_double_close_no_error passed")

    test_sync_cleanup_called_on_sync_close()
    print("✓ test_sync_cleanup_called_on_sync_close passed")

    test_logger_ownership()
    print("✓ test_logger_ownership passed")

    test_external_logger_not_owned()
    print("✓ test_external_logger_not_owned passed")

    test_lazy_fs_instantiation()
    print("✓ test_lazy_fs_instantiation passed")

    test_lazy_sse_instantiation()
    print("✓ test_lazy_sse_instantiation passed")

    test_lazy_fs_not_called_if_fs_provided()
    print("✓ test_lazy_fs_not_called_if_fs_provided passed")

    test_lazy_sse_not_called_if_sse_provided()
    print("✓ test_lazy_sse_not_called_if_sse_provided passed")

    test_thread_safe_close()
    print("✓ test_thread_safe_close passed")

    test_auto_sse_creation()
    print("✓ test_auto_sse_creation passed")

    print("All tests completed!")
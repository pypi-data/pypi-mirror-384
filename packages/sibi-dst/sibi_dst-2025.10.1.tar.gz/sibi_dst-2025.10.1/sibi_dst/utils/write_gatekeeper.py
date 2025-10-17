# write_gatekeeper.py
from __future__ import annotations
import threading

_LOCK = threading.Lock()
_SEMS: dict[str, threading.Semaphore] = {}

def get_write_sem(key: str, max_concurrency: int) -> threading.Semaphore:
    """
    Return a process-local semaphore that caps concurrent writers for a given key.
    Key should be a stable path prefix, e.g., 's3://bucket/prefix'.
    """
    with _LOCK:
        sem = _SEMS.get(key)
        if sem is None:
            sem = threading.Semaphore(max(1, int(max_concurrency)))
            _SEMS[key] = sem
        return sem
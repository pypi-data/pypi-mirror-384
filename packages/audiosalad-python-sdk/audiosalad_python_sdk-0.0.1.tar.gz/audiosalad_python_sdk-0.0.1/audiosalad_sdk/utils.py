"""Mocked utils for the AudioSalad SDK."""

import logging
from typing import Any, Dict


def log_system_event(
    event_type: str, description: str, level, additional_data: Dict[str, Any]
):
    """Log a system event with a string or int logging level."""
    if isinstance(level, str):
        level_value = getattr(logging, level.upper(), logging.INFO)
    else:
        level_value = int(level)

    logging.log(level_value, f"{event_type}: {description}")
    logging.log(level_value, f"Additional data: {additional_data}")


class _SimpleCache:
    """
    Super lightweight cache used by AudioSaladWeb.
    Supports .get/.set API and ignores TTL in tests.
    """

    def __init__(self):
        self._data: Dict[str, Any] = {}

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def set(self, key: str, value: Any, _timeout_seconds: int | None = None):
        self._data[key] = value


# Public cache object (used by AudioSaladWeb)
cache = _SimpleCache()


def memoize(func):
    """
    Optional memoizing decorator (kept in case you need the previous decorator behavior elsewhere).
    Not used by AudioSaladWeb which relies on the cache object above.
    """
    store: Dict[tuple, Any] = {}

    def wrapper(*args, **kwargs):
        k = (args, tuple(sorted(kwargs.items())))
        if k in store:
            return store[k]
        res = func(*args, **kwargs)
        store[k] = res
        return res

    return wrapper

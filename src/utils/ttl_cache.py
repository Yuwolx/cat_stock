from __future__ import annotations

import time
from typing import Any, Hashable


_CACHE: dict[Hashable, tuple[float, Any]] = {}


def get_ttl_cache(key: Hashable, ttl_seconds: int = 300) -> Any | None:
    entry = _CACHE.get(key)
    if not entry:
        return None
    created_at, value = entry
    if time.time() - created_at > ttl_seconds:
        _CACHE.pop(key, None)
        return None
    return value


def set_ttl_cache(key: Hashable, value: Any) -> Any:
    _CACHE[key] = (time.time(), value)
    return value


def clear_ttl_cache() -> None:
    _CACHE.clear()

from __future__ import annotations


def future_result(futures: dict[str, object], key: str, default: object) -> object:
    try:
        return futures[key].result()
    except Exception:
        return default

from __future__ import annotations

import requests

from src.utils.ttl_cache import get_ttl_cache, set_ttl_cache


FEAR_GREED_URL = "https://api.alternative.me/fng/"


def get_fear_greed_index(use_mock_data: bool = False) -> dict:
    if use_mock_data:
        return {
            "value": 62,
            "classification": "Greed",
            "timestamp": None,
        }

    try:
        cache_key = ("alternative_fng", "latest")
        cached = get_ttl_cache(cache_key)
        if cached is not None:
            return cached

        response = requests.get(FEAR_GREED_URL, params={"limit": 1}, timeout=10)
        response.raise_for_status()
        data = response.json().get("data", [])
        if not data:
            return {"value": None, "classification": None, "timestamp": None}
        latest = data[0]
        return set_ttl_cache(cache_key, {
            "value": int(latest["value"]) if str(latest.get("value", "")).isdigit() else None,
            "classification": latest.get("value_classification"),
            "timestamp": latest.get("timestamp"),
        })
    except Exception:
        return {"value": None, "classification": None, "timestamp": None}

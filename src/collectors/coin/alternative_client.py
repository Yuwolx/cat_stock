from __future__ import annotations

import requests


FEAR_GREED_URL = "https://api.alternative.me/fng/"


def get_fear_greed_index(use_mock_data: bool = False) -> dict:
    if use_mock_data:
        return {
            "value": 62,
            "classification": "Greed",
            "timestamp": None,
        }

    try:
        response = requests.get(FEAR_GREED_URL, params={"limit": 1}, timeout=10)
        response.raise_for_status()
        data = response.json().get("data", [])
        if not data:
            return {"value": None, "classification": None, "timestamp": None}
        latest = data[0]
        return {
            "value": int(latest["value"]) if str(latest.get("value", "")).isdigit() else None,
            "classification": latest.get("value_classification"),
            "timestamp": latest.get("timestamp"),
        }
    except Exception:
        return {"value": None, "classification": None, "timestamp": None}

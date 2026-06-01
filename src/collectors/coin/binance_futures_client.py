from __future__ import annotations

from typing import Any

import requests


BASE_URL = "https://fapi.binance.com"
HEADERS = {
    "accept": "application/json",
    "user-agent": "cat-stock/1.0",
}


def _get_json(path: str, params: dict[str, Any] | None = None) -> Any:
    response = requests.get(f"{BASE_URL}{path}", params=params, headers=HEADERS, timeout=10)
    response.raise_for_status()
    return response.json()


def _parse_float(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).replace(",", ""))
    except ValueError:
        return None


def _pct_change(current: float | None, previous: float | None) -> float | None:
    if current is None or previous is None or previous == 0:
        return None
    return ((current / previous) - 1) * 100


def get_futures_risk(symbol: str, use_mock_data: bool = False) -> dict:
    market = f"{symbol.strip().upper()}USDT"
    if use_mock_data:
        return {
            "symbol": market,
            "is_available": True,
            "mark_price_usd": 73_900,
            "latest_funding_rate_pct": 0.012,
            "avg_funding_rate_pct": 0.009,
            "annualized_funding_pct": 9.86,
            "open_interest": 105_000,
            "open_interest_value_usd": 7_800_000_000,
            "open_interest_change_24h_pct": 4.8,
            "warning": "보통",
        }

    try:
        funding_rows = _get_json("/fapi/v1/fundingRate", params={"symbol": market, "limit": 9})
        open_interest = _get_json("/fapi/v1/openInterest", params={"symbol": market})
        hist = _get_json(
            "/futures/data/openInterestHist",
            params={"symbol": market, "period": "1h", "limit": 25},
        )
    except Exception:
        return {
            "symbol": market,
            "is_available": False,
            "latest_funding_rate_pct": None,
            "avg_funding_rate_pct": None,
            "annualized_funding_pct": None,
            "open_interest": None,
            "open_interest_value_usd": None,
            "open_interest_change_24h_pct": None,
            "warning": "연결 안 됨",
        }

    rates = [_parse_float(row.get("fundingRate")) for row in funding_rows if isinstance(row, dict)]
    rates = [rate for rate in rates if rate is not None]
    latest_rate = rates[-1] if rates else None
    avg_rate = sum(rates) / len(rates) if rates else None
    latest_funding_row = funding_rows[-1] if isinstance(funding_rows, list) and funding_rows else {}

    hist_rows = hist if isinstance(hist, list) else []
    latest_hist = hist_rows[-1] if hist_rows else {}
    previous_hist = hist_rows[0] if len(hist_rows) > 1 else {}
    latest_value = _parse_float(latest_hist.get("sumOpenInterestValue"))
    previous_value = _parse_float(previous_hist.get("sumOpenInterestValue"))
    funding_pct = latest_rate * 100 if latest_rate is not None else None
    avg_funding_pct = avg_rate * 100 if avg_rate is not None else None
    annualized = avg_rate * 3 * 365 * 100 if avg_rate is not None else None
    oi_change = _pct_change(latest_value, previous_value)

    warning = "보통"
    if funding_pct is not None and funding_pct >= 0.05:
        warning = "롱 과열 주의"
    if oi_change is not None and oi_change >= 15:
        warning = "OI 급증 주의"
    if funding_pct is not None and funding_pct <= -0.03:
        warning = "숏 쏠림 주의"

    return {
        "symbol": market,
        "is_available": True,
        "mark_price_usd": _parse_float(latest_funding_row.get("markPrice")),
        "latest_funding_rate_pct": funding_pct,
        "avg_funding_rate_pct": avg_funding_pct,
        "annualized_funding_pct": annualized,
        "open_interest": _parse_float(open_interest.get("openInterest")),
        "open_interest_value_usd": latest_value,
        "open_interest_change_24h_pct": oi_change,
        "warning": warning,
    }

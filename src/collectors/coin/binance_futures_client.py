from __future__ import annotations

from typing import Any

import requests

from src.utils.ttl_cache import get_ttl_cache, set_ttl_cache


BASE_URL = "https://fapi.binance.com"
HEADERS = {
    "accept": "application/json",
    "user-agent": "cat-stock/1.0",
}
USD_M_PERPETUAL_LABEL = "USD-M 무기한 선물"


def _empty_futures_payload(symbol: str, warning: str) -> dict:
    return {
        "symbol": symbol,
        "contract_type": "PERPETUAL",
        "contract_label": USD_M_PERPETUAL_LABEL,
        "is_available": False,
        "mark_price_usd": None,
        "latest_funding_rate_pct": None,
        "avg_funding_rate_pct": None,
        "annualized_funding_pct": None,
        "open_interest": None,
        "open_interest_value_usd": None,
        "open_interest_change_24h_pct": None,
        "warning": warning,
    }


def _get_json(path: str, params: dict[str, Any] | None = None) -> Any:
    cache_key = ("binance_futures", path, tuple(sorted((params or {}).items())))
    cached = get_ttl_cache(cache_key)
    if cached is not None:
        return cached

    response = requests.get(f"{BASE_URL}{path}", params=params, headers=HEADERS, timeout=10)
    response.raise_for_status()
    return set_ttl_cache(cache_key, response.json())


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
            "contract_type": "PERPETUAL",
            "contract_label": USD_M_PERPETUAL_LABEL,
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
        return _empty_futures_payload(market, "연결 안 됨")

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
    open_interest_amount = _parse_float(open_interest.get("openInterest")) if isinstance(open_interest, dict) else None
    oi_change = _pct_change(latest_value, previous_value)

    if funding_pct is None and open_interest_amount is None and latest_value is None:
        return _empty_futures_payload(market, "데이터 없음")

    warning = "보통"
    if funding_pct is not None and funding_pct >= 0.05:
        warning = "롱 과열 주의"
    if oi_change is not None and oi_change >= 15:
        warning = "OI 급증 주의"
    if funding_pct is not None and funding_pct <= -0.03:
        warning = "숏 쏠림 주의"
    if warning == "보통" and any(
        value is None
        for value in (funding_pct, avg_funding_pct, annualized, open_interest_amount, latest_value, oi_change)
    ):
        warning = "일부 데이터 비어 있음"

    return {
        "symbol": market,
        "contract_type": "PERPETUAL",
        "contract_label": USD_M_PERPETUAL_LABEL,
        "is_available": True,
        "mark_price_usd": _parse_float(latest_funding_row.get("markPrice")),
        "latest_funding_rate_pct": funding_pct,
        "avg_funding_rate_pct": avg_funding_pct,
        "annualized_funding_pct": annualized,
        "open_interest": open_interest_amount,
        "open_interest_value_usd": latest_value,
        "open_interest_change_24h_pct": oi_change,
        "warning": warning,
    }

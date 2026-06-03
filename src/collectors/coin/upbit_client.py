from __future__ import annotations

from typing import Any

import requests

from src.utils.ttl_cache import get_ttl_cache, set_ttl_cache


BASE_URL = "https://api.upbit.com/v1"
HEADERS = {
    "accept": "application/json",
    "user-agent": "cat-stock/1.0",
}


def _get_json(path: str, params: dict[str, Any] | None = None) -> Any:
    cache_key = ("upbit", path, tuple(sorted((params or {}).items())))
    cached = get_ttl_cache(cache_key)
    if cached is not None:
        return cached

    response = requests.get(f"{BASE_URL}{path}", params=params, headers=HEADERS, timeout=10)
    response.raise_for_status()
    return set_ttl_cache(cache_key, response.json())


def _chunked(items: list[str], size: int) -> list[list[str]]:
    return [items[index : index + size] for index in range(0, len(items), size)]


def get_krw_markets(use_mock_data: bool = False) -> list[dict]:
    if use_mock_data:
        return [
            {"market": "KRW-BTC", "korean_name": "비트코인", "english_name": "Bitcoin", "warning": False},
            {"market": "KRW-ETH", "korean_name": "이더리움", "english_name": "Ethereum", "warning": False},
            {"market": "KRW-XRP", "korean_name": "리플", "english_name": "XRP", "warning": False},
        ]

    try:
        rows = _get_json("/market/all", params={"isDetails": "true"})
    except Exception:
        return []

    markets = []
    for row in rows if isinstance(rows, list) else []:
        market = row.get("market", "")
        if not market.startswith("KRW-"):
            continue
        event = row.get("market_event") or {}
        markets.append(
            {
                "market": market,
                "korean_name": row.get("korean_name"),
                "english_name": row.get("english_name"),
                "warning": bool(event.get("warning")),
            }
        )
    return markets


def get_tickers(markets: list[str], use_mock_data: bool = False) -> list[dict]:
    if use_mock_data:
        mocked = {
            "KRW-BTC": {"market": "KRW-BTC", "trade_price": 151_000_000, "signed_change_rate": 0.018, "acc_trade_price_24h": 750_000_000_000},
            "KRW-ETH": {"market": "KRW-ETH", "trade_price": 5_470_000, "signed_change_rate": 0.011, "acc_trade_price_24h": 310_000_000_000},
            "KRW-XRP": {"market": "KRW-XRP", "trade_price": 3_200, "signed_change_rate": -0.006, "acc_trade_price_24h": 220_000_000_000},
        }
        return [mocked[market] for market in markets if market in mocked]

    results: list[dict] = []
    for batch in _chunked(markets, 100):
        try:
            rows = _get_json("/ticker", params={"markets": ",".join(batch)})
        except Exception:
            continue
        if isinstance(rows, list):
            results.extend(rows)
    return results


def get_krw_ticker_leaders(limit: int = 10, use_mock_data: bool = False) -> list[dict]:
    markets = get_krw_markets(use_mock_data=use_mock_data)
    market_meta = {item["market"]: item for item in markets}
    tickers = get_tickers([item["market"] for item in markets], use_mock_data=use_mock_data)

    leaders = []
    for ticker in tickers:
        market = ticker.get("market")
        meta = market_meta.get(market, {})
        leaders.append(
            {
                "market": market,
                "symbol": (market or "").replace("KRW-", ""),
                "korean_name": meta.get("korean_name"),
                "english_name": meta.get("english_name"),
                "trade_price": ticker.get("trade_price"),
                "signed_change_rate": ticker.get("signed_change_rate"),
                "acc_trade_price_24h": ticker.get("acc_trade_price_24h"),
                "warning": meta.get("warning"),
            }
        )

    return sorted(leaders, key=lambda row: row.get("acc_trade_price_24h") or 0, reverse=True)[:limit]


def get_krw_market_for_symbol(symbol: str, use_mock_data: bool = False) -> dict | None:
    target = f"KRW-{symbol.strip().upper()}"
    markets = get_krw_markets(use_mock_data=use_mock_data)
    for market in markets:
        if market.get("market") == target:
            return market
    return None


def get_daily_candles(market: str, count: int = 90, use_mock_data: bool = False) -> list[dict]:
    if use_mock_data:
        return [
            {
                "candle_date_time_kst": f"2026-05-{index + 1:02d}T00:00:00",
                "trade_price": 150_000_000 + index * 120_000,
                "candle_acc_trade_price": 100_000_000_000 + index * 1_000_000_000,
            }
            for index in range(min(count, 30))
        ]

    try:
        rows = _get_json("/candles/days", params={"market": market, "count": min(count, 200)})
    except Exception:
        return []
    return list(reversed(rows)) if isinstance(rows, list) else []

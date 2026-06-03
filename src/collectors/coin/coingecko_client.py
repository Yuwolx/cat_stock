from __future__ import annotations

import time
from functools import lru_cache
from typing import Any

import requests


BASE_URL = "https://api.coingecko.com/api/v3"
HEADERS = {
    "accept": "application/json",
    "user-agent": "cat-stock/1.0",
}
_STATUS = {"rate_limited": False, "error": None}


class CoinGeckoRateLimitError(RuntimeError):
    pass


def reset_coingecko_status() -> None:
    _STATUS["rate_limited"] = False
    _STATUS["error"] = None


def get_coingecko_status() -> dict:
    return dict(_STATUS)


def _mark_error(error: str, *, rate_limited: bool = False) -> None:
    if rate_limited:
        _STATUS["rate_limited"] = True
    _STATUS["error"] = error


def _get_json(path: str, params: dict[str, Any] | None = None) -> Any:
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            response = requests.get(f"{BASE_URL}{path}", params=params, headers=HEADERS, timeout=6)
            if response.status_code == 429:
                _mark_error("CoinGecko rate limit", rate_limited=True)
                if attempt < 2:
                    retry_after = response.headers.get("retry-after")
                    wait_seconds = min(float(retry_after), 3.0) if retry_after and retry_after.replace(".", "", 1).isdigit() else 1.0
                    time.sleep(wait_seconds)
                    continue
                raise CoinGeckoRateLimitError("CoinGecko rate limit")
            if response.status_code in {408, 500, 502, 503, 504} and attempt < 2:
                retry_after = response.headers.get("retry-after")
                wait_seconds = min(float(retry_after), 2.0) if retry_after and retry_after.replace(".", "", 1).isdigit() else 0.8
                time.sleep(wait_seconds)
                continue
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            last_error = exc
            if isinstance(exc, CoinGeckoRateLimitError):
                raise
            if attempt < 2:
                time.sleep(0.5)
                continue
            _mark_error(str(exc))
            raise
    if last_error:
        raise last_error
    raise RuntimeError("CoinGecko request failed")


def get_global_market_snapshot(use_mock_data: bool = False) -> dict:
    if use_mock_data:
        return {
            "total_market_cap_usd": 2_650_000_000_000,
            "total_volume_usd": 118_000_000_000,
            "market_cap_change_24h_pct": 1.8,
            "btc_dominance": 53.4,
            "eth_dominance": 16.8,
            "active_cryptocurrencies": 13_500,
            "markets": 1_100,
        }

    try:
        data = _get_json("/global").get("data", {})
        return {
            "total_market_cap_usd": (data.get("total_market_cap") or {}).get("usd"),
            "total_volume_usd": (data.get("total_volume") or {}).get("usd"),
            "market_cap_change_24h_pct": data.get("market_cap_change_percentage_24h_usd"),
            "btc_dominance": (data.get("market_cap_percentage") or {}).get("btc"),
            "eth_dominance": (data.get("market_cap_percentage") or {}).get("eth"),
            "active_cryptocurrencies": data.get("active_cryptocurrencies"),
            "markets": data.get("markets"),
        }
    except Exception:
        return {
            "total_market_cap_usd": None,
            "total_volume_usd": None,
            "market_cap_change_24h_pct": None,
            "btc_dominance": None,
            "eth_dominance": None,
            "active_cryptocurrencies": None,
            "markets": None,
        }


def get_coin_markets(
    ids: list[str] | None = None,
    per_page: int = 20,
    use_mock_data: bool = False,
) -> list[dict]:
    if use_mock_data:
        sample = [
            ("bitcoin", "btc", "Bitcoin", 108_500, 2_160_000_000_000, 52_000_000_000, 1, 1.2, 4.8, 8.1),
            ("ethereum", "eth", "Ethereum", 3_950, 476_000_000_000, 28_000_000_000, 2, 0.8, 6.2, 10.4),
            ("solana", "sol", "Solana", 178, 82_000_000_000, 5_800_000_000, 5, 4.1, 12.8, 22.0),
        ]
        rows = [
            {
                "id": row[0],
                "symbol": row[1],
                "name": row[2],
                "current_price": row[3],
                "market_cap": row[4],
                "total_volume": row[5],
                "market_cap_rank": row[6],
                "price_change_percentage_24h": row[7],
                "price_change_percentage_7d_in_currency": row[8],
                "price_change_percentage_30d_in_currency": row[9],
                "fully_diluted_valuation": None,
                "circulating_supply": None,
                "total_supply": None,
                "max_supply": None,
            }
            for row in sample
        ]
        if ids:
            wanted = set(ids)
            rows = [row for row in rows if row["id"] in wanted]
        return rows[:per_page]

    params: dict[str, Any] = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": per_page,
        "page": 1,
        "sparkline": "false",
        "price_change_percentage": "24h,7d,30d",
        "locale": "en",
    }
    if ids:
        params["ids"] = ",".join(ids)

    try:
        rows = _get_json("/coins/markets", params=params)
        if not isinstance(rows, list):
            return []
        return rows
    except Exception:
        return []


def get_category_markets(limit: int = 8, use_mock_data: bool = False) -> list[dict]:
    if use_mock_data:
        return [
            {"name": "Layer 1", "market_cap": 1_900_000_000_000, "market_cap_change_24h": 1.3, "volume_24h": 75_000_000_000},
            {"name": "Decentralized Finance", "market_cap": 120_000_000_000, "market_cap_change_24h": 2.1, "volume_24h": 8_200_000_000},
            {"name": "Meme", "market_cap": 85_000_000_000, "market_cap_change_24h": -1.4, "volume_24h": 12_300_000_000},
            {"name": "Artificial Intelligence", "market_cap": 54_000_000_000, "market_cap_change_24h": 3.8, "volume_24h": 5_100_000_000},
        ][:limit]

    try:
        rows = _get_json("/coins/categories", params={"order": "market_cap_desc"})
        if not isinstance(rows, list):
            return []
        return rows[:limit]
    except Exception:
        return []


def search_coins(query: str, limit: int = 8, use_mock_data: bool = False) -> list[dict]:
    if use_mock_data:
        sample = [
            {"id": "bitcoin", "name": "Bitcoin", "symbol": "BTC", "market_cap_rank": 1},
            {"id": "ethereum", "name": "Ethereum", "symbol": "ETH", "market_cap_rank": 2},
            {"id": "solana", "name": "Solana", "symbol": "SOL", "market_cap_rank": 7},
        ]
        q = query.strip().lower()
        return [row for row in sample if q in row["id"] or q in row["name"].lower() or q == row["symbol"].lower()][:limit]

    try:
        data = _get_json("/search", params={"query": query})
        rows = data.get("coins", []) if isinstance(data, dict) else []
        return rows[:limit] if isinstance(rows, list) else []
    except Exception:
        return []


def _detail_from_market_row(coin_id: str, row: dict) -> dict:
    if not row:
        return {}
    return {
        "id": row.get("id") or coin_id,
        "symbol": row.get("symbol"),
        "name": row.get("name") or coin_id,
        "market_cap_rank": row.get("market_cap_rank"),
        "categories": [],
        "description": {"en": "CoinGecko 상세 데이터가 제한되어 기본 시세 데이터만 표시합니다."},
        "links": {"homepage": [], "whitepaper": "", "repos_url": {"github": []}},
        "market_data": {
            "current_price": {"usd": row.get("current_price")},
            "market_cap": {"usd": row.get("market_cap")},
            "fully_diluted_valuation": {"usd": row.get("fully_diluted_valuation")},
            "total_volume": {"usd": row.get("total_volume")},
            "circulating_supply": row.get("circulating_supply"),
            "total_supply": row.get("total_supply"),
            "max_supply": row.get("max_supply"),
            "ath": {"usd": row.get("ath")},
            "ath_change_percentage": {"usd": row.get("ath_change_percentage")},
            "atl": {"usd": row.get("atl")},
            "price_change_percentage_24h": row.get("price_change_percentage_24h"),
            "price_change_percentage_7d": row.get("price_change_percentage_7d_in_currency"),
            "price_change_percentage_30d": row.get("price_change_percentage_30d_in_currency"),
        },
        "community_data": {},
        "developer_data": {},
    }


def get_coin_detail(coin_id: str, use_mock_data: bool = False) -> dict:
    if use_mock_data:
        return {
            "id": coin_id,
            "symbol": "btc" if coin_id == "bitcoin" else "sol",
            "name": "Bitcoin" if coin_id == "bitcoin" else "Solana",
            "market_cap_rank": 1 if coin_id == "bitcoin" else 7,
            "categories": ["Layer 1 (L1)", "Smart Contract Platform"],
            "description": {"en": "A major crypto asset used as a benchmark for market learning."},
            "links": {"homepage": ["https://example.com"], "whitepaper": "", "repos_url": {"github": []}},
            "market_data": {
                "current_price": {"usd": 108_500, "krw": 151_000_000},
                "market_cap": {"usd": 2_160_000_000_000},
                "fully_diluted_valuation": {"usd": 2_160_000_000_000},
                "total_volume": {"usd": 52_000_000_000},
                "circulating_supply": 19_900_000,
                "total_supply": 19_900_000,
                "max_supply": 21_000_000,
                "ath": {"usd": 112_000},
                "ath_change_percentage": {"usd": -3.2},
                "atl": {"usd": 67.81},
                "price_change_percentage_24h": 1.2,
                "price_change_percentage_7d": 4.8,
                "price_change_percentage_30d": 8.1,
            },
            "community_data": {"twitter_followers": None, "reddit_subscribers": None},
            "developer_data": {"stars": None, "forks": None, "commit_count_4_weeks": None},
        }

    try:
        return dict(_get_coin_detail_live(coin_id))
    except Exception:
        rows = get_coin_markets([coin_id], per_page=1, use_mock_data=use_mock_data)
        return _detail_from_market_row(coin_id, rows[0] if rows else {})


@lru_cache(maxsize=128)
def _get_coin_detail_live(coin_id: str) -> tuple[tuple[str, Any], ...]:
    data = _get_json(
        f"/coins/{coin_id}",
        params={
            "localization": "false",
            "tickers": "false",
            "market_data": "true",
            "community_data": "true",
            "developer_data": "true",
            "sparkline": "false",
        },
    )
    return tuple(data.items()) if isinstance(data, dict) else tuple()


def get_coin_market_chart(coin_id: str, days: int = 30, use_mock_data: bool = False) -> dict:
    if use_mock_data:
        base = 100_000 if coin_id == "bitcoin" else 4_000 if coin_id == "ethereum" else 180
        prices = [[index, base * (1 + (index - days / 2) * 0.004)] for index in range(days)]
        volumes = [[index, 20_000_000_000 * (1 + (index % 7) * 0.08)] for index in range(days)]
        market_caps = [[index, base * 20_000_000 * (1 + (index - days / 2) * 0.003)] for index in range(days)]
        return {"prices": prices, "market_caps": market_caps, "total_volumes": volumes}

    try:
        return dict(_get_coin_market_chart_live(coin_id, days))
    except Exception:
        return {"prices": [], "market_caps": [], "total_volumes": []}


@lru_cache(maxsize=64)
def _get_coin_market_chart_live(coin_id: str, days: int) -> tuple[tuple[str, tuple[tuple[float, float], ...]], ...]:
    params = {
        "vs_currency": "usd",
        "days": str(days),
    }
    if days >= 30:
        params["interval"] = "daily"
    data = _get_json(f"/coins/{coin_id}/market_chart", params=params)
    if not isinstance(data, dict):
        return (("prices", tuple()), ("market_caps", tuple()), ("total_volumes", tuple()))
    result = []
    for key in ("prices", "market_caps", "total_volumes"):
        rows = []
        for row in data.get(key, []):
            if isinstance(row, (list, tuple)) and len(row) >= 2:
                rows.append((row[0], row[1]))
        result.append((key, tuple(rows)))
    return tuple(result)

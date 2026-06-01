from __future__ import annotations

from functools import lru_cache
from typing import Any

import requests


API_BASE_URL = "https://api.llama.fi"
STABLECOIN_BASE_URL = "https://stablecoins.llama.fi"
HEADERS = {
    "accept": "application/json",
    "user-agent": "cat-stock/1.0",
}


def _get_json(base_url: str, path: str, params: dict[str, Any] | None = None) -> Any:
    response = requests.get(f"{base_url}{path}", params=params, headers=HEADERS, timeout=12)
    response.raise_for_status()
    return response.json()


def _parse_usd(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).replace(",", ""))
    except ValueError:
        return None


@lru_cache(maxsize=1)
def _get_protocols_live() -> tuple[dict, ...]:
    data = _get_json(API_BASE_URL, "/protocols")
    return tuple(data) if isinstance(data, list) else tuple()


@lru_cache(maxsize=1)
def _get_fees_live() -> dict:
    data = _get_json(
        API_BASE_URL,
        "/overview/fees",
        params={"excludeTotalDataChart": "true", "excludeTotalDataChartBreakdown": "true"},
    )
    return data if isinstance(data, dict) else {}


@lru_cache(maxsize=1)
def _get_open_interest_live() -> dict:
    data = _get_json(
        API_BASE_URL,
        "/overview/open-interest",
        params={"excludeTotalDataChart": "true", "excludeTotalDataChartBreakdown": "true"},
    )
    return data if isinstance(data, dict) else {}


@lru_cache(maxsize=1)
def _get_stablecoins_live() -> dict:
    data = _get_json(STABLECOIN_BASE_URL, "/stablecoins")
    return data if isinstance(data, dict) else {}


@lru_cache(maxsize=1)
def _get_stablecoin_chains_live() -> tuple[dict, ...]:
    data = _get_json(STABLECOIN_BASE_URL, "/stablecoinchains")
    return tuple(data) if isinstance(data, list) else tuple()


def get_protocols(use_mock_data: bool = False) -> list[dict]:
    if use_mock_data:
        return [
            {
                "name": "Aave",
                "slug": "aave",
                "symbol": "AAVE",
                "category": "Lending",
                "chains": ["Ethereum", "Arbitrum"],
                "gecko_id": "aave",
                "tvl": 21_500_000_000,
                "change_1d": 1.8,
                "change_7d": 5.3,
            },
            {
                "name": "Uniswap",
                "slug": "uniswap",
                "symbol": "UNI",
                "category": "Dexes",
                "chains": ["Ethereum", "Base"],
                "gecko_id": "uniswap",
                "tvl": 6_400_000_000,
                "change_1d": -0.4,
                "change_7d": 2.1,
            },
        ]

    try:
        data = _get_protocols_live()
    except Exception:
        return []
    return [dict(row) for row in data]


def get_top_protocols(limit: int = 10, use_mock_data: bool = False) -> list[dict]:
    rows = [
        {
            "name": item.get("name"),
            "slug": item.get("slug"),
            "symbol": item.get("symbol"),
            "category": item.get("category"),
            "chains": item.get("chains") or [],
            "gecko_id": item.get("gecko_id"),
            "tvl": _parse_usd(item.get("tvl")),
            "change_1d": item.get("change_1d"),
            "change_7d": item.get("change_7d"),
        }
        for item in get_protocols(use_mock_data=use_mock_data)
        if item.get("tvl") and item.get("category") != "CEX"
    ]
    return sorted(rows, key=lambda row: row.get("tvl") or 0, reverse=True)[:limit]


def find_protocol_for_coin(coin_id: str, symbol: str = "", name: str = "", use_mock_data: bool = False) -> dict | None:
    coin_id_l = coin_id.strip().lower()
    symbol_l = symbol.strip().lower()
    name_l = name.strip().lower()
    candidates = []

    for item in get_protocols(use_mock_data=use_mock_data):
        gecko_id = str(item.get("gecko_id") or "").lower()
        item_symbol = str(item.get("symbol") or "").lower()
        item_name = str(item.get("name") or "").lower()
        if gecko_id and gecko_id == coin_id_l:
            candidates.append(item)
        elif symbol_l and item_symbol == symbol_l and item_name == name_l:
            candidates.append(item)

    if not candidates:
        return None

    selected = sorted(candidates, key=lambda row: row.get("tvl") or 0, reverse=True)[0]
    return {
        "name": selected.get("name"),
        "slug": selected.get("slug"),
        "symbol": selected.get("symbol"),
        "category": selected.get("category"),
        "chains": selected.get("chains") or [],
        "tvl": _parse_usd(selected.get("tvl")),
        "change_1d": selected.get("change_1d"),
        "change_7d": selected.get("change_7d"),
        "url": selected.get("url"),
        "description": selected.get("description"),
    }


def get_fees_overview(limit: int = 8, use_mock_data: bool = False) -> dict:
    if use_mock_data:
        return {
            "total24h": 42_000_000,
            "total7d": 290_000_000,
            "change_1d": 4.2,
            "protocols": [
                {"name": "Uniswap", "category": "Dexes", "total24h": 5_800_000, "total7d": 40_000_000},
                {"name": "Aave", "category": "Lending", "total24h": 2_100_000, "total7d": 15_000_000},
            ],
        }

    try:
        data = _get_fees_live()
    except Exception:
        return {"total24h": None, "total7d": None, "change_1d": None, "protocols": []}

    protocols = [
        {
            "name": item.get("displayName") or item.get("name"),
            "slug": item.get("slug"),
            "category": item.get("category"),
            "chains": item.get("chains") or [],
            "total24h": _parse_usd(item.get("total24h")),
            "total7d": _parse_usd(item.get("total7d")),
            "change_1d": item.get("change_1d"),
        }
        for item in data.get("protocols", [])
        if item.get("total24h")
    ]
    protocols = sorted(protocols, key=lambda row: row.get("total24h") or 0, reverse=True)[:limit]
    return {
        "total24h": _parse_usd(data.get("total24h")),
        "total7d": _parse_usd(data.get("total7d")),
        "change_1d": data.get("change_1d"),
        "protocols": protocols,
    }


def get_open_interest_overview(limit: int = 6, use_mock_data: bool = False) -> dict:
    if use_mock_data:
        return {
            "total24h": 18_000_000_000,
            "total7d": 120_000_000_000,
            "protocols": [
                {"name": "Hyperliquid", "category": "Derivatives", "total24h": 9_000_000_000},
                {"name": "dYdX", "category": "Derivatives", "total24h": 1_700_000_000},
            ],
        }

    try:
        data = _get_open_interest_live()
    except Exception:
        return {"total24h": None, "total7d": None, "protocols": []}

    protocols = [
        {
            "name": item.get("displayName") or item.get("name"),
            "slug": item.get("slug"),
            "category": item.get("category"),
            "chains": item.get("chains") or [],
            "total24h": _parse_usd(item.get("total24h")),
            "total7d": _parse_usd(item.get("total7d")),
        }
        for item in data.get("protocols", [])
        if item.get("total24h")
    ]
    protocols = sorted(protocols, key=lambda row: row.get("total24h") or 0, reverse=True)[:limit]
    return {
        "total24h": _parse_usd(data.get("total24h")),
        "total7d": _parse_usd(data.get("total7d")),
        "protocols": protocols,
    }


def get_stablecoin_snapshot(limit: int = 8, use_mock_data: bool = False) -> dict:
    if use_mock_data:
        return {
            "total_circulating_usd": 165_000_000_000,
            "change_1d_pct": 0.2,
            "change_7d_pct": 1.1,
            "change_30d_pct": 3.7,
            "top_assets": [
                {"name": "Tether", "symbol": "USDT", "circulating_usd": 112_000_000_000, "change_7d_pct": 0.8},
                {"name": "USD Coin", "symbol": "USDC", "circulating_usd": 38_000_000_000, "change_7d_pct": 2.0},
            ],
            "top_chains": [
                {"name": "Ethereum", "circulating_usd": 82_000_000_000},
                {"name": "Tron", "circulating_usd": 55_000_000_000},
            ],
        }

    try:
        data = _get_stablecoins_live()
        chains = _get_stablecoin_chains_live()
    except Exception:
        return {
            "total_circulating_usd": None,
            "change_1d_pct": None,
            "change_7d_pct": None,
            "change_30d_pct": None,
            "top_assets": [],
            "top_chains": [],
        }

    assets = data.get("peggedAssets", []) if isinstance(data, dict) else []
    normalized_assets = []
    total = 0.0
    prev_day = 0.0
    prev_week = 0.0
    prev_month = 0.0

    for item in assets:
        current = _parse_usd((item.get("circulating") or {}).get("peggedUSD")) or 0
        day = _parse_usd((item.get("circulatingPrevDay") or {}).get("peggedUSD")) or 0
        week = _parse_usd((item.get("circulatingPrevWeek") or {}).get("peggedUSD")) or 0
        month = _parse_usd((item.get("circulatingPrevMonth") or {}).get("peggedUSD")) or 0
        total += current
        prev_day += day
        prev_week += week
        prev_month += month
        normalized_assets.append(
            {
                "name": item.get("name"),
                "symbol": item.get("symbol"),
                "circulating_usd": current,
                "change_1d_pct": ((current / day) - 1) * 100 if day else None,
                "change_7d_pct": ((current / week) - 1) * 100 if week else None,
                "change_30d_pct": ((current / month) - 1) * 100 if month else None,
            }
        )

    top_chains = [
        {"name": item.get("name"), "circulating_usd": _parse_usd((item.get("totalCirculatingUSD") or {}).get("peggedUSD"))}
        for item in chains
        if item.get("totalCirculatingUSD")
    ]

    return {
        "total_circulating_usd": total or None,
        "change_1d_pct": ((total / prev_day) - 1) * 100 if prev_day else None,
        "change_7d_pct": ((total / prev_week) - 1) * 100 if prev_week else None,
        "change_30d_pct": ((total / prev_month) - 1) * 100 if prev_month else None,
        "top_assets": sorted(normalized_assets, key=lambda row: row.get("circulating_usd") or 0, reverse=True)[:limit],
        "top_chains": sorted(top_chains, key=lambda row: row.get("circulating_usd") or 0, reverse=True)[:limit],
    }

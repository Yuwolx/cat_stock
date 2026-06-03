from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from src.collectors.coin.alternative_client import get_fear_greed_index
from src.collectors.coin.coingecko_client import (
    get_coingecko_status,
    get_category_markets,
    get_coin_market_chart,
    get_coin_markets,
    get_global_market_snapshot,
    reset_coingecko_status,
)
from src.collectors.coin.defillama_client import (
    get_fees_overview,
    get_stablecoin_snapshot,
    get_top_protocols,
)
from src.collectors.coin.upbit_client import get_krw_ticker_leaders, get_tickers
from src.collectors.market.global_collector import get_global_macro_snapshot
from src.formatters.coin_market_formatter import format_coin_market_briefing
from src.utils.date_utils import KST, today_kst_string
from src.utils.file_utils import save_output_text


def _parse_number(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    cleaned = re.sub(r"[^0-9.\-]", "", str(value))
    if not cleaned or cleaned in {".", "-", "-."}:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _normalize_upbit_change(rows: list[dict]) -> list[dict]:
    normalized = []
    for row in rows:
        item = dict(row)
        rate = item.get("signed_change_rate")
        item["change_pct"] = float(rate) * 100 if rate is not None else None
        normalized.append(item)
    return normalized


def _calculate_kimchi_premium(
    btc_krw: float | None,
    btc_usd: float | None,
    usdkrw: float | None,
) -> float | None:
    if not btc_krw or not btc_usd or not usdkrw:
        return None
    global_krw_price = btc_usd * usdkrw
    if global_krw_price <= 0:
        return None
    return ((btc_krw / global_krw_price) - 1) * 100


def _latest_series_value(rows: list) -> float | None:
    if not rows:
        return None
    last = rows[-1]
    if isinstance(last, (list, tuple)) and len(last) >= 2:
        return _parse_number(last[1])
    return None


def _future_result(futures: dict[str, object], key: str, default: object) -> object:
    try:
        return futures[key].result()
    except Exception:
        return default


def _market_regime(payload: dict) -> dict:
    global_market = payload.get("global_market", {})
    majors = payload.get("majors", {})
    fear_greed = payload.get("fear_greed", {})

    btc_24h = _parse_number((majors.get("bitcoin") or {}).get("price_change_percentage_24h"))
    eth_24h = _parse_number((majors.get("ethereum") or {}).get("price_change_percentage_24h"))
    market_24h = _parse_number(global_market.get("market_cap_change_24h_pct"))
    fear_value = _parse_number(fear_greed.get("value"))
    kimchi = _parse_number(payload.get("kimchi_premium_pct"))

    if kimchi is not None and kimchi >= 3:
        return {
            "label": "한국 과열 관찰",
            "tone": "warn",
            "message": "국내 거래소 가격이 글로벌보다 비싸게 거래되는지 확인해야 합니다.",
        }
    if (btc_24h is not None and btc_24h < -1) and (eth_24h is not None and eth_24h < -1):
        return {
            "label": "위험 회피",
            "tone": "risk",
            "message": "기준 자산이 같이 약합니다. 알트 추격보다 방어력을 먼저 봅니다.",
        }
    if (market_24h is not None and market_24h > 0) and (btc_24h is not None and btc_24h > 0) and (fear_value is None or fear_value >= 35):
        return {
            "label": "위험 선호",
            "tone": "good",
            "message": "시장 전체와 BTC가 함께 강합니다. 섹터 확산 여부를 봅니다.",
        }
    return {
        "label": "관망",
        "tone": "neutral",
        "message": "지표가 엇갈립니다. BTC/ETH와 거래대금 방향을 먼저 확인합니다.",
    }


def generate_coin_market_report(use_mock_data: bool = False) -> dict:
    reset_coingecko_status()
    target_date = today_kst_string()
    target_datetime = datetime.now(KST).strftime("%Y-%m-%d %H:%M KST")

    with ThreadPoolExecutor(max_workers=9) as executor:
        futures = {
            "global_market": executor.submit(get_global_market_snapshot, use_mock_data=use_mock_data),
            "top_coins": executor.submit(get_coin_markets, per_page=20, use_mock_data=use_mock_data),
            "categories": executor.submit(get_category_markets, limit=8, use_mock_data=use_mock_data),
            "fear_greed": executor.submit(get_fear_greed_index, use_mock_data=use_mock_data),
            "upbit_leaders": executor.submit(get_krw_ticker_leaders, limit=10, use_mock_data=use_mock_data),
            "btc_ticker": executor.submit(get_tickers, ["KRW-BTC"], use_mock_data=use_mock_data),
            "btc_chart": executor.submit(get_coin_market_chart, "bitcoin", days=30, use_mock_data=use_mock_data),
            "eth_chart": executor.submit(get_coin_market_chart, "ethereum", days=30, use_mock_data=use_mock_data),
            "stablecoins": executor.submit(get_stablecoin_snapshot, limit=6, use_mock_data=use_mock_data),
            "top_protocols": executor.submit(get_top_protocols, limit=8, use_mock_data=use_mock_data),
            "fees": executor.submit(get_fees_overview, limit=6, use_mock_data=use_mock_data),
            "macro": executor.submit(get_global_macro_snapshot, target_date, use_mock_data=use_mock_data),
        }

    global_market = _future_result(futures, "global_market", {})
    top_coins = _future_result(futures, "top_coins", [])
    major_rows = [row for row in top_coins if row.get("id") in {"bitcoin", "ethereum"}]
    if len(major_rows) < 2:
        major_rows = get_coin_markets(["bitcoin", "ethereum"], per_page=2, use_mock_data=use_mock_data)
    categories = _future_result(futures, "categories", [])
    fear_greed = _future_result(futures, "fear_greed", {})
    upbit_leaders = _normalize_upbit_change(_future_result(futures, "upbit_leaders", []))
    charts = {
        "bitcoin": _future_result(futures, "btc_chart", {"prices": [], "market_caps": [], "total_volumes": []}),
        "ethereum": _future_result(futures, "eth_chart", {"prices": [], "market_caps": [], "total_volumes": []}),
    }

    stablecoins = _future_result(futures, "stablecoins", {})
    top_protocols = _future_result(futures, "top_protocols", [])
    fees = _future_result(futures, "fees", {})

    btc_ticker = _future_result(futures, "btc_ticker", [])
    btc_krw = _parse_number((btc_ticker[0] if btc_ticker else {}).get("trade_price"))
    majors = {row.get("id"): row for row in major_rows}
    btc_usd = _parse_number((majors.get("bitcoin") or {}).get("current_price"))
    eth_usd = _parse_number((majors.get("ethereum") or {}).get("current_price"))

    macro = _future_result(futures, "macro", {})
    usdkrw = _parse_number(macro.get("usdkrw"))
    kimchi_premium_pct = _calculate_kimchi_premium(btc_krw, btc_usd, usdkrw)

    payload = {
        "target_date": target_date,
        "target_datetime": target_datetime,
        "is_mock_data": use_mock_data,
        "global_market": global_market,
        "majors": majors,
        "top_coins": top_coins,
        "categories": categories,
        "fear_greed": fear_greed,
        "upbit_leaders": upbit_leaders,
        "charts": charts,
        "stablecoins": stablecoins,
        "top_protocols": top_protocols,
        "fees": fees,
        "eth_btc_ratio": eth_usd / btc_usd if eth_usd and btc_usd else None,
        "btc_30d_volume_latest": _latest_series_value((charts.get("bitcoin") or {}).get("total_volumes") or []),
        "usdkrw": macro.get("usdkrw"),
        "kimchi_premium_pct": kimchi_premium_pct,
    }
    coingecko_status = get_coingecko_status()
    payload["source_status"] = {"coingecko": coingecko_status}
    payload["data_warnings"] = (
        ["CoinGecko rate limit으로 일부 데이터가 비었을 수 있습니다."] if coingecko_status.get("rate_limited") else []
    )
    payload["regime"] = _market_regime(payload)

    text = format_coin_market_briefing(payload)
    path = save_output_text("coin_market", target_date, text)
    return {"text": text, "path": path, "payload": payload}

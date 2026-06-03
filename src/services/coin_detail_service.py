from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from src.collectors.coin.binance_futures_client import get_futures_risk
from src.collectors.coin.coingecko_client import (
    get_coingecko_status,
    get_coin_detail,
    get_coin_market_chart,
    reset_coingecko_status,
    search_coins,
)
from src.collectors.coin.defillama_client import find_protocol_for_coin
from src.collectors.coin.upbit_client import get_daily_candles, get_krw_market_for_symbol, get_tickers
from src.collectors.market.global_collector import get_global_macro_snapshot
from src.formatters.coin_detail_formatter import format_coin_detail_report
from src.services.coin_market_service import _calculate_kimchi_premium, _parse_number
from src.utils.date_utils import KST, today_kst_string
from src.utils.file_utils import save_output_text


COIN_ALIASES = {
    "비트코인": "bitcoin",
    "btc": "bitcoin",
    "bitcoin": "bitcoin",
    "이더리움": "ethereum",
    "eth": "ethereum",
    "ethereum": "ethereum",
    "솔라나": "solana",
    "sol": "solana",
    "solana": "solana",
    "리플": "ripple",
    "엑스알피": "ripple",
    "xrp": "ripple",
    "도지": "dogecoin",
    "도지코인": "dogecoin",
    "doge": "dogecoin",
    "체인링크": "chainlink",
    "link": "chainlink",
    "온도": "ondo-finance",
    "ondo": "ondo-finance",
    "월드코인": "worldcoin-wld",
    "wld": "worldcoin-wld",
}

COIN_SYMBOLS = {
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "solana": "SOL",
    "ripple": "XRP",
    "dogecoin": "DOGE",
    "chainlink": "LINK",
    "ondo-finance": "ONDO",
    "worldcoin-wld": "WLD",
}

COIN_NAMES = {
    "bitcoin": "Bitcoin",
    "ethereum": "Ethereum",
    "solana": "Solana",
    "ripple": "XRP",
    "dogecoin": "Dogecoin",
    "chainlink": "Chainlink",
    "ondo-finance": "Ondo",
    "worldcoin-wld": "Worldcoin",
}


def _strip_html(value: str | None) -> str:
    if not value:
        return ""
    without_tags = re.sub(r"<[^>]+>", " ", value)
    collapsed = re.sub(r"\s+", " ", without_tags).strip()
    return collapsed[:600]


def _ratio(numerator: float | None, denominator: float | None) -> str | None:
    if numerator is None or denominator is None or denominator == 0:
        return None
    return f"{numerator / denominator:.2f}x"


def _ratio_number(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None or denominator == 0:
        return None
    return numerator / denominator


def _build_risk_flags(
    fdv_to_mcap: float | None,
    volume_to_mcap: float | None,
    kimchi_premium_pct: float | None,
    futures: dict,
    upbit_warning: bool,
) -> list[dict]:
    flags: list[dict] = []
    if fdv_to_mcap is not None and fdv_to_mcap >= 2:
        flags.append(
            {
                "label": "희석 위험",
                "level": "warn",
                "message": "FDV가 시총보다 큽니다. 앞으로 풀릴 물량과 언락 일정을 확인합니다.",
            }
        )
    if volume_to_mcap is not None and volume_to_mcap >= 0.2:
        flags.append(
            {
                "label": "거래량 과열",
                "level": "warn",
                "message": "시총 대비 거래량이 큽니다. 단기 회전율과 급락 리스크를 봅니다.",
            }
        )
    if kimchi_premium_pct is not None and abs(kimchi_premium_pct) >= 3:
        flags.append(
            {
                "label": "국내 가격 괴리",
                "level": "warn",
                "message": "업비트 가격이 글로벌 가격과 벌어졌습니다. 국내 수급만 따라가지 않도록 봅니다.",
            }
        )
    if futures.get("is_available") and futures.get("warning") not in {None, "보통"}:
        flags.append(
            {
                "label": "파생상품 쏠림",
                "level": "warn",
                "message": f"{futures.get('warning')} 상태입니다. 펀딩비와 OI 변화를 같이 봅니다.",
            }
        )
    if upbit_warning:
        flags.append(
            {
                "label": "거래소 유의",
                "level": "risk",
                "message": "업비트 유의/주의 플래그가 있습니다. 공지와 상장 상태를 확인합니다.",
            }
        )
    if not flags:
        flags.append(
            {
                "label": "큰 경고 없음",
                "level": "ok",
                "message": "연결된 지표 기준으로 즉시 보이는 과열 신호는 약합니다. 그래도 뉴스와 온체인 지표는 별도로 봅니다.",
            }
        )
    return flags


def _minimal_detail(coin_id: str, query: str, candidates: list[dict]) -> dict:
    candidate = candidates[0] if candidates else {}
    symbol = COIN_SYMBOLS.get(coin_id) or str(candidate.get("symbol") or query).upper()
    name = COIN_NAMES.get(coin_id) or candidate.get("name") or query or coin_id
    return {
        "id": coin_id,
        "symbol": symbol,
        "name": name,
        "market_cap_rank": candidate.get("market_cap_rank"),
        "categories": [],
        "description": {"en": "CoinGecko 상세 데이터가 제한되어 대체 가능한 시세와 위험 지표 위주로 표시합니다."},
        "links": {"homepage": [], "whitepaper": "", "repos_url": {"github": []}},
        "market_data": {
            "current_price": {},
            "market_cap": {},
            "fully_diluted_valuation": {},
            "total_volume": {},
            "ath": {},
            "ath_change_percentage": {},
            "atl": {},
        },
        "community_data": {},
        "developer_data": {},
    }


def _future_result(futures: dict[str, object], key: str, default: object) -> object:
    try:
        return futures[key].result()
    except Exception:
        return default


def _chart_from_upbit_candles(candles: list[dict], usdkrw: float | None) -> dict:
    if not candles or not usdkrw:
        return {"prices": [], "market_caps": [], "total_volumes": []}
    prices = []
    volumes = []
    for index, row in enumerate(candles):
        price = _parse_number(row.get("trade_price"))
        volume = _parse_number(row.get("candle_acc_trade_price"))
        if price is not None:
            prices.append([index, price / usdkrw])
        if volume is not None:
            volumes.append([index, volume / usdkrw])
    return {"prices": prices, "market_caps": [], "total_volumes": volumes}


def resolve_coin_id(query: str, use_mock_data: bool = False) -> dict:
    normalized = query.strip().lower()
    if not normalized:
        return {"coin_id": None, "candidates": []}

    alias_id = COIN_ALIASES.get(normalized)
    if alias_id:
        return {"coin_id": alias_id, "candidates": [{"id": alias_id, "name": query.strip(), "symbol": normalized.upper()}]}

    candidates = search_coins(query, limit=8, use_mock_data=use_mock_data)
    if not candidates:
        return {"coin_id": normalized, "candidates": []}

    exact = None
    for item in candidates:
        if normalized in {str(item.get("id", "")).lower(), str(item.get("symbol", "")).lower(), str(item.get("name", "")).lower()}:
            exact = item
            break
    selected = exact or candidates[0]
    return {"coin_id": selected.get("id"), "candidates": candidates}


def generate_coin_detail_report(query: str, use_mock_data: bool = False) -> dict:
    reset_coingecko_status()
    target_date = today_kst_string()
    target_datetime = datetime.now(KST).strftime("%Y-%m-%d %H:%M KST")
    resolved = resolve_coin_id(query, use_mock_data=use_mock_data)
    coin_id = resolved.get("coin_id")
    if not coin_id:
        return {"error": "코인명을 입력해주세요.", "candidates": [], "text": "", "payload": {}}

    detail = get_coin_detail(coin_id, use_mock_data=use_mock_data)
    if not detail:
        detail = _minimal_detail(coin_id, query, resolved.get("candidates", []))

    market_data = detail.get("market_data") or {}
    symbol = str(detail.get("symbol") or "").upper()
    current_price_usd = _parse_number((market_data.get("current_price") or {}).get("usd"))
    market_cap_usd = _parse_number((market_data.get("market_cap") or {}).get("usd"))
    fdv_usd = _parse_number((market_data.get("fully_diluted_valuation") or {}).get("usd"))
    volume_usd = _parse_number((market_data.get("total_volume") or {}).get("usd"))

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            "upbit_market": executor.submit(get_krw_market_for_symbol, symbol, use_mock_data=use_mock_data),
            "macro": executor.submit(get_global_macro_snapshot, target_date, use_mock_data=use_mock_data),
            "price_chart": executor.submit(get_coin_market_chart, coin_id, days=90, use_mock_data=use_mock_data),
            "defi_protocol": executor.submit(
                find_protocol_for_coin,
                coin_id,
                symbol=symbol,
                name=str(detail.get("name") or ""),
                use_mock_data=use_mock_data,
            ),
            "futures": executor.submit(get_futures_risk, symbol, use_mock_data=use_mock_data),
        }

    upbit_market = _future_result(futures, "upbit_market", None)
    ticker = {}
    if upbit_market:
        rows = get_tickers([upbit_market["market"]], use_mock_data=use_mock_data)
        ticker = rows[0] if rows else {}

    macro = _future_result(futures, "macro", {})
    usdkrw = _parse_number(macro.get("usdkrw"))
    upbit_price = _parse_number(ticker.get("trade_price"))
    upbit_change_rate = ticker.get("signed_change_rate")
    upbit_change_pct = float(upbit_change_rate) * 100 if upbit_change_rate is not None else None
    description = _strip_html((detail.get("description") or {}).get("en"))
    price_chart = _future_result(futures, "price_chart", {"prices": [], "market_caps": [], "total_volumes": []})
    defi_protocol = _future_result(futures, "defi_protocol", None)
    futures_risk = _future_result(futures, "futures", {}) if symbol else {}
    if current_price_usd is None:
        current_price_usd = _parse_number(futures_risk.get("mark_price_usd"))
    kimchi_premium_pct = _calculate_kimchi_premium(upbit_price, current_price_usd, usdkrw)
    if not price_chart.get("prices") and upbit_market:
        price_chart = _chart_from_upbit_candles(
            get_daily_candles(upbit_market["market"], count=90, use_mock_data=use_mock_data),
            usdkrw,
        )
    fdv_to_mcap_number = _ratio_number(fdv_usd, market_cap_usd)
    volume_to_mcap_number = _ratio_number(volume_usd, market_cap_usd)

    payload = {
        "target_date": target_date,
        "target_datetime": target_datetime,
        "query": query,
        "candidates": resolved.get("candidates", []),
        "basics": {
            "id": detail.get("id"),
            "name": detail.get("name"),
            "symbol": symbol,
            "market_cap_rank": detail.get("market_cap_rank"),
            "image": (detail.get("image") or {}).get("large"),
        },
        "market": {
            "current_price_usd": current_price_usd,
            "current_price_krw": _parse_number((market_data.get("current_price") or {}).get("krw")) or upbit_price,
            "market_cap_usd": market_cap_usd,
            "fdv_usd": fdv_usd,
            "volume_usd": volume_usd,
            "change_24h_pct": market_data.get("price_change_percentage_24h"),
            "change_7d_pct": market_data.get("price_change_percentage_7d"),
            "change_30d_pct": market_data.get("price_change_percentage_30d"),
            "ath_usd": (market_data.get("ath") or {}).get("usd"),
            "ath_change_pct": (market_data.get("ath_change_percentage") or {}).get("usd"),
            "atl_usd": (market_data.get("atl") or {}).get("usd"),
        },
        "supply": {
            "circulating_supply": market_data.get("circulating_supply"),
            "total_supply": market_data.get("total_supply"),
            "max_supply": market_data.get("max_supply"),
        },
        "upbit": {
            "is_listed": bool(upbit_market),
            "market": (upbit_market or {}).get("market"),
            "korean_name": (upbit_market or {}).get("korean_name"),
            "warning": (upbit_market or {}).get("warning"),
            "trade_price": upbit_price,
            "change_pct": upbit_change_pct,
            "acc_trade_price_24h": ticker.get("acc_trade_price_24h"),
            "kimchi_premium_pct": kimchi_premium_pct,
        },
        "risk": {
            "fdv_to_mcap": _ratio(fdv_usd, market_cap_usd),
            "volume_to_mcap": _ratio(volume_usd, market_cap_usd),
            "fdv_to_mcap_number": fdv_to_mcap_number,
            "volume_to_mcap_number": volume_to_mcap_number,
        },
        "risk_flags": _build_risk_flags(
            fdv_to_mcap_number,
            volume_to_mcap_number,
            kimchi_premium_pct,
            futures_risk,
            bool((upbit_market or {}).get("warning")),
        ),
        "price_chart": price_chart,
        "defi_protocol": defi_protocol or {},
        "futures": futures_risk,
        "project": {
            "categories": detail.get("categories") or [],
            "description": description,
            "homepage": next((url for url in (detail.get("links") or {}).get("homepage", []) if url), ""),
            "whitepaper": (detail.get("links") or {}).get("whitepaper") or "",
            "twitter": (detail.get("links") or {}).get("twitter_screen_name") or "",
        },
        "community": detail.get("community_data") or {},
        "developer": detail.get("developer_data") or {},
        "usdkrw": macro.get("usdkrw"),
    }
    coingecko_status = get_coingecko_status()
    payload["source_status"] = {"coingecko": coingecko_status}
    payload["data_warnings"] = (
        ["CoinGecko rate limit으로 일부 데이터가 비었을 수 있습니다."] if coingecko_status.get("rate_limited") else []
    )

    text = format_coin_detail_report(payload)
    path = save_output_text(f"coin_{payload['basics']['id']}", target_date, text)
    return {"text": text, "path": path, "payload": payload, "error": None}

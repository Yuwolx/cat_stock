from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from src.collectors.market.global_collector import get_global_macro_snapshot, get_korean_index_trend
from src.collectors.market.krx_collector import (
    get_derivatives_snapshot,
    get_investor_flows,
    get_market_indices,
)
from src.collectors.market.naver_market_collector import (
    get_market_event_lists,
    get_market_news,
    get_market_reports,
    get_sector_changes,
    get_trading_value_leaders,
)
from src.formatters.market_formatter import format_market_briefing
from src.services.column_service import generate_market_column
from src.utils.date_utils import resolve_stock_trading_date
from src.utils.file_utils import save_output_text
from src.utils.report_store import is_finalized_date, load_payload, save_payload
from src.utils.ttl_cache import get_ttl_cache, set_ttl_cache


def _empty_indices() -> dict:
    return {
        "kospi": {"close": None, "change_pct": None, "turnover_trillion_krw": None, "change_points": None},
        "kosdaq": {"close": None, "change_pct": None, "turnover_trillion_krw": None, "change_points": None},
    }


def _empty_investor_flows() -> dict:
    return {
        "summary": {"foreign": None, "institution": None, "retail": None},
        "by_market": {
            "kospi": {"foreign": None, "institution": None, "retail": None},
            "kosdaq": {"foreign": None, "institution": None, "retail": None},
        },
        "foreign_top_buy": [],
        "foreign_top_sell": [],
        "institution_top_buy": [],
        "institution_top_sell": [],
    }


def _empty_derivatives() -> dict:
    return {
        "futures_foreign_net": None,
        "futures_institution_net": None,
        "futures_contract_code": None,
        "futures_warning": None,
        "program_arbitrage": None,
        "program_non_arbitrage": None,
        "program_total": None,
        "program_by_market": {
            "kospi": {"arbitrage": None, "non_arbitrage": None, "total": None},
            "kosdaq": {"arbitrage": None, "non_arbitrage": None, "total": None},
        },
    }


def _empty_market_events() -> dict:
    return {
        "new_highs": [],
        "new_lows": [],
        "upper_limit": [],
        "after_hours_movers": [],
        "rising_over_5pct": [],
    }


def _is_empty_data(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, (list, tuple, set)):
        return len(value) == 0
    if isinstance(value, dict):
        if not value:
            return True
        return all(_is_empty_data(item) for item in value.values())
    return False


def _resolve_collector(futures: dict[str, object], key: str, default: object) -> tuple[object, dict]:
    try:
        data = futures[key].result()
    except Exception as exc:
        return default, {"status": "error", "error": str(exc)}

    if _is_empty_data(data):
        return data, {"status": "empty", "error": None}
    return data, {"status": "ok", "error": None}


def generate_market_briefing(target_date: str, use_mock_data: bool = False) -> dict:
    cache_key = ("market_briefing", target_date, use_mock_data)
    cached = get_ttl_cache(cache_key)
    if cached is not None:
        return cached

    date_context = resolve_stock_trading_date(target_date)
    data_date = date_context["target_date"]

    # 이미 끝난 거래일은 저장된 payload로 즉시 서빙 (날짜 맥락만 요청자 기준으로 갱신)
    if not use_mock_data and is_finalized_date(data_date):
        stored = load_payload("market", "briefing", data_date)
        if stored is not None:
            payload = {**stored, **date_context}
            text = format_market_briefing(payload)
            path = save_output_text("market_briefing", data_date, text)
            return set_ttl_cache(cache_key, {"text": text, "path": path, "payload": payload})

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            "indices": executor.submit(get_market_indices, data_date, use_mock_data=use_mock_data),
            "index_trend": executor.submit(get_korean_index_trend, data_date, use_mock_data=use_mock_data),
            "global_macro": executor.submit(get_global_macro_snapshot, data_date, use_mock_data=use_mock_data),
            "leaders": executor.submit(get_trading_value_leaders, data_date, use_mock_data=use_mock_data),
            "sectors": executor.submit(get_sector_changes, use_mock_data=use_mock_data),
            "investor_flows": executor.submit(get_investor_flows, data_date, use_mock_data=use_mock_data),
            "derivatives": executor.submit(get_derivatives_snapshot, data_date, use_mock_data=use_mock_data),
            "market_events": executor.submit(get_market_event_lists, data_date, use_mock_data=use_mock_data),
            "news_items": executor.submit(get_market_news, use_mock_data=use_mock_data),
            "market_reports": executor.submit(get_market_reports, use_mock_data=use_mock_data),
        }

    collector_status: dict[str, dict] = {}
    indices, collector_status["indices"] = _resolve_collector(futures, "indices", _empty_indices())
    index_trend, collector_status["index_trend"] = _resolve_collector(futures, "index_trend", {})
    global_macro, collector_status["global_macro"] = _resolve_collector(futures, "global_macro", {})
    leaders, collector_status["leaders"] = _resolve_collector(futures, "leaders", [])
    sectors, collector_status["sectors"] = _resolve_collector(futures, "sectors", [])
    investor_flows, collector_status["investor_flows"] = _resolve_collector(
        futures,
        "investor_flows",
        _empty_investor_flows(),
    )
    derivatives, collector_status["derivatives"] = _resolve_collector(futures, "derivatives", _empty_derivatives())
    market_events, collector_status["market_events"] = _resolve_collector(futures, "market_events", _empty_market_events())
    news_items, collector_status["news_items"] = _resolve_collector(futures, "news_items", [])
    market_reports, collector_status["market_reports"] = _resolve_collector(futures, "market_reports", [])

    payload = {
        **date_context,
        "is_mock_data": use_mock_data,
        "indices": indices,
        "index_trend": index_trend,
        "global_macro": global_macro,
        "leaders": leaders,
        "sectors": sectors,
        "investor_flows": investor_flows,
        "derivatives": derivatives,
        "market_events": market_events,
        "news_items": news_items,
        "market_reports": market_reports,
        "collector_status": collector_status,
    }
    payload["column"] = generate_market_column(payload)
    text = format_market_briefing(payload)
    path = save_output_text("market_briefing", data_date, text)
    if not use_mock_data and is_finalized_date(data_date):
        save_payload("market", "briefing", data_date, payload)
    return set_ttl_cache(cache_key, {"text": text, "path": path, "payload": payload})

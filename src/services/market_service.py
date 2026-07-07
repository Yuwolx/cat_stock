from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

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
from src.utils.date_utils import KST, resolve_stock_trading_date
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


# v2: 저장 조건(수집기 전부 정상 + 07시 이후) 도입 이전의 저장분은
# '현재 데이터가 과거 날짜로 라벨링'됐을 수 있어 키를 올려 무효화한다
_STORE_KEY = "briefing.v2"


def _now_kst() -> datetime:
    return datetime.now(KST)


def _cache_ttl_seconds() -> int:
    """장마감 후(16시~자정)엔 데이터가 확정이므로 자정까지 캐시를 연장한다.

    5분마다 확정 데이터를 재크롤링하고 AI 칼럼을 다시 생성하는 낭비를 막고,
    같은 저녁 사용자들이 동일한 브리핑을 보게 한다.
    """
    now = _now_kst()
    if now.hour >= 16:
        midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        return max(300, int((midnight - now).total_seconds()))
    return 300


def _is_storable(collector_status: dict) -> bool:
    """모든 수집기가 정상일 때만 영구 저장 — 실패분을 박제하면 자연 치유가 없다."""
    return bool(collector_status) and all(
        (status or {}).get("status") == "ok" for status in collector_status.values()
    )


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
    cached = get_ttl_cache(cache_key, ttl_seconds=_cache_ttl_seconds())
    if cached is not None:
        return cached

    date_context = resolve_stock_trading_date(target_date)
    data_date = date_context["target_date"]

    # 이미 끝난 거래일은 저장된 payload로 즉시 서빙 (날짜 맥락만 요청자 기준으로 갱신)
    if not use_mock_data and is_finalized_date(data_date):
        stored = load_payload("market", _STORE_KEY, data_date)
        if stored is not None:
            payload = {**stored, **date_context}
            text = format_market_briefing(payload)
            path = save_output_text("market_briefing", data_date, text)
            return set_ttl_cache(cache_key, {"text": text, "path": path, "payload": payload})

        # 저장본 없는 과거 날짜는 생성을 거절한다. 수집기는 항상 '지금'의
        # 네이버/KRX 화면을 읽으므로, 지나간 날짜로 라벨을 붙이면 거짓 데이터가 된다.
        latest_trading_date = resolve_stock_trading_date(None)["target_date"]
        if data_date != latest_trading_date:
            notice = (
                f"[시황 브리핑 - {data_date}]\n\n"
                "이 날짜의 저장된 브리핑이 없습니다.\n"
                "수집기는 '지금'의 시장 화면을 읽기 때문에, 지나간 날짜를 나중에 생성하면 "
                "오늘 데이터가 그 날짜로 잘못 저장됩니다. 그래서 만들지 않았어요.\n"
                "브리핑은 그날그날 생성된 것이 자동으로 보관됩니다 — 앞으로 쌓이는 날짜들은 언제든 다시 볼 수 있어요."
            )
            return {"text": notice, "path": None, "payload": None}

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
    # 저장 조건: 확정 거래일 + 모든 수집기 정상 + KST 07시 이후
    # (자정~새벽엔 미국 세션이 진행 중이라 글로벌 지표가 미완성 값으로 박제될 수 있다)
    if (
        not use_mock_data
        and is_finalized_date(data_date)
        and _is_storable(collector_status)
        and _now_kst().hour >= 7
    ):
        save_payload("market", _STORE_KEY, data_date, payload)
    return set_ttl_cache(cache_key, {"text": text, "path": path, "payload": payload})

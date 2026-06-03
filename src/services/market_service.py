from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from src.collectors.kis_client import get_token
from src.collectors.market.dart_collector import get_major_disclosures
from src.collectors.market.global_collector import get_global_macro_snapshot
from src.collectors.market.kis_market_collector import get_futures_investor_flow
from src.collectors.market.krx_collector import (
    get_derivatives_snapshot,
    get_investor_flows,
    get_market_indices,
)
from src.collectors.market.naver_market_collector import (
    get_market_event_lists,
    get_sector_changes,
    get_trading_value_leaders,
)
from src.config.settings import get_settings
from src.formatters.market_formatter import format_market_briefing
from src.services.column_service import generate_market_column
from src.utils.concurrency import future_result
from src.utils.file_utils import save_output_text


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


def _prime_kis_token(app_key: str, app_secret: str) -> None:
    try:
        get_token(app_key, app_secret)
    except Exception:
        pass


def generate_market_briefing(target_date: str, use_mock_data: bool = False) -> dict:
    settings = get_settings()
    has_kis = bool(settings.kis_app_key and settings.kis_app_secret)
    if has_kis and not use_mock_data:
        _prime_kis_token(settings.kis_app_key, settings.kis_app_secret)

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {
            "indices": executor.submit(get_market_indices, target_date, use_mock_data=use_mock_data),
            "global_macro": executor.submit(get_global_macro_snapshot, target_date, use_mock_data=use_mock_data),
            "leaders": executor.submit(get_trading_value_leaders, target_date, use_mock_data=use_mock_data),
            "sectors": executor.submit(get_sector_changes, use_mock_data=use_mock_data),
            "investor_flows": executor.submit(get_investor_flows, target_date, use_mock_data=use_mock_data),
            "derivatives": executor.submit(get_derivatives_snapshot, target_date, use_mock_data=use_mock_data),
            "market_events": executor.submit(get_market_event_lists, target_date, use_mock_data=use_mock_data),
            "disclosures": executor.submit(
                get_major_disclosures,
                target_date,
                api_key=settings.dart_api_key,
                use_mock_data=use_mock_data,
            ),
        }

    derivatives = future_result(futures, "derivatives", _empty_derivatives())

    # KIS API 선물 수급 — 성공 시 네이버 기반 None 값 덮어씀
    if has_kis and not use_mock_data:
        kis_futures = get_futures_investor_flow(settings.kis_app_key, settings.kis_app_secret)
        if kis_futures.get("futures_foreign_net") is not None:
            derivatives["futures_foreign_net"] = kis_futures["futures_foreign_net"]
        if kis_futures.get("futures_institution_net") is not None:
            derivatives["futures_institution_net"] = kis_futures["futures_institution_net"]

    payload = {
        "target_date": target_date,
        "is_mock_data": use_mock_data,
        "indices": future_result(futures, "indices", _empty_indices()),
        "global_macro": future_result(futures, "global_macro", {}),
        "leaders": future_result(futures, "leaders", []),
        "sectors": future_result(futures, "sectors", []),
        "investor_flows": future_result(futures, "investor_flows", _empty_investor_flows()),
        "derivatives": derivatives,
        "market_events": future_result(futures, "market_events", _empty_market_events()),
        "disclosures": future_result(futures, "disclosures", []),
    }
    payload["column"] = generate_market_column(payload)
    text = format_market_briefing(payload)
    path = save_output_text("market_briefing", target_date, text)
    return {"text": text, "path": path, "payload": payload}

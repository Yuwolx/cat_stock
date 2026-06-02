from __future__ import annotations

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
from src.utils.file_utils import save_output_text


def generate_market_briefing(target_date: str, use_mock_data: bool = False) -> dict:
    settings = get_settings()
    has_kis = bool(settings.kis_app_key and settings.kis_app_secret)
    derivatives = get_derivatives_snapshot(target_date, use_mock_data=use_mock_data)

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
        "indices": get_market_indices(target_date, use_mock_data=use_mock_data),
        "global_macro": get_global_macro_snapshot(target_date, use_mock_data=use_mock_data),
        "leaders": get_trading_value_leaders(target_date, use_mock_data=use_mock_data),
        "sectors": get_sector_changes(use_mock_data=use_mock_data),
        "investor_flows": get_investor_flows(target_date, use_mock_data=use_mock_data),
        "derivatives": derivatives,
        "market_events": get_market_event_lists(target_date, use_mock_data=use_mock_data),
        "disclosures": get_major_disclosures(
            target_date,
            api_key=settings.dart_api_key,
            use_mock_data=use_mock_data,
        ),
    }
    payload["column"] = generate_market_column(payload)
    text = format_market_briefing(payload)
    path = save_output_text("market_briefing", target_date, text)
    return {"text": text, "path": path, "payload": payload}

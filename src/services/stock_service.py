from __future__ import annotations

from src.collectors.stock.dart_stock_collector import (
    get_financial_summary,
    get_stock_disclosures,
)
from src.collectors.stock.naver_stock_collector import (
    get_stock_basics,
    get_stock_investor_flows,
)
from src.collectors.stock.short_selling_collector import get_short_selling_snapshot
from src.config.settings import get_settings
from src.formatters.stock_formatter import format_stock_report
from src.utils.date_utils import today_kst_string
from src.utils.file_utils import save_output_text


def generate_stock_report(stock_name: str, use_mock_data: bool | None = None) -> dict:
    settings = get_settings()
    target_date = today_kst_string()
    effective_mock_data = settings.use_mock_data if use_mock_data is None else use_mock_data
    payload = {
        "target_date": target_date,
        "is_mock_data": effective_mock_data,
        "basics": get_stock_basics(stock_name, use_mock_data=effective_mock_data),
        "flows": get_stock_investor_flows(stock_name, use_mock_data=effective_mock_data),
        "financials": get_financial_summary(
            stock_name,
            api_key=settings.dart_api_key,
            use_mock_data=effective_mock_data,
        ),
        "disclosures": get_stock_disclosures(
            stock_name,
            api_key=settings.dart_api_key,
            use_mock_data=effective_mock_data,
        ),
        "short_selling": get_short_selling_snapshot(stock_name, use_mock_data=effective_mock_data),
    }
    text = format_stock_report(payload)
    path = save_output_text(f"stock_{stock_name}", target_date, text)
    return {"text": text, "path": path, "payload": payload}

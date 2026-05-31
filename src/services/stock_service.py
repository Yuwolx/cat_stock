from __future__ import annotations

from src.collectors.stock.dart_stock_collector import (
    get_financial_summary,
    get_stock_disclosures,
)
from src.collectors.stock.fnguide_report_collector import get_fnguide_reports
from src.collectors.stock.kis_stock_collector import (
    get_short_selling_ratio,
    get_stock_investor_flow_krw,
)
from src.collectors.stock.naver_stock_collector import (
    get_stock_basics,
    get_stock_code,
    get_stock_investor_flows,
)
from src.collectors.stock.short_selling_collector import get_short_selling_snapshot
from src.config.settings import get_settings
from src.formatters.stock_formatter import format_stock_report
from src.utils.date_utils import today_kst_string
from src.utils.file_utils import save_output_text


def generate_stock_report(
    stock_name: str,
    report_from: str | None = None,
    report_to: str | None = None,
    use_mock_data: bool = False,
) -> dict:
    settings = get_settings()
    target_date = today_kst_string()
    from_date = (report_from or target_date).replace("-", "")
    to_date = (report_to or report_from or target_date).replace("-", "")

    code = get_stock_code(stock_name) if not use_mock_data else None
    reports = get_fnguide_reports(code, from_date, to_date) if code else []

    has_kis = bool(settings.kis_app_key and settings.kis_app_secret)
    kis_flow = (
        get_stock_investor_flow_krw(code, settings.kis_app_key, settings.kis_app_secret)
        if code and has_kis and not use_mock_data
        else {"foreign_today": None, "institution_today": None, "retail_today": None}
    )
    kis_short = (
        get_short_selling_ratio(code, settings.kis_app_key, settings.kis_app_secret)
        if code and has_kis and not use_mock_data
        else None
    )

    naver_snapshot = get_short_selling_snapshot(stock_name, use_mock_data=use_mock_data)

    payload = {
        "target_date": target_date,
        "report_date": f"{report_from or target_date} ~ {report_to or report_from or target_date}",
        "is_mock_data": use_mock_data,
        "basics": get_stock_basics(stock_name, use_mock_data=use_mock_data),
        "flows": get_stock_investor_flows(stock_name, use_mock_data=use_mock_data),
        "financials": get_financial_summary(
            stock_name,
            api_key=settings.dart_api_key,
            use_mock_data=use_mock_data,
        ),
        "disclosures": get_stock_disclosures(
            stock_name,
            api_key=settings.dart_api_key,
            use_mock_data=use_mock_data,
        ),
        "short_selling": {
            "short_balance_ratio": kis_short or naver_snapshot.get("short_balance_ratio"),
            "consensus_target_price": naver_snapshot.get("consensus_target_price"),
        },
        "kis_flow": kis_flow,
        "reports": reports,
    }
    text = format_stock_report(payload)
    path = save_output_text(f"stock_{stock_name}", target_date, text)
    return {"text": text, "path": path, "payload": payload}

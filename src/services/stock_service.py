from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from src.collectors.kis_client import get_token
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
from src.services.column_service import generate_stock_column
from src.utils.concurrency import future_result
from src.utils.date_utils import today_kst_string
from src.utils.file_utils import save_output_text


SHORT_BALANCE_RATIO_UNSUPPORTED = "미제공"


def _empty_basics(stock_name: str) -> dict:
    return {
        "name": stock_name,
        "price": None,
        "change_pct": None,
        "turnover_krw_billion": None,
        "market_cap": None,
        "year_high_low": None,
        "per": None,
        "pbr": None,
        "roe": None,
        "ma_position": {"ma5": None, "ma20": None, "ma60": None},
    }


def _empty_flows() -> dict:
    return {
        "foreign_20d": None,
        "institution_20d": None,
        "news": [],
        "news_items": [],
        "naver_reports": [],
    }


def _empty_disclosures() -> dict:
    return {
        "disclosures": [],
        "major_shareholder_ratio": None,
        "risk_flags": [],
    }


def _empty_kis_flow() -> dict:
    return {
        "foreign_today": None,
        "institution_today": None,
        "retail_today": None,
    }


def _empty_short_selling() -> dict:
    return {
        "short_balance_ratio": SHORT_BALANCE_RATIO_UNSUPPORTED,
        "short_sale_volume_ratio": None,
        "consensus_target_price": None,
    }


def _prime_kis_token(app_key: str, app_secret: str) -> None:
    try:
        get_token(app_key, app_secret)
    except Exception:
        pass


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

    try:
        code = get_stock_code(stock_name) if not use_mock_data else None
    except Exception:
        code = None

    has_kis = bool(settings.kis_app_key and settings.kis_app_secret)
    should_use_kis = bool(code and has_kis and not use_mock_data)
    if should_use_kis:
        _prime_kis_token(settings.kis_app_key, settings.kis_app_secret)

    with ThreadPoolExecutor(max_workers=7) as executor:
        futures = {
            "basics": executor.submit(get_stock_basics, stock_name, use_mock_data=use_mock_data),
            "flows": executor.submit(get_stock_investor_flows, stock_name, use_mock_data=use_mock_data),
            "financials": executor.submit(
                get_financial_summary,
                stock_name,
                api_key=settings.dart_api_key,
                use_mock_data=use_mock_data,
            ),
            "disclosures": executor.submit(
                get_stock_disclosures,
                stock_name,
                api_key=settings.dart_api_key,
                use_mock_data=use_mock_data,
            ),
            "naver_snapshot": executor.submit(get_short_selling_snapshot, stock_name, use_mock_data=use_mock_data),
        }
        if code:
            futures["reports"] = executor.submit(get_fnguide_reports, code, from_date, to_date)
        if should_use_kis:
            futures["kis_flow"] = executor.submit(
                get_stock_investor_flow_krw,
                code,
                settings.kis_app_key,
                settings.kis_app_secret,
            )
            futures["kis_short"] = executor.submit(
                get_short_selling_ratio,
                code,
                settings.kis_app_key,
                settings.kis_app_secret,
            )

    reports = future_result(futures, "reports", []) if code else []
    kis_flow = future_result(futures, "kis_flow", _empty_kis_flow()) if should_use_kis else _empty_kis_flow()
    kis_short_sale_volume_ratio = future_result(futures, "kis_short", None) if should_use_kis else None
    naver_snapshot = future_result(futures, "naver_snapshot", _empty_short_selling())

    payload = {
        "target_date": target_date,
        "report_date": f"{report_from or target_date} ~ {report_to or report_from or target_date}",
        "is_mock_data": use_mock_data,
        "basics": future_result(futures, "basics", _empty_basics(stock_name)),
        "flows": future_result(futures, "flows", _empty_flows()),
        "financials": future_result(futures, "financials", []),
        "disclosures": future_result(futures, "disclosures", _empty_disclosures()),
        "short_selling": {
            "short_balance_ratio": (
                naver_snapshot.get("short_balance_ratio")
                if use_mock_data
                else SHORT_BALANCE_RATIO_UNSUPPORTED
            ),
            "short_sale_volume_ratio": kis_short_sale_volume_ratio,
            "consensus_target_price": naver_snapshot.get("consensus_target_price"),
        },
        "kis_flow": kis_flow,
        "reports": reports,
    }
    payload["column"] = generate_stock_column(payload)
    text = format_stock_report(payload)
    path = save_output_text(f"stock_{stock_name}", target_date, text)
    return {"text": text, "path": path, "payload": payload}

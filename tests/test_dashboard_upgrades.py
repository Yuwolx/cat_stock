from src.ui.dashboard import build_market_dashboard, build_stock_dashboard, build_theme_dashboard
from tests.test_prompt_format_contract import (
    _full_market_payload,
    _full_stock_payload,
    _full_theme_payload,
)


def test_market_ticker_colors_positive_change() -> None:
    payload = _full_market_payload()  # kospi change_pct = 1.0 (숫자, "+" 없음)

    html = build_market_dashboard(payload)

    assert '<div class="t-val up">+1.00%</div>' in html


def test_market_dashboard_includes_index_trend_chart() -> None:
    payload = _full_market_payload()
    payload["index_trend"] = {
        "kospi": {"closes": [2588.3, 2601.2, 2612.8, 2598.4, 2624.9, 2640.6]},
        "kosdaq": {"closes": [829.5, 832.1, 835.7, 838.2, 836.9, 840.3]},
    }

    html = build_market_dashboard(payload)

    assert "INDEX TREND" in html


def test_market_dashboard_compresses_movers() -> None:
    payload = _full_market_payload()
    payload["market_events"]["new_highs"] = [f"종목{i}" for i in range(50)]

    html = build_market_dashboard(payload)

    assert "종목14" in html
    assert "종목15" not in html
    assert "외 35종목" in html


def test_stock_dashboard_uses_daily_flow_chart() -> None:
    payload = _full_stock_payload()
    payload["flows"]["daily_flows"] = {
        "dates": ["2026.05.23", "2026.05.26", "2026.05.27", "2026.05.28", "2026.05.29"],
        "close": [76000.0, 76800.0, 77500.0, 78100.0, 78500.0],
        "foreign": [-52000.0, 118000.0, 296000.0, 447000.0, 384000.0],
        "institution": [21000.0, -64000.0, -98000.0, -120000.0, -81000.0],
    }

    html = build_stock_dashboard(payload)

    assert "INVESTOR FLOW — DAILY" in html


def test_stock_dashboard_falls_back_to_aggregate_chart() -> None:
    html = build_stock_dashboard(_full_stock_payload())

    assert "INVESTOR FLOW — 20 DAYS" in html


def test_theme_dashboard_renders_real_data() -> None:
    html = build_theme_dashboard(_full_theme_payload())

    assert "준비 중" not in html
    assert "하나마이크론" in html
    assert "THEME MOVERS" in html
    assert "CONSTITUENTS" in html
    assert "THEME WIRE" in html


def test_theme_dashboard_handles_empty_stocks() -> None:
    payload = _full_theme_payload()
    payload["stocks"] = []

    html = build_theme_dashboard(payload)

    assert "테마 종목 데이터 없음" in html

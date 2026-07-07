from src.formatters.market_formatter import format_market_briefing
from src.formatters.stock_formatter import format_stock_report
from src.utils.trend_utils import (
    consecutive_streak,
    format_flow_trend_line,
    format_price_trend_line,
)
from tests.test_prompt_format_contract import _full_market_payload, _full_stock_payload


def test_consecutive_streak_counts_from_latest() -> None:
    assert consecutive_streak([-100, 200, 300, 400]) == (True, 3)
    assert consecutive_streak([100, -200, -300]) == (False, 2)
    assert consecutive_streak([100, 200, None, 300]) == (True, 3)  # None(결측일)은 건너뛰고 계산


def test_consecutive_streak_handles_empty_and_zero() -> None:
    assert consecutive_streak([]) is None
    assert consecutive_streak([None, None]) is None
    assert consecutive_streak([100, 0]) is None


def test_format_flow_trend_line_shows_streak_and_series() -> None:
    line = format_flow_trend_line("외국인 일별", [-52000, 118000, 296000, 447000, 384000])

    assert line is not None
    assert line.startswith("외국인 일별 최근 5일(과거→최근)")
    assert "-5.2만주 → +11.8만주 → +29.6만주 → +44.7만주 → +38.4만주" in line
    assert "4일 연속 순매수" in line


def test_format_flow_trend_line_small_values_in_shares() -> None:
    line = format_flow_trend_line("기관 일별", [1200, -3400])

    assert line is not None
    assert "+1,200주" in line
    assert "-3,400주" in line


def test_format_flow_trend_line_empty_returns_none() -> None:
    assert format_flow_trend_line("외국인 일별", []) is None
    assert format_flow_trend_line("외국인 일별", [None, None]) is None


def test_format_price_trend_line_shows_cumulative_and_streak() -> None:
    line = format_price_trend_line("코스피", [2588.3, 2601.2, 2612.8, 2598.4, 2624.9, 2640.6], digits=2)

    assert line is not None
    assert line.startswith("코스피 최근 5거래일(과거→최근)")
    assert "2,601.2 → 2,612.8 → 2,598.4 → 2,624.9 → 2,640.6" in line
    assert "5일 누적 +1.5%" in line
    assert "2일 연속 상승" in line


def test_format_price_trend_line_needs_two_points() -> None:
    assert format_price_trend_line("코스피", [2600.0]) is None
    assert format_price_trend_line("코스피", []) is None


def test_stock_report_includes_daily_flow_trends() -> None:
    payload = _full_stock_payload()
    payload["flows"]["daily_flows"] = {
        "dates": ["2026.05.23", "2026.05.26", "2026.05.27", "2026.05.28", "2026.05.29"],
        "close": [76000.0, 76800.0, 77500.0, 78100.0, 78500.0],
        "foreign": [-52000.0, 118000.0, 296000.0, 447000.0, 384000.0],
        "institution": [21000.0, -64000.0, -98000.0, -120000.0, -81000.0],
    }

    result = format_stock_report(payload)

    assert "종가 흐름 최근 5거래일(과거→최근) 76,000 → 76,800 → 77,500 → 78,100 → 78,500" in result
    assert "4일 연속 상승" in result
    assert "외국인 일별 최근 5일(과거→최근)" in result
    assert "4일 연속 순매수" in result
    assert "기관 일별 최근 5일(과거→최근)" in result
    assert "4일 연속 순매도" in result


def test_stock_report_without_daily_flows_unchanged() -> None:
    result = format_stock_report(_full_stock_payload())

    assert "종가 흐름" not in result
    assert "일별 최근" not in result


def test_market_briefing_includes_index_trend() -> None:
    payload = _full_market_payload()
    payload["index_trend"] = {
        "kospi": {"closes": [2588.3, 2601.2, 2612.8, 2598.4, 2624.9, 2640.6]},
        "kosdaq": {"closes": [829.5, 832.1, 835.7, 838.2, 836.9, 840.3]},
    }

    result = format_market_briefing(payload)

    assert "코스피 최근 5거래일(과거→최근)" in result
    assert "코스닥 최근 5거래일(과거→최근)" in result
    assert "2일 연속 상승" in result


def test_market_briefing_without_index_trend_unchanged() -> None:
    result = format_market_briefing(_full_market_payload())

    assert "최근 5거래일" not in result

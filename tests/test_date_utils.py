from datetime import date

from src.utils import date_utils


def test_resolve_stock_trading_date_uses_krx_calendar_when_available(monkeypatch) -> None:
    monkeypatch.setattr(date_utils, "_nearest_krx_business_day", lambda day: date(2026, 6, 25))

    result = date_utils.resolve_stock_trading_date("2026-06-25")

    assert result["requested_date"] == "2026-06-25"
    assert result["target_date"] == "2026-06-25"
    assert result["basis"] == "krx_calendar"
    assert result["is_adjusted"] is False


def test_weekend_request_respects_holiday_friday(monkeypatch) -> None:
    # 일요일 요청, 직전 금요일(6/26)이 공휴일이라 KRX 캘린더가 목요일(6/25)을 반환
    monkeypatch.setattr(date_utils, "_nearest_krx_business_day", lambda day: date(2026, 6, 25))

    result = date_utils.resolve_stock_trading_date("2026-06-28")

    assert result["target_date"] == "2026-06-25"
    assert result["basis"] == "krx_calendar"


def test_resolve_stock_trading_date_falls_back_to_previous_weekday(monkeypatch) -> None:
    monkeypatch.setattr(date_utils, "_nearest_krx_business_day", lambda day: None)

    result = date_utils.resolve_stock_trading_date("2026-06-28")

    assert result["requested_date"] == "2026-06-28"
    assert result["target_date"] == "2026-06-26"
    assert result["requested_weekday"] == "일"
    assert result["resolved_weekday"] == "금"
    assert result["is_adjusted"] is True
    assert result["basis"] == "weekday_fallback"

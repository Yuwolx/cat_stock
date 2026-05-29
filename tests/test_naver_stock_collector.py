from src.collectors.stock.naver_stock_collector import _to_number


def test_to_number_preserves_negative_arrow() -> None:
    assert _to_number("▼1,234") == -1234.0


def test_to_number_preserves_positive_arrow() -> None:
    assert _to_number("▲1,234") == 1234.0


def test_to_number_returns_none_for_empty_text() -> None:
    assert _to_number("") is None

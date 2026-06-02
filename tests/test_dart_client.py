import pytest

from src.collectors.dart_client import _validate_api_key
from src.collectors.stock.dart_stock_collector import get_stock_disclosures


def test_validate_api_key_rejects_non_dart_key() -> None:
    with pytest.raises(RuntimeError, match="40자리 인증키"):
        _validate_api_key("not-a-dart-key=value")


def test_validate_api_key_accepts_40_char_alnum_key() -> None:
    key = "a" * 40

    assert _validate_api_key(key) == key


def test_stock_disclosures_handles_invalid_dart_key() -> None:
    result = get_stock_disclosures("삼성전자", api_key="not-a-dart-key=value", use_mock_data=False)

    assert result["major_shareholder_ratio"] is None
    assert result["risk_flags"] == []
    assert "DART 조회 실패" in result["disclosures"][0]

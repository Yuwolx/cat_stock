import pytest
import zipfile
from io import BytesIO
from types import SimpleNamespace

from src.collectors import dart_client
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


def test_corp_code_index_uses_file_cache_after_process_cache_clear(monkeypatch, tmp_path) -> None:
    key = "a" * 40
    calls: list[str] = []
    xml = """
    <result>
      <list>
        <corp_name>삼성전자</corp_name>
        <corp_code>00126380</corp_code>
        <stock_code>005930</stock_code>
      </list>
    </result>
    """
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("CORPCODE.xml", xml.encode("utf-8"))

    def fake_get(url: str, params: dict, timeout: int, headers: dict) -> SimpleNamespace:
        calls.append(url)
        return SimpleNamespace(content=buffer.getvalue(), raise_for_status=lambda: None)

    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path))
    monkeypatch.setattr(dart_client.requests, "get", fake_get)
    dart_client.get_corp_code_index.cache_clear()

    first = dart_client.get_corp_code_index(key)
    dart_client.get_corp_code_index.cache_clear()
    second = dart_client.get_corp_code_index(key)

    assert first == second
    assert first[0]["corp_code"] == "00126380"
    assert len(calls) == 1

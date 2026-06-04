from io import BytesIO
from types import SimpleNamespace
from zipfile import ZipFile

from src.collectors.market import kis_market_collector as collector


def _master_zip(text: str) -> bytes:
    buffer = BytesIO()
    with ZipFile(buffer, "w") as archive:
        archive.writestr("fo_idx_code_mts.mst", text.encode("cp949"))
    return buffer.getvalue()


def test_get_kospi200_nearest_future_code_reads_master(monkeypatch) -> None:
    collector.get_kospi200_nearest_future_code.cache_clear()
    master = "\n".join(
        [
            "1|A01609|KR4A01690002|F 202609| |00000.00|2|2001|KOSPI200",
            "1|A01606|KR4A01660005|F 202606| |00000.00|1|2001|KOSPI200",
            "B|A05606|KR4A05660001|미니F 202606| |00000.00|1|2001|KOSPI200",
        ]
    )

    monkeypatch.setattr(
        collector.requests,
        "get",
        lambda url, timeout=20: SimpleNamespace(content=_master_zip(master), raise_for_status=lambda: None),
    )

    assert collector.get_kospi200_nearest_future_code() == "A01606"


def test_get_futures_investor_flow_marks_kis_endpoint_unsupported(monkeypatch) -> None:
    monkeypatch.setattr(collector, "get_kospi200_nearest_future_code", lambda: "A01606")

    result = collector.get_futures_investor_flow("app", "secret")

    assert result == {
        "futures_foreign_net": None,
        "futures_institution_net": None,
        "futures_contract_code": "A01606",
        "futures_warning": collector.FUTURES_INVESTOR_FLOW_UNSUPPORTED_WARNING,
    }

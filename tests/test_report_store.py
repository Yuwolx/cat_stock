from datetime import datetime, timedelta

from src.services import market_service
from src.utils.date_utils import KST
from src.utils.report_store import is_finalized_date, load_payload, save_payload
from src.utils.ttl_cache import clear_ttl_cache
from tests.test_service_cache import _patch_market_collectors
from tests.test_stock_parallel_service import _date_context


def _kst_date(offset_days: int = 0) -> str:
    return (datetime.now(KST) + timedelta(days=offset_days)).strftime("%Y-%m-%d")


def test_is_finalized_date_only_for_past_days() -> None:
    assert is_finalized_date(_kst_date(-1)) is True
    assert is_finalized_date(_kst_date(0)) is False
    assert is_finalized_date(_kst_date(1)) is False


def test_save_and_load_roundtrip() -> None:
    payload = {"indices": {"kospi": {"close": 2640.0}}, "한글": "값"}

    save_payload("market", "briefing", "2026-06-03", payload)

    assert load_payload("market", "briefing", "2026-06-03") == payload
    assert load_payload("market", "briefing", "2026-06-04") is None
    assert load_payload("stock", "briefing", "2026-06-03") is None


def test_save_overwrites_same_key() -> None:
    save_payload("market", "briefing", "2026-06-03", {"v": 1})
    save_payload("market", "briefing", "2026-06-03", {"v": 2})

    assert load_payload("market", "briefing", "2026-06-03") == {"v": 2}


def test_market_briefing_served_from_store_after_restart(monkeypatch) -> None:
    calls: list[str] = []
    _patch_market_collectors(monkeypatch, calls)

    first = market_service.generate_market_briefing("2026-06-03", use_mock_data=False)
    count_after_first = len(calls)
    assert count_after_first > 0

    clear_ttl_cache()  # 재시작 시뮬레이션 — 메모리 캐시는 사라져도 DB는 남는다
    second = market_service.generate_market_briefing("2026-06-03", use_mock_data=False)

    assert len(calls) == count_after_first  # 수집기 재호출 없음
    assert second["text"] == first["text"]
    assert second["payload"]["indices"] == first["payload"]["indices"]
    assert second["payload"]["column"] == first["payload"]["column"]


def test_stored_payload_gets_requesters_date_context(monkeypatch) -> None:
    calls: list[str] = []
    _patch_market_collectors(monkeypatch, calls)

    market_service.generate_market_briefing("2026-06-03", use_mock_data=False)
    clear_ttl_cache()

    # 다른 요청 맥락(주말 보정)으로 같은 거래일을 다시 요청
    adjusted_context = _date_context("2026-06-03", requested="2026-06-07", adjusted=True)
    monkeypatch.setattr(market_service, "resolve_stock_trading_date", lambda target_date: adjusted_context)
    result = market_service.generate_market_briefing("2026-06-07", use_mock_data=False)

    assert len(calls) > 0
    assert result["payload"]["requested_date"] == "2026-06-07"
    assert result["payload"]["is_adjusted"] is True
    assert result["payload"]["target_date"] == "2026-06-03"


def test_mock_data_never_touches_store(monkeypatch) -> None:
    calls: list[str] = []
    _patch_market_collectors(monkeypatch, calls)

    market_service.generate_market_briefing("2026-06-03", use_mock_data=True)

    assert load_payload("market", "briefing", "2026-06-03") is None

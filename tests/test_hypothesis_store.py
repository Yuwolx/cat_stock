from src.services import coin_study_note_service
from src.utils.hypothesis_store import (
    VERDICT_LABELS,
    list_hypotheses,
    save_hypothesis,
    set_verdict,
    verdict_stats,
)


def test_save_and_list_roundtrip() -> None:
    note = {"coin": "SOL", "hypothesis": "TVL 회복", "invalidating_condition": "거래대금 감소"}
    snapshot = {"BTC 가격 (USD)": 64000.0, "공포탐욕지수": "55"}

    hypothesis_id = save_hypothesis(note, snapshot)

    assert hypothesis_id is not None
    items = list_hypotheses()
    assert len(items) == 1
    assert items[0]["id"] == hypothesis_id
    assert items[0]["note"]["coin"] == "SOL"
    assert items[0]["snapshot"]["BTC 가격 (USD)"] == 64000.0
    assert items[0]["verdict"] is None


def test_list_orders_newest_first() -> None:
    first = save_hypothesis({"coin": "A"}, {})
    second = save_hypothesis({"coin": "B"}, {})

    items = list_hypotheses()

    assert [item["id"] for item in items] == [second, first]


def test_verdict_and_stats() -> None:
    a = save_hypothesis({"coin": "A", "hypothesis": "x"}, {})
    b = save_hypothesis({"coin": "B", "hypothesis": "y"}, {})
    save_hypothesis({"coin": "C", "hypothesis": "z"}, {})

    assert set_verdict(a, "right") is True
    assert set_verdict(b, "wrong") is True
    assert set_verdict(b, "nonsense") is False

    stats = verdict_stats()
    assert stats["total"] == 3
    assert stats["judged"] == 2
    assert stats["right"] == 1
    assert stats["wrong"] == 1

    judged = {item["id"]: item["verdict"] for item in list_hypotheses()}
    assert judged[a] == "right"
    assert judged[b] == "wrong"


def test_verdict_labels_complete() -> None:
    assert set(VERDICT_LABELS) == {"right", "partial", "wrong", "invalidated"}


def test_note_with_hypothesis_is_recorded(monkeypatch) -> None:
    monkeypatch.setattr(coin_study_note_service, "collect_market_snapshot", lambda: {"공포탐욕지수": "40"})
    monkeypatch.setattr(coin_study_note_service, "save_output_text", lambda prefix, date, text: "/tmp/note.txt")

    result = coin_study_note_service.generate_coin_study_note(
        regime="관망",
        market_reason="",
        sector="DeFi",
        sector_reason="",
        coin="AAVE",
        hypothesis="대출 수요 회복",
        invalidating_condition="TVL 감소",
        next_metric="fees",
        next_source="DefiLlama",
    )

    assert result["hypothesis_id"] is not None
    assert "기록 시점 시장 스냅샷" in result["text"]
    items = list_hypotheses()
    assert len(items) == 1
    assert items[0]["note"]["coin"] == "AAVE"
    assert items[0]["snapshot"] == {"공포탐욕지수": "40"}


def test_note_without_hypothesis_is_not_recorded(monkeypatch) -> None:
    monkeypatch.setattr(coin_study_note_service, "collect_market_snapshot", lambda: {})
    monkeypatch.setattr(coin_study_note_service, "save_output_text", lambda prefix, date, text: "/tmp/note.txt")

    result = coin_study_note_service.generate_coin_study_note(
        regime="관망",
        market_reason="",
        sector="",
        sector_reason="",
        coin="",
        hypothesis="",
        invalidating_condition="",
        next_metric="",
        next_source="",
    )

    assert result["hypothesis_id"] is None
    assert list_hypotheses() == []

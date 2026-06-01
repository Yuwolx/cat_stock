from src.formatters.coin_study_note_formatter import format_coin_study_note


def test_coin_study_note_formatter_includes_hypothesis_and_invalidating_condition() -> None:
    payload = {
        "target_datetime": "2026-05-31 21:00 KST",
        "regime": "관망",
        "market_reason": "BTC는 강하지만 알트 확산은 약함",
        "sector": "DeFi",
        "sector_reason": "TVL과 수수료가 같이 증가",
        "coin": "AAVE",
        "hypothesis": "대출 수요 회복",
        "invalidating_condition": "TVL 감소와 수수료 둔화",
        "next_metric": "fees",
        "next_source": "DefiLlama",
    }

    result = format_coin_study_note(payload)

    assert "[CAT COIN 학습 노트 - 2026-05-31 21:00 KST]" in result
    assert "■ 오늘 본 코인" in result
    assert "상승/하락 원인 가설: 대출 수요 회복" in result
    assert "반증 조건: TVL 감소와 수수료 둔화" in result

from __future__ import annotations

from src.utils.text_utils import display_value, section


def format_coin_study_note(payload: dict) -> str:
    chunks = [
        f"[CAT COIN 학습 노트 - {payload.get('target_datetime', '-')}]",
        section(
            "오늘 시장 국면",
            [
                f"국면: {display_value(payload.get('regime'))}",
                f"근거: {display_value(payload.get('market_reason'))}",
            ],
        ),
        section(
            "가장 강한 섹터",
            [
                f"섹터: {display_value(payload.get('sector'))}",
                f"강한 이유로 보이는 데이터: {display_value(payload.get('sector_reason'))}",
            ],
        ),
        section(
            "오늘 본 코인",
            [
                f"코인: {display_value(payload.get('coin'))}",
                f"상승/하락 원인 가설: {display_value(payload.get('hypothesis'))}",
                f"반증 조건: {display_value(payload.get('invalidating_condition'))}",
            ],
        ),
        section(
            "다음에 확인할 것",
            [
                f"지표: {display_value(payload.get('next_metric'))}",
                f"자료: {display_value(payload.get('next_source'))}",
            ],
        ),
    ]
    return "\n\n".join(chunks).strip()

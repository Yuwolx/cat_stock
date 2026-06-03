from __future__ import annotations

from src.formatters.coin_market_formatter import _display
from src.utils.text_utils import section


def format_coin_study_note(payload: dict) -> str:
    chunks = [
        f"[CAT COIN 학습 노트 - {payload.get('target_datetime', '-')}]",
        section(
            "오늘 시장 국면",
            [
                f"국면: {_display(payload.get('regime'))}",
                f"근거: {_display(payload.get('market_reason'))}",
            ],
        ),
        section(
            "가장 강한 섹터",
            [
                f"섹터: {_display(payload.get('sector'))}",
                f"강한 이유로 보이는 데이터: {_display(payload.get('sector_reason'))}",
            ],
        ),
        section(
            "오늘 본 코인",
            [
                f"코인: {_display(payload.get('coin'))}",
                f"상승/하락 원인 가설: {_display(payload.get('hypothesis'))}",
                f"반증 조건: {_display(payload.get('invalidating_condition'))}",
            ],
        ),
        section(
            "다음에 확인할 것",
            [
                f"지표: {_display(payload.get('next_metric'))}",
                f"자료: {_display(payload.get('next_source'))}",
            ],
        ),
    ]
    return "\n\n".join(chunks).strip()

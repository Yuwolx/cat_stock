from __future__ import annotations

from datetime import datetime

from src.formatters.coin_study_note_formatter import format_coin_study_note
from src.utils.date_utils import KST, today_kst_string
from src.utils.file_utils import save_output_text


def generate_coin_study_note(
    regime: str,
    market_reason: str,
    sector: str,
    sector_reason: str,
    coin: str,
    hypothesis: str,
    invalidating_condition: str,
    next_metric: str,
    next_source: str,
) -> dict:
    target_date = today_kst_string()
    payload = {
        "target_date": target_date,
        "target_datetime": datetime.now(KST).strftime("%Y-%m-%d %H:%M KST"),
        "regime": regime,
        "market_reason": market_reason,
        "sector": sector,
        "sector_reason": sector_reason,
        "coin": coin,
        "hypothesis": hypothesis,
        "invalidating_condition": invalidating_condition,
        "next_metric": next_metric,
        "next_source": next_source,
    }
    text = format_coin_study_note(payload)
    path = save_output_text("coin_study_note", target_date, text)
    return {"text": text, "path": path, "payload": payload}

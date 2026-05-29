from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo


KST = ZoneInfo("Asia/Seoul")


def today_kst_string() -> str:
    return datetime.now(KST).strftime("%Y-%m-%d")


def compact_date(date_text: str) -> str:
    return date_text.replace("-", "")

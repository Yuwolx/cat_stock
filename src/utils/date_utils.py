from __future__ import annotations

import logging
from datetime import date, datetime, timedelta

from zoneinfo import ZoneInfo


KST = ZoneInfo("Asia/Seoul")
WEEKDAY_KO = ["월", "화", "수", "목", "금", "토", "일"]


def today_kst_string() -> str:
    return datetime.now(KST).strftime("%Y-%m-%d")


def compact_date(date_text: str) -> str:
    return date_text.replace("-", "")


def _coerce_date(value: str | date | None) -> date:
    if value is None:
        return datetime.now(KST).date()
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.strptime(value, "%Y-%m-%d").date()


def _parse_krx_date(value: object) -> date | None:
    text = str(value or "").strip()
    if not text:
        return None
    if len(text) == 6:
        text = f"20{text}"
    if len(text) != 8 or not text.isdigit():
        return None
    return datetime.strptime(text, "%Y%m%d").date()


def _previous_weekday(day: date) -> date:
    resolved = day
    while resolved.weekday() >= 5:
        resolved -= timedelta(days=1)
    return resolved


_business_day_cache: dict[date, date] = {}


def _nearest_krx_business_day(day: date) -> date | None:
    """코스피 일별 시세의 마지막 행 날짜 = 가장 가까운 실제 거래일 (휴장일 반영).

    캐시 정책:
    - 실패(None)는 캐시하지 않는다 — 일시 오류를 박제하면 휴장일 보정이 꺼진다.
    - 지난 날짜의 매핑은 불변이므로 영구 캐시.
    - 오늘의 매핑은 개장 시점(09시)에 '어제→오늘'로 바뀌므로 5분 TTL만 준다.
    """
    from src.utils.ttl_cache import get_ttl_cache, set_ttl_cache

    permanent = _business_day_cache.get(day)
    if permanent is not None:
        return permanent
    cached = get_ttl_cache(("krx_business_day", day))
    if cached is not None:
        return cached

    try:
        from src.utils.naver_index_history import fetch_index_daily_rows

        rows = fetch_index_daily_rows("KOSPI", day - timedelta(days=14), day)
    except Exception:
        return None

    trading_days = [_parse_krx_date(row[0]) for row in rows]
    valid = [parsed for parsed in trading_days if parsed and parsed <= day]
    if not valid:
        return None

    resolved = max(valid)
    if day < datetime.now(KST).date():
        if len(_business_day_cache) > 64:
            _business_day_cache.clear()
        _business_day_cache[day] = resolved
    else:
        set_ttl_cache(("krx_business_day", day), resolved)
    return resolved


def weekday_ko(day: str | date) -> str:
    parsed = _coerce_date(day)
    return WEEKDAY_KO[parsed.weekday()]


def resolve_stock_trading_date(requested_date: str | date | None = None) -> dict:
    requested = _coerce_date(requested_date)
    if requested.weekday() >= 5:
        # 주말이라도 직전 금요일이 공휴일일 수 있으므로 KRX 캘린더로 재확인
        base = _previous_weekday(requested)
        resolved = _nearest_krx_business_day(base)
        basis = "krx_calendar"
        if resolved is None:
            resolved = base
            basis = "weekday_fallback"
    else:
        resolved = _nearest_krx_business_day(requested)
        basis = "krx_calendar"
        if resolved is None:
            resolved = _previous_weekday(requested)
            basis = "weekday_fallback"

    adjusted = requested != resolved
    resolved_label = f"{resolved.isoformat()} {weekday_ko(resolved)}요일"
    return {
        "requested_date": requested.isoformat(),
        "target_date": resolved.isoformat(),
        "resolved_date": resolved.isoformat(),
        "requested_weekday": weekday_ko(requested),
        "resolved_weekday": weekday_ko(resolved),
        "is_adjusted": adjusted,
        "basis": basis,
        "resolved_label": resolved_label,
        "date_note": (
            f"요청일 {requested.isoformat()} {weekday_ko(requested)}요일은 휴장일일 수 있어 "
            f"최근 거래일 {resolved_label} 기준으로 분석합니다."
            if adjusted
            else f"분석 기준일: {resolved_label}"
        ),
    }

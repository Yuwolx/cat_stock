from __future__ import annotations

from src.utils.text_utils import format_number


def consecutive_streak(values: list) -> tuple[bool, int] | None:
    """과거→최근 순서 값 목록에서, 최근일부터 부호가 같은 날이 며칠 연속인지.

    반환: (양수 여부, 연속 일수). 최근 값이 없거나 0이면 None.
    """
    cleaned = [v for v in values if v is not None]
    if not cleaned or not cleaned[-1]:
        return None
    positive = cleaned[-1] > 0
    count = 0
    for value in reversed(cleaned):
        if not value or (value > 0) != positive:
            break
        count += 1
    return positive, count


def _format_shares_compact(value: float) -> str:
    if abs(value) >= 10_000:
        text = f"{value / 10_000:+,.1f}"
        if text.endswith(".0"):
            text = text[:-2]
        return f"{text}만주"
    return f"{value:+,.0f}주"


def format_flow_trend_line(label: str, values: list) -> str | None:
    """일별 순매수 흐름 라인. values는 과거→최근 순서의 주 수.

    예: '외국인 일별 최근 5일(과거→최근) +12.5만주 → ... | 3일 연속 순매수'
    """
    cleaned = [v for v in values if v is not None]
    if not cleaned:
        return None
    recent = cleaned[-5:]
    series = " → ".join(_format_shares_compact(v) for v in recent)
    line = f"{label} 최근 {len(recent)}일(과거→최근) {series}"
    streak = consecutive_streak(cleaned)
    if streak and streak[1] >= 2:
        line += f" | {streak[1]}일 연속 {'순매수' if streak[0] else '순매도'}"
    return line


def format_price_trend_line(label: str, closes: list, digits: int = 0) -> str | None:
    """종가/지수 흐름 라인. closes는 과거→최근 순서.

    예: '코스피 최근 5거래일(과거→최근) 2,601.2 → ... | 5일 누적 +1.5% | 3일 연속 상승'
    """
    cleaned = [float(v) for v in closes if v is not None]
    if len(cleaned) < 2:
        return None
    recent = cleaned[-5:]
    series = " → ".join(format_number(v, digits=digits) for v in recent)
    parts = [f"{label} 최근 {len(recent)}거래일(과거→최근) {series}"]
    if recent[0]:
        cumulative_pct = (recent[-1] - recent[0]) / recent[0] * 100
        parts.append(f"{len(recent)}일 누적 {cumulative_pct:+.1f}%")
    diffs = [after - before for before, after in zip(cleaned, cleaned[1:])]
    streak = consecutive_streak(diffs)
    if streak and streak[1] >= 2:
        parts.append(f"{streak[1]}일 연속 {'상승' if streak[0] else '하락'}")
    return " | ".join(parts)

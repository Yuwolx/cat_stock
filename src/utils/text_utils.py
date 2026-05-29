from __future__ import annotations


def format_list(items: list[str]) -> str:
    return ", ".join(items) if items else "데이터 없음"


def bullet_lines(items: list[str]) -> list[str]:
    return [f"- {item}" for item in items]


def section(title: str, lines: list[str]) -> str:
    body = "\n".join(f"- {line}" for line in lines)
    return f"■ {title}\n{body}"


def display_value(value: object, fallback: str = "연결 예정") -> str:
    if value is None:
        return fallback
    if isinstance(value, str) and not value.strip():
        return fallback
    return str(value)


def format_krw_amount(value: str | None) -> str:
    if value is None:
        return "-"
    cleaned = value.replace(",", "").strip()
    if not cleaned.isdigit():
        return value

    amount = int(cleaned)
    one_trillion = 1_000_000_000_000
    one_hundred_million = 100_000_000

    if amount >= one_trillion:
        jo = amount / one_trillion
        return f"{jo:.1f}조"
    if amount >= one_hundred_million:
        eok = amount / one_hundred_million
        return f"{eok:.0f}억"
    return f"{amount:,}"

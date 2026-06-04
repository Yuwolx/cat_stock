from __future__ import annotations

import re


def format_list(items: list[str]) -> str:
    return ", ".join(items) if items else "데이터 없음"


def bullet_lines(items: list[str]) -> list[str]:
    return [f"- {item}" for item in items]


def section(title: str, lines: list[str]) -> str:
    body = "\n".join(f"- {line}" for line in lines)
    return f"■ {title}\n{body}"


def display_value(value: object, fallback: str = "—") -> str:
    if value is None:
        return fallback
    if isinstance(value, str) and not value.strip():
        return fallback
    return str(value)


def _parse_number(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()
    if not text:
        return None

    cleaned = re.sub(r"[,\s]", "", text)
    match = re.search(r"[-+]?\d+(?:\.\d+)?", cleaned)
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None


def _format_decimal(value: float, digits: int = 1) -> str:
    if value == 0:
        return "0"
    if digits <= 0:
        return f"{value:,.0f}"
    formatted = f"{value:,.{digits}f}"
    return formatted.rstrip("0").rstrip(".")


def format_number(value: object, digits: int = 1, fallback: str = "—") -> str:
    number = _parse_number(value)
    if number is None:
        return fallback
    return _format_decimal(number, digits)


def format_krw_eok(value: object, fallback: str = "—") -> str:
    number = _parse_number(value)
    if number is None:
        return fallback

    explicit_plus = isinstance(value, str) and value.strip().startswith("+") and number > 0
    prefix = "+" if explicit_plus else ""
    if abs(number) >= 10_000:
        return f"{prefix}{_format_decimal(number / 10_000, 1)}조"
    return f"{prefix}{_format_decimal(number, 1)}억"


def format_krw_amount(value: object | None) -> str:
    if value is None:
        return "—"

    text = str(value).strip()
    unit_match = re.fullmatch(r"([-+]?\d[\d,]*(?:\.\d+)?)\s*(조|억|원)", text)
    if unit_match:
        number = _parse_number(unit_match.group(1))
        unit = unit_match.group(2)
        if number is None:
            return text
        if unit == "억":
            return format_krw_eok(unit_match.group(1))
        return f"{_format_decimal(number, 1)}{unit}"

    cleaned = text.replace(",", "").strip()
    if not re.fullmatch(r"[-+]?\d+(?:\.\d+)?", cleaned):
        return text

    amount = float(cleaned)
    one_trillion = 1_000_000_000_000
    one_hundred_million = 100_000_000

    if abs(amount) >= one_trillion:
        jo = amount / one_trillion
        return f"{_format_decimal(jo, 1)}조"
    if abs(amount) >= one_hundred_million:
        eok = amount / one_hundred_million
        return f"{_format_decimal(eok, 1)}억"
    return _format_decimal(amount, 1)

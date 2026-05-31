from __future__ import annotations

import re

import requests
from bs4 import BeautifulSoup


HEADERS = {"User-Agent": "Mozilla/5.0"}


def _fetch_soup(url: str) -> BeautifulSoup:
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.encoding = response.apparent_encoding or response.encoding
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def _normalize(text: str) -> str:
    return re.sub(r"[\s\-_·/]", "", text).lower()


def _find_theme_no(theme_name: str) -> str | None:
    """테마 목록 페이지에서 테마명으로 themeNo 검색"""
    try:
        soup = _fetch_soup("https://finance.naver.com/sise/theme.naver")
    except Exception:
        return None

    normalized_target = _normalize(theme_name)
    best_no: str | None = None

    for link in soup.select('a[href*="theme_detail.naver"]'):
        name = link.get_text(strip=True)
        href = link.get("href", "")
        match = re.search(r"themeNo=(\d+)", href)
        if not match:
            continue
        normalized_name = _normalize(name)
        if normalized_name == normalized_target:
            return match.group(1)
        if normalized_target in normalized_name and best_no is None:
            best_no = match.group(1)

    return best_no


def _parse_theme_detail(theme_no: str) -> list[dict]:
    """테마 상세 페이지에서 종목 목록 파싱"""
    try:
        soup = _fetch_soup(
            f"https://finance.naver.com/sise/theme_detail.naver?themeNo={theme_no}"
        )
    except Exception:
        return []

    stocks: list[dict] = []
    for row in soup.select("table.type_1 tr, table.type_2 tr"):
        link = row.select_one('a[href*="/item/main.naver?code="]')
        if not link:
            continue
        cells = row.select("td")
        if len(cells) < 3:
            continue

        name = link.get_text(strip=True)
        if not name:
            continue

        price = cells[1].get_text(strip=True) if len(cells) > 1 else None
        change_pct_raw = cells[2].get_text(strip=True) if len(cells) > 2 else None

        # 등락률 부호 처리
        if change_pct_raw:
            sign_prefix = (
                "+" if any(t in (cells[2].get("class") or []) for t in ("up", "red"))
                else "-" if any(t in (cells[2].get("class") or []) for t in ("down", "blue"))
                else ""
            )
            if sign_prefix and not change_pct_raw.startswith(("+", "-", "▲", "▼")):
                change_pct_raw = sign_prefix + change_pct_raw

        stocks.append(
            {
                "name": name,
                "price": price,
                "change_pct": change_pct_raw,
                "market_cap": None,
                "per": None,
                "pbr": None,
            }
        )
        if len(stocks) >= 20:
            break

    return stocks


def get_theme_stocks(theme_name: str, use_mock_data: bool = True) -> list[dict]:
    if use_mock_data:
        return [
            {
                "name": "하나마이크론",
                "market_cap": "1.7조",
                "price": "164,200",
                "change_pct": "+3.1%",
                "per": "34.2",
                "pbr": "6.8",
            },
            {
                "name": "ISC",
                "market_cap": "1.9조",
                "price": "72,800",
                "change_pct": "-1.4%",
                "per": "19.3",
                "pbr": "2.7",
            },
        ]

    theme_no = _find_theme_no(theme_name)
    if not theme_no:
        return []
    return _parse_theme_detail(theme_no)

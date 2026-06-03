from __future__ import annotations

import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


HEADERS = {"User-Agent": "Mozilla/5.0"}
NAVER_FINANCE_BASE_URL = "https://finance.naver.com"


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

    for link in soup.select('a[href*="sise_group_detail.naver"][href*="type=theme"], a[href*="theme_detail.naver"]'):
        name = link.get_text(strip=True)
        href = link.get("href", "")
        match = re.search(r"(?:themeNo|no)=(\d+)", href)
        if not match:
            continue
        normalized_name = _normalize(name)
        if normalized_name == normalized_target:
            return match.group(1)
        if normalized_target in normalized_name and best_no is None:
            best_no = match.group(1)

    return best_no


def _compact_text(text: str | None) -> str | None:
    if not text:
        return None
    return re.sub(r"\s+", " ", text).strip()


def _extract_code(href: str | None) -> str | None:
    match = re.search(r"code=(\d{6})", href or "")
    return match.group(1) if match else None


def _parse_stock_valuation(code: str) -> dict:
    try:
        soup = _fetch_soup(f"{NAVER_FINANCE_BASE_URL}/item/main.naver?code={code}")
    except Exception:
        return {"market_cap": None, "per": None, "pbr": None}

    market_sum = soup.select_one("#_market_sum")
    per = soup.select_one("#_per")
    pbr = soup.select_one("#_pbr")
    market_cap = _compact_text(market_sum.parent.get_text(" ", strip=True)) if market_sum and market_sum.parent else None
    return {
        "market_cap": market_cap,
        "per": _compact_text(per.get_text(" ", strip=True)) if per else None,
        "pbr": _compact_text(pbr.get_text(" ", strip=True)) if pbr else None,
    }


def _parse_theme_detail(theme_no: str) -> list[dict]:
    """테마 상세 페이지에서 종목 목록 파싱"""
    try:
        soup = _fetch_soup(
            f"{NAVER_FINANCE_BASE_URL}/sise/sise_group_detail.naver?type=theme&no={theme_no}"
        )
    except Exception:
        return []

    stocks: list[dict] = []
    for row in soup.select("table.type_1 tr, table.type_2 tr, table.type_5 tr"):
        link = row.select_one('a[href*="/item/main.naver?code="]')
        if not link:
            continue
        cells = row.select("td")
        if len(cells) < 3:
            continue

        name = link.get_text(strip=True)
        if not name:
            continue

        cell_texts = [cell.get_text(" ", strip=True) for cell in cells]
        price_idx = 2 if len(cell_texts) > 4 and "테마 편입 사유" in cell_texts[1] else 1
        change_pct_idx = price_idx + 2
        price = cell_texts[price_idx] if len(cell_texts) > price_idx else None
        change_pct_raw = cell_texts[change_pct_idx] if len(cell_texts) > change_pct_idx else None

        # 등락률 부호 처리
        if change_pct_raw and len(cells) > change_pct_idx:
            sign_prefix = (
                "+" if any(t in (cells[change_pct_idx].get("class") or []) for t in ("up", "red"))
                else "-" if any(t in (cells[change_pct_idx].get("class") or []) for t in ("down", "blue"))
                else ""
            )
            if sign_prefix and not change_pct_raw.startswith(("+", "-", "▲", "▼")):
                change_pct_raw = sign_prefix + change_pct_raw

        code = _extract_code(urljoin(NAVER_FINANCE_BASE_URL, link.get("href", "")))
        valuation = _parse_stock_valuation(code) if code else {"market_cap": None, "per": None, "pbr": None}
        stocks.append(
            {
                "name": name,
                "price": price,
                "change_pct": change_pct_raw,
                "market_cap": valuation.get("market_cap"),
                "per": valuation.get("per"),
                "pbr": valuation.get("pbr"),
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

from __future__ import annotations

import logging
import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from src.utils.ttl_cache import get_ttl_cache, set_ttl_cache


HEADERS = {"User-Agent": "Mozilla/5.0"}
NAVER_FINANCE_BASE_URL = "https://finance.naver.com"
logger = logging.getLogger(__name__)


def _fetch_soup(url: str) -> BeautifulSoup:
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.encoding = response.apparent_encoding or response.encoding
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def _normalize(text: str) -> str:
    return re.sub(r"[\s\-_·/]", "", text).lower()


def _load_theme_directory() -> dict[str, str]:
    """네이버 테마 목록 전 페이지를 읽어 {정규화된 테마명: themeNo} 사전 구성.

    목록은 등락률순 페이지네이션이라 1페이지만 읽으면 그날 순위권 밖 테마를
    못 찾는다. 전체(~7페이지)를 읽고 1시간 캐시한다.
    """
    cached = get_ttl_cache("naver_theme_directory", ttl_seconds=3600)
    if cached is not None:
        return cached

    directory: dict[str, str] = {}
    for page in range(1, 11):
        soup = _fetch_soup(f"{NAVER_FINANCE_BASE_URL}/sise/theme.naver?page={page}")
        theme_links = soup.select(
            'a[href*="sise_group_detail.naver"][href*="type=theme"], a[href*="theme_detail.naver"]'
        )
        if not theme_links:
            break
        for link in theme_links:
            name = link.get_text(strip=True)
            href = link.get("href", "")
            match = re.search(r"(?:themeNo|no)=(\d+)", href)
            if not match or not name:
                continue
            directory.setdefault(_normalize(name), match.group(1))

    if not directory:
        logger.warning(
            "Naver parser returned 0 rows: theme_list (%s)",
            f"{NAVER_FINANCE_BASE_URL}/sise/theme.naver",
        )
        return directory
    if len(directory) < 50:
        # 중간 페이지가 빈 200 응답이면 부분 사전이 만들어질 수 있다 — 캐시하지 않고 다음 요청에 재시도
        logger.warning("Naver theme directory looks partial (%d entries) — not caching", len(directory))
        return directory
    return set_ttl_cache("naver_theme_directory", directory)


def _find_theme_no(theme_name: str) -> str | None:
    """테마 목록에서 테마명으로 themeNo 검색 (정확 일치 우선, 부분 일치 폴백)"""
    try:
        directory = _load_theme_directory()
    except Exception:
        return None

    normalized_target = _normalize(theme_name)
    if normalized_target in directory:
        return directory[normalized_target]
    for name, theme_no in directory.items():
        if normalized_target in name:
            return theme_no
    return None


def _compact_text(text: str | None) -> str | None:
    if not text:
        return None
    return re.sub(r"\s+", " ", text).strip()


def _normalize_market_cap(text: str | None) -> str | None:
    compacted = _compact_text(text)
    if not compacted:
        return None
    return re.sub(r"\s+(억원|조원|원)$", r"\1", compacted)


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
    market_cap = _normalize_market_cap(market_sum.parent.get_text(" ", strip=True)) if market_sum and market_sum.parent else None
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

    if not stocks:
        logger.warning(
            "Naver parser returned 0 rows: theme_detail (%s)",
            f"{NAVER_FINANCE_BASE_URL}/sise/sise_group_detail.naver?type=theme&no={theme_no}",
        )
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

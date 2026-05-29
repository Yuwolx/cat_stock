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


def _to_number(text: str) -> float | None:
    cleaned = re.sub(r"[^\d.-]", "", text or "")
    if not cleaned:
        return None
    return float(cleaned)


def _sum_numbers(*values: float | None) -> float | None:
    valid = [value for value in values if value is not None]
    if not valid:
        return None
    return round(sum(valid), 2)


def _parse_summary_from_links(soup: BeautifulSoup, href: str) -> dict[str, float | None]:
    summary = {"foreign": None, "institution": None, "retail": None}
    mapping = {"외국인": "foreign", "기관": "institution", "개인": "retail"}

    for anchor in soup.select(f'a[href="{href}"]'):
        text = anchor.get_text(" ", strip=True)
        match = re.search(r"(개인|외국인|기관)\s*([+-]?[0-9,]+)\s*억", text)
        if match:
            summary[mapping[match.group(1)]] = _to_number(match.group(2))

    if all(value is None for value in summary.values()):
        for anchor in soup.select(f'a[href="{href}"]'):
            parent_text = anchor.parent.parent.get_text(" ", strip=True) if anchor.parent and anchor.parent.parent else ""
            for label, number in re.findall(r"(개인|외국인|기관)\s*([+-]?[0-9,]+)\s*억", parent_text):
                summary[mapping[label]] = _to_number(number)

    return summary


def _parse_program_summary(soup: BeautifulSoup, href: str) -> dict[str, float | None]:
    summary = {"arbitrage": None, "non_arbitrage": None, "total": None}
    mapping = {"차익": "arbitrage", "비차익": "non_arbitrage", "전체": "total"}

    for anchor in soup.select(f'a[href="{href}"]'):
        text = anchor.parent.parent.get_text(" ", strip=True) if anchor.parent and anchor.parent.parent else anchor.get_text(" ", strip=True)
        matches = re.findall(r"(차익|비차익|전체)\s*([+-]?[0-9,]+)\s*억", text)
        if matches:
            for label, number in matches:
                summary[mapping[label]] = _to_number(number)
            break

    return summary


def _parse_name_table_from_page(url: str, limit: int = 10) -> list[str]:
    soup = _fetch_soup(url)
    items: list[str] = []
    selectors = ["table.type_2 tr", "table.type_5 tr"]
    seen_codes: set[str] = set()

    for selector in selectors:
        for row in soup.select(selector):
            link = row.select_one('a[href*="/item/main.naver?code="]') or row.select_one("a.tltle")
            if not link:
                continue
            href = link.get("href", "")
            if href in seen_codes:
                continue
            seen_codes.add(href)
            items.append(link.get_text(strip=True))
            if len(items) >= limit:
                return items
    return items


def _merge_unique(items: list[str], limit: int = 10) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        merged.append(item)
        if len(merged) >= limit:
            break
    return merged


def get_home_market_snapshot(use_mock_data: bool = True) -> dict:
    if use_mock_data:
        return {
            "investor_summary": {
                "kospi": {"foreign": -19522, "institution": 28224, "retail": -9137},
                "kosdaq": {"foreign": -834, "institution": -2303, "retail": 3057},
                "total": {"foreign": -20356, "institution": 25921, "retail": -6080},
            },
            "foreign_top_buy": ["삼성전자", "SK하이닉스", "현대차"],
            "foreign_top_sell": ["LG에너지솔루션", "POSCO홀딩스", "에코프로비엠"],
            "institution_top_buy": ["KB금융", "NAVER", "기아"],
            "institution_top_sell": ["삼성바이오로직스", "한화에어로스페이스", "셀트리온"],
            "program_summary": {
                "kospi": {"arbitrage": 5786, "non_arbitrage": -12723, "total": -6938},
                "kosdaq": {"arbitrage": 2, "non_arbitrage": -1456, "total": -1454},
                "total": {"arbitrage": 5788, "non_arbitrage": -14179, "total": -8392},
            },
            "upper_limit": ["녹십자홀딩스2우", "삼성전자우"],
        }

    soup = _fetch_soup("https://finance.naver.com/sise/")

    def parse_name_table(table_id: str, limit: int = 5) -> list[str]:
        table = soup.select_one(f"#{table_id}")
        if not table:
            return []
        names: list[str] = []
        for row in table.select("tr"):
            link = row.select_one("a")
            if link:
                names.append(link.get_text(strip=True))
            if len(names) >= limit:
                break
        return names

    investor_kospi = _parse_summary_from_links(soup, "/sise/sise_trans_style.naver")
    investor_kosdaq = _parse_summary_from_links(soup, "/sise/sise_trans_style.naver?sosok=02")
    program_kospi = _parse_program_summary(soup, "/sise/sise_program.naver")
    program_kosdaq = _parse_program_summary(soup, "/sise/sise_program.naver?sosok=02")

    return {
        "investor_summary": {
            "kospi": investor_kospi,
            "kosdaq": investor_kosdaq,
            "total": {
                "foreign": _sum_numbers(investor_kospi["foreign"], investor_kosdaq["foreign"]),
                "institution": _sum_numbers(investor_kospi["institution"], investor_kosdaq["institution"]),
                "retail": _sum_numbers(investor_kospi["retail"], investor_kosdaq["retail"]),
            },
        },
        "foreign_top_buy": parse_name_table("frgn_deal_tab_0"),
        "foreign_top_sell": parse_name_table("frgn_deal_tab_1"),
        "institution_top_buy": parse_name_table("organ_deal_tab_0"),
        "institution_top_sell": parse_name_table("organ_deal_tab_1"),
        "program_summary": {
            "kospi": program_kospi,
            "kosdaq": program_kosdaq,
            "total": {
                "arbitrage": _sum_numbers(program_kospi["arbitrage"], program_kosdaq["arbitrage"]),
                "non_arbitrage": _sum_numbers(program_kospi["non_arbitrage"], program_kosdaq["non_arbitrage"]),
                "total": _sum_numbers(program_kospi["total"], program_kosdaq["total"]),
            },
        },
        "upper_limit": _merge_unique(
            _parse_name_table_from_page("https://finance.naver.com/sise/sise_upper.naver", limit=10)
            + _parse_name_table_from_page("https://finance.naver.com/sise/sise_upper.naver?sosok=1", limit=10),
            limit=10,
        ),
    }


def get_trading_value_leaders(target_date: str, use_mock_data: bool = True) -> list[dict]:
    if use_mock_data:
        return [
            {"name": "삼성전자", "price": "79,200", "change_pct": 1.41, "turnover_krw_billion": 1765},
            {"name": "SK하이닉스", "price": "212,000", "change_pct": 3.92, "turnover_krw_billion": 1541},
            {"name": "현대차", "price": "241,500", "change_pct": 0.84, "turnover_krw_billion": 983},
        ]

    soup = _fetch_soup("https://finance.naver.com/sise/sise_quant.naver")
    items: list[dict] = []
    for row in soup.select("table.type_2 tr"):
        cells = [cell.get_text(" ", strip=True) for cell in row.select("td")]
        link = row.select_one("a.tltle")
        if not link or len(cells) < 7:
            continue

        turnover_million_krw = _to_number(cells[6])
        if turnover_million_krw is None:
            continue

        items.append(
            {
                "name": link.get_text(strip=True),
                "price": cells[2],
                "change_pct": _to_number(cells[4]),
                "turnover_krw_billion": round(turnover_million_krw / 100, 1),
            }
        )

    items.sort(key=lambda item: item["turnover_krw_billion"], reverse=True)
    return items[:20]


def get_market_event_lists(target_date: str, use_mock_data: bool = True) -> dict:
    if use_mock_data:
        return {
            "new_highs": ["HD현대일렉트릭", "두산", "한화오션"],
            "new_lows": ["에코프로", "에코프로비엠"],
            "upper_limit": ["녹십자홀딩스2우"],
            "after_hours_movers": ["하나머티리얼즈 +4.8%", "ISC -3.2%"],
        }

    snapshot = get_home_market_snapshot(use_mock_data=False)
    return {
        "new_highs": [],
        "new_lows": [],
        "upper_limit": snapshot.get("upper_limit", []),
        "after_hours_movers": [],
    }

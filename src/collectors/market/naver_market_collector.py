from __future__ import annotations

import logging
import re
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup


HEADERS = {"User-Agent": "Mozilla/5.0"}
NAVER_FINANCE_BASE_URL = "https://finance.naver.com"
logger = logging.getLogger(__name__)


def _warn_empty_parser(name: str, url: str) -> None:
    logger.warning("Naver parser returned 0 rows: %s (%s)", name, url)


def _fetch_soup(url: str, encoding: str | None = None) -> BeautifulSoup:
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.encoding = encoding or response.apparent_encoding or response.encoding
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
    try:
        soup = _fetch_soup(url)
    except Exception:
        return []
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


def _market_news_url_from_href(href: str) -> str | None:
    if not href:
        return None

    absolute_url = urljoin(NAVER_FINANCE_BASE_URL, href)
    query = parse_qs(urlparse(absolute_url).query)
    office_id = (query.get("office_id") or [""])[0]
    article_id = (query.get("article_id") or [""])[0]
    if office_id and article_id:
        return f"https://n.news.naver.com/mnews/article/{office_id}/{article_id}"
    return absolute_url


def _parse_market_news_items(soup: BeautifulSoup, limit: int = 12) -> list[dict]:
    items: list[dict] = []
    seen: set[str] = set()

    for link in soup.select(".articleSubject a"):
        title = link.get_text(" ", strip=True)
        if not title:
            continue

        url = _market_news_url_from_href(link.get("href", ""))
        key = url or title
        if key in seen:
            continue

        wrapper = link.find_parent("dl")
        summary = wrapper.select_one(".articleSummary") if wrapper else None
        source = summary.select_one(".press").get_text(" ", strip=True) if summary and summary.select_one(".press") else ""
        date_text = summary.select_one(".wdate").get_text(" ", strip=True) if summary and summary.select_one(".wdate") else ""

        items.append({"title": title, "url": url or "", "source": source, "date": date_text})
        seen.add(key)
        if len(items) >= limit:
            break

    return items


def get_market_news(use_mock_data: bool = True, limit: int = 12) -> list[dict]:
    if use_mock_data:
        return [
            {
                "title": "코스피 강세 속 반도체주 거래대금 증가",
                "url": "https://n.news.naver.com/mnews/article/000/0000000001",
                "source": "샘플경제",
                "date": "2026-06-03 09:00:00",
            },
            {
                "title": "원달러 환율 안정에 외국인 수급 개선",
                "url": "https://n.news.naver.com/mnews/article/000/0000000002",
                "source": "샘플뉴스",
                "date": "2026-06-03 10:00:00",
            },
        ][:limit]

    try:
        url = f"{NAVER_FINANCE_BASE_URL}/news/mainnews.naver"
        soup = _fetch_soup(url, encoding="euc-kr")
        items = _parse_market_news_items(soup, limit=limit)
        if not items:
            _warn_empty_parser("market_news", url)
        return items
    except Exception as exc:
        logger.warning("Naver parser failed: market_news (%s)", exc)
        return []


def get_sector_changes(use_mock_data: bool = True) -> list[dict]:
    """테마/그룹별 등락률 수집 (네이버 sise_group.naver)

    실제 페이지 컬럼 구조 (검증 완료):
      cells[0] = 테마/그룹명  cells[1] = 전일대비(%)  cells[2~] = 종목 수 등
    """
    if use_mock_data:
        return [
            {"name": "반도체", "change_pct": +2.8},
            {"name": "자동차", "change_pct": +1.1},
            {"name": "2차전지", "change_pct": -1.4},
            {"name": "바이오", "change_pct": +0.6},
            {"name": "은행", "change_pct": +0.3},
        ]

    try:
        url = "https://finance.naver.com/sise/sise_group.naver"
        soup = _fetch_soup(url)
        items: list[dict] = []
        for row in soup.select("table.type_1 tr"):
            link = row.select_one("a")
            cells = row.select("td")
            if not link or len(cells) < 2:
                continue
            name = link.get_text(strip=True)
            if not name:
                continue
            # cells[1] = 전일대비 등락률 (예: "+11.90%", "-2.30%")
            rate_text = cells[1].get_text(strip=True).replace("%", "").replace("+", "")
            rate = _to_number(rate_text)
            items.append({"name": name, "change_pct": rate})
            if len(items) >= 20:
                break
        if not items:
            _warn_empty_parser("sector_changes", url)
        return items
    except Exception as exc:
        logger.warning("Naver parser failed: sector_changes (%s)", exc)
        return []


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

    url = "https://finance.naver.com/sise/sise_quant.naver"
    soup = _fetch_soup(url)
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
    result = items[:20]
    if not result:
        _warn_empty_parser("trading_value_leaders", url)
    return result


def _stock_code_from_href(href: str) -> str | None:
    match = re.search(r"code=(\d{6})", href or "")
    return match.group(1) if match else None


def _with_page(url: str, page: int) -> str:
    if page <= 1:
        return url
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}page={page}"


def _parse_rise_fall_rows(url: str, market: str | None = None) -> list[dict]:
    rows: list[dict] = []
    try:
        soup = _fetch_soup(url)
    except Exception:
        return rows

    for row in soup.select("table.type_2 tr"):
        link = row.select_one('a[href*="/item/main.naver?code="]') or row.select_one("a.tltle")
        cells = [cell.get_text(" ", strip=True) for cell in row.select("td")]
        if not link or len(cells) < 5:
            continue

        href = link.get("href", "")
        change_pct_text = cells[4]
        rows.append(
            {
                "name": link.get_text(strip=True),
                "code": _stock_code_from_href(href),
                "market": market,
                "price": cells[2] if len(cells) > 2 else None,
                "change_text": cells[3] if len(cells) > 3 else None,
                "change_pct": _to_number(change_pct_text),
                "change_pct_text": change_pct_text,
            }
        )

    return rows


def _format_rise_fall_item(item: dict) -> str:
    rate = item.get("change_pct_text")
    return f"{item['name']} {rate}" if rate else item["name"]


def _parse_rise_fall_page(url: str, limit: int = 10) -> list[str]:
    """상승/하락 종목 페이지에서 종목명 + 등락률 파싱"""
    return [_format_rise_fall_item(item) for item in _parse_rise_fall_rows(url)[:limit]]


def _collect_rise_fall_rankings(
    market_urls: list[tuple[str, str]],
    limit: int,
    *,
    descending: bool,
    max_pages: int = 2,
) -> list[str]:
    rows: list[dict] = []
    seen: set[str] = set()

    for market, url in market_urls:
        market_rows: list[dict] = []
        for page in range(1, max_pages + 1):
            page_rows = _parse_rise_fall_rows(_with_page(url, page), market=market)
            if not page_rows:
                break
            for row in page_rows:
                key = row.get("code") or row["name"]
                if key in seen:
                    continue
                seen.add(key)
                market_rows.append(row)
                rows.append(row)
            if len(market_rows) >= limit:
                break

    rows.sort(key=lambda item: item.get("change_pct") if item.get("change_pct") is not None else 0, reverse=descending)
    return [_format_rise_fall_item(item) for item in rows[:limit]]


def _parse_nxt_movers(limit: int = 10) -> list[str]:
    """시간외 단일가(NXT) 급등락 종목 — nxt_sise_rise/fall.naver"""
    movers: list[str] = []
    for url in (
        "https://finance.naver.com/sise/nxt_sise_rise.naver",
        "https://finance.naver.com/sise/nxt_sise_fall.naver",
    ):
        movers.extend(_parse_rise_fall_page(url, limit=limit // 2 + 1))
    return movers[:limit]


def get_rising_stocks_over_threshold(
    threshold_pct: float = 5.0,
    limit: int = 30,
    max_pages: int = 3,
    use_mock_data: bool = True,
) -> list[dict]:
    if use_mock_data:
        return [
            {
                "name": "LG헬로비전",
                "code": "037560",
                "market": "KOSPI",
                "price": "2,860",
                "change_pct": 30.0,
                "change_pct_text": "+30.00%",
            },
            {
                "name": "로보스타",
                "code": "090360",
                "market": "KOSDAQ",
                "price": "122,200",
                "change_pct": 30.0,
                "change_pct_text": "+30.00%",
            },
            {
                "name": "LG씨엔에스",
                "code": "064400",
                "market": "KOSPI",
                "price": "143,700",
                "change_pct": 26.27,
                "change_pct_text": "+26.27%",
            },
        ][:limit]

    items: list[dict] = []
    seen: set[str] = set()
    market_urls = [
        ("KOSPI", "https://finance.naver.com/sise/sise_rise.naver?sosok=0"),
        ("KOSDAQ", "https://finance.naver.com/sise/sise_rise.naver?sosok=1"),
    ]

    for market, url in market_urls:
        for page in range(1, max_pages + 1):
            page_rows = _parse_rise_fall_rows(_with_page(url, page), market=market)
            if not page_rows:
                break

            reached_below_threshold = False
            for row in page_rows:
                change_pct = row.get("change_pct")
                if change_pct is None:
                    continue
                if change_pct < threshold_pct:
                    reached_below_threshold = True
                    continue

                key = row.get("code") or row["name"]
                if key in seen:
                    continue
                seen.add(key)
                items.append(row)

            if reached_below_threshold:
                break

    items.sort(key=lambda item: item.get("change_pct") or 0, reverse=True)
    return items[:limit]


def get_market_event_lists(target_date: str, use_mock_data: bool = True) -> dict:
    if use_mock_data:
        return {
            "new_highs": [f"상승상위{i} +{50 - i / 10:.2f}%" for i in range(1, 51)],
            "new_lows": [f"하락상위{i} -{20 - i / 10:.2f}%" for i in range(1, 21)],
            "upper_limit": ["녹십자홀딩스2우"],
            "after_hours_movers": ["하나머티리얼즈 +4.8%", "ISC -3.2%"],
            "rising_over_5pct": get_rising_stocks_over_threshold(use_mock_data=True),
        }

    snapshot = get_home_market_snapshot(use_mock_data=False)

    # 52주 신고가/신저가 URL(sise_high/low.naver)은 네이버에서 폐기됨
    # 당일 상승/하락 상위 종목으로 대체 (sise_rise/fall.naver)
    daily_highs = _collect_rise_fall_rankings(
        [
            ("KOSPI", "https://finance.naver.com/sise/sise_rise.naver?sosok=0"),
            ("KOSDAQ", "https://finance.naver.com/sise/sise_rise.naver?sosok=1"),
        ],
        limit=50,
        descending=True,
    )
    daily_lows = _collect_rise_fall_rankings(
        [
            ("KOSPI", "https://finance.naver.com/sise/sise_fall.naver?sosok=0"),
            ("KOSDAQ", "https://finance.naver.com/sise/sise_fall.naver?sosok=1"),
        ],
        limit=20,
        descending=False,
    )
    if not daily_highs:
        _warn_empty_parser("daily_rise_rankings", "https://finance.naver.com/sise/sise_rise.naver")
    if not daily_lows:
        _warn_empty_parser("daily_fall_rankings", "https://finance.naver.com/sise/sise_fall.naver")

    return {
        "new_highs": daily_highs,
        "new_lows": daily_lows,
        "upper_limit": snapshot.get("upper_limit", []),
        "after_hours_movers": _parse_nxt_movers(limit=10),
        "rising_over_5pct": get_rising_stocks_over_threshold(use_mock_data=False),
    }

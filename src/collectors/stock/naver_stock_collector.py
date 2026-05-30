from __future__ import annotations

import re
from datetime import date, timedelta
from functools import lru_cache
from io import StringIO

import FinanceDataReader as fdr
import pandas as pd
import requests
from bs4 import BeautifulSoup


HEADERS = {"User-Agent": "Mozilla/5.0"}


def _normalize_name(name: str) -> str:
    return re.sub(r"\s+", "", name).strip().lower()


@lru_cache(maxsize=1)
def _get_listing() -> pd.DataFrame:
    try:
        df = fdr.StockListing("KRX")
        if not df.empty:
            return df
    except Exception:
        pass
    return pd.DataFrame(columns=["Code", "Name"])


def _find_stock_row(stock_name: str) -> pd.Series | None:
    listing = _get_listing().copy()
    normalized_target = _normalize_name(stock_name)
    normalized_names = listing["Name"].astype(str).map(_normalize_name)

    exact = listing.loc[normalized_names == normalized_target]
    if not exact.empty:
        return exact.iloc[0]

    contains = listing.loc[normalized_names.str.contains(normalized_target, na=False, regex=False)]
    if not contains.empty:
        return contains.iloc[0]
    return None


def get_stock_code(stock_name: str) -> str | None:
    row = _find_stock_row(stock_name)
    if row is not None:
        return str(row["Code"]).zfill(6)
    return _search_stock_code_naver(stock_name)


def _search_stock_code_naver(stock_name: str) -> str | None:
    try:
        resp = requests.get(
            "https://ac.stock.naver.com/ac",
            params={"q": stock_name, "target": "stock,index,marketindicator"},
            headers=HEADERS,
            timeout=10,
        )
        items = resp.json().get("items", [])
        for item in items:
            code = item.get("code", "")
            name = item.get("name", "")
            if _normalize_name(name) == _normalize_name(stock_name) and len(code) == 6:
                return code
        if items:
            code = items[0].get("code", "")
            return code if len(code) == 6 else None
    except Exception:
        pass
    return None


def _fetch(url: str, encoding: str | None = None) -> str:
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()
    response.encoding = encoding or response.apparent_encoding or response.encoding
    return response.text


def _fetch_soup(url: str, encoding: str | None = None) -> BeautifulSoup:
    return BeautifulSoup(_fetch(url, encoding=encoding), "html.parser")


def _read_html_tables(url: str, encoding: str = "utf-8") -> list[pd.DataFrame]:
    html = _fetch(url, encoding=encoding)
    return pd.read_html(StringIO(html))


def _to_number(text: str | None) -> float | None:
    raw = (text or "").strip()
    if not raw:
        return None

    sign = -1 if any(token in raw for token in ("▼", "▽")) else 1
    cleaned = re.sub(r"[^\d.]", "", raw)
    if not cleaned:
        return None
    try:
        value = float(cleaned)
    except ValueError:
        return None
    if sign < 0:
        return -value
    return value


def _format_signed_shares(quantity: float | None) -> str | None:
    if quantity is None or pd.isna(quantity):
        return None
    return f"{int(quantity):+,}주"


def _format_market_cap(marcap: float | int | None) -> str | None:
    if marcap is None or pd.isna(marcap):
        return None
    try:
        value = float(marcap)
    except (TypeError, ValueError):
        return None
    if value >= 1_000_000_000_000:
        return f"{value / 1_000_000_000_000:.1f}조"
    return f"{value / 100_000_000:.0f}억"


def _parse_main_basics(code: str) -> dict:
    soup = _fetch_soup(f"https://finance.naver.com/item/main.naver?code={code}", encoding="cp949")

    title = soup.title.get_text(strip=True).split(":")[0] if soup.title else code
    price_node = soup.select_one("p.no_today span.blind")
    current_price = price_node.get_text(strip=True) if price_node else None

    change_node = soup.select_one("p.no_exday em span.blind")
    change_point = change_node.get_text(strip=True) if change_node else None
    change_rate_node = soup.select_one(
        "p.no_exday em.no_up span.blind, p.no_exday em.no_down span.blind, p.no_exday em.no_sgap span.blind"
    )
    change_pct = change_rate_node.get_text(strip=True) if change_rate_node else None

    no_info_values = [span.get_text(strip=True) for span in soup.select("table.no_info span.blind")]
    turnover_billion = None
    year_high_low = None
    if len(no_info_values) >= 11:
        turnover_million = _to_number(no_info_values[10])
        turnover_billion = round((turnover_million or 0) / 100, 1) if turnover_million else None
    if len(no_info_values) >= 8:
        year_high_low = f"{no_info_values[6]} / {no_info_values[7]}"

    per = soup.select_one("#_per")
    pbr = soup.select_one("#_pbr")

    roe = None
    financial_table = soup.select_one("table.tb_type1.tb_num.tb_type1_ifrs")
    if financial_table:
        for row in financial_table.select("tr"):
            header = row.select_one("th")
            if not header:
                continue
            header_text = header.get_text(" ", strip=True)
            if "ROE" in header_text:
                values = [td.get_text(" ", strip=True) for td in row.select("td") if td.get_text(" ", strip=True)]
                if values:
                    roe = values[-1]
                break

    return {
        "name": title or code,
        "price": current_price,
        "change_point": change_point,
        "change_pct": f"{change_pct}%" if change_pct and not str(change_pct).endswith("%") else change_pct,
        "turnover_krw_billion": turnover_billion,
        "year_high_low": year_high_low,
        "per": per.get_text(strip=True) if per else None,
        "pbr": pbr.get_text(strip=True) if pbr else None,
        "roe": f"{roe}%" if roe and not str(roe).endswith("%") else roe,
    }


def _get_frgn_tables(code: str) -> list[pd.DataFrame]:
    return _read_html_tables(
        f"https://finance.naver.com/item/frgn.naver?code={code}&page=1",
        encoding="cp949",
    )


def _build_ma_position(code: str) -> dict[str, str | None]:
    start = (date.today() - timedelta(days=160)).strftime("%Y-%m-%d")
    history = fdr.DataReader(code, start)
    if history.empty or "Close" not in history.columns or len(history) < 60:
        return {"ma5": None, "ma20": None, "ma60": None}

    closes = history["Close"].astype(float)
    latest_close = float(closes.iloc[-1])

    def compare(window: int) -> str | None:
        if len(closes) < window:
            return None
        ma_value = float(closes.tail(window).mean())
        diff_pct = ((latest_close - ma_value) / ma_value) * 100 if ma_value else 0
        if diff_pct > 1:
            return f"상회 ({diff_pct:+.2f}%)"
        if diff_pct < -1:
            return f"하회 ({diff_pct:+.2f}%)"
        return f"근접 ({diff_pct:+.2f}%)"

    return {
        "ma5": compare(5),
        "ma20": compare(20),
        "ma60": compare(60),
    }


def _parse_investor_flow_table(code: str) -> pd.DataFrame:
    tables = _get_frgn_tables(code)
    for table in tables:
        if table.shape[1] >= 9 and table.shape[0] >= 5:
            df = table.copy()
            first_value = str(df.iloc[1, 0]) if len(df.index) > 1 else ""
            if not re.match(r"\d{4}\.\d{2}\.\d{2}", first_value):
                continue
            df.columns = [
                "date",
                "close",
                "change",
                "change_pct",
                "volume",
                "institution",
                "foreign",
                "foreign_holdings",
                "foreign_ratio",
            ]
            return df
    return pd.DataFrame()


def _parse_consensus_from_frgn(code: str) -> dict[str, str | None]:
    tables = _get_frgn_tables(code)
    for table in tables:
        if table.shape != (2, 2):
            continue

        first_label = str(table.iloc[0, 0]).strip()
        second_label = str(table.iloc[1, 0]).strip()
        if "목표주가" not in first_label or "52주" not in second_label:
            continue

        target_cell = str(table.iloc[0, 1]).strip()
        year_high_low_cell = str(table.iloc[1, 1]).strip()

        target_match = re.search(r"([0-9,]+)\s*$", target_cell)
        opinion_match = re.search(r"(매수|중립|보유|시장수익률|매도)", target_cell)

        target_price = f"{target_match.group(1)}원" if target_match else None
        year_high_low = year_high_low_cell.replace("l", "/").replace(" ", "")

        return {
            "target_price": target_price,
            "opinion": opinion_match.group(1) if opinion_match else None,
            "year_high_low": year_high_low,
        }
    return {"target_price": None, "opinion": None, "year_high_low": None}


def _parse_news_results(stock_name: str, limit: int = 6) -> list[str]:
    code = _search_stock_code_naver(stock_name)
    if code:
        return _parse_news_by_code(code, limit)
    return []


def _parse_news_by_code(code: str, limit: int = 6) -> list[str]:
    try:
        response = requests.get(
            f"https://finance.naver.com/item/news_news.naver?code={code}&page=1&clusterId=",
            headers={**HEADERS, "Referer": f"https://finance.naver.com/item/news.naver?code={code}"},
            timeout=20,
        )
        response.encoding = "euc-kr"
        soup = BeautifulSoup(response.text, "html.parser")
        items: list[str] = []
        for row in soup.select("tr"):
            title = row.select_one("td.title a")
            info = row.select_one("td.info")
            date = row.select_one("td.date")
            if not title:
                continue
            text = title.get_text(strip=True)
            source = info.get_text(strip=True) if info else ""
            date_str = date.get_text(strip=True) if date else ""
            line = f"{text}" + (f" ({source}, {date_str})" if source else "")
            items.append(line)
            if len(items) >= limit:
                break
        return items
    except Exception:
        return []


def _parse_report_rows(code: str, limit: int = 5) -> list[dict]:
    soup = _fetch_soup(
        f"https://finance.naver.com/research/company_list.naver?searchType=itemCode&itemCode={code}",
        encoding="cp949",
    )
    items: list[dict] = []
    for row in soup.select("table.type_1 tr"):
        report_link = row.select_one('a[href*="company_read.naver"]')
        if not report_link:
            continue
        row_text = [segment.strip() for segment in row.get_text(" | ", strip=True).split("|") if segment.strip()]
        title = report_link.get_text(strip=True)
        broker = row_text[2] if len(row_text) > 2 else None
        report_date = row_text[3] if len(row_text) > 3 else None
        pdf_link = None
        for anchor in row.select("a[href]"):
            href = anchor.get("href", "")
            if href.endswith(".pdf"):
                pdf_link = href
                break
        items.append(
            {
                "title": title,
                "broker": broker,
                "date": report_date,
                "detail_url": f"https://finance.naver.com/research/{report_link.get('href')}",
                "pdf_url": pdf_link,
            }
        )
        if len(items) >= limit:
            break
    return items


def _enrich_report(item: dict) -> dict:
    try:
        soup = _fetch_soup(item["detail_url"], encoding="cp949")
    except Exception:
        return {**item, "opinion": None, "target_price": None}

    header_values = [em.get_text(strip=True) for em in soup.select("em")]
    target_price = None
    opinion = None
    if len(header_values) >= 3:
        target_price = header_values[1]
        opinion = header_values[2]

    if not target_price or not opinion:
        first_td = soup.select_one("table td")
        if first_td:
            first_td_text = first_td.get_text(" ", strip=True)
            target_match = re.search(r"목표가\s*([0-9,]+)", first_td_text)
            opinion_match = re.search(r"투자의견\s*([가-힣A-Za-z]+)", first_td_text)
            if target_match and not target_price:
                target_price = target_match.group(1)
            if opinion_match and not opinion:
                opinion = opinion_match.group(1)

    return {
        **item,
        "target_price": f"{target_price}원" if target_price and not str(target_price).endswith("원") else target_price,
        "opinion": opinion,
    }


def get_stock_basics(stock_name: str, use_mock_data: bool = True) -> dict:
    if use_mock_data:
        return {
            "name": stock_name,
            "price": "78,500",
            "change_pct": "+1.82%",
            "turnover_krw_billion": 842,
            "market_cap": "46.8조",
            "year_high_low": "88,000 / 61,500",
            "per": "18.4",
            "pbr": "1.52",
            "roe": "12.8%",
            "ma_position": {"ma5": "상회 (+2.10%)", "ma20": "상회 (+6.30%)", "ma60": "근접 (+0.85%)"},
        }

    row = _find_stock_row(stock_name)
    if row is None:
        return {
            "name": stock_name,
            "price": None,
            "change_pct": None,
            "turnover_krw_billion": None,
            "market_cap": None,
            "year_high_low": None,
            "per": None,
            "pbr": None,
            "roe": None,
            "ma_position": {"ma5": None, "ma20": None, "ma60": None},
        }

    code = str(row["Code"]).zfill(6)
    basics = _parse_main_basics(code)
    consensus = _parse_consensus_from_frgn(code)
    history_start = (date.today() - timedelta(days=370)).strftime("%Y-%m-%d")
    history = fdr.DataReader(code, history_start)

    basics["name"] = str(row["Name"])
    basics["code"] = code
    basics["market_cap"] = _format_market_cap(row.get("Marcap"))
    basics["price"] = f"{int(row['Close']):,}" if pd.notna(row.get("Close")) else basics.get("price")
    change_ratio = row.get("ChagesRatio")
    basics["change_pct"] = f"{float(change_ratio):+.2f}%" if pd.notna(change_ratio) else basics.get("change_pct")
    amount = row.get("Amount")
    basics["turnover_krw_billion"] = (
        round(float(amount) / 100_000_000, 1) if pd.notna(amount) else basics.get("turnover_krw_billion")
    )
    if not history.empty:
        basics["year_high_low"] = f"{int(history['High'].max()):,} / {int(history['Low'].min()):,}"
    elif consensus.get("year_high_low"):
        basics["year_high_low"] = consensus["year_high_low"]
    basics["ma_position"] = _build_ma_position(code)
    return basics


def get_stock_investor_flows(stock_name: str, use_mock_data: bool = True) -> dict:
    if use_mock_data:
        return {
            "foreign_20d": "+1,245,000주",
            "institution_20d": "-342,000주",
            "news": [
                f"{stock_name}: 업황 개선 기대감 관련 기사",
                f"{stock_name}: 증권사 목표가 상향 기사",
            ],
            "naver_reports": [
                f"{stock_name}: 매수 / 목표가 95,000원",
            ],
        }

    row = _find_stock_row(stock_name)
    if row is None:
        return {"foreign_20d": None, "institution_20d": None, "news": [], "naver_reports": []}

    code = str(row["Code"]).zfill(6)
    flow_df = _parse_investor_flow_table(code)
    foreign_sum = None
    institution_sum = None
    if not flow_df.empty:
        flow_df = flow_df.dropna(subset=["date"]).head(20).copy()
        flow_df["foreign"] = pd.to_numeric(flow_df["foreign"], errors="coerce")
        flow_df["institution"] = pd.to_numeric(flow_df["institution"], errors="coerce")
        foreign_sum = flow_df["foreign"].sum(min_count=1)
        institution_sum = flow_df["institution"].sum(min_count=1)

    report_rows = [_enrich_report(item) for item in _parse_report_rows(code, limit=5)]
    naver_report_lines = []
    for item in report_rows:
        segments = [s for s in [item.get("broker"), item.get("opinion"), item.get("target_price"), item.get("date")] if s]
        line = f"{item['title']}" + (f" | {' / '.join(segments)}" if segments else "")
        naver_report_lines.append(line)

    return {
        "foreign_20d": _format_signed_shares(foreign_sum),
        "institution_20d": _format_signed_shares(institution_sum),
        "news": _parse_news_by_code(code, limit=6),
        "naver_reports": naver_report_lines,
    }

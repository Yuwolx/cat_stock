from __future__ import annotations

import re

import requests
from bs4 import BeautifulSoup

from src.collectors.market.naver_market_collector import get_home_market_snapshot


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


def _parse_index_page(index_code: str) -> dict:
    soup = _fetch_soup(f"https://finance.naver.com/sise/sise_index.naver?code={index_code}")

    now_value = _to_number(soup.select_one("#now_value").get_text(strip=True))
    change_text = soup.select_one("#change_value_and_rate").get_text(" ", strip=True)
    amount_text = soup.select_one("#amount").get_text(strip=True)
    matches = re.findall(r"([+-]?[0-9,]+(?:\.\d+)?)", change_text)

    change_points = _to_number(matches[0]) if matches else None
    change_pct = _to_number(matches[1]) if len(matches) > 1 else None
    amount_million_krw = _to_number(amount_text)

    return {
        "close": now_value,
        "change_pct": change_pct,
        "turnover_trillion_krw": round((amount_million_krw or 0) / 1_000_000, 2) if amount_million_krw else None,
        "change_points": change_points,
    }


def get_market_indices(target_date: str, use_mock_data: bool = True) -> dict:
    if use_mock_data:
        return {
            "kospi": {"close": 2647.4, "change_pct": 0.84, "turnover_trillion_krw": 12.8, "change_points": 22.41},
            "kosdaq": {"close": 845.1, "change_pct": -0.12, "turnover_trillion_krw": 7.1, "change_points": -1.03},
        }

    try:
        return {
            "kospi": _parse_index_page("KOSPI"),
            "kosdaq": _parse_index_page("KOSDAQ"),
        }
    except Exception:
        return {
            "kospi": {"close": None, "change_pct": None, "turnover_trillion_krw": None, "change_points": None},
            "kosdaq": {"close": None, "change_pct": None, "turnover_trillion_krw": None, "change_points": None},
        }


def get_investor_flows(target_date: str, use_mock_data: bool = True) -> dict:
    if use_mock_data:
        return {
            "summary": {"foreign": -20356, "institution": 25921, "retail": -6080},
            "by_market": {
                "kospi": {"foreign": -19522, "institution": 28224, "retail": -9137},
                "kosdaq": {"foreign": -834, "institution": -2303, "retail": 3057},
            },
            "foreign_top_buy": ["삼성전자", "SK하이닉스", "현대차"],
            "foreign_top_sell": ["LG에너지솔루션", "POSCO홀딩스", "에코프로비엠"],
            "institution_top_buy": ["KB금융", "NAVER", "기아"],
            "institution_top_sell": ["삼성바이오로직스", "한화에어로스페이스", "셀트리온"],
        }

    try:
        snapshot = get_home_market_snapshot(use_mock_data=False)
    except Exception:
        snapshot = {}

    return {
        "summary": snapshot.get("investor_summary", {}).get(
            "total",
            {"foreign": None, "institution": None, "retail": None},
        ),
        "by_market": {
            "kospi": snapshot.get("investor_summary", {}).get(
                "kospi",
                {"foreign": None, "institution": None, "retail": None},
            ),
            "kosdaq": snapshot.get("investor_summary", {}).get(
                "kosdaq",
                {"foreign": None, "institution": None, "retail": None},
            ),
        },
        "foreign_top_buy": snapshot.get("foreign_top_buy", []),
        "foreign_top_sell": snapshot.get("foreign_top_sell", []),
        "institution_top_buy": snapshot.get("institution_top_buy", []),
        "institution_top_sell": snapshot.get("institution_top_sell", []),
    }


def get_derivatives_snapshot(target_date: str, use_mock_data: bool = True) -> dict:
    if use_mock_data:
        return {
            "futures_foreign_net": 3421,
            "futures_institution_net": -1187,
            "program_arbitrage": 5788,
            "program_non_arbitrage": -14179,
            "program_total": -8392,
            "program_by_market": {
                "kospi": {"arbitrage": 5786, "non_arbitrage": -12723, "total": -6938},
                "kosdaq": {"arbitrage": 2, "non_arbitrage": -1456, "total": -1454},
            },
        }

    try:
        snapshot = get_home_market_snapshot(use_mock_data=False)
    except Exception:
        snapshot = {}

    total_program = snapshot.get("program_summary", {}).get("total", {})
    return {
        "futures_foreign_net": None,
        "futures_institution_net": None,
        "program_arbitrage": total_program.get("arbitrage"),
        "program_non_arbitrage": total_program.get("non_arbitrage"),
        "program_total": total_program.get("total"),
        "program_by_market": {
            "kospi": snapshot.get("program_summary", {}).get(
                "kospi",
                {"arbitrage": None, "non_arbitrage": None, "total": None},
            ),
            "kosdaq": snapshot.get("program_summary", {}).get(
                "kosdaq",
                {"arbitrage": None, "non_arbitrage": None, "total": None},
            ),
        },
    }

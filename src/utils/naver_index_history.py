"""네이버 금융 지수 일별 시세 (siseJson) 공용 fetch.

거래일 보정(date_utils)과 지수 흐름 수집(global_collector)이 함께 사용한다.
응답은 파이썬 리터럴 형태의 2차원 배열:
[['날짜', '시가', '고가', '저가', '종가', '거래량', '외국인소진율'], ["20260601", ...], ...]
"""

from __future__ import annotations

import ast
from datetime import date

import requests

NAVER_INDEX_URL = "https://api.finance.naver.com/siseJson.naver"
_HEADERS = {"User-Agent": "Mozilla/5.0"}


def fetch_index_daily_rows(symbol: str, start: date, end: date) -> list[list]:
    """지수(KOSPI/KOSDAQ) 일별 시세 행 목록을 과거→최근 순서로 반환."""
    params = {
        "symbol": symbol,
        "requestType": "1",
        "startTime": start.strftime("%Y%m%d"),
        "endTime": end.strftime("%Y%m%d"),
        "timeframe": "day",
    }
    response = requests.get(NAVER_INDEX_URL, params=params, headers=_HEADERS, timeout=10)
    response.raise_for_status()
    rows = ast.literal_eval(response.text.strip())
    return [row for row in rows[1:] if isinstance(row, list) and len(row) >= 5]


def fetch_index_closes(symbol: str, start: date, end: date) -> list[float]:
    """지수 종가 목록 (과거→최근)."""
    return [
        float(row[4])
        for row in fetch_index_daily_rows(symbol, start, end)
        if isinstance(row[4], (int, float))
    ]

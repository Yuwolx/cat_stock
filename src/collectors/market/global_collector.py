from __future__ import annotations

from datetime import datetime, timedelta

import FinanceDataReader as fdr
import pandas as pd

from src.utils.naver_index_history import fetch_index_closes


GLOBAL_SYMBOLS = {
    "dow": "DJI",
    "sp500": "S&P500",
    "nasdaq": "IXIC",
    "usdkrw": "USD/KRW",
    "us10y": "US10YT",
    "wti": "CL=F",
    "shanghai": "SSEC",
    "shenzhen": "SZSC",
}

KOREAN_INDEX_SYMBOLS = {
    "kospi": "KOSPI",
    "kosdaq": "KOSDAQ",
}


def get_korean_index_trend(target_date: str, use_mock_data: bool = True) -> dict:
    """코스피/코스닥 최근 종가 흐름 (과거→최근, 최대 10거래일)."""
    if use_mock_data:
        return {
            "kospi": {"closes": [2588.3, 2601.2, 2612.8, 2598.4, 2624.9, 2640.6]},
            "kosdaq": {"closes": [829.5, 832.1, 835.7, 838.2, 836.9, 840.3]},
        }

    target = datetime.strptime(target_date, "%Y-%m-%d").date()
    start = target - timedelta(days=30)
    result: dict[str, dict] = {}
    for key, symbol in KOREAN_INDEX_SYMBOLS.items():
        try:
            closes = fetch_index_closes(symbol, start, target)
        except Exception:
            closes = []
        result[key] = {"closes": closes[-10:]}
    return result


def _read_series(symbol: str, target_date: str) -> pd.DataFrame:
    target = datetime.strptime(target_date, "%Y-%m-%d").date()
    start = (target - timedelta(days=14)).strftime("%Y-%m-%d")
    df = fdr.DataReader(symbol, start)
    if df.empty:
        return df
    df = df[df.index.date <= target]
    if "Close" in df.columns:
        df = df[df["Close"].notna()]
    return df.tail(2)


def _format_change(df: pd.DataFrame) -> str | None:
    if len(df) < 2:
        return None
    latest_close = float(df["Close"].iloc[-1])
    prev_close = float(df["Close"].iloc[-2])
    if prev_close == 0:
        return None
    pct = ((latest_close - prev_close) / prev_close) * 100
    return f"{pct:+.2f}%"


def _format_last_close(df: pd.DataFrame, prefix: str = "", suffix: str = "") -> str | None:
    if df.empty:
        return None
    latest_close = float(df["Close"].iloc[-1])
    if latest_close >= 1000:
        return f"{prefix}{latest_close:,.2f}{suffix}"
    return f"{prefix}{latest_close:.2f}{suffix}"


def get_global_macro_snapshot(target_date: str, use_mock_data: bool = True) -> dict:
    if use_mock_data:
        return {
            "dow": "+0.36%",
            "sp500": "+0.74%",
            "nasdaq": "+1.21%",
            "usdkrw": "1,361.40",
            "us10y": "4.42%",
            "wti": "$77.31",
            "shanghai": "-0.28%",
            "shenzhen": "+0.11%",
        }

    def safe_read(key: str) -> pd.DataFrame:
        try:
            return _read_series(GLOBAL_SYMBOLS[key], target_date)
        except Exception:
            return pd.DataFrame()

    dow_df = safe_read("dow")
    sp_df = safe_read("sp500")
    nasdaq_df = safe_read("nasdaq")
    fx_df = safe_read("usdkrw")
    us10y_df = safe_read("us10y")
    wti_df = safe_read("wti")
    sh_df = safe_read("shanghai")
    sz_df = safe_read("shenzhen")

    return {
        "dow": _format_change(dow_df),
        "sp500": _format_change(sp_df),
        "nasdaq": _format_change(nasdaq_df),
        "usdkrw": _format_last_close(fx_df),
        "us10y": _format_last_close(us10y_df, suffix="%"),
        "wti": _format_last_close(wti_df, prefix="$"),
        "shanghai": _format_change(sh_df),
        "shenzhen": _format_change(sz_df),
    }

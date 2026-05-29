from __future__ import annotations

import re

from src.collectors.stock.naver_stock_collector import (
    _enrich_report,
    _find_stock_row,
    _parse_consensus_from_frgn,
    _parse_report_rows,
)


def _parse_target_prices(values: list[str]) -> list[int]:
    numbers: list[int] = []
    for value in values:
        cleaned = re.sub(r"[^\d]", "", value or "")
        if cleaned:
            numbers.append(int(cleaned))
    return numbers


def get_short_selling_snapshot(stock_name: str, use_mock_data: bool = True) -> dict:
    if use_mock_data:
        return {"short_balance_ratio": "1.84%", "consensus_target_price": "91,000원"}

    row = _find_stock_row(stock_name)
    if row is None:
        return {"short_balance_ratio": None, "consensus_target_price": None}

    code = str(row["Code"]).zfill(6)
    consensus_from_page = _parse_consensus_from_frgn(code)
    if consensus_from_page.get("target_price"):
        return {
            "short_balance_ratio": None,
            "consensus_target_price": consensus_from_page["target_price"],
        }

    report_rows = [_enrich_report(item) for item in _parse_report_rows(code, limit=5)]
    target_values = _parse_target_prices([item.get("target_price", "") for item in report_rows])

    consensus = None
    if target_values:
        consensus = f"{round(sum(target_values) / len(target_values)):,}원"

    return {"short_balance_ratio": None, "consensus_target_price": consensus}

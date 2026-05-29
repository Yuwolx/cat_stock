from __future__ import annotations

import re
from datetime import datetime

from src.collectors.dart_client import (
    find_corp_by_name,
    get_single_company_major_accounts,
    list_disclosures,
    recent_date_range,
)


REPORT_CODE_LABELS = {
    "11013": "Q1",
    "11012": "H1",
    "11014": "Q3",
    "11011": "FY",
}

RISK_KEYWORDS = {
    "CB 발행 가능성": ["전환사채", "CB"],
    "BW 발행 가능성": ["신주인수권부사채", "BW"],
    "유상증자 이슈": ["유상증자"],
    "전환우선주 이슈": ["전환우선주", "우선주"],
}


def _select_amount(rows: list[dict], account_names: list[str]) -> str | None:
    # Prefer consolidated financial statements when both exist.
    ordered = sorted(rows, key=lambda row: 0 if row.get("fs_div") == "CFS" else 1)
    normalized_candidates = {name.replace(" ", "") for name in account_names}
    for row in ordered:
        account_name = (row.get("account_nm") or "").replace(" ", "")
        if account_name in normalized_candidates:
            return row.get("thstrm_amount") or row.get("thstrm_add_amount")
    return None


def _period_sort_key(date_text: str) -> str:
    matches = re.findall(r"\d{4}\.\d{2}\.\d{2}", date_text or "")
    if matches:
        return matches[-1].replace(".", "")
    return "00000000"


def _candidate_reports(current_year: int) -> list[tuple[int, str]]:
    report_codes = ["11013", "11012", "11014", "11011"]
    candidates: list[tuple[int, str]] = []
    for year in range(current_year, current_year - 3, -1):
        for report_code in report_codes:
            candidates.append((year, report_code))
    return candidates


def get_stock_disclosures(
    stock_name: str,
    api_key: str = "",
    use_mock_data: bool = True,
) -> dict:
    if use_mock_data or not api_key:
        return {
            "disclosures": [
                f"{stock_name}: 분기보고서 제출",
                f"{stock_name}: 주요사항보고서 점검 필요",
            ],
            "major_shareholder_ratio": "20.1%",
            "risk_flags": ["CB 없음", "BW 없음", "최근 유상증자 없음", "부채비율 점검 필요"],
        }
    corp = find_corp_by_name(stock_name, api_key)
    if not corp:
        return {
            "disclosures": ["DART에서 종목명을 찾지 못했습니다."],
            "major_shareholder_ratio": None,
            "risk_flags": [],
        }

    start_date, end_date = recent_date_range(days=45)
    try:
        items = list_disclosures(
            api_key=api_key,
            start_date=start_date,
            end_date=end_date,
            corp_code=corp["corp_code"],
            page_count=20,
            last_reprt_at="Y",
        )
    except Exception as exc:
        return {
            "disclosures": [f"DART 조회 실패: {exc}"],
            "major_shareholder_ratio": None,
            "risk_flags": [],
        }

    disclosure_lines = [f"{item['report_nm']} ({item['rcept_dt']})" for item in items[:12]]
    risk_flags: list[str] = []
    joined = " ".join(disclosure_lines)
    for label, keywords in RISK_KEYWORDS.items():
        if any(keyword in joined for keyword in keywords):
            risk_flags.append(label)

    return {
        "disclosures": disclosure_lines or ["최근 공시가 없습니다."],
        "major_shareholder_ratio": None,
        "risk_flags": risk_flags,
    }


def get_financial_summary(stock_name: str, api_key: str = "", use_mock_data: bool = True) -> list[dict]:
    if use_mock_data or not api_key:
        return [
            {"quarter": "2025Q2", "sales": "18.4조", "op_income": "2.1조", "net_income": "1.7조"},
            {"quarter": "2025Q3", "sales": "19.1조", "op_income": "2.4조", "net_income": "1.9조"},
            {"quarter": "2025Q4", "sales": "20.0조", "op_income": "2.6조", "net_income": "2.0조"},
            {"quarter": "2026Q1", "sales": "19.8조", "op_income": "2.3조", "net_income": "1.8조"},
        ]
    corp = find_corp_by_name(stock_name, api_key)
    if not corp:
        return []

    current_year = datetime.now().year
    reports: list[dict] = []
    seen_labels: set[str] = set()

    for business_year, report_code in _candidate_reports(current_year):
        try:
            rows = get_single_company_major_accounts(
                api_key=api_key,
                corp_code=corp["corp_code"],
                business_year=business_year,
                report_code=report_code,
            )
        except Exception:
            continue

        if not rows:
            continue

        label = f"{business_year}{REPORT_CODE_LABELS[report_code]}"
        if label in seen_labels:
            continue

        sales = _select_amount(rows, ["매출액", "영업수익"])
        op_income = _select_amount(rows, ["영업이익"])
        net_income = _select_amount(rows, ["당기순이익", "분기순이익", "반기순이익"])
        period_key = _period_sort_key(rows[0].get("thstrm_dt", ""))
        reports.append(
            {
                "quarter": label,
                "sales": sales or "-",
                "op_income": op_income or "-",
                "net_income": net_income or "-",
                "period_key": period_key,
            }
        )
        seen_labels.add(label)
        if len(reports) >= 4:
            break

    reports.sort(key=lambda row: row.get("period_key", "00000000"), reverse=True)
    return [
        {
            "quarter": row["quarter"],
            "sales": row["sales"],
            "op_income": row["op_income"],
            "net_income": row["net_income"],
        }
        for row in reports[:4]
    ]

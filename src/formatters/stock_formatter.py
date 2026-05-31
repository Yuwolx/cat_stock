from __future__ import annotations

from src.utils.text_utils import display_value, format_krw_amount, format_list, section


def _format_turnover(value: object) -> str:
    if value is None:
        return "연결 예정"
    try:
        return f"{int(value):,}"
    except (ValueError, TypeError):
        return str(value)


def format_stock_report(payload: dict) -> str:
    basics = payload["basics"]
    flows = payload["flows"]
    disclosures = payload["disclosures"]
    short_selling = payload["short_selling"]
    financials = payload["financials"]

    financial_lines = [
        (
            f"{row['quarter']} | 매출 {format_krw_amount(row['sales'])} | "
            f"영업이익 {format_krw_amount(row['op_income'])} | "
            f"순이익 {format_krw_amount(row['net_income'])}"
        )
        for row in financials
    ]

    reports = payload.get("reports", [])
    if reports:
        report_section_parts = [f"■ 증권사 리포트 ({payload['report_date']})"]
        for r in reports:
            report_section_parts.append(f"- [{r['date']}] {r['title']} | {r['broker']}")
            if r.get("summary"):
                report_section_parts.append(f"  {r['summary']}")
        report_section = "\n".join(report_section_parts)
    else:
        report_section = f"■ 증권사 리포트 ({payload['report_date']})\n- 데이터 없음"

    sections = [
        f"[개별 종목 분석 - {basics['name']} - {payload['target_date']}]",
        "현재는 더미 데이터가 포함되어 있습니다." if payload["is_mock_data"] else "",
        section(
            "기본 정보",
            [
                (
                    f"현재가 {display_value(basics['price'])} | "
                    f"등락률 {display_value(basics['change_pct'])} | "
                    f"거래대금 {_format_turnover(basics['turnover_krw_billion'])}억"
                ),
                (
                    f"시가총액 {display_value(basics['market_cap'])} | "
                    f"52주 고저 {display_value(basics['year_high_low'])}"
                ),
                (
                    f"PER {display_value(basics['per'])} | "
                    f"PBR {display_value(basics['pbr'])} | "
                    f"ROE {display_value(basics['roe'])}"
                ),
            ],
        ),
        section(
            "이동평균선 위치",
            [
                f"5일선 {display_value(basics['ma_position']['ma5'])}",
                f"20일선 {display_value(basics['ma_position']['ma20'])}",
                f"60일선 {display_value(basics['ma_position']['ma60'])}",
            ],
        ),
        section(
            "수급",
            [
                f"외국인 최근 20일 누적 순매수 {display_value(flows['foreign_20d'])} (주 수 기준)",
                f"기관 최근 20일 누적 순매수 {display_value(flows['institution_20d'])} (주 수 기준)",
                f"공매도 잔고 비율 {display_value(short_selling['short_balance_ratio'])}",
            ],
        ),
        section("재무 요약", financial_lines or ["데이터 없음"]),
        section("최근 공시", disclosures["disclosures"] or ["데이터 없음"]),
        section("최근 뉴스", flows["news"] or ["데이터 없음"]),
        report_section,
        section(
            "추가 체크",
            [
                f"컨센서스 목표가 {display_value(short_selling['consensus_target_price'])}",
                f"대주주 지분율 {display_value(disclosures['major_shareholder_ratio'])}",
                f"리스크 체크 {format_list(disclosures['risk_flags'])}",
            ],
        ),
    ]
    return "\n\n".join(filter(None, sections)).strip()

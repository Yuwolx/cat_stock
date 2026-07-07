from __future__ import annotations

from src.utils.data_status import data_status_section, stock_missing_items
from src.utils.text_utils import display_value, format_krw_amount, format_krw_eok, format_list, section
from src.utils.trend_utils import format_flow_trend_line, format_price_trend_line


def _format_turnover(value: object) -> str:
    return format_krw_eok(value)


def _format_krw_flow(value: object) -> str:
    return format_krw_amount(value)


def _format_accumulated_flow(amount_value: object, share_value: object) -> str:
    if amount_value:
        return _format_krw_flow(amount_value)
    return display_value(share_value)


def _flow_basis(amount_value: object) -> str:
    return "금액 기준" if amount_value else "주 수 기준"


def _date_context_lines(payload: dict) -> list[str]:
    if not payload.get("is_adjusted"):
        return []
    return [
        f"요청일: {payload.get('requested_date')} {payload.get('requested_weekday', '')}요일".strip(),
        f"분석 기준일: {payload.get('resolved_date') or payload.get('target_date')} {payload.get('resolved_weekday', '')}요일",
        "주말/휴장일에는 최근 거래일 기준 데이터로 보정합니다.",
    ]


def format_stock_report(payload: dict) -> str:
    basics = payload["basics"]
    flows = payload["flows"]
    disclosures = payload["disclosures"]
    short_selling = payload["short_selling"]
    financials = payload["financials"]
    kis_flow = payload.get("kis_flow", {})
    foreign_20d_krw = kis_flow.get("foreign_20d_krw")
    institution_20d_krw = kis_flow.get("institution_20d_krw")

    daily_flows = flows.get("daily_flows") or {}
    close_trend_line = format_price_trend_line("종가 흐름", daily_flows.get("close") or [], digits=0)
    flow_trend_lines = [
        line
        for line in [
            format_flow_trend_line("외국인 일별", daily_flows.get("foreign") or []),
            format_flow_trend_line("기관 일별", daily_flows.get("institution") or []),
        ]
        if line
    ]

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
        "\n".join(_date_context_lines(payload)),
        "현재는 더미 데이터가 포함되어 있습니다." if payload["is_mock_data"] else "",
        data_status_section(stock_missing_items(payload)) or "",
        section(
            "기본 정보",
            [
                (
                    f"현재가 {display_value(basics['price'])} | "
                    f"등락률 {display_value(basics['change_pct'])} | "
                    f"거래대금 {_format_turnover(basics['turnover_krw_billion'])}"
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
                *([close_trend_line] if close_trend_line else []),
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
                f"외국인 20일 누적 순매수 {_format_accumulated_flow(foreign_20d_krw, flows['foreign_20d'])} "
                f"({_flow_basis(foreign_20d_krw)})",
                f"기관 20일 누적 순매수 {_format_accumulated_flow(institution_20d_krw, flows['institution_20d'])} "
                f"({_flow_basis(institution_20d_krw)})",
                f"외국인 당일 순매수 {_format_krw_flow(kis_flow.get('foreign_today_krw'))} (금액 기준)",
                f"기관 당일 순매수 {_format_krw_flow(kis_flow.get('institution_today_krw'))} (금액 기준)",
                *flow_trend_lines,
                f"공매도 거래량 비중 {display_value(short_selling.get('short_sale_volume_ratio'), '—')}",
            ],
        ),
        section("재무 요약", financial_lines or ["데이터 없음"]),
        section("최근 공시", disclosures["disclosures"] or ["데이터 없음"]),
        section("최근 뉴스", flows["news"] or ["데이터 없음"]),
        section("네이버 리포트", flows.get("naver_reports") or ["데이터 없음"]),
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

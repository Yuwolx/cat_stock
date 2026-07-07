from __future__ import annotations

from src.utils.data_status import data_status_section, market_missing_items
from src.utils.news_formatting import format_news_item
from src.utils.text_utils import display_value, format_krw_amount, format_krw_eok, format_list, format_number, section


def _fmt_number(value: object, digits: int = 1) -> str:
    return format_number(value, digits=digits)


def _fmt_pct(value: object) -> str:
    return f"{_fmt_number(value)}%"


def _fmt_signed_pct(value: object) -> str:
    if value is None or (isinstance(value, str) and not value.strip()):
        return "—"
    try:
        return f"{float(value):+.1f}%".replace(".0%", "%")
    except (TypeError, ValueError):
        return display_value(value)


def _fmt_krw_jo(value: object) -> str:
    if value is None or (isinstance(value, str) and not value.strip()):
        return "—"
    return format_krw_amount(f"{value}조")


def _format_rising_stock(item: object) -> str:
    if not isinstance(item, dict):
        return str(item)

    name = item.get("name") or "종목명 없음"
    market = item.get("market")
    price = display_value(item.get("price"))
    change_pct = item.get("change_pct")
    if change_pct is None:
        change_text = display_value(item.get("change_pct_text"))
    else:
        try:
            change_text = f"{float(change_pct):+.2f}%"
        except (TypeError, ValueError):
            change_text = display_value(change_pct)

    market_text = f"({market}) " if market else ""
    return f"{market_text}{name} | 현재가 {price} | 등락률 {change_text}"


def _date_context_lines(payload: dict) -> list[str]:
    if not payload.get("is_adjusted"):
        return []
    return [
        f"요청일: {payload.get('requested_date')} {payload.get('requested_weekday', '')}요일".strip(),
        f"분석 기준일: {payload.get('resolved_date') or payload.get('target_date')} {payload.get('resolved_weekday', '')}요일",
        "주말/휴장일에는 최근 거래일 기준 데이터로 보정합니다.",
    ]


def format_market_briefing(payload: dict) -> str:
    indices = payload["indices"]
    global_macro = payload["global_macro"]
    investor_flows = payload["investor_flows"]
    derivatives = payload["derivatives"]
    market_events = payload["market_events"]
    leaders = payload["leaders"]
    sectors = payload.get("sectors", [])
    rising_over_5pct = market_events.get("rising_over_5pct", [])
    news_items = payload.get("news_items", [])
    market_reports = payload.get("market_reports", [])

    header = f"[시황 브리핑 데이터 - {payload['target_date']}]"
    mock_notice = "현재는 더미 데이터가 포함되어 있습니다." if payload["is_mock_data"] else ""

    leader_lines = [
        (
            f"{item['name']} | 현재가 {display_value(item['price'])} | "
            f"등락률 {_fmt_pct(item.get('change_pct'))} | "
            f"거래대금 {format_krw_eok(item.get('turnover_krw_billion'))}"
        )
        for item in leaders
    ]
    investor_by_market = investor_flows.get("by_market", {})
    program_by_market = derivatives.get("program_by_market", {})

    program_lines = [
        f"프로그램 차익 합산 {format_krw_eok(derivatives['program_arbitrage'])}",
        f"프로그램 비차익 합산 {format_krw_eok(derivatives['program_non_arbitrage'])}",
        (
            f"프로그램 코스피 차익 {format_krw_eok(program_by_market.get('kospi', {}).get('arbitrage'))} | "
            f"비차익 {format_krw_eok(program_by_market.get('kospi', {}).get('non_arbitrage'))} | "
            f"전체 {format_krw_eok(program_by_market.get('kospi', {}).get('total'))}"
        ),
        (
            f"프로그램 코스닥 차익 {format_krw_eok(program_by_market.get('kosdaq', {}).get('arbitrage'))} | "
            f"비차익 {format_krw_eok(program_by_market.get('kosdaq', {}).get('non_arbitrage'))} | "
            f"전체 {format_krw_eok(program_by_market.get('kosdaq', {}).get('total'))}"
        ),
    ]

    sections = [
        section(
            "한국 지수",
            [
                (
                    f"코스피 지수 {_fmt_number(indices['kospi'].get('close'))} | "
                    f"등락률 {_fmt_pct(indices['kospi']['change_pct'])} | "
                    f"거래대금 {_fmt_krw_jo(indices['kospi']['turnover_trillion_krw'])} | "
                    f"전일대비 {_fmt_number(indices['kospi']['change_points'])}pt"
                ),
                (
                    f"코스닥 지수 {_fmt_number(indices['kosdaq'].get('close'))} | "
                    f"등락률 {_fmt_pct(indices['kosdaq']['change_pct'])} | "
                    f"거래대금 {_fmt_krw_jo(indices['kosdaq']['turnover_trillion_krw'])} | "
                    f"전일대비 {_fmt_number(indices['kosdaq']['change_points'])}pt"
                ),
            ],
        ),
        section(
            "글로벌/매크로",
            [
                f"다우 {display_value(global_macro['dow'])}",
                f"S&P500 {display_value(global_macro['sp500'])}",
                f"나스닥 {display_value(global_macro['nasdaq'])}",
                f"달러/원 {display_value(global_macro['usdkrw'])}",
                f"미국 10년물 {display_value(global_macro['us10y'])}",
                f"WTI {display_value(global_macro['wti'])}",
                f"상해 {display_value(global_macro['shanghai'])}",
                f"심천 {display_value(global_macro['shenzhen'])}",
            ],
        ),
        section("거래대금 상위", leader_lines or ["데이터 없음"]),
        section(
            "테마/그룹 등락",
            [
                f"{item['name']} {_fmt_signed_pct(item.get('change_pct'))}"
                for item in sectors
            ] or ["데이터 없음"],
        ),
        section(
            "외국인/기관 수급",
            [
                (
                    f"순매수 요약 외국인 {format_krw_eok(investor_flows['summary']['foreign'])} | "
                    f"기관 {format_krw_eok(investor_flows['summary']['institution'])} | "
                    f"개인 {format_krw_eok(investor_flows['summary']['retail'])}"
                ),
                (
                    f"코스피 수급 외국인 {format_krw_eok(investor_by_market.get('kospi', {}).get('foreign'))} | "
                    f"기관 {format_krw_eok(investor_by_market.get('kospi', {}).get('institution'))} | "
                    f"개인 {format_krw_eok(investor_by_market.get('kospi', {}).get('retail'))}"
                ),
                (
                    f"코스닥 수급 외국인 {format_krw_eok(investor_by_market.get('kosdaq', {}).get('foreign'))} | "
                    f"기관 {format_krw_eok(investor_by_market.get('kosdaq', {}).get('institution'))} | "
                    f"개인 {format_krw_eok(investor_by_market.get('kosdaq', {}).get('retail'))}"
                ),
                f"외국인 순매수 상위 {format_list(investor_flows['foreign_top_buy'])}",
                f"외국인 순매도 상위 {format_list(investor_flows['foreign_top_sell'])}",
                f"기관 순매수 상위 {format_list(investor_flows['institution_top_buy'])}",
                f"기관 순매도 상위 {format_list(investor_flows['institution_top_sell'])}",
            ],
        ),
        section(
            "파생/프로그램 매매",
            program_lines,
        ),
        section(
            "시장 이벤트",
            [
                f"5% 이상 상승 종목 {format_list([_format_rising_stock(item) for item in rising_over_5pct[:50]])}",
                f"당일 하락 상위 {format_list(market_events['new_lows'][:20])}",
                f"상한가 {format_list(market_events['upper_limit'])}",
                f"시간외 단일가 급등락 {format_list(market_events['after_hours_movers'])}",
            ],
        ),
        section("주요 뉴스", [format_news_item(item) for item in news_items] or ["데이터 없음"]),
        section("증권사 리포트", [format_news_item(item) for item in market_reports] or ["데이터 없음"]),
    ]

    chunks = [header]
    chunks.extend(_date_context_lines(payload))
    if mock_notice:
        chunks.append(mock_notice)
    status_section = data_status_section(market_missing_items(payload))
    if status_section:
        chunks.append(status_section)
    chunks.extend(sections)
    return "\n\n".join(chunks).strip()

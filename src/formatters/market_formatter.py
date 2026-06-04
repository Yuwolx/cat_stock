from __future__ import annotations

from src.utils.news_formatting import format_news_item
from src.utils.text_utils import display_value, format_list, section


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

    header = f"[시황 브리핑 데이터 - {payload['target_date']}]"
    mock_notice = "현재는 더미 데이터가 포함되어 있습니다." if payload["is_mock_data"] else ""

    leader_lines = [
        (
            f"{item['name']} | 현재가 {display_value(item['price'])} | "
            f"등락률 {display_value(item['change_pct'])}% | "
            f"거래대금 {display_value(item['turnover_krw_billion'])}억"
        )
        for item in leaders
    ]
    investor_by_market = investor_flows.get("by_market", {})
    program_by_market = derivatives.get("program_by_market", {})
    foreign_futures = derivatives.get("futures_foreign_net")
    institution_futures = derivatives.get("futures_institution_net")

    sections = [
        section(
            "한국 지수",
            [
                (
                    f"코스피 지수 {display_value(indices['kospi'].get('close'))} | "
                    f"등락률 {display_value(indices['kospi']['change_pct'])}% | "
                    f"거래대금 {display_value(indices['kospi']['turnover_trillion_krw'])}조 | "
                    f"전일대비 {display_value(indices['kospi']['change_points'])}pt"
                ),
                (
                    f"코스닥 지수 {display_value(indices['kosdaq'].get('close'))} | "
                    f"등락률 {display_value(indices['kosdaq']['change_pct'])}% | "
                    f"거래대금 {display_value(indices['kosdaq']['turnover_trillion_krw'])}조 | "
                    f"전일대비 {display_value(indices['kosdaq']['change_points'])}pt"
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
                f"{item['name']} {'+' if (item['change_pct'] or 0) >= 0 else ''}{display_value(item['change_pct'])}%"
                for item in sectors
            ] or ["데이터 없음"],
        ),
        section(
            "외국인/기관 수급",
            [
                (
                    f"순매수 요약 외국인 {display_value(investor_flows['summary']['foreign'])}억 | "
                    f"기관 {display_value(investor_flows['summary']['institution'])}억 | "
                    f"개인 {display_value(investor_flows['summary']['retail'])}억"
                ),
                (
                    f"코스피 수급 외국인 {display_value(investor_by_market.get('kospi', {}).get('foreign'))}억 | "
                    f"기관 {display_value(investor_by_market.get('kospi', {}).get('institution'))}억 | "
                    f"개인 {display_value(investor_by_market.get('kospi', {}).get('retail'))}억"
                ),
                (
                    f"코스닥 수급 외국인 {display_value(investor_by_market.get('kosdaq', {}).get('foreign'))}억 | "
                    f"기관 {display_value(investor_by_market.get('kosdaq', {}).get('institution'))}억 | "
                    f"개인 {display_value(investor_by_market.get('kosdaq', {}).get('retail'))}억"
                ),
                f"외국인 순매수 상위 {format_list(investor_flows['foreign_top_buy'])}",
                f"외국인 순매도 상위 {format_list(investor_flows['foreign_top_sell'])}",
                f"기관 순매수 상위 {format_list(investor_flows['institution_top_buy'])}",
                f"기관 순매도 상위 {format_list(investor_flows['institution_top_sell'])}",
            ],
        ),
        section(
            "파생/프로그램 매매",
            [
                (
                    f"외국인 코스피200 선물 순매수 {foreign_futures}계약"
                    if foreign_futures is not None
                    else "외국인 코스피200 선물 순매수 데이터 없음"
                ),
                (
                    f"기관 코스피200 선물 순매수 {institution_futures}계약"
                    if institution_futures is not None
                    else "기관 코스피200 선물 순매수 데이터 없음"
                ),
                f"코스피200 선물 근월물 코드 {display_value(derivatives.get('futures_contract_code'))}",
                f"선물 수급 경고 {display_value(derivatives.get('futures_warning'), '없음')}",
                f"프로그램 차익 합산 {display_value(derivatives['program_arbitrage'])}억",
                f"프로그램 비차익 합산 {display_value(derivatives['program_non_arbitrage'])}억",
                (
                    f"프로그램 코스피 차익 {display_value(program_by_market.get('kospi', {}).get('arbitrage'))}억 | "
                    f"비차익 {display_value(program_by_market.get('kospi', {}).get('non_arbitrage'))}억 | "
                    f"전체 {display_value(program_by_market.get('kospi', {}).get('total'))}억"
                ),
                (
                    f"프로그램 코스닥 차익 {display_value(program_by_market.get('kosdaq', {}).get('arbitrage'))}억 | "
                    f"비차익 {display_value(program_by_market.get('kosdaq', {}).get('non_arbitrage'))}억 | "
                    f"전체 {display_value(program_by_market.get('kosdaq', {}).get('total'))}억"
                ),
            ],
        ),
        section(
            "시장 이벤트",
            [
                f"당일 상승 상위 {format_list(market_events['new_highs'][:50])}",
                f"5% 이상 상승 종목 {format_list([_format_rising_stock(item) for item in rising_over_5pct])}",
                f"당일 하락 상위 {format_list(market_events['new_lows'][:20])}",
                f"상한가 {format_list(market_events['upper_limit'])}",
                f"시간외 단일가 급등락 {format_list(market_events['after_hours_movers'])}",
            ],
        ),
        section("주요 뉴스", [format_news_item(item) for item in news_items] or ["데이터 없음"]),
    ]

    chunks = [header]
    if mock_notice:
        chunks.append(mock_notice)
    chunks.extend(sections)
    return "\n\n".join(chunks).strip()

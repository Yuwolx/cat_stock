from __future__ import annotations

from src.formatters.coin_market_formatter import EMPTY_VALUE, _display, _fmt_krw, _fmt_pct, _fmt_usd
from src.utils.text_utils import section


def _fmt_number(value: object) -> str:
    if value is None:
        return EMPTY_VALUE
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if number >= 1_000_000_000:
        return f"{number / 1_000_000_000:.2f}B"
    if number >= 1_000_000:
        return f"{number / 1_000_000:.2f}M"
    return f"{number:,.0f}"


def format_coin_detail_report(payload: dict) -> str:
    basics = payload.get("basics", {})
    market = payload.get("market", {})
    supply = payload.get("supply", {})
    upbit = payload.get("upbit", {})
    risk = payload.get("risk", {})
    project = payload.get("project", {})
    defi_protocol = payload.get("defi_protocol", {})
    futures = payload.get("futures", {})
    risk_flags = payload.get("risk_flags", [])
    futures_label = futures.get("contract_label") or "Binance USD-M"

    chunks = [
        f"[개별 코인 공부 - {_display(basics.get('name'))} - {payload.get('target_datetime', '-')}]",
        section(
            "기본 정보",
            [
                f"이름 {_display(basics.get('name'))} ({_display(basics.get('symbol'))})",
                f"CoinGecko ID {_display(basics.get('id'))}",
                f"시총 순위 #{_display(basics.get('market_cap_rank'))}",
                f"카테고리 {', '.join(project.get('categories', [])[:5]) or EMPTY_VALUE}",
            ],
        ),
        section(
            "가격 / 규모",
            [
                f"현재가 {_fmt_usd(market.get('current_price_usd'))}",
                f"24h {_fmt_pct(market.get('change_24h_pct'))} | 7d {_fmt_pct(market.get('change_7d_pct'))} | 30d {_fmt_pct(market.get('change_30d_pct'))}",
                f"시가총액 {_fmt_usd(market.get('market_cap_usd'))}",
                f"FDV {_fmt_usd(market.get('fdv_usd'))}",
                f"24h 거래량 {_fmt_usd(market.get('volume_usd'))}",
                f"ATH {_fmt_usd(market.get('ath_usd'))} | ATH 대비 {_fmt_pct(market.get('ath_change_pct'))}",
            ],
        ),
        section(
            "공급 구조",
            [
                f"유통량 {_fmt_number(supply.get('circulating_supply'))}",
                f"총공급량 {_fmt_number(supply.get('total_supply'))}",
                f"최대공급량 {_fmt_number(supply.get('max_supply'))}",
                f"FDV / 시총 {_display(risk.get('fdv_to_mcap'))}",
            ],
        ),
        section(
            "업비트 KRW",
            [
                (
                    f"{_display(upbit.get('market'))} | 현재가 {_fmt_krw(upbit.get('trade_price'))} | "
                    f"24h {_fmt_pct(upbit.get('change_pct'))} | 거래대금 {_fmt_krw(upbit.get('acc_trade_price_24h'))}"
                    if upbit.get("is_listed")
                    else "업비트 KRW 마켓 미상장 또는 조회 실패"
                ),
                f"김치 프리미엄 {_fmt_pct(upbit.get('kimchi_premium_pct'))}",
                f"유의/주의 {_display(upbit.get('warning'))}",
            ],
        ),
        section(
            "리스크 체크",
            [
                f"시총 대비 거래량 {_display(risk.get('volume_to_mcap'))}",
                f"FDV 희석 비율 {_display(risk.get('fdv_to_mcap'))}",
                f"ATH 대비 위치 {_fmt_pct(market.get('ath_change_pct'))}",
                f"국내 수급 과열 {_fmt_pct(upbit.get('kimchi_premium_pct'))}",
                *[
                    f"{_display(item.get('label'))}: {_display(item.get('message'))}"
                    for item in risk_flags
                ],
            ],
        ),
        section(
            "온체인 / DeFi",
            [
                (
                    f"{_display(defi_protocol.get('name'))} | TVL {_fmt_usd(defi_protocol.get('tvl'))} | "
                    f"24h {_fmt_pct(defi_protocol.get('change_1d'))} | 7d {_fmt_pct(defi_protocol.get('change_7d'))}"
                    if defi_protocol
                    else "DefiLlama 프로토콜 매핑 없음"
                ),
            ],
        ),
        section(
            "파생상품",
            [
                (
                    f"{_display(futures.get('symbol'))} ({futures_label}) | 펀딩비 {_fmt_pct(futures.get('latest_funding_rate_pct'))} | "
                    f"연율 환산 {_fmt_pct(futures.get('annualized_funding_pct'))} | "
                    f"OI 변화 {_fmt_pct(futures.get('open_interest_change_24h_pct'))} | {_display(futures.get('warning'))}"
                    if futures.get("is_available")
                    else "Binance USD-M 선물 데이터 없음"
                ),
            ],
        ),
        section(
            "공부 질문",
            [
                "이 코인의 핵심 수요가 수수료, 담보, 스테이킹, 밈, 거버넌스 중 무엇인지 설명하기",
                "가격 상승이 거래량 증가를 동반했는지 확인하기",
                "FDV가 시총보다 크다면 앞으로 어떤 희석 이벤트가 있을지 찾아보기",
                "업비트 가격과 글로벌 가격이 크게 다르면 국내 수급 과열인지 확인하기",
            ],
        ),
    ]
    return "\n\n".join(chunks).strip()

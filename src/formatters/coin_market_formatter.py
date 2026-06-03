from __future__ import annotations

from src.utils.text_utils import display_value, section


EMPTY_VALUE = "—"


def _display(value: object) -> str:
    return display_value(value, EMPTY_VALUE)


def _fmt_pct(value: object) -> str:
    if value is None:
        return EMPTY_VALUE
    try:
        return f"{float(value):+.2f}%"
    except (TypeError, ValueError):
        return str(value)


def _fmt_usd(value: object) -> str:
    if value is None:
        return EMPTY_VALUE
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if number >= 1_000_000_000_000:
        return f"${number / 1_000_000_000_000:.2f}T"
    if number >= 1_000_000_000:
        return f"${number / 1_000_000_000:.1f}B"
    if number >= 1_000_000:
        return f"${number / 1_000_000:.1f}M"
    if number >= 1:
        return f"${number:,.2f}"
    return f"${number:.6f}"


def _fmt_krw(value: object) -> str:
    if value is None:
        return EMPTY_VALUE
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if number >= 1_000_000_000_000:
        return f"{number / 1_000_000_000_000:.2f}조"
    if number >= 100_000_000:
        return f"{number / 100_000_000:.0f}억"
    return f"{number:,.0f}원"


def format_coin_market_briefing(payload: dict) -> str:
    global_market = payload.get("global_market", {})
    majors = payload.get("majors", {})
    fear_greed = payload.get("fear_greed", {})
    upbit_leaders = payload.get("upbit_leaders", [])
    top_coins = payload.get("top_coins", [])
    categories = payload.get("categories", [])
    regime = payload.get("regime", {})
    stablecoins = payload.get("stablecoins", {})
    fees = payload.get("fees", {})
    protocols = payload.get("top_protocols", [])

    btc = majors.get("bitcoin", {})
    eth = majors.get("ethereum", {})

    leader_lines = [
        (
            f"{item.get('korean_name') or item.get('symbol')} ({item.get('market')}) | "
            f"현재가 {_fmt_krw(item.get('trade_price'))} | "
            f"등락률 {_fmt_pct(item.get('change_pct'))} | "
            f"거래대금 {_fmt_krw(item.get('acc_trade_price_24h'))}"
        )
        for item in upbit_leaders[:10]
    ]

    top_coin_lines = [
        (
            f"#{item.get('market_cap_rank') or '-'} {item.get('name')} ({str(item.get('symbol', '')).upper()}) | "
            f"가격 {_fmt_usd(item.get('current_price'))} | "
            f"24h {_fmt_pct(item.get('price_change_percentage_24h'))} | "
            f"시총 {_fmt_usd(item.get('market_cap'))}"
        )
        for item in top_coins[:10]
    ]

    category_lines = [
        (
            f"{item.get('name')} | "
            f"24h {_fmt_pct(item.get('market_cap_change_24h'))} | "
            f"시총 {_fmt_usd(item.get('market_cap'))}"
        )
        for item in categories[:8]
    ]

    protocol_lines = [
        (
            f"{item.get('name')} | TVL {_fmt_usd(item.get('tvl'))} | "
            f"24h {_fmt_pct(item.get('change_1d'))} | 카테고리 {_display(item.get('category'))}"
        )
        for item in protocols[:6]
    ]

    fee_lines = [
        (
            f"{item.get('name')} | 24h 수수료 {_fmt_usd(item.get('total24h'))} | "
            f"7d {_fmt_usd(item.get('total7d'))}"
        )
        for item in (fees.get("protocols") or [])[:6]
    ]

    chunks = [
        f"[코인 시황 대시보드 - {payload.get('target_datetime', '-')}]",
        section(
            "시장 온도",
            [
                f"시장 국면 {_display(regime.get('label'))} - {_display(regime.get('message'))}",
                f"총 코인 시총 {_fmt_usd(global_market.get('total_market_cap_usd'))}",
                f"24h 거래대금 {_fmt_usd(global_market.get('total_volume_usd'))}",
                f"전체 시총 24h 변화 {_fmt_pct(global_market.get('market_cap_change_24h_pct'))}",
                f"BTC 도미넌스 {_fmt_pct(global_market.get('btc_dominance'))}",
                f"ETH 도미넌스 {_fmt_pct(global_market.get('eth_dominance'))}",
                f"ETH/BTC 비율 {_display(payload.get('eth_btc_ratio'))}",
            ],
        ),
        section(
            "BTC / ETH",
            [
                (
                    f"BTC {_fmt_usd(btc.get('current_price'))} | "
                    f"24h {_fmt_pct(btc.get('price_change_percentage_24h'))} | "
                    f"7d {_fmt_pct(btc.get('price_change_percentage_7d_in_currency'))}"
                ),
                (
                    f"ETH {_fmt_usd(eth.get('current_price'))} | "
                    f"24h {_fmt_pct(eth.get('price_change_percentage_24h'))} | "
                    f"7d {_fmt_pct(eth.get('price_change_percentage_7d_in_currency'))}"
                ),
            ],
        ),
        section(
            "심리 / 한국 수급",
            [
                f"공포탐욕지수 {_display(fear_greed.get('value'))} ({_display(fear_greed.get('classification'))})",
                f"김치 프리미엄 {_fmt_pct(payload.get('kimchi_premium_pct'))}",
                f"USD/KRW {_display(payload.get('usdkrw'))}",
                f"스테이블코인 시총 {_fmt_usd(stablecoins.get('total_circulating_usd'))} | 7d {_fmt_pct(stablecoins.get('change_7d_pct'))}",
            ],
        ),
        section("업비트 KRW 거래대금 상위", leader_lines or ["데이터 없음"]),
        section("글로벌 시총 상위", top_coin_lines or ["데이터 없음"]),
        section("섹터 온도", category_lines or ["데이터 없음"]),
        section("DeFi TVL 상위", protocol_lines or ["데이터 없음"]),
        section("프로토콜 수수료 상위", fee_lines or ["데이터 없음"]),
        section(
            "오늘의 공부 질문",
            [
                "BTC가 오르는 장인지, 알트까지 퍼지는 장인지 도미넌스로 확인하기",
                "업비트 거래대금 상위와 글로벌 시총 상위가 같은지 비교하기",
                "김치 프리미엄이 높다면 국내 수급 과열인지 의심하기",
                "섹터 강세가 단기 가격 반응인지 실제 사용량 증가인지 다음 단계에서 확인하기",
            ],
        ),
    ]
    return "\n\n".join(chunks).strip()

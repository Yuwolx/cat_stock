from __future__ import annotations

from src.formatters.coin_market_formatter import _display, _fmt_pct, _fmt_usd
from src.utils.text_utils import section


def format_coin_sector_report(payload: dict) -> str:
    categories = payload.get("categories", [])
    representative = payload.get("representative_coins", [])
    strongest = payload.get("strongest_sector", {})
    weakest = payload.get("weakest_sector", {})
    stablecoins = payload.get("stablecoins", {})
    fees = payload.get("fees", {})
    protocols = payload.get("top_protocols", [])

    category_lines = [
        (
            f"{_display(item.get('name'))} | 24h {_fmt_pct(item.get('market_cap_change_24h'))} | "
            f"시총 {_fmt_usd(item.get('market_cap'))} | 거래대금 {_fmt_usd(item.get('volume_24h'))}"
        )
        for item in categories
    ]

    coin_lines = [
        (
            f"{_display(item.get('sector'))} - {_display(item.get('name'))} ({_display(item.get('symbol')).upper()}) | "
            f"순위 #{_display(item.get('market_cap_rank'))} | 가격 {_fmt_usd(item.get('current_price'))} | "
            f"24h {_fmt_pct(item.get('price_change_percentage_24h'))}"
        )
        for item in representative
    ]

    playbook_lines = [
        (
            f"{_display(item.get('name'))} | 볼 것: {_display(item.get('watch'))} | 조심할 것: {_display(item.get('risk'))}"
        )
        for item in payload.get("playbooks", [])[:8]
    ]

    protocol_lines = [
        (
            f"{_display(item.get('name'))} | {_display(item.get('category'))} | TVL {_fmt_usd(item.get('tvl'))} | "
            f"24h {_fmt_pct(item.get('change_1d'))}"
        )
        for item in protocols[:8]
    ]

    fee_lines = [
        f"{_display(item.get('name'))} | 24h 수수료 {_fmt_usd(item.get('total24h'))} | 7d {_fmt_usd(item.get('total7d'))}"
        for item in (fees.get("protocols") or [])[:6]
    ]

    chunks = [
        f"[코인 섹터 공부 - {payload.get('target_datetime', '-')}]",
        section(
            "섹터 요약",
            [
                f"가장 강한 섹터 {_display(strongest.get('name'))} ({_fmt_pct(strongest.get('market_cap_change_24h'))})",
                f"가장 약한 섹터 {_display(weakest.get('name'))} ({_fmt_pct(weakest.get('market_cap_change_24h'))})",
                f"추적 섹터 수 {len(categories)}개",
            ],
        ),
        section("섹터 히트맵", category_lines or ["데이터 없음"]),
        section("대표 코인", coin_lines or ["데이터 없음"]),
        section(
            "DeFi / 스테이블코인",
            [
                f"스테이블코인 전체 시총 {_fmt_usd(stablecoins.get('total_circulating_usd'))} | 7d {_fmt_pct(stablecoins.get('change_7d_pct'))}",
                f"프로토콜 24h 수수료 {_fmt_usd(fees.get('total24h'))}",
            ],
        ),
        section("TVL 상위 프로토콜", protocol_lines or ["데이터 없음"]),
        section("수수료 상위 프로토콜", fee_lines or ["데이터 없음"]),
        section("섹터별 공부 포인트", playbook_lines or ["데이터 없음"]),
        section(
            "오늘의 공부 질문",
            [
                "강한 섹터가 단기 가격 반응인지 실제 사용량 증가인지 구분하기",
                "대표 코인 3개가 같이 움직이는지, 한 코인만 튀는지 비교하기",
                "섹터 시총 대비 거래대금이 과열인지 확인하기",
                "섹터 이름이 멋있어 보여도 수익 구조와 사용자 지표가 있는지 확인하기",
            ],
        ),
    ]
    return "\n\n".join(chunks).strip()

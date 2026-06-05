from __future__ import annotations

from src.utils.text_utils import display_value, section


EMPTY_VALUE = "—"


def _display(value: object) -> str:
    return display_value(value, fallback=EMPTY_VALUE)


def format_theme_report(payload: dict) -> str:
    stocks = payload["stocks"]
    news_bundle = payload["news_bundle"]
    peer_bundle = payload["peer_bundle"]

    stock_lines = [
        (
            f"{_display(item.get('name'))} | 시총 {_display(item.get('market_cap'))} | 현재가 {_display(item.get('price'))} | "
            f"등락률 {_display(item.get('change_pct'))} | PER {_display(item.get('per'))} | PBR {_display(item.get('pbr'))}"
        )
        for item in stocks
    ]

    sections = [
        f"[테마 공부 - {payload['theme_name']} - {payload['target_date']}]",
        section("테마 관련 종목", stock_lines or ["데이터 없음"]),
        section("최근 관련 뉴스", news_bundle["news"] or ["데이터 없음"]),
        section("관련 공시", peer_bundle["disclosures"] or ["데이터 없음"]),
        section("증권사 리포트 요약", news_bundle["reports"] or ["데이터 없음"]),
    ]
    return "\n\n".join(filter(None, sections)).strip()

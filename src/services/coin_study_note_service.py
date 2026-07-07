from __future__ import annotations

from datetime import datetime

from src.formatters.coin_study_note_formatter import format_coin_study_note
from src.utils.date_utils import KST, today_kst_string
from src.utils.file_utils import save_output_text
from src.utils.hypothesis_store import save_hypothesis


def collect_market_snapshot() -> dict:
    """가설 기록/대조에 쓰는 시장 상태 요약. 수집 실패 항목은 빠진다."""
    try:
        from src.services.coin_market_service import generate_coin_market_report

        payload = generate_coin_market_report()["payload"]
    except Exception:
        return {}

    majors = payload.get("majors") or {}
    btc = majors.get("bitcoin") or {}
    eth = majors.get("ethereum") or {}
    global_market = payload.get("global_market") or {}
    fear_greed = payload.get("fear_greed") or {}

    def _round(value: object, digits: int = 2) -> object:
        if isinstance(value, float):
            return round(value, digits)
        return value

    snapshot = {
        "BTC 가격 (USD)": _round(btc.get("current_price")),
        "BTC 24h (%)": _round(btc.get("price_change_percentage_24h")),
        "ETH 가격 (USD)": _round(eth.get("current_price")),
        "ETH 24h (%)": _round(eth.get("price_change_percentage_24h")),
        "BTC 도미넌스 (%)": _round(global_market.get("btc_dominance")),
        "총 시총 (USD)": _round(global_market.get("total_market_cap_usd"), 0),
        "공포탐욕지수": fear_greed.get("value"),
        "김치 프리미엄 (%)": _round(payload.get("kimchi_premium_pct")),
    }
    return {key: value for key, value in snapshot.items() if value is not None}


def generate_coin_study_note(
    regime: str,
    market_reason: str,
    sector: str,
    sector_reason: str,
    coin: str,
    hypothesis: str,
    invalidating_condition: str,
    next_metric: str,
    next_source: str,
) -> dict:
    target_date = today_kst_string()
    snapshot = collect_market_snapshot()
    payload = {
        "target_date": target_date,
        "target_datetime": datetime.now(KST).strftime("%Y-%m-%d %H:%M KST"),
        "regime": regime,
        "market_reason": market_reason,
        "sector": sector,
        "sector_reason": sector_reason,
        "coin": coin,
        "hypothesis": hypothesis,
        "invalidating_condition": invalidating_condition,
        "next_metric": next_metric,
        "next_source": next_source,
        "snapshot": snapshot,
    }
    text = format_coin_study_note(payload)
    path = save_output_text("coin_study_note", target_date, text)

    # 가설이 있는 노트만 채점판에 기록한다 (빈 노트는 훈련 대상이 아님)
    hypothesis_id = None
    if (hypothesis or "").strip():
        hypothesis_id = save_hypothesis(payload, snapshot)

    return {"text": text, "path": path, "payload": payload, "hypothesis_id": hypothesis_id}

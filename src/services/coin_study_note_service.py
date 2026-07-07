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


# 한 줄 예측 대상 → 채점에 쓸 스냅샷 지표
QUICK_TARGETS = {
    "비트코인": "BTC 가격 (USD)",
    "이더리움": "ETH 가격 (USD)",
    "알트코인 전반": "총 시총 (USD)",
}

QUICK_DIRECTIONS = ["오를 것 같다", "내릴 것 같다", "횡보할 것 같다"]


def record_quick_prediction(target: str, direction: str, reason: str = "") -> int | None:
    """초보용 한 줄 예측 — 클릭 몇 번으로 가설 루프에 들어오게 한다."""
    snapshot = collect_market_snapshot()
    note = {
        "type": "quick",
        "coin": target,
        "direction": direction,
        "hypothesis": direction,
        "reason": (reason or "").strip(),
        "invalidating_condition": "",
        "metric_key": QUICK_TARGETS.get(target),
        "target_datetime": datetime.now(KST).strftime("%Y-%m-%d %H:%M KST"),
    }
    return save_hypothesis(note, snapshot)


def evaluate_quick_prediction(note: dict, snapshot: dict, now_snapshot: dict) -> dict | None:
    """한 줄 예측의 '기록 후 변화율'과 판정 힌트. 계산 불가면 None."""
    metric_key = note.get("metric_key")
    if not metric_key:
        return None
    try:
        then_value = float(snapshot.get(metric_key))
        now_value = float(now_snapshot.get(metric_key))
    except (TypeError, ValueError):
        return None
    if not then_value:
        return None

    change_pct = (now_value / then_value - 1) * 100
    direction = note.get("direction") or ""
    if abs(change_pct) < 1:
        comment = "아직 크게 움직이지 않았어요"
    elif (change_pct > 0 and "오를" in direction) or (change_pct < 0 and "내릴" in direction):
        comment = "예측과 일치해 보여요"
    elif "횡보" in direction:
        comment = "횡보 예측과는 어긋나 보여요"
    else:
        comment = "예측과 어긋나 보여요"
    return {"metric_key": metric_key, "change_pct": change_pct, "comment": comment}


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

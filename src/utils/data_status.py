from __future__ import annotations

from src.utils.text_utils import section

MARKET_COLLECTOR_LABELS = {
    "indices": "한국 지수",
    "global_macro": "글로벌 매크로",
    "leaders": "거래대금 상위",
    "sectors": "테마/그룹 등락",
    "investor_flows": "외국인/기관 수급",
    "derivatives": "파생/프로그램 매매",
    "market_events": "시장 이벤트",
    "news_items": "시장 뉴스",
    "market_reports": "증권사 리포트",
}


def market_missing_items(payload: dict) -> list[str]:
    collector_status = payload.get("collector_status", {})
    if collector_status:
        missing = []
        for key, label in MARKET_COLLECTOR_LABELS.items():
            status = collector_status.get(key, {})
            if status.get("status") == "error":
                missing.append(f"{label} (수집 오류)")
            elif status.get("status") == "empty":
                missing.append(f"{label} (빈 결과)")
        return missing

    missing = []
    inv = payload.get("investor_flows", {})
    if not inv.get("foreign_top_buy") and not inv.get("institution_top_buy"):
        missing.append("외국인/기관 수급 상위 종목")
    macro = payload.get("global_macro", {})
    if not macro or all(v is None for v in macro.values()):
        missing.append("글로벌 매크로")
    if not payload.get("sectors"):
        missing.append("테마/그룹 등락")
    return missing


def stock_missing_items(payload: dict) -> list[str]:
    missing = []
    basics = payload.get("basics", {})
    if not basics.get("price"):
        missing.append("기본 시세 (종목명 확인 필요)")
    flows = payload.get("flows", {})
    kis_flow = payload.get("kis_flow", {})
    has_flow_data = (
        flows.get("foreign_20d")
        or flows.get("institution_20d")
        or kis_flow.get("foreign_20d_krw")
        or kis_flow.get("institution_20d_krw")
    )
    if not has_flow_data:
        missing.append("외국인/기관 수급")
    disc = payload.get("disclosures", {})
    if not disc.get("disclosures"):
        missing.append("DART 공시 (API 키 확인 필요)")
    if not payload.get("financials"):
        missing.append("재무 요약 (API 키 확인 필요)")
    return missing


def theme_missing_items(payload: dict) -> list[str]:
    missing = []
    if not payload.get("stocks"):
        missing.append("테마 관련 종목 (테마명 재확인)")
    if not payload.get("news_bundle", {}).get("news"):
        missing.append("관련 뉴스")
    return missing


def data_status_section(missing: list[str]) -> str | None:
    """수집 실패/누락 항목을 프롬프트 텍스트에 포함할 섹션으로 변환.

    이 텍스트의 최종 소비자는 화면을 보는 사람이 아니라 붙여넣기되는 LLM이므로,
    누락 항목을 추정으로 채우지 않도록 명시적인 지시를 함께 넣는다.
    """
    if not missing:
        return None
    return section(
        "데이터 수집 안내",
        [
            "다음 항목은 이번 수집에서 확보하지 못함: " + ", ".join(missing),
            "위 항목은 값을 추정하거나 일반론으로 채우지 말고, 데이터 없음을 전제로 분석할 것.",
        ],
    )

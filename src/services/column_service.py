from __future__ import annotations

from src.config.settings import get_settings
from src.utils.logger import get_logger


LOGGER = get_logger(__name__)
OPENAI_COLUMN_MODEL = "gpt-4o-mini"


def _extract_response_text(response: object) -> str | None:
    output_text = getattr(response, "output_text", None)
    if output_text:
        return str(output_text).strip()

    output = getattr(response, "output", None) or []
    chunks: list[str] = []
    for item in output:
        for content in getattr(item, "content", []) or []:
            text = getattr(content, "text", None)
            if text:
                chunks.append(str(text))
    joined = "".join(chunks).strip()
    return joined or None


def _call_gpt(prompt: str, max_tokens: int = 600) -> dict:
    api_key = get_settings().openai_api_key
    if not api_key:
        return {"text": None, "reason": "missing_api_key"}
    try:
        from openai import OpenAI
    except ImportError:
        return {"text": None, "reason": "package_missing"}

    try:
        client = OpenAI(api_key=api_key, timeout=20.0)
        response = client.responses.create(
            model=OPENAI_COLUMN_MODEL,
            input=prompt,
            max_output_tokens=max_tokens,
        )
        text = _extract_response_text(response)
        if not text:
            return {"text": None, "reason": "api_error"}
        return {"text": text, "reason": "ok"}
    except Exception as exc:
        LOGGER.warning("AI column generation failed: %s", exc)
        return {"text": None, "reason": "api_error"}


def _split_title_body(text: str, fallback_title: str) -> dict:
    """'제목\n---\n본문' 형식을 분리"""
    if "---" in text:
        parts = text.split("---", 1)
        return {"title": parts[0].strip(), "body": parts[1].strip()}
    lines = text.strip().splitlines()
    if len(lines) >= 2:
        return {"title": lines[0].strip(), "body": "\n".join(lines[1:]).strip()}
    return {"title": fallback_title, "body": text}


def _available_column(parts: dict) -> dict:
    return {
        "is_available": True,
        "reason": "ok",
        "title": parts.get("title"),
        "body": parts.get("body"),
    }


def _unavailable_column(reason: str) -> dict:
    return {
        "is_available": False,
        "reason": reason,
        "title": None,
        "body": None,
    }


def generate_stock_column(payload: dict) -> dict:
    """개별 종목 AI 분석 칼럼 생성"""
    basics = payload.get("basics", {})
    flows = payload.get("flows", {})
    kis = payload.get("kis_flow", {})
    fin = payload.get("financials", [])
    disc = payload.get("disclosures", {})
    short = payload.get("short_selling", {})

    fin_summary = ""
    if fin:
        latest = fin[-1]
        fin_summary = f"최근 분기: 매출 {latest.get('sales','?')} / 영업이익 {latest.get('op_income','?')} / 순이익 {latest.get('net_income','?')}"

    news_titles = "\n".join(f"- {n}" for n in flows.get("news", [])[:4])
    risk_flags = ", ".join(disc.get("risk_flags", [])) or "없음"

    prompt = f"""다음 한국 주식 데이터를 바탕으로 경제신문 칼럼을 작성해줘.

[종목 현황]
종목명: {basics.get('name')}
현재가: {basics.get('price')} ({basics.get('change_pct')})
시가총액: {basics.get('market_cap')} / PER {basics.get('per')} / PBR {basics.get('pbr')} / ROE {basics.get('roe')}
52주 고저: {basics.get('year_high_low')}
이동평균: 5일 {basics.get('ma_position',{}).get('ma5')} / 20일 {basics.get('ma_position',{}).get('ma20')} / 60일 {basics.get('ma_position',{}).get('ma60')}
외국인 20일 누적: {kis.get('foreign_20d_krw') or flows.get('foreign_20d')}
기관 20일 누적: {kis.get('institution_20d_krw') or flows.get('institution_20d')}
공매도 거래량 비중: {short.get('short_sale_volume_ratio') or '?'}
공매도 잔고 비율: {short.get('short_balance_ratio') or '?'}
컨센서스 목표가: {short.get('consensus_target_price','?')}
{fin_summary}
재무 리스크: {risk_flags}
대주주 지분: {disc.get('major_shareholder_ratio','?')}

[최근 뉴스 헤드라인]
{news_titles}

[작성 지침]
- 한국 경제신문 수석 애널리스트 논조
- 첫 줄: 칼럼 제목 (15-25자, 날카롭고 구체적)
- 구분자: ---
- 본문: 200-280자 (3-4문장), 핵심 데이터 1-2개 인용
- 투자 권유 없이 시장 구조 분석 관점
- 마지막 문장은 전망 또는 주목 포인트로 마무리"""

    result = _call_gpt(prompt, max_tokens=700)
    text = result.get("text")
    if not text:
        return _unavailable_column(str(result.get("reason") or "unknown"))
    return _available_column(_split_title_body(text, fallback_title=f"{basics.get('name','?')} 분석"))


def generate_market_column(payload: dict) -> dict:
    """시황 브리핑 AI 칼럼 생성"""
    indices = payload.get("indices", {})
    macro = payload.get("global_macro", {})
    flows = payload.get("investor_flows", {})
    events = payload.get("market_events", {})
    sectors = payload.get("sectors", [])
    target_date = payload.get("target_date", "")

    top_sectors = ", ".join(
        f"{s['name']} {'+' if (s.get('change_pct') or 0) >= 0 else ''}{s.get('change_pct','?')}%"
        for s in sorted(sectors, key=lambda x: abs(x.get("change_pct") or 0), reverse=True)[:4]
    ) if sectors else "없음"

    upper_limit = ", ".join(events.get("upper_limit", [])[:5]) or "없음"
    after_hours = ", ".join(events.get("after_hours_movers", [])[:4]) or "없음"

    prompt = f"""다음 한국 증시 시황 데이터를 바탕으로 일간 시황 칼럼을 작성해줘.

[날짜] {target_date}

[지수]
코스피: {indices.get('kospi',{}).get('close','?')} ({indices.get('kospi',{}).get('change_pct','?')}%)
코스닥: {indices.get('kosdaq',{}).get('close','?')} ({indices.get('kosdaq',{}).get('change_pct','?')}%)

[글로벌 매크로]
미국: 다우 {macro.get('dow')} / S&P500 {macro.get('sp500')} / 나스닥 {macro.get('nasdaq')}
달러원: {macro.get('usdkrw')} / 미국10년물: {macro.get('us10y')} / WTI: {macro.get('wti')}
중국: 상해 {macro.get('shanghai')} / 심천 {macro.get('shenzhen')}

[수급 요약]
외국인: {flows.get('summary',{}).get('foreign','?')}억
기관: {flows.get('summary',{}).get('institution','?')}억
개인: {flows.get('summary',{}).get('retail','?')}억

[시장 이벤트]
상한가: {upper_limit}
시간외 단일가: {after_hours}
주요 테마/그룹: {top_sectors}

[작성 지침]
- 한국 경제신문 증권부 기자/칼럼니스트 논조
- 첫 줄: 오늘 시장을 한 문장으로 정의하는 제목 (15-25자)
- 구분자: ---
- 본문: 220-300자, 오늘 시장의 핵심 흐름 1-2가지 중심
- 글로벌 → 국내 연결고리, 수급 주체 행동, 주목할 섹터 순서
- 투자 권유 없이 시장 해석 관점"""

    result = _call_gpt(prompt, max_tokens=700)
    text = result.get("text")
    if not text:
        return _unavailable_column(str(result.get("reason") or "unknown"))
    return _available_column(_split_title_body(text, fallback_title=f"{target_date} 시황"))

from __future__ import annotations

import hashlib
from datetime import date
from html import escape

from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from src.config.settings import get_settings
from src.services.coin_detail_service import generate_coin_detail_report
from src.services.market_service import generate_market_briefing
from src.services.coin_market_service import generate_coin_market_report
from src.services.coin_sector_service import generate_coin_sector_report
from src.services.coin_study_note_service import generate_coin_study_note
from src.services.stock_service import generate_stock_report
from src.services.theme_service import generate_theme_report
from src.ui.components import (
    inject_app_styles,
    render_ctrl_section,
    render_list,
    render_note,
    render_page_intro,
    render_shell,
    render_shell_with_toggle,
)
from src.ui.dashboard import build_market_dashboard, build_stock_dashboard, build_theme_dashboard
from src.ui.coin_dashboard import (
    build_coin_detail_dashboard,
    build_coin_detail_empty_state,
    build_coin_market_dashboard,
    build_coin_market_empty_state,
    build_coin_sector_dashboard,
    build_coin_sector_empty_state,
)
from src.utils.data_status import market_missing_items, stock_missing_items, theme_missing_items
from src.utils.date_utils import resolve_stock_trading_date


def _render_dashboard_with_text_output(
    *,
    result_key: str,
    box_key: str,
    placeholder: str,
    dashboard_builder,
) -> None:
    result = st.session_state.get(result_key)
    if result:
        _render_output_box(result["text"], placeholder, box_key=box_key)
    else:
        _render_output_box("", placeholder, box_key=box_key)


def _open_newspaper_view(title: str, html: str, file_name: str) -> None:
    st.session_state["newspaper_view"] = {
        "title": title,
        "html": html,
        "file_name": file_name,
    }


def _render_newspaper_button(*, title: str, html: str, file_name: str, key: str) -> None:
    if st.button("오늘의 신문", use_container_width=False, key=key):
        _open_newspaper_view(title, html, file_name)
        st.rerun()


def _render_newspaper_view() -> None:
    view = st.session_state.get("newspaper_view") or {}
    html = str(view.get("html") or "")
    title = str(view.get("title") or "신문 보기")
    file_name = str(view.get("file_name") or "dashboard.html")

    top_col, action_col = st.columns([1, 1], gap="small")
    with top_col:
        if st.button("← 텍스트 화면으로 돌아가기", key="newspaper_back"):
            st.session_state.pop("newspaper_view", None)
            st.rerun()
    with action_col:
        st.download_button(
            "HTML 다운로드",
            data=html,
            file_name=file_name,
            mime="text/html",
            use_container_width=False,
            key="newspaper_download",
        )

    st.markdown(f'<div class="newspaper-view-title">{escape(title)}</div>', unsafe_allow_html=True)
    st.html(html)


def render_app() -> None:
    settings = get_settings()
    icon_path = Path("cat_stock_image.png")
    try:
        from PIL import Image
        page_icon = Image.open(icon_path) if icon_path.exists() else "🐱"
    except Exception:
        page_icon = "🐱"
    st.set_page_config(
        page_title=settings.app_title,
        page_icon=page_icon,
        layout="wide",
    )
    inject_app_styles()

    if st.session_state.get("newspaper_view"):
        _render_newspaper_view()
        return

    mode = st.session_state.get("mode", "stock")
    render_shell_with_toggle(mode)

    if mode == "stock":
        _render_stock_mode()
    else:
        _render_coin_mode()


def _render_stock_mode() -> None:
    """STOCK 모드 — 기존 3개 탭"""
    market_tab, stock_tab, theme_tab = st.tabs(["시황 브리핑", "개별 종목 분석", "테마 공부"])
    with market_tab:
        _render_market_page()
    with stock_tab:
        _render_stock_page()
    with theme_tab:
        _render_theme_page()


def _render_coin_mode() -> None:
    """COIN 모드 — 공부용 대시보드"""
    guide_tab, coin_tab, single_tab, sector_tab, note_tab = st.tabs(["처음 가이드", "코인 시황", "개별 코인", "섹터 공부", "학습 노트"])
    with guide_tab:
        _render_coin_beginner_guide()
    with coin_tab:
        _render_coin_market_page()
    with single_tab:
        _render_coin_detail_page()
    with sector_tab:
        _render_coin_sector_page()
    with note_tab:
        _render_coin_study_note_page()


def _render_coin_beginner_guide() -> None:
    st.markdown(
        """
        <section class="coin-guide">
          <div class="coin-guide__hero">
            <div class="coin-guide__panel">
              <p class="coin-guide__eyebrow">Beginner Guide</p>
              <h2 class="coin-guide__title">코인은 가격보다 흐름부터 보면 덜 어렵습니다.</h2>
              <p class="coin-guide__lead">
                코인 시장은 24시간 움직이고 용어도 낯설어서 처음엔 숫자가 전부 뒤섞여 보입니다.
                먼저 시장 온도, 돈이 몰리는 방향, 개별 코인의 위험 요인을 순서대로 보면
                오늘 무슨 일이 일어났는지 훨씬 차분하게 읽을 수 있습니다.
              </p>
            </div>
            <div class="coin-guide__rules">
              <div class="coin-guide__rule">
                <strong>시장</strong>
                <span>BTC와 ETH가 전체 분위기를 잡습니다. 둘이 약하면 알트코인은 더 흔들릴 수 있습니다.</span>
              </div>
              <div class="coin-guide__rule">
                <strong>돈길</strong>
                <span>도미넌스, 거래대금, 섹터 강도를 보면 돈이 어디로 이동하는지 보입니다.</span>
              </div>
              <div class="coin-guide__rule">
                <strong>위험</strong>
                <span>FDV, 김치 프리미엄, 펀딩비, OI는 과열과 희석 위험을 확인하는 장치입니다.</span>
              </div>
            </div>
          </div>

          <div class="coin-guide__section">
            <p class="coin-guide__section-title">처음 보는 순서</p>
            <div class="coin-guide__flow">
              <div class="coin-guide-step">
                <div class="coin-guide-step__num">1</div>
                <p class="coin-guide-step__title">시장 온도</p>
                <p class="coin-guide-step__copy">총 시총, BTC, ETH, 거래대금으로 시장이 강한지 약한지 봅니다.</p>
              </div>
              <div class="coin-guide-step">
                <div class="coin-guide-step__num">2</div>
                <p class="coin-guide-step__title">심리</p>
                <p class="coin-guide-step__copy">공포탐욕지수와 도미넌스로 과열인지 방어장인지 확인합니다.</p>
              </div>
              <div class="coin-guide-step">
                <div class="coin-guide-step__num">3</div>
                <p class="coin-guide-step__title">한국 수급</p>
                <p class="coin-guide-step__copy">업비트 거래대금과 김치 프리미엄으로 국내 과열을 봅니다.</p>
              </div>
              <div class="coin-guide-step">
                <div class="coin-guide-step__num">4</div>
                <p class="coin-guide-step__title">섹터</p>
                <p class="coin-guide-step__copy">L1, DeFi, AI, Meme 같은 섹터 중 어디가 강한지 비교합니다.</p>
              </div>
              <div class="coin-guide-step">
                <div class="coin-guide-step__num">5</div>
                <p class="coin-guide-step__title">개별 코인</p>
                <p class="coin-guide-step__copy">시총, FDV, TVL, 거래량, 펀딩비로 움직임의 이유를 좁힙니다.</p>
              </div>
            </div>
          </div>

          <div class="coin-guide__section">
            <p class="coin-guide__section-title">기본 용어를 이렇게 읽습니다</p>
            <div class="coin-guide__cards">
              <div class="coin-guide-card">
                <span class="coin-guide-card__chip coin-guide-card__chip--core">기준</span>
                <p class="coin-guide-card__name">BTC</p>
                <p class="coin-guide-card__desc">코인 시장의 기준 자산입니다. BTC가 흔들리면 대부분의 코인도 영향을 받습니다.</p>
              </div>
              <div class="coin-guide-card">
                <span class="coin-guide-card__chip coin-guide-card__chip--core">기준</span>
                <p class="coin-guide-card__name">ETH</p>
                <p class="coin-guide-card__desc">스마트컨트랙트 생태계의 대표 자산입니다. 알트 시장 체력을 볼 때 같이 봅니다.</p>
              </div>
              <div class="coin-guide-card">
                <span class="coin-guide-card__chip coin-guide-card__chip--flow">돈길</span>
                <p class="coin-guide-card__name">도미넌스</p>
                <p class="coin-guide-card__desc">전체 시총에서 BTC 비중입니다. 오르면 BTC 중심, 내리면 알트 확산을 의심합니다.</p>
              </div>
              <div class="coin-guide-card">
                <span class="coin-guide-card__chip coin-guide-card__chip--flow">돈길</span>
                <p class="coin-guide-card__name">거래대금</p>
                <p class="coin-guide-card__desc">관심의 크기입니다. 가격만 오르고 거래대금이 작으면 지속성을 조심합니다.</p>
              </div>
              <div class="coin-guide-card">
                <span class="coin-guide-card__chip coin-guide-card__chip--learn">크기</span>
                <p class="coin-guide-card__name">시가총액</p>
                <p class="coin-guide-card__desc">가격보다 중요한 코인의 전체 크기입니다. 서로 다른 코인을 비교할 때 먼저 봅니다.</p>
              </div>
              <div class="coin-guide-card">
                <span class="coin-guide-card__chip coin-guide-card__chip--risk">위험</span>
                <p class="coin-guide-card__name">FDV</p>
                <p class="coin-guide-card__desc">모든 물량이 풀렸다고 가정한 가치입니다. 시총보다 너무 크면 희석을 확인합니다.</p>
              </div>
              <div class="coin-guide-card">
                <span class="coin-guide-card__chip coin-guide-card__chip--learn">사용량</span>
                <p class="coin-guide-card__name">TVL</p>
                <p class="coin-guide-card__desc">프로토콜에 예치된 자금입니다. DeFi 코인은 실제 사용량을 볼 때 중요합니다.</p>
              </div>
              <div class="coin-guide-card">
                <span class="coin-guide-card__chip coin-guide-card__chip--risk">과열</span>
                <p class="coin-guide-card__name">김치 프리미엄</p>
                <p class="coin-guide-card__desc">한국 가격이 글로벌보다 비싼 정도입니다. 높으면 국내 수급 과열을 의심합니다.</p>
              </div>
              <div class="coin-guide-card">
                <span class="coin-guide-card__chip coin-guide-card__chip--risk">레버리지</span>
                <p class="coin-guide-card__name">펀딩비/OI</p>
                <p class="coin-guide-card__desc">선물 시장의 쏠림입니다. 높아질수록 급격한 청산 변동성을 조심합니다.</p>
              </div>
              <div class="coin-guide-card">
                <span class="coin-guide-card__chip coin-guide-card__chip--flow">유동성</span>
                <p class="coin-guide-card__name">스테이블코인</p>
                <p class="coin-guide-card__desc">시장 안의 대기 자금처럼 봅니다. 늘면 매수 여력이 커질 수 있습니다.</p>
              </div>
            </div>
          </div>

          <div class="coin-guide__section">
            <p class="coin-guide__section-title">초보자가 자주 헷갈리는 장면</p>
            <div class="coin-guide__signals">
              <div class="coin-guide-signal">
                <p class="coin-guide-signal__label">BTC 상승 + 도미넌스 상승</p>
                <p class="coin-guide-signal__text">시장은 강하지만 돈이 BTC 쪽에 몰린 상태일 수 있습니다. 알트 추격은 천천히 봅니다.</p>
              </div>
              <div class="coin-guide-signal">
                <p class="coin-guide-signal__label">가격 상승 + 거래대금 부족</p>
                <p class="coin-guide-signal__text">관심이 얕은 상승일 수 있습니다. 다음 캔들보다 거래대금 지속 여부를 확인합니다.</p>
              </div>
              <div class="coin-guide-signal">
                <p class="coin-guide-signal__label">김치 프리미엄 급등</p>
                <p class="coin-guide-signal__text">국내 수급이 과열됐을 수 있습니다. 글로벌 가격과 함께 비교해야 합니다.</p>
              </div>
            </div>
          </div>

          <div class="coin-guide__footer">
            이 가이드는 매수/매도 판단이 아니라 공부 순서를 잡기 위한 기준입니다. 숫자를 하나씩 외우기보다
            "시장 전체, 돈의 방향, 개별 코인의 위험" 순서로 읽는 연습을 목표로 합니다.
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_coin_placeholder(title: str, description: str) -> None:
    ctrl_col, out_col = st.columns([4, 6], gap="large")
    with ctrl_col:
        render_page_intro("Coming Soon", title)
        render_note(f"개발 중입니다. 곧 {description} 데이터를 제공할 예정입니다.", tone="info")
    with out_col:
        _render_output_box("", "코인 데이터 기능을 준비 중입니다.", box_key=f"coin-placeholder-{title}")


def _render_coin_market_page() -> None:
    ctrl_col, out_col = st.columns([4, 6], gap="large")

    with ctrl_col:
        render_page_intro(
            "Coin Market",
            "시장 온도부터 확인합니다",
            "BTC, ETH, 도미넌스, 심리, 한국 거래소 수급을 한 번에 봅니다.",
        )
        if st.button("시황 불러오기", type="primary", use_container_width=False, key="coin_market_generate"):
            with st.spinner("코인 데이터를 불러오고 있습니다..."):
                result = generate_coin_market_report()
            st.session_state["coin_market_result"] = result

        with st.expander("연결 데이터"):
            render_list(
                [
                    "CoinGecko 글로벌 시총 · 거래대금 · BTC/ETH · 글로벌 시총 상위",
                    "CoinGecko BTC/ETH 30일 가격 차트",
                    "CoinGecko 섹터 카테고리 온도",
                    "Alternative.me 공포탐욕지수",
                    "Upbit KRW 마켓 거래대금 상위",
                    "USD/KRW 기반 BTC 김치 프리미엄",
                    "DefiLlama 스테이블코인 공급 · DeFi TVL · 프로토콜 수수료",
                ]
            )

        if "coin_market_result" in st.session_state:
            result = st.session_state["coin_market_result"]
            _render_data_warnings(result["payload"])
            st.download_button(
                "학습 노트 TXT",
                data=result["text"],
                file_name=f"coin_market_{_compact_date(result['payload']['target_date'])}.txt",
                mime="text/plain",
                use_container_width=False,
            )

    with out_col:
        result = st.session_state.get("coin_market_result")
        if result:
            st.html(build_coin_market_dashboard(result["payload"]))
        else:
            st.html(build_coin_market_empty_state())


def _render_coin_detail_page() -> None:
    ctrl_col, out_col = st.columns([4, 6], gap="large")

    with ctrl_col:
        render_page_intro(
            "Single Coin",
            "코인 하나를 구조적으로 봅니다",
            "가격보다 시총, FDV, 공급, 업비트 수급, 리스크 체크를 같이 봅니다.",
        )
        coin_query = st.text_input("코인명 또는 심볼", placeholder="예: 비트코인, BTC, 솔라나, SOL")
        if st.button("코인 분석", type="primary", use_container_width=False, key="coin_detail_generate"):
            query = coin_query.strip()
            if not query:
                render_note("코인명이나 심볼을 먼저 입력해주세요.", tone="warn")
            else:
                with st.spinner("코인 구조를 불러오고 있습니다..."):
                    result = generate_coin_detail_report(query)
                if result.get("error"):
                    st.session_state["coin_detail_error"] = result
                    render_note(result["error"], tone="warn")
                else:
                    st.session_state["coin_detail_result"] = result
                    st.session_state.pop("coin_detail_error", None)

        with st.expander("연결 데이터"):
            render_list(
                [
                    "CoinGecko 검색 · 코인 상세 · 가격 · 시총 · FDV · 공급 구조",
                    "CoinGecko 카테고리 · 프로젝트 설명 · 커뮤니티/개발 지표",
                    "Upbit KRW 상장 여부 · 현재가 · 거래대금",
                    "USD/KRW 기반 개별 코인 김치 프리미엄",
                    "FDV/시총 · 거래량/시총 · ATH 대비 위치",
                    "CoinGecko 90일 가격 차트",
                    "DefiLlama 프로토콜 TVL 매핑",
                    "Binance USD-M 펀딩비 · 미결제약정",
                ]
            )

        error = st.session_state.get("coin_detail_error")
        if error and error.get("candidates"):
            with st.expander("검색 후보"):
                render_list(
                    [
                        f"{item.get('name')} ({str(item.get('symbol', '')).upper()}) · ID {item.get('id')}"
                        for item in error["candidates"]
                    ]
                )

        if "coin_detail_result" in st.session_state:
            result = st.session_state["coin_detail_result"]
            _render_data_warnings(result["payload"])
            st.download_button(
                "학습 노트 TXT",
                data=result["text"],
                file_name=f"coin_{result['payload']['basics']['id']}_{_compact_date(result['payload']['target_date'])}.txt",
                mime="text/plain",
                use_container_width=False,
            )

    with out_col:
        result = st.session_state.get("coin_detail_result")
        if result:
            st.html(build_coin_detail_dashboard(result["payload"]))
        else:
            st.html(build_coin_detail_empty_state())


def _render_coin_sector_page() -> None:
    ctrl_col, out_col = st.columns([4, 6], gap="large")

    with ctrl_col:
        render_page_intro(
            "Sector Study",
            "섹터별로 코인을 공부합니다",
            "카테고리별 시총, 거래대금, 대표 코인, 공부 포인트를 한 번에 봅니다.",
        )
        if st.button("섹터 불러오기", type="primary", use_container_width=False, key="coin_sector_generate"):
            with st.spinner("섹터 데이터를 불러오고 있습니다..."):
                result = generate_coin_sector_report()
            st.session_state["coin_sector_result"] = result

        with st.expander("연결 데이터"):
            render_list(
                [
                    "CoinGecko 카테고리별 시총 · 24h 변화 · 거래대금",
                    "CoinGecko 카테고리별 top 3 코인 ID",
                    "대표 코인 가격 · 시총 · 24h 등락률",
                    "Layer 1 · DeFi · AI · Meme 등 섹터별 공부 포인트",
                    "DefiLlama TVL 상위 프로토콜 · 수수료 · 스테이블코인 공급",
                ]
            )

        if "coin_sector_result" in st.session_state:
            result = st.session_state["coin_sector_result"]
            _render_data_warnings(result["payload"])
            st.download_button(
                "학습 노트 TXT",
                data=result["text"],
                file_name=f"coin_sector_{_compact_date(result['payload']['target_date'])}.txt",
                mime="text/plain",
                use_container_width=False,
            )

    with out_col:
        result = st.session_state.get("coin_sector_result")
        if result:
            st.html(build_coin_sector_dashboard(result["payload"]))
        else:
            st.html(build_coin_sector_empty_state())


def _render_coin_study_note_page() -> None:
    ctrl_col, out_col = st.columns([4, 6], gap="large")

    with ctrl_col:
        render_page_intro(
            "Study Note",
            "오늘 배운 것을 내 말로 남깁니다",
            "시장 국면, 강한 섹터, 본 코인, 반증 조건을 짧게 정리합니다.",
        )
        regime = st.selectbox(
            "시장 국면",
            ["관망", "위험 선호", "위험 회피", "알트 확산", "한국 과열"],
            key="coin_note_regime",
        )
        market_reason = st.text_area("시장 국면 근거", placeholder="예: BTC는 상승했지만 도미넌스도 올라서 알트 확산은 아직 약함")
        sector = st.text_input("가장 강한 섹터", placeholder="예: Layer 1, DeFi, Stablecoin")
        sector_reason = st.text_area("섹터가 강해 보이는 이유", placeholder="예: 섹터 시총과 거래대금이 같이 증가했고 대표 코인들이 동반 상승")
        coin = st.text_input("오늘 본 코인", placeholder="예: SOL")
        hypothesis = st.text_area("상승/하락 원인 가설", placeholder="예: 거래대금 증가와 생태계 TVL 회복이 같이 보임")
        invalidating_condition = st.text_area("반증 조건", placeholder="예: 거래대금이 줄고 펀딩비만 높아지면 단기 과열로 봄")
        next_metric = st.text_input("다음에 확인할 지표", placeholder="예: TVL, fees, funding rate, unlock")
        next_source = st.text_input("다음에 볼 자료", placeholder="예: 공식 docs, DefiLlama, 거래소 공지")

        if st.button("노트 만들기", type="primary", use_container_width=False, key="coin_note_generate"):
            result = generate_coin_study_note(
                regime=regime,
                market_reason=market_reason,
                sector=sector,
                sector_reason=sector_reason,
                coin=coin,
                hypothesis=hypothesis,
                invalidating_condition=invalidating_condition,
                next_metric=next_metric,
                next_source=next_source,
            )
            st.session_state["coin_note_result"] = result

        if "coin_note_result" in st.session_state:
            result = st.session_state["coin_note_result"]
            st.download_button(
                "학습 노트 TXT",
                data=result["text"],
                file_name=f"coin_study_note_{_compact_date(result['payload']['target_date'])}.txt",
                mime="text/plain",
                use_container_width=False,
            )

    with out_col:
        result_text = st.session_state.get("coin_note_result", {}).get("text", "")
        _render_output_box(
            result_text,
            "내용을 적고 노트 만들기 버튼을 누르면 시장 국면, 섹터, 코인 가설, 반증 조건이 정리됩니다.",
            box_key="coin-study-note",
        )

    _render_hypothesis_scoreboard()


def _format_snapshot_value(value: object) -> str:
    if value is None:
        return "—"
    if isinstance(value, (int, float)):
        if abs(value) >= 1_000_000_000:
            return f"{value / 1_000_000_000:,.1f}B"
        if abs(value) >= 1_000:
            return f"{value:,.0f}"
        return f"{value:,.2f}"
    return str(value)


def _render_hypothesis_scoreboard() -> None:
    """가설 채점판 — 기록 시점 스냅샷과 현재 데이터를 대조해 스스로 판정한다."""
    from src.services.coin_study_note_service import collect_market_snapshot
    from src.utils.hypothesis_store import VERDICT_LABELS, list_hypotheses, set_verdict, verdict_stats

    hypotheses = list_hypotheses(limit=20)

    render_ctrl_section("가설 채점판")
    if not hypotheses:
        render_note(
            "가설이 담긴 노트를 만들면 그 순간의 시장 스냅샷과 함께 여기에 기록됩니다. "
            "며칠 뒤 다시 열어 시장이 채점하게 해보세요.",
            tone="info",
        )
        return

    stats = verdict_stats()
    pending = stats["total"] - stats["judged"]
    st.markdown(
        f'<p class="cat-section__copy">기록 {stats["total"]}건 · 판정 대기 {pending}건 — '
        f'맞음 {stats["right"]} · 부분 {stats["partial"]} · 틀림 {stats["wrong"]} · 반증됨 {stats["invalidated"]}</p>',
        unsafe_allow_html=True,
    )

    if st.button("지금 시장 데이터로 대조", key="hypothesis_refresh_now"):
        with st.spinner("현재 시장 스냅샷을 가져오는 중..."):
            st.session_state["hypothesis_now_snapshot"] = collect_market_snapshot()
    now_snapshot = st.session_state.get("hypothesis_now_snapshot") or {}

    for item in hypotheses:
        note = item["note"]
        created = str(item["created_at"])[:16].replace("T", " ")
        subject = note.get("coin") or note.get("sector") or note.get("regime") or "시장"
        verdict_label = VERDICT_LABELS.get(item["verdict"], "판정 대기")
        with st.expander(f"[{verdict_label}] {created} · {subject} — {str(note.get('hypothesis') or '')[:40]}"):
            st.markdown(
                f"**가설** — {escape(str(note.get('hypothesis') or '—'))}<br>"
                f"**반증 조건** — {escape(str(note.get('invalidating_condition') or '—'))}",
                unsafe_allow_html=True,
            )
            snapshot = item["snapshot"]
            if snapshot:
                rows = "".join(
                    f"<tr><td>{escape(key)}</td>"
                    f"<td style='text-align:right'>{escape(_format_snapshot_value(value))}</td>"
                    f"<td style='text-align:right'>{escape(_format_snapshot_value(now_snapshot.get(key))) if now_snapshot else '—'}</td></tr>"
                    for key, value in snapshot.items()
                )
                st.markdown(
                    "<table style='width:100%;font-size:12px;border-collapse:collapse'>"
                    "<thead><tr><th style='text-align:left'>지표</th>"
                    "<th style='text-align:right'>기록 시점</th><th style='text-align:right'>지금</th></tr></thead>"
                    f"<tbody>{rows}</tbody></table>",
                    unsafe_allow_html=True,
                )
                if not now_snapshot:
                    st.caption("'지금 시장 데이터로 대조'를 누르면 오른쪽 열이 채워집니다.")
            else:
                st.caption("기록 시점 스냅샷이 없습니다 (수집 실패).")

            if item["verdict"] is None:
                cols = st.columns(4)
                for col, (verdict_key, label) in zip(cols, VERDICT_LABELS.items()):
                    with col:
                        if st.button(label, key=f"verdict_{item['id']}_{verdict_key}", use_container_width=True):
                            set_verdict(item["id"], verdict_key)
                            st.rerun()
            else:
                judged_at = str(item.get("verdict_at") or "")[:10]
                st.caption(f"판정: {verdict_label} ({judged_at})")


def _render_market_page() -> None:
    ctrl_col, out_col = st.columns([4, 6], gap="large")

    with ctrl_col:
        render_page_intro("Market Briefing", "오늘 시황을 한 번에 정리합니다")
        render_ctrl_section("오늘의 브리핑")
        default_stock_date = date.fromisoformat(resolve_stock_trading_date(date.today())["target_date"])
        if st.button("오늘의 브리핑 내리기", type="primary", use_container_width=True, key="market_generate"):
            with st.spinner("내리는 중입니다..."):
                result = generate_market_briefing(default_stock_date.isoformat())
            st.session_state["market_result"] = result

        with st.expander("다른 날짜 보기"):
            target_date = st.date_input("기준일", value=default_stock_date, format="YYYY-MM-DD")
            if st.button("이 날짜로 내리기", use_container_width=True, key="market_generate_dated"):
                with st.spinner("내리는 중입니다..."):
                    result = generate_market_briefing(target_date.isoformat())
                st.session_state["market_result"] = result

        with st.expander("연결 데이터"):
            render_list(
                [
                    "코스피 · 코스닥 지수와 거래대금",
                    "다우 · S&P500 · 나스닥 · 달러원 · 미국 10년물 · WTI · 상해 · 심천",
                    "거래대금 상위 종목",
                    "업종별 등락률",
                    "외국인 · 기관 순매수/순매도 상위",
                    "등락률 상승 50개 · 하락 20개 · 상한가 · 시간외 단일가",
                    "시장 뉴스 제목 · 원문 링크",
                    "프로그램 차익 · 비차익",
                ]
            )

        if "market_result" in st.session_state:
            result = st.session_state["market_result"]
            _render_missing_data_warnings(result["payload"], "market")
            dash_html = build_market_dashboard(result["payload"])
            market_dashboard_file = f"market_dashboard_{_compact_date(result['payload']['target_date'])}.html"
            _render_newspaper_button(
                title="시황 브리핑 신문",
                html=dash_html,
                file_name=market_dashboard_file,
                key="market_newspaper_view",
            )
            st.download_button(
                ".txt 저장",
                data=result["text"],
                file_name=f"market_briefing_{_compact_date(result['payload']['target_date'])}.txt",
                mime="text/plain",
                use_container_width=False,
            )
            st.download_button(
                "신문 .html 저장",
                data=dash_html,
                file_name=market_dashboard_file,
                mime="text/html",
                use_container_width=False,
            )

    with out_col:
        _render_dashboard_with_text_output(
            result_key="market_result",
            box_key="market",
            placeholder="오늘의 브리핑 내리기를 누르면 여기에 오늘의 텍스트가 담깁니다.",
            dashboard_builder=build_market_dashboard,
        )


def _render_stock_page() -> None:
    ctrl_col, out_col = st.columns([4, 6], gap="large")

    with ctrl_col:
        render_page_intro("Single Stock", "종목 하나를 빠르게 분석합니다")
        render_ctrl_section("분석 설정")
        stock_name = st.text_input("종목명", placeholder="예: 삼성전자")
        default_stock_date = date.fromisoformat(resolve_stock_trading_date(date.today())["target_date"])
        report_dates = st.date_input(
            "리포트 기간",
            value=(default_stock_date, default_stock_date),
            format="YYYY-MM-DD",
        )
        if st.button("종목 분석 내리기", type="primary", use_container_width=True, key="stock_generate"):
            name = stock_name.strip()
            if not name:
                render_note("종목명을 먼저 입력해주세요.", tone="warn")
            else:
                dates = report_dates if isinstance(report_dates, (list, tuple)) else (report_dates, report_dates)
                from_iso = dates[0].isoformat()
                to_iso = dates[1].isoformat() if len(dates) > 1 else from_iso
                with st.spinner("정리하고 있습니다..."):
                    result = generate_stock_report(name, report_from=from_iso, report_to=to_iso)
                st.session_state["stock_result"] = result

        with st.expander("연결 데이터"):
            render_list(
                [
                    "현재가 · 등락률 · 거래대금 · 시가총액",
                    "52주 고저 · PER · PBR · ROE",
                    "이동평균선 위치",
                    "외국인 · 기관 최근 20일 누적 수급",
                    "DART 공시 · 최근 재무 요약 · 대주주 지분율",
                    "최근 뉴스 헤드라인 · 원문 링크 · 증권사 리포트 · 컨센서스 목표가",
                ]
            )

        if "stock_result" in st.session_state:
            result = st.session_state["stock_result"]
            _render_missing_data_warnings(result["payload"], "stock")
            dash_html = build_stock_dashboard(result["payload"])
            stock_dashboard_file = f"stock_{result['payload']['basics']['name']}_dashboard.html"
            _render_newspaper_button(
                title=f"{result['payload']['basics']['name']} 신문",
                html=dash_html,
                file_name=stock_dashboard_file,
                key="stock_newspaper_view",
            )
            st.download_button(
                ".txt 저장",
                data=result["text"],
                file_name=f"stock_{result['payload']['basics']['name']}.txt",
                mime="text/plain",
                use_container_width=False,
            )
            st.download_button(
                "신문 .html 저장",
                data=dash_html,
                file_name=stock_dashboard_file,
                mime="text/html",
                use_container_width=False,
            )

    with out_col:
        _render_dashboard_with_text_output(
            result_key="stock_result",
            box_key="stock",
            placeholder="종목명을 입력하고 종목 분석 내리기를 누르면 여기에 결과가 담깁니다.",
            dashboard_builder=build_stock_dashboard,
        )


def _render_theme_page() -> None:
    ctrl_col, out_col = st.columns([4, 6], gap="large")

    with ctrl_col:
        render_page_intro("Theme Study", "테마 공부 자료를 정리합니다")
        render_ctrl_section("분석 설정")
        theme_name = st.text_input("테마명", placeholder="예: HBM, 2차전지, 원전")
        if st.button("테마 자료 내리기", type="primary", use_container_width=True, key="theme_generate"):
            name = theme_name.strip()
            if not name:
                render_note("테마명을 먼저 입력해주세요.", tone="warn")
            else:
                with st.spinner("정리하고 있습니다..."):
                    result = generate_theme_report(name)
                st.session_state["theme_result"] = result

        with st.expander("연결 데이터"):
            render_list(
                [
                    "네이버 테마 관련 종목 목록 (현재가 · 등락률)",
                    "네이버 뉴스 검색 (테마명 기준 최근 뉴스)",
                    "공시 · 리포트 요약은 준비 중",
                ]
            )

        if "theme_result" in st.session_state:
            result = st.session_state["theme_result"]
            _render_missing_data_warnings(result["payload"], "theme")
            dash_html = build_theme_dashboard(result["payload"])
            theme_dashboard_file = f"theme_{result['payload']['theme_name']}_dashboard.html"
            _render_newspaper_button(
                title=f"{result['payload']['theme_name']} 테마 신문",
                html=dash_html,
                file_name=theme_dashboard_file,
                key="theme_newspaper_view",
            )
            st.download_button(
                ".txt 저장",
                data=result["text"],
                file_name=f"theme_{result['payload']['theme_name']}.txt",
                mime="text/plain",
                use_container_width=False,
            )
            st.download_button(
                "신문 .html 저장",
                data=dash_html,
                file_name=theme_dashboard_file,
                mime="text/html",
                use_container_width=False,
            )

    with out_col:
        _render_dashboard_with_text_output(
            result_key="theme_result",
            box_key="theme",
            placeholder="테마명을 입력하고 테마 자료 내리기를 누르면 여기에 결과가 담깁니다.",
            dashboard_builder=build_theme_dashboard,
        )


def _render_missing_data_warnings(payload: dict, mode: str) -> None:
    """수집 실패 항목을 경고로 표시 (프롬프트 텍스트와 같은 판정 사용)"""
    if mode == "market":
        missing = market_missing_items(payload)
    elif mode == "stock":
        missing = stock_missing_items(payload)
    elif mode == "theme":
        missing = theme_missing_items(payload)
    else:
        missing = []

    if missing:
        render_note("수집 실패 항목: " + " · ".join(missing), tone="warn")


def _render_data_warnings(payload: dict) -> None:
    warnings = payload.get("data_warnings") or []
    if warnings:
        render_note("데이터 경고: " + " · ".join(str(item) for item in warnings), tone="warn")


_OUTPUT_LABELS: dict[str, str] = {
    "market": "MARKET BRIEFING",
    "stock": "STOCK ANALYSIS",
    "theme": "THEME STUDY",
    "coin_market": "COIN MARKET",
    "coin_detail": "COIN ANALYSIS",
    "coin_sector": "SECTOR STUDY",
    "coin_note": "STUDY NOTE",
}


def _render_output_box(result_text: str, placeholder: str, box_key: str) -> None:
    has_result = bool(result_text)
    box_seed = f"{box_key}|{placeholder}"
    box_id = "cat-output-" + hashlib.sha1(box_seed.encode("utf-8")).hexdigest()[:12]
    label = _OUTPUT_LABELS.get(box_key, "ANALYSIS OUTPUT")
    content_html = (
        f'<pre class="cat-output-pre">{escape(result_text)}</pre>'
        if has_result
        else f'<div class="cat-output-placeholder">{escape(placeholder)}</div>'
    )
    disabled_attr = "" if has_result else "disabled"
    st.html(
        f"""
        <div id="{box_id}" class="cat-output-shell">
          <div class="cat-output-header">
            <span class="cat-output-label">{escape(label)}</span>
            <button class="cat-copy-button" type="button" data-cat-copy-target="{box_id}" {disabled_attr}>복사</button>
          </div>
          <div class="cat-output-body">
            {content_html}
          </div>
          <textarea id="{box_id}-copy-source" class="cat-output-copy-source" readonly>{escape(result_text)}</textarea>
        </div>
        """
    )

    copy_script = """
    <style>
      html, body { margin: 0; padding: 0; width: 0; height: 0; overflow: hidden; background: transparent !important; }
    </style>
    <script>
      (() => {
        try {
          const frame = window.frameElement;
          if (frame) {
            frame.setAttribute("allowtransparency", "true");
            frame.style.display = "none";
            frame.style.width = "0";
            frame.style.height = "0";
            frame.style.background = "transparent";
            frame.style.border = "0";
            if (frame.parentElement) {
              frame.parentElement.style.display = "none";
              frame.parentElement.style.background = "transparent";
            }
          }
        } catch (error) {}

        const doc = window.parent && window.parent.document;
        if (!doc) {
          return;
        }

        async function writeClipboard(text, source) {
          const parentWindow = window.parent || window;
          if (parentWindow.navigator.clipboard && parentWindow.isSecureContext) {
            await parentWindow.navigator.clipboard.writeText(text);
            return;
          }

          source.focus();
          source.select();
          doc.execCommand("copy");
          source.blur();
        }

        function resetButton(button) {
          button.textContent = "복사";
          button.classList.remove("is-copied", "is-failed");
        }

        function bindCopyButtons() {
          const buttons = doc.querySelectorAll("[data-cat-copy-target]");
          buttons.forEach((button) => {
            if (button.dataset.catCopyBound === "1") {
              return;
            }
            button.dataset.catCopyBound = "1";

            button.addEventListener("click", async () => {
              if (button.disabled) {
                return;
              }

              const targetId = button.getAttribute("data-cat-copy-target");
              const source = doc.getElementById(`${targetId}-copy-source`);
              const text = source ? source.value : "";
              if (!text) {
                return;
              }

              try {
                await writeClipboard(text, source);
                button.textContent = "복사됨";
                button.classList.add("is-copied");
                button.classList.remove("is-failed");
              } catch (error) {
                button.textContent = "복사 실패";
                button.classList.add("is-failed");
                button.classList.remove("is-copied");
              }

              window.setTimeout(() => resetButton(button), 1400);
            });
          });
        }

        bindCopyButtons();

        if (!window.__catOutputObserver) {
          window.__catOutputObserver = new MutationObserver(bindCopyButtons);
          window.__catOutputObserver.observe(doc.body, { childList: true, subtree: true });
        }
      })();
    </script>
    """
    components.html(copy_script, height=0, scrolling=False)


def _compact_date(date_text: str) -> str:
    return date_text.replace("-", "")

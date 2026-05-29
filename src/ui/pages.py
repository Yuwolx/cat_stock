from __future__ import annotations

from datetime import date

import streamlit as st

from src.config.settings import get_settings
from src.services.market_service import generate_market_briefing
from src.services.stock_service import generate_stock_report
from src.services.theme_service import generate_theme_report
from src.ui.components import (
    inject_app_styles,
    render_card_header,
    render_list,
    render_note,
    render_output_panel,
    render_page_intro,
    render_shell,
    render_status_strip,
)


def render_app() -> None:
    settings = get_settings()
    st.set_page_config(
        page_title=settings.app_title,
        page_icon="cat_stock_image.png",
        layout="wide",
    )
    inject_app_styles()
    render_shell(
        "오늘의 주식 정보를 정리해드립니다",
        "시황 브리핑, 개별 종목 분석, 테마 공부 — 세 가지를 생성하고 바로 복사할 수 있습니다.",
    )
    status_col, mock_col = st.columns([0.84, 0.16], vertical_alignment="center")
    with status_col:
        render_status_strip(bool(settings.dart_api_key), settings.output_dir)
    with mock_col:
        use_mock_data = st.checkbox("더미 데이터", value=settings.use_mock_data)

    market_tab, stock_tab, theme_tab = st.tabs(["시황 브리핑", "개별 종목 분석", "테마 공부"])

    with market_tab:
        _render_market_page(use_mock_data)

    with stock_tab:
        _render_stock_page(use_mock_data)

    with theme_tab:
        _render_theme_page(use_mock_data)


def _render_market_page(use_mock_data: bool) -> None:
    render_page_intro(
        "Market Briefing",
        "장 마감 요약을 한 번에 만듭니다.",
    )

    form_col, info_col = st.columns([1.12, 0.88], gap="large")

    with form_col:
        render_card_header(
            "Generate",
            "시황 브리핑 생성",
            "장 마감 기준 날짜를 선택하고 버튼을 누르면 결과 텍스트가 아래에 나타납니다.",
        )
        target_date = st.date_input("기준일", value=date.today(), format="YYYY-MM-DD")
        trigger = st.button("시황 브리핑 생성", type="primary", use_container_width=True, key="market_generate")
        if trigger:
            with st.spinner("시황 브리핑을 정리하고 있습니다..."):
                result = generate_market_briefing(target_date.isoformat(), use_mock_data=use_mock_data)
            st.session_state["market_result"] = result

    with info_col:
        render_card_header(
            "Current coverage",
            "현재 연결 데이터",
            "지금 실제 결과 텍스트에 포함되는 항목입니다.",
        )
        render_list(
            [
                "코스피 · 코스닥 지수와 거래대금",
                "다우 · S&P500 · 나스닥 · 달러원 · 미국 10년물 · WTI · 상해",
                "거래대금 상위 종목",
                "외국인 · 기관 순매수/순매도 상위",
                "프로그램 차익 · 비차익, 상한가 종목, DART 주요 공시",
            ]
        )

    if "market_result" in st.session_state:
        result = st.session_state["market_result"]
        render_output_panel(
            result["text"],
            f"market_briefing_{_compact_date(result['payload']['target_date'])}.txt",
            result["path"],
        )


def _render_stock_page(use_mock_data: bool) -> None:
    render_page_intro(
        "Single Stock",
        "종목 하나를 공시와 재무 중심으로 정리합니다.",
    )

    form_col, info_col = st.columns([1.12, 0.88], gap="large")

    with form_col:
        render_card_header(
            "Input",
            "종목명 입력",
            "예시는 삼성전자, 현대차처럼 일반적으로 쓰는 종목명을 그대로 넣으면 됩니다.",
        )
        stock_name = st.text_input("종목명", placeholder="예: 삼성전자")
        trigger = st.button("개별 종목 분석 생성", type="primary", use_container_width=True, key="stock_generate")
        if trigger:
            name = stock_name.strip()
            if not name:
                render_note("종목명을 먼저 입력해주세요.", tone="warn")
            else:
                with st.spinner("종목 분석 텍스트를 정리하고 있습니다..."):
                    result = generate_stock_report(name, use_mock_data=use_mock_data)
                st.session_state["stock_result"] = result

    with info_col:
        render_card_header(
            "Current coverage",
            "현재 연결 데이터",
            "개별 종목 분석 화면에서 실제로 불러오는 데이터입니다.",
        )
        render_list(
            [
                "DART 최근 공시 목록",
                "DART 주요 계정 기준 분기 · 반기 · 연간 재무 요약",
                "종목명 기반 corp code 자동 매핑",
                "결과 텍스트 저장과 TXT 다운로드",
            ]
        )

    if "stock_result" in st.session_state:
        result = st.session_state["stock_result"]
        render_output_panel(
            result["text"],
            f"stock_{result['payload']['basics']['name']}.txt",
            result["path"],
        )


def _render_theme_page(use_mock_data: bool) -> None:
    render_page_intro(
        "Theme Study",
        "테마 단위로 공부할 입력 재료를 정리합니다.",
    )

    form_col, info_col = st.columns([1.12, 0.88], gap="large")

    with form_col:
        render_card_header(
            "Input",
            "테마명 입력",
            "예시는 HBM, 2차전지, 원전처럼 실제로 묶어 부르는 테마명을 그대로 쓰면 됩니다.",
        )
        theme_name = st.text_input("테마명", placeholder="예: HBM, 2차전지, 원전")
        trigger = st.button("테마 공부 자료 생성", type="primary", use_container_width=True, key="theme_generate")
        if trigger:
            name = theme_name.strip()
            if not name:
                render_note("테마명을 먼저 입력해주세요.", tone="warn")
            else:
                with st.spinner("테마 텍스트를 정리하고 있습니다..."):
                    result = generate_theme_report(name, use_mock_data=use_mock_data)
                st.session_state["theme_result"] = result

    with info_col:
        render_card_header(
            "Next coverage",
            "추가 예정 데이터",
            "테마 공부 화면에 다음 단계로 연결할 항목입니다.",
        )
        render_list(
            [
                "관련 종목 리스트",
                "테마 관련 뉴스와 공시",
                "글로벌 피어 비교",
                "증권사 리포트 요약",
            ]
        )

    if "theme_result" in st.session_state:
        result = st.session_state["theme_result"]
        render_output_panel(
            result["text"],
            f"theme_{result['payload']['theme_name']}.txt",
            result["path"],
        )


def _compact_date(date_text: str) -> str:
    return date_text.replace("-", "")

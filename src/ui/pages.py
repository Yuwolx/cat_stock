from __future__ import annotations

from datetime import date
from html import escape

import streamlit as st
import streamlit.components.v1 as components

from src.config.settings import get_settings
from src.services.market_service import generate_market_briefing
from src.services.stock_service import generate_stock_report
from src.services.theme_service import generate_theme_report
from src.ui.components import (
    inject_app_styles,
    render_list,
    render_note,
    render_page_intro,
    render_shell,
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
        "주식 데이터를 정리해드립니다.",
        "시황 브리핑, 개별 종목 분석, 테마 공부 자료를 만들고 바로 복사할 수 있습니다.",
    )

    market_tab, stock_tab, theme_tab = st.tabs(["시황 브리핑", "개별 종목 분석", "테마 공부"])

    with market_tab:
        _render_market_page()

    with stock_tab:
        _render_stock_page()

    with theme_tab:
        _render_theme_page()


def _render_market_page() -> None:
    ctrl_col, out_col = st.columns([4, 6], gap="large")

    with ctrl_col:
        render_page_intro("Market Briefing", "오늘 시황을 한 번에 정리합니다")
        input_col, _ = st.columns([0.62, 0.38], gap="small")
        with input_col:
            target_date = st.date_input("기준일", value=date.today(), format="YYYY-MM-DD")
            if st.button("브리핑 생성", type="primary", use_container_width=False, key="market_generate"):
                with st.spinner("정리하고 있습니다..."):
                    result = generate_market_briefing(target_date.isoformat())
                st.session_state["market_result"] = result

            with st.expander("연결 데이터"):
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
                st.download_button(
                    "TXT 다운로드",
                    data=result["text"],
                    file_name=f"market_briefing_{_compact_date(result['payload']['target_date'])}.txt",
                    mime="text/plain",
                    use_container_width=False,
                )

    with out_col:
        result_text = st.session_state.get("market_result", {}).get("text", "")
        _render_output_box(result_text, "기준일을 선택하고 생성 버튼을 누르면 여기에 결과가 나타납니다.")


def _render_stock_page() -> None:
    ctrl_col, out_col = st.columns([4, 6], gap="large")

    with ctrl_col:
        render_page_intro("Single Stock", "종목 하나를 빠르게 분석합니다")
        input_col, _ = st.columns([0.62, 0.38], gap="small")
        with input_col:
            stock_name = st.text_input("종목명", placeholder="예: 삼성전자")
            if st.button("분석 생성", type="primary", use_container_width=False, key="stock_generate"):
                name = stock_name.strip()
                if not name:
                    render_note("종목명을 먼저 입력해주세요.", tone="warn")
                else:
                    with st.spinner("정리하고 있습니다..."):
                        result = generate_stock_report(name)
                    st.session_state["stock_result"] = result

            with st.expander("연결 데이터"):
                render_list(
                    [
                        "현재가 · 등락률 · 거래대금 · 시가총액",
                        "52주 고저 · PER · PBR · ROE",
                        "이동평균선 위치",
                        "외국인 · 기관 최근 20일 누적 수급",
                        "DART 공시 · 최근 재무 요약 · 대주주 지분율",
                        "최근 뉴스 · 증권사 리포트 · 컨센서스 목표가",
                    ]
                )

            if "stock_result" in st.session_state:
                result = st.session_state["stock_result"]
                st.download_button(
                    "TXT 다운로드",
                    data=result["text"],
                    file_name=f"stock_{result['payload']['basics']['name']}.txt",
                    mime="text/plain",
                    use_container_width=False,
                )

    with out_col:
        result_text = st.session_state.get("stock_result", {}).get("text", "")
        _render_output_box(result_text, "종목명을 입력하고 생성 버튼을 누르면 여기에 결과가 나타납니다.")


def _render_theme_page() -> None:
    ctrl_col, out_col = st.columns([4, 6], gap="large")

    with ctrl_col:
        render_page_intro("Theme Study", "테마 공부 자료를 정리합니다")
        input_col, _ = st.columns([0.62, 0.38], gap="small")
        with input_col:
            theme_name = st.text_input("테마명", placeholder="예: HBM, 2차전지, 원전")
            if st.button("자료 생성", type="primary", use_container_width=False, key="theme_generate"):
                name = theme_name.strip()
                if not name:
                    render_note("테마명을 먼저 입력해주세요.", tone="warn")
                else:
                    with st.spinner("정리하고 있습니다..."):
                        result = generate_theme_report(name)
                    st.session_state["theme_result"] = result

            with st.expander("현재 상태"):
                render_list(
                    [
                        "테마 화면은 아직 실데이터 연결 전입니다.",
                        "지금은 구조와 출력 형식만 준비되어 있습니다.",
                        "실데이터 연결 후 뉴스 · 공시 · 리포트 · 글로벌 피어가 채워집니다.",
                    ]
                )

            if "theme_result" in st.session_state:
                result = st.session_state["theme_result"]
                st.download_button(
                    "TXT 다운로드",
                    data=result["text"],
                    file_name=f"theme_{result['payload']['theme_name']}.txt",
                    mime="text/plain",
                    use_container_width=False,
                )

    with out_col:
        result_text = st.session_state.get("theme_result", {}).get("text", "")
        _render_output_box(result_text, "테마명을 입력하고 생성 버튼을 누르면 여기에 결과가 나타납니다.")


def _render_output_box(result_text: str, placeholder: str) -> None:
    has_result = bool(result_text)
    escaped_text = escape(result_text) if has_result else ""
    escaped_placeholder = escape(placeholder)
    button_state = "" if has_result else "disabled"
    button_style = (
        "opacity:1;cursor:pointer;"
        if has_result
        else "opacity:0.42;cursor:default;"
    )
    content_html = (
        f"""<pre id="output-text" style="margin:0; padding:12px 14px 14px 14px; height:360px; overflow:auto; white-space:pre-wrap; word-break:break-word; font:11.5px/1.55 'SF Mono','Fira Code','Cascadia Code',ui-monospace,monospace; color:#303743; background:#faf7f1;">{escaped_text}</pre>"""
        if has_result
        else f"""<div id="output-text" style="height:360px; padding:12px 14px 14px 14px; display:flex; align-items:center; justify-content:center; text-align:center; font:12px/1.6 Inter,-apple-system,BlinkMacSystemFont,system-ui,sans-serif; color:#6f7683; background:#faf7f1;">{escaped_placeholder}</div>"""
    )
    html = f"""
    <div style="border:1px solid rgba(17,19,24,0.14); border-radius:12px; background:#faf7f1; overflow:hidden;">
      <div style="display:flex; justify-content:flex-end; align-items:center; padding:10px 12px 0 12px;">
        <button
          id="copy-btn"
          style="
            min-height:32px;
            padding:0 14px;
            border-radius:999px;
            border:1px solid rgba(0,102,204,0.22);
            background:#ffffff;
            color:#0066cc;
            font-size:12px;
            font-weight:500;
            letter-spacing:-0.01em;
            {button_style}
          "
          {button_state}
          onclick="copyOutput()"
        >
          복사
        </button>
      </div>
      {content_html}
    </div>
    <script>
      async function copyOutput() {{
        const button = document.getElementById('copy-btn');
        if (button.disabled) {{
          return;
        }}
        const text = document.getElementById('output-text').innerText;
        try {{
          await navigator.clipboard.writeText(text);
          const original = button.innerText;
          button.innerText = '복사됨';
          button.style.background = '#0066cc';
          button.style.color = '#ffffff';
          button.style.borderColor = '#0066cc';
          setTimeout(() => {{
            button.innerText = original;
            button.style.background = '#ffffff';
            button.style.color = '#0066cc';
            button.style.borderColor = 'rgba(0,102,204,0.22)';
          }}, 1200);
        }} catch (e) {{
          button.innerText = '실패';
          setTimeout(() => {{ button.innerText = '복사'; }}, 1200);
        }}
      }}
    </script>
    """
    components.html(html, height=420)


def _compact_date(date_text: str) -> str:
    return date_text.replace("-", "")

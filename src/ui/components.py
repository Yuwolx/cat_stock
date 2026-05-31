from __future__ import annotations

import base64
from html import escape
from pathlib import Path

import streamlit as st


def _load_logo_b64() -> str:
    img_path = Path(__file__).parent.parent.parent / "cat_stock_image.png"
    if img_path.exists():
        return base64.b64encode(img_path.read_bytes()).decode()
    return ""


_LOGO_B64 = _load_logo_b64()


def inject_app_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Manrope:wght@600;700;800&display=swap');

        :root {
          --bg: #faf7f1;
          --bg-soft: #f3efe7;
          --surface: rgba(255, 255, 255, 0.55);
          --ink: #111318;
          --ink-soft: #303743;
          --muted: #6f7683;
          --line: rgba(17, 19, 24, 0.09);
          --line-strong: rgba(17, 19, 24, 0.14);
          --blue: #8b97e8;
          --blue-soft: rgba(139, 151, 232, 0.12);
          --green-soft: rgba(93, 177, 128, 0.12);
          --amber-soft: rgba(220, 149, 67, 0.14);
        }

        html, body, [class*="css"], [data-testid="stAppViewContainer"] {
          font-family: Inter, -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
        }

        [data-testid="stAppViewContainer"] {
          background:
            radial-gradient(circle at top left, rgba(139, 151, 232, 0.10), transparent 26%),
            linear-gradient(180deg, #fdfbf7 0%, var(--bg) 100%);
          color: var(--ink);
        }

        [data-testid="stHeader"],
        [data-testid="stToolbar"],
        #MainMenu,
        footer {
          display: none !important;
        }

        [data-testid="stSidebar"] {
          display: none !important;
        }

        .block-container {
          max-width: 1520px;
          padding-top: 22px;
          padding-bottom: 56px;
          padding-left: 22px;
          padding-right: 22px;
        }

        .cat-shell {
          margin-bottom: 14px;
        }

        .cat-shell__eyebrow {
          margin: 0 0 10px;
          color: var(--muted);
          font-size: 10px;
          font-weight: 700;
          letter-spacing: 0.10em;
          text-transform: uppercase;
        }

        .cat-shell__title {
          margin: 0;
          color: var(--ink);
          font-family: Manrope, Inter, sans-serif;
          font-size: clamp(26px, 2.8vw, 38px);
          line-height: 1.04;
          font-weight: 800;
          letter-spacing: -0.05em;
          word-break: keep-all;
          overflow-wrap: break-word;
        }

        .cat-shell__sub {
          margin: 6px 0 0;
          color: var(--muted);
          font-size: 13px;
          line-height: 1.5;
          font-weight: 400;
          letter-spacing: -0.01em;
          max-width: 660px;
          word-break: keep-all;
        }

        /* ── Streamlit 컴포넌트 간 기본 간격 압축 ── */
        .block-container > [data-testid="stVerticalBlock"] {
          gap: 4px !important;
        }

        [data-baseweb="tab-list"] {
          display: flex !important;
          flex-direction: row !important;
          flex-wrap: nowrap !important;
          align-items: flex-end !important;
          gap: 28px !important;
          margin-top: 2px !important;
          margin-bottom: 10px !important;
          border-bottom: 1px solid var(--line) !important;
          padding-bottom: 0 !important;
        }

        [data-baseweb="tab-border"] {
          display: none !important;
        }

        [data-baseweb="tab"] {
          min-height: 30px !important;
          padding: 0 0 8px !important;
          border: 0 !important;
          border-radius: 0 !important;
          background: transparent !important;
          color: rgba(17, 19, 24, 0.38) !important;
          font-size: 13px !important;
          font-weight: 600 !important;
          letter-spacing: -0.01em !important;
          box-shadow: none !important;
          white-space: nowrap !important;
        }

        [aria-selected="true"] {
          color: var(--ink) !important;
        }

        [data-baseweb="tab-highlight"] {
          background: var(--blue) !important;
          height: 2px !important;
          border-radius: 999px !important;
        }

        .cat-section {
          margin: 0 0 10px;
        }

        .cat-section__eyebrow {
          margin: 0 0 8px;
          color: var(--muted);
          font-size: 11px;
          font-weight: 700;
          letter-spacing: 0.08em;
          text-transform: uppercase;
        }

        .cat-section__title {
          margin: 0;
          color: var(--ink);
          font-family: Manrope, Inter, sans-serif;
          font-size: clamp(17px, 1.8vw, 22px);
          line-height: 1.08;
          font-weight: 800;
          letter-spacing: -0.04em;
          word-break: keep-all;
          overflow-wrap: break-word;
        }

        .cat-section__copy {
          margin: 6px 0 0;
          max-width: 680px;
          color: var(--muted);
          font-size: 12px;
          line-height: 1.5;
          letter-spacing: -0.01em;
          word-break: keep-all;
        }

        div[data-testid="stVerticalBlockBorderWrapper"] {
          border: 0 !important;
          border-radius: 0 !important;
          background: transparent !important;
          box-shadow: none !important;
          padding: 0 !important;
        }

        /* 컬럼 내부 상단 여백 제거 */
        [data-testid="column"],
        [data-testid="column"] > div,
        [data-testid="column"] > [data-testid="stVerticalBlock"] {
          padding-top: 0 !important;
          margin-top: 0 !important;
        }

        [data-testid="column"] > [data-testid="stVerticalBlock"] > div:first-child {
          margin-top: 0 !important;
          padding-top: 0 !important;
        }

        .cat-list {
          list-style: none;
          margin: 14px 0 0;
          padding: 0;
        }

        .cat-list li {
          display: flex;
          align-items: baseline;
          gap: 10px;
          padding: 9px 0;
          border-top: 1px solid var(--line);
          color: var(--ink-soft);
          font-size: 12px;
          line-height: 1.5;
          letter-spacing: -0.01em;
          word-break: keep-all;
        }

        .cat-list li::before {
          content: "—";
          flex-shrink: 0;
          color: var(--line-strong);
          font-size: 12px;
        }

        .cat-note {
          margin: 0 0 22px;
          padding: 0 0 0 14px;
          border-left: 2px solid transparent;
          font-size: 12px;
          line-height: 1.5;
          letter-spacing: -0.01em;
        }

        .cat-note--warn {
          border-left-color: #d79046;
          color: #8a5a1f;
        }

        .cat-note--info {
          border-left-color: #6f8fe2;
          color: #405387;
        }

        [data-testid="stWidgetLabel"] p,
        .stDateInput label p,
        .stTextInput label p,
        .stTextArea label p,
        .stCheckbox label p {
          color: var(--ink) !important;
          font-size: 11px !important;
          font-weight: 700 !important;
          letter-spacing: -0.01em !important;
        }

        /* 날짜 / 텍스트 단행 입력 — 밑줄 스타일 */
        .stDateInput [data-baseweb="input"],
        .stTextInput [data-baseweb="input"] {
          border-radius: 0 !important;
          border: 0 !important;
          border-bottom: 1px solid var(--line-strong) !important;
          background: transparent !important;
          box-shadow: none !important;
          padding-left: 0 !important;
          padding-right: 0 !important;
        }

        .stDateInput [data-baseweb="input"] > div,
        .stTextInput [data-baseweb="input"] > div {
          background: transparent !important;
        }

        .stDateInput input,
        .stTextInput input {
          background: transparent !important;
          color: var(--ink) !important;
          font-size: 13px !important;
          line-height: 1.4 !important;
          letter-spacing: -0.01em !important;
          padding-left: 0 !important;
          padding-right: 0 !important;
          caret-color: var(--blue) !important;
        }

        .stDateInput input,
        .stDateInput [data-baseweb="input"] {
          cursor: pointer !important;
        }

        .stTextInput [data-baseweb="input"] {
          transition: border-bottom-color 180ms ease !important;
        }

        .stTextInput [data-baseweb="input"]:focus-within {
          border-bottom-color: var(--blue) !important;
          border-bottom-width: 1.5px !important;
        }

        .stDateInput input::placeholder,
        .stTextInput input::placeholder {
          color: #b0b8c1 !important;
          opacity: 1 !important;
          transition: opacity 120ms ease !important;
        }

        .stTextInput input:focus::placeholder {
          opacity: 0 !important;
        }

        /* 달력 아이콘 */
        .stDateInput [data-baseweb="input"] {
          position: relative;
        }

        .stDateInput [data-baseweb="input"]::after {
          content: "📅";
          position: absolute;
          right: 2px;
          top: 50%;
          transform: translateY(-50%);
          font-size: 13px;
          pointer-events: none;
          opacity: 0.55;
        }

        .stButton > button,
        .stDownloadButton > button {
          min-height: 34px;
          padding: 0 14px;
          font-size: 12px;
          font-weight: 500;
          letter-spacing: -0.01em;
          box-shadow: none !important;
          transition: transform 120ms ease, opacity 120ms ease, border-color 120ms ease, background-color 120ms ease, color 120ms ease;
        }

        .stButton > button {
          background: linear-gradient(135deg, #6f8cf1 0%, #7c72e8 100%) !important;
          color: #ffffff !important;
          border: 0 !important;
          border-radius: 14px !important;
        }

        .stDownloadButton > button {
          background: transparent !important;
          color: #0066cc !important;
          border: 1px solid rgba(0, 102, 204, 0.34) !important;
          border-radius: 12px !important;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover {
          transform: translateY(-1px);
          opacity: 1;
        }

        .stButton > button:hover {
          background: linear-gradient(135deg, #6785ee 0%, #7669e2 100%) !important;
        }

        .stDownloadButton > button:hover {
          background: rgba(0, 102, 204, 0.06) !important;
          border-color: rgba(0, 102, 204, 0.48) !important;
          color: #0071e3 !important;
        }

        .stCaption p {
          color: var(--muted) !important;
          font-size: 11px !important;
        }

        /* 출력 텍스트 박스 */
        .stTextArea textarea {
          font: 11.5px/1.55 'SF Mono','Fira Code','Cascadia Code',ui-monospace,monospace !important;
          color: #303743 !important;
          background: #faf7f1 !important;
          border: 1px solid rgba(17,19,24,0.14) !important;
          border-radius: 12px !important;
          resize: none !important;
          box-shadow: none !important;
        }
        .stTextArea textarea:focus {
          box-shadow: none !important;
          border-color: rgba(17,19,24,0.14) !important;
        }
        .stTextArea [data-baseweb="textarea"] {
          background: transparent !important;
          border: none !important;
        }

        /* 결과 없을 때 플레이스홀더 */
        .output-placeholder {
          height: 420px;
          border: 1px solid rgba(17,19,24,0.14);
          border-radius: 12px;
          background: #faf7f1;
          display: flex;
          align-items: center;
          justify-content: center;
          text-align: center;
          color: #6f7683;
          font-size: 12px;
          line-height: 1.6;
        }

        details {
          background: transparent !important;
          border: 0 !important;
          border-top: 1px solid var(--line) !important;
          border-radius: 0 !important;
          padding: 0 !important;
        }

        details summary {
          font-size: 12px !important;
          font-weight: 600 !important;
          color: var(--muted) !important;
          letter-spacing: -0.01em !important;
          padding: 10px 0 !important;
          cursor: pointer;
        }

        details[open] summary {
          color: var(--ink) !important;
        }

        @media (max-width: 833px) {
          .block-container {
            padding-left: 18px;
            padding-right: 18px;
          }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_shell(title: str, sub: str = "") -> None:
    title_html = "<br>".join(escape(line) for line in title.splitlines())
    sub_html = f'<p class="cat-shell__sub">{escape(sub)}</p>' if sub else ""
    st.markdown(
        f"""
        <section class="cat-shell">
          <p class="cat-shell__eyebrow">
            {f'<img src="data:image/png;base64,{_LOGO_B64}" style="width:18px;height:18px;object-fit:contain;vertical-align:middle;margin-right:6px;border-radius:4px;">' if _LOGO_B64 else ""}
            CAT STOCK
          </p>
          <h1 class="cat-shell__title">{title_html}</h1>
          {sub_html}
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_shell_with_toggle(mode: str) -> None:
    """eyebrow 자체가 STOCK ↔ COIN 토글 버튼인 shell 헤더.

    st.button key에 Streamlit이 자동으로 붙여주는 .st-key-{key} 클래스를
    이용해 이 버튼만 eyebrow 텍스트처럼 스타일링한다.
    """
    service_label = "CAT STOCK" if mode == "stock" else "CAT COIN"
    title = (
        "주식 데이터를 정리해드립니다."
        if mode == "stock"
        else "코인 데이터를 정리해드립니다."
    )
    sub = (
        "시황 브리핑, 개별 종목 분석, 테마 공부 자료를 만들고 바로 복사할 수 있습니다."
        if mode == "stock"
        else "코인 시황, 개별 코인 분석, 섹터 공부 자료를 만들고 바로 복사할 수 있습니다."
    )

    logo_before = ""
    if _LOGO_B64:
        logo_before = f"""
        .st-key-mode_logo_toggle button::before {{
            content: "";
            display: inline-block;
            width: 32px;
            height: 32px;
            background-image: url("data:image/png;base64,{_LOGO_B64}");
            background-size: contain;
            background-repeat: no-repeat;
            vertical-align: middle;
            margin-right: 8px;
            border-radius: 6px;
        }}
        """

    st.markdown(
        f"""
        <style>
        /* ── mode logo toggle ── */
        .st-key-mode_logo_toggle {{
            margin-bottom: 0 !important;
        }}
        .st-key-mode_logo_toggle button {{
            background: transparent !important;
            background-image: none !important;
            border: 0 !important;
            border-radius: 0 !important;
            box-shadow: none !important;
            padding: 0 !important;
            min-height: 0 !important;
            height: auto !important;
            color: var(--muted, #6f7683) !important;
            font-size: 14px !important;
            font-weight: 800 !important;
            letter-spacing: -0.02em !important;
            cursor: pointer !important;
            transition: color 120ms ease !important;
            font-family: Manrope, Inter, -apple-system, BlinkMacSystemFont, system-ui, sans-serif !important;
            transform: none !important;
            line-height: 1 !important;
        }}
        .st-key-mode_logo_toggle button p {{
            font-size: 14px !important;
            font-weight: 800 !important;
            letter-spacing: -0.02em !important;
            color: inherit !important;
            margin: 0 !important;
        }}
        .st-key-mode_logo_toggle button:hover {{
            color: var(--ink, #111318) !important;
            background: transparent !important;
            background-image: none !important;
            box-shadow: none !important;
            transform: none !important;
            opacity: 1 !important;
        }}
        .st-key-mode_logo_toggle button:active {{
            transform: none !important;
            box-shadow: none !important;
        }}
        {logo_before}
        </style>
        """,
        unsafe_allow_html=True,
    )

    if st.button(service_label, key="mode_logo_toggle"):
        st.session_state["mode"] = "coin" if mode == "stock" else "stock"
        st.rerun()

    title_html = "<br>".join(escape(line) for line in title.splitlines())
    sub_html = f'<p class="cat-shell__sub">{escape(sub)}</p>' if sub else ""
    st.markdown(
        f"""
        <div class="cat-shell" style="margin-top: -18px;">
          <h1 class="cat-shell__title">{title_html}</h1>
          {sub_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_page_intro(eyebrow: str, title: str, copy: str = "") -> None:
    copy_html = f'<p class="cat-section__copy">{escape(copy)}</p>' if copy else ""
    st.markdown(
        f"""
        <section class="cat-section">
          <p class="cat-section__eyebrow">{escape(eyebrow)}</p>
          <h2 class="cat-section__title">{escape(title)}</h2>
          {copy_html}
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_list(items: list[str]) -> None:
    list_html = "".join(f"<li>{escape(item)}</li>" for item in items)
    st.markdown(f'<ul class="cat-list">{list_html}</ul>', unsafe_allow_html=True)


def render_note(message: str, tone: str = "info") -> None:
    cls = "cat-note--warn" if tone == "warn" else "cat-note--info"
    st.markdown(f'<div class="cat-note {cls}">{escape(message)}</div>', unsafe_allow_html=True)

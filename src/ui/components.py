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
          max-width: 1440px;
          padding-top: 36px;
          padding-bottom: 84px;
          padding-left: 28px;
          padding-right: 28px;
        }

        .cat-shell {
          margin-bottom: 22px;
        }

        .cat-shell__eyebrow {
          margin: 0 0 10px;
          color: var(--muted);
          font-size: 11px;
          font-weight: 700;
          letter-spacing: 0.10em;
          text-transform: uppercase;
        }

        .cat-shell__title {
          margin: 0;
          color: var(--ink);
          font-family: Manrope, Inter, sans-serif;
          font-size: clamp(34px, 3.8vw, 52px);
          line-height: 1.04;
          font-weight: 800;
          letter-spacing: -0.05em;
          word-break: keep-all;
          overflow-wrap: break-word;
        }

        .cat-shell__sub {
          margin: 12px 0 0;
          color: var(--muted);
          font-size: 16px;
          line-height: 1.62;
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
          gap: 20px !important;
          margin-top: 6px !important;
          margin-bottom: 14px !important;
          border-bottom: 1px solid var(--line) !important;
          padding-bottom: 0 !important;
        }

        [data-baseweb="tab"] {
          min-height: 36px !important;
          padding: 0 0 8px !important;
          border: 0 !important;
          border-radius: 0 !important;
          background: transparent !important;
          color: rgba(17, 19, 24, 0.38) !important;
          font-size: 14px !important;
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
          margin: 0 0 16px;
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
          font-size: clamp(22px, 2.4vw, 30px);
          line-height: 1.08;
          font-weight: 800;
          letter-spacing: -0.04em;
          word-break: keep-all;
          overflow-wrap: break-word;
        }

        .cat-section__copy {
          margin: 10px 0 0;
          max-width: 680px;
          color: var(--muted);
          font-size: 15px;
          line-height: 1.62;
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

        .cat-card-header__eyebrow {
          margin-bottom: 8px;
          color: var(--muted);
          font-size: 11px;
          font-weight: 700;
          letter-spacing: 0.08em;
          text-transform: uppercase;
        }

        .cat-card-header__title {
          margin: 0 0 8px;
          color: var(--ink);
          font-family: Manrope, Inter, sans-serif;
          font-size: clamp(20px, 2vw, 25px);
          line-height: 1.14;
          font-weight: 800;
          letter-spacing: -0.04em;
          word-break: keep-all;
          overflow-wrap: break-word;
        }

        .cat-card-header__copy {
          margin: 0 0 16px;
          color: var(--muted);
          font-size: 13px;
          line-height: 1.58;
          letter-spacing: -0.01em;
          word-break: keep-all;
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
          padding: 11px 0;
          border-top: 1px solid var(--line);
          color: var(--ink-soft);
          font-size: 13.5px;
          line-height: 1.56;
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
          font-size: 13px;
          line-height: 1.56;
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

        .cat-output {
          margin-top: 38px;
          padding-top: 22px;
          border-top: 1px solid var(--line);
        }

        .cat-output__header {
          display: flex;
          align-items: baseline;
          justify-content: space-between;
          gap: 16px;
          margin-bottom: 14px;
          flex-wrap: wrap;
        }

        .cat-output__eyebrow {
          color: var(--muted);
          font-size: 11px;
          font-weight: 700;
          letter-spacing: 0.08em;
          text-transform: uppercase;
        }

        .cat-output__title {
          margin: 0;
          color: var(--ink);
          font-family: Manrope, Inter, sans-serif;
          font-size: clamp(20px, 2vw, 26px);
          line-height: 1.1;
          font-weight: 800;
          letter-spacing: -0.04em;
          word-break: keep-all;
        }

        [data-testid="stWidgetLabel"] p,
        .stDateInput label p,
        .stTextInput label p,
        .stTextArea label p,
        .stCheckbox label p {
          color: var(--ink) !important;
          font-size: 12px !important;
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
          font-size: 15px !important;
          line-height: 1.55 !important;
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

        /* 출력 텍스트에어리어 — 디자인 통일 박스 */
        [data-testid="stTextArea"] [data-baseweb="textarea"] {
          border-radius: 12px !important;
          border: 1px solid var(--line-strong) !important;
          background-color: #faf7f1 !important;
          box-shadow: none !important;
          overflow: hidden !important;
        }

        [data-testid="stTextArea"] [data-baseweb="textarea"] > div {
          background-color: #faf7f1 !important;
        }

        [data-testid="stTextArea"] textarea {
          background-color: #faf7f1 !important;
          color: var(--ink-soft) !important;
          padding: 18px !important;
          font-size: 13px !important;
          line-height: 1.7 !important;
        }

        [data-testid="stTextArea"] textarea::placeholder {
          color: var(--muted) !important;
          opacity: 0.7 !important;
          font-size: 13px !important;
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
          min-height: 44px;
          border-radius: 999px;
          padding: 0 18px;
          font-size: 14px;
          font-weight: 600;
          letter-spacing: -0.01em;
          transition: transform 120ms ease, opacity 120ms ease;
        }

        .stButton > button {
          background: var(--blue) !important;
          color: #ffffff !important;
          border: 1px solid rgba(139, 151, 232, 0.76) !important;
        }

        .stDownloadButton > button {
          background: transparent !important;
          color: var(--blue) !important;
          border: 1px solid rgba(139, 151, 232, 0.34) !important;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover {
          transform: scale(0.985);
          opacity: 0.94;
        }

        .stTextArea textarea {
          font-family: "SF Mono", "Fira Code", "Cascadia Code", ui-monospace, monospace !important;
          font-size: 12.5px !important;
          line-height: 1.7 !important;
        }

        .stCaption p {
          color: var(--muted) !important;
          font-size: 11px !important;
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

          .cat-block--with-line {
            padding-left: 0;
            border-left: 0;
            padding-top: 24px;
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


def render_status_strip(has_dart_key: bool, output_dir: Path) -> None:
    dart_color = "#3da968" if has_dart_key else "#cf7c28"
    dart_label = "연결됨" if has_dart_key else "미연결"
    dot = "width:6px;height:6px;border-radius:50%;display:inline-block;margin-right:6px;flex-shrink:0;"
    item = "display:inline-flex;align-items:center;font-size:12px;color:#6f7683;white-space:nowrap;letter-spacing:-0.01em;"
    label = "font-weight:600;color:#111318;margin-right:4px;"
    st.markdown(
        f"""
        <div style="display:flex;flex-direction:row;flex-wrap:nowrap;align-items:center;gap:18px;margin:8px 0 6px;">
          <span style="{item}"><span style="{dot}background:{dart_color};"></span><span style="{label}">DART</span>{dart_label}</span>
          <span style="{item}"><span style="{dot}background:#8b97e8;"></span><span style="{label}">출력</span>{escape(output_dir.name)}</span>
          <span style="{item}"><span style="{dot}background:#8b97e8;"></span>복사용 텍스트 생성</span>
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


def render_block_open(with_line: bool = False) -> None:
    class_name = "cat-block cat-block--with-line" if with_line else "cat-block"
    st.markdown(f'<div class="{class_name}">', unsafe_allow_html=True)


def render_block_close() -> None:
    st.markdown("</div>", unsafe_allow_html=True)


def render_card_header(eyebrow: str, title: str, copy: str) -> None:
    st.markdown(
        f"""
        <div class="cat-card-header__eyebrow">{escape(eyebrow)}</div>
        <div class="cat-card-header__title">{escape(title)}</div>
        <div class="cat-card-header__copy">{escape(copy)}</div>
        """,
        unsafe_allow_html=True,
    )


def render_list(items: list[str]) -> None:
    list_html = "".join(f"<li>{escape(item)}</li>" for item in items)
    st.markdown(f'<ul class="cat-list">{list_html}</ul>', unsafe_allow_html=True)


def render_note(message: str, tone: str = "info") -> None:
    cls = "cat-note--warn" if tone == "warn" else "cat-note--info"
    st.markdown(f'<div class="cat-note {cls}">{escape(message)}</div>', unsafe_allow_html=True)


def render_output_panel(result_text: str, download_name: str, saved_path: Path) -> None:
    st.markdown(
        """
        <section class="cat-output">
          <div class="cat-output__header">
            <span class="cat-output__eyebrow">Generated Output</span>
            <h2 class="cat-output__title">결과 텍스트</h2>
          </div>
        """,
        unsafe_allow_html=True,
    )
    st.text_area("output", result_text, height=520, label_visibility="collapsed")
    button_col, caption_col = st.columns([0.22, 0.78])
    with button_col:
        st.download_button(
            "TXT 다운로드",
            data=result_text,
            file_name=download_name,
            mime="text/plain",
            use_container_width=True,
        )
    with caption_col:
        st.caption(f"저장: {saved_path}")
    st.markdown("</section>", unsafe_allow_html=True)

from __future__ import annotations

import base64
from datetime import datetime
from html import escape
from pathlib import Path

import streamlit as st

from src.utils.date_utils import KST, WEEKDAY_KO


def _load_logo_b64() -> str:
    img_path = Path(__file__).parent.parent.parent / "cat_stock_image.png"
    if img_path.exists():
        return base64.b64encode(img_path.read_bytes()).decode()
    return ""


_LOGO_B64 = _load_logo_b64()


def inject_app_styles() -> None:
    if _LOGO_B64:
        st.markdown(
            f"""<script>
            (function() {{
                var link = document.querySelector("link[rel*='icon']");
                if (!link) {{ link = document.createElement('link'); document.head.appendChild(link); }}
                link.type = 'image/png';
                link.rel = 'shortcut icon';
                link.href = 'data:image/png;base64,{_LOGO_B64}';
            }})();
            </script>""",
            unsafe_allow_html=True,
        )
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Manrope:wght@600;700;800&display=swap');

        :root {
          --bg: #f2f0eb;
          --bg-soft: #edebe9;
          --surface: #ffffff;
          --ink: #212b26;
          --ink-soft: #3c4a45;
          --muted: #77776f;
          --line: #dfdcd4;
          --line-strong: #cfccc2;
          --green: #006241;
          --house: #1e3932;
          --gold: #cba258;
          --blue: #006241; /* 구 악센트 참조 호환 */
          --blue-soft: rgba(0, 98, 65, 0.10);
          --green-soft: rgba(0, 98, 65, 0.10);
          --amber-soft: rgba(203, 162, 88, 0.16);
        }

        html, body, [class*="css"], [data-testid="stAppViewContainer"] {
          font-family: Inter, -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
        }

        [data-testid="stAppViewContainer"] {
          background: var(--bg);
          color: var(--ink);
        }

        [data-testid="stHeader"],
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        [data-testid="stStatusWidget"],
        .stAppDeployButton,
        #MainMenu,
        footer {
          display: none !important;
        }

        [data-testid="stSidebar"] {
          display: none !important;
        }

        iframe[title="st.iframe"],
        iframe.stIFrame {
          background: transparent !important;
          color-scheme: light !important;
        }

        [data-testid="stElementContainer"]:has(> iframe[title="st.iframe"]) {
          background: transparent !important;
        }

        .block-container {
          max-width: 1520px;
          padding-top: 0;
          padding-bottom: 56px;
          padding-left: 22px;
          padding-right: 22px;
        }

        .cat-shell {
          margin-bottom: 14px;
        }

        /* 스타일/스크립트 주입 전용 markdown 요소가 차지하는 공간 제거 */
        [data-testid="stElementContainer"]:has([data-testid="stMarkdownContainer"] > style:first-child:last-child),
        [data-testid="stElementContainer"]:has([data-testid="stMarkdownContainer"] > script:first-child:last-child) {
          display: none !important;
        }

        /* ── 하우스 그린 헤더 밴드 (풀블리드) ── */
        .st-key-mode_logo_toggle {
          background: var(--house);
          width: 100vw !important;
          max-width: none !important;
          margin-left: calc(50% - 50vw) !important;
          padding: 20px calc(50vw - 50%) 0 !important;
          box-shadow: 0 26px 0 var(--house); /* 요소 사이 flex gap을 같은 색으로 메움 */
        }

        .cat-shell--band {
          background: var(--house);
          width: 100vw;
          margin-left: calc(50% - 50vw);
          padding: 4px calc(50vw - 50%) 24px;
          border-bottom: 1px solid rgba(203, 162, 88, 0.55);
          margin-bottom: 16px;
        }

        .cat-shell--band .cat-shell__title {
          color: #fdfcf9;
          font-size: clamp(21px, 2.2vw, 27px);
          font-weight: 700;
          letter-spacing: -0.015em;
        }

        .cat-shell--band .cat-shell__sub {
          color: rgba(255, 255, 255, 0.62);
          letter-spacing: 0.01em;
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
          background: var(--green) !important;
          height: 2px !important;
          border-radius: 0 !important;
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
          caret-color: var(--green) !important;
        }

        .stDateInput input,
        .stDateInput [data-baseweb="input"] {
          cursor: pointer !important;
        }

        .stTextInput [data-baseweb="input"] {
          transition: border-bottom-color 180ms ease !important;
        }

        .stTextInput [data-baseweb="input"]:focus-within {
          border-bottom-color: var(--green) !important;
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
          background: transparent !important;
          color: var(--house) !important;
          border: 1px solid var(--house) !important;
          border-radius: 3px !important;
          letter-spacing: 0.04em !important;
          font-weight: 600 !important;
        }

        .stButton > button[data-testid="stBaseButton-primary"],
        .stButton > button[kind="primary"] {
          background: var(--green) !important;
          color: #ffffff !important;
          border: 1px solid var(--green) !important;
          font-weight: 700 !important;
        }

        .stDownloadButton > button {
          background: transparent !important;
          color: var(--house) !important;
          border: 1px solid var(--house) !important;
          border-radius: 3px !important;
          letter-spacing: 0.04em !important;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover {
          transform: none;
          opacity: 1;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover {
          background: var(--bg-soft) !important;
          color: var(--house) !important;
        }

        .stButton > button[data-testid="stBaseButton-primary"]:hover,
        .stButton > button[kind="primary"]:hover {
          background: var(--house) !important;
          border-color: var(--house) !important;
          color: #ffffff !important;
        }

        .stCaption p {
          color: var(--muted) !important;
          font-size: 11px !important;
        }

        /* 출력 텍스트 박스 */
        .stTextArea textarea {
          font: 11.5px/1.55 'SF Mono','Fira Code','Cascadia Code',ui-monospace,monospace !important;
          color: var(--ink-soft) !important;
          background: #ffffff !important;
          border: 1px solid var(--line) !important;
          border-radius: 4px !important;
          resize: none !important;
          box-shadow: none !important;
        }
        .stTextArea textarea:focus {
          box-shadow: none !important;
          border-color: var(--line) !important;
        }
        .stTextArea [data-baseweb="textarea"] {
          background: transparent !important;
          border: none !important;
        }

        /* 결과 없을 때 플레이스홀더 */
        .output-placeholder {
          height: 420px;
          border: 1px solid var(--line);
          border-radius: 4px;
          background: #ffffff;
          display: flex;
          align-items: center;
          justify-content: center;
          text-align: center;
          color: var(--muted);
          font-size: 12px;
          line-height: 1.6;
        }

        /* ── 출력 박스: 보고 있는 화면 높이에 맞춤 ── */
        .cat-output-shell {
          box-sizing: border-box;
          display: flex;
          flex-direction: column;
          width: 100%;
          height: clamp(320px, calc(100dvh - 400px), 860px);
          min-width: 0;
          overflow: hidden;
          border: 1px solid var(--line);
          border-radius: 4px;
          background: #ffffff;
        }

        /* 출력 헤더 바 */
        .cat-output-header {
          box-sizing: border-box;
          flex: 0 0 44px;
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 0 16px;
          background: #ffffff;
          border-bottom: 1px solid var(--line);
          border-radius: 4px 4px 0 0;
        }

        .cat-output-label {
          flex: 1;
          display: flex;
          align-items: center;
          gap: 10px;
          color: var(--muted);
          font: 600 9.5px/1 "SF Mono", "Cascadia Code", ui-monospace, monospace;
          letter-spacing: 0.14em;
          text-transform: uppercase;
        }

        .cat-output-label::before {
          content: "";
          display: inline-block;
          width: 22px;
          height: 1px;
          background: var(--gold);
          flex-shrink: 0;
        }

        .cat-copy-button {
          flex-shrink: 0;
          min-height: 28px;
          padding: 0 15px;
          border: 1px solid var(--house);
          border-radius: 3px;
          background: var(--house);
          color: #ffffff;
          font: 600 11px/1 -apple-system, BlinkMacSystemFont, "Inter", system-ui, sans-serif;
          letter-spacing: 0.05em;
          cursor: pointer;
          transition: background-color 140ms ease, border-color 140ms ease, color 140ms ease, opacity 140ms ease;
        }

        .cat-copy-button:hover:not(:disabled) {
          background: var(--green);
          border-color: var(--green);
          color: #ffffff;
        }

        .cat-copy-button:disabled {
          opacity: 0.28;
          cursor: default;
        }

        .cat-copy-button.is-copied {
          background: rgba(0, 98, 65, 0.10);
          border-color: var(--green);
          color: var(--green);
        }

        .cat-copy-button.is-failed {
          background: transparent;
          border-color: rgba(179, 38, 30, 0.5);
          color: #b3261e;
        }

        /* 출력 콘텐츠 영역 */
        .cat-output-body {
          box-sizing: border-box;
          flex: 1 1 auto;
          min-height: 0;
          overflow: hidden;
          display: flex;
          flex-direction: column;
          background: #ffffff;
        }

        .cat-output-pre,
        .cat-output-placeholder {
          box-sizing: border-box;
          flex: 1 1 auto;
          min-height: 0;
          height: auto;
          margin: 0;
          padding: 14px 16px 18px;
          overflow: auto;
          white-space: pre-wrap;
          word-break: keep-all;
          overflow-wrap: anywhere;
          color: var(--ink-soft);
          background: #ffffff;
        }

        .cat-output-pre {
          font: 12px/1.62 "SF Mono", "Cascadia Code", ui-monospace, monospace;
        }

        .cat-output-pre::-webkit-scrollbar,
        .cat-output-placeholder::-webkit-scrollbar {
          width: 5px;
        }

        .cat-output-pre::-webkit-scrollbar-thumb,
        .cat-output-placeholder::-webkit-scrollbar-thumb {
          background: var(--line);
        }

        .cat-output-placeholder {
          display: flex;
          align-items: center;
          justify-content: center;
          text-align: center;
          color: var(--muted);
          font: 12px/1.6 -apple-system, BlinkMacSystemFont, "Inter", system-ui, sans-serif;
        }

        .cat-output-copy-source {
          position: fixed;
          left: -9999px;
          top: 0;
          width: 1px;
          height: 1px;
          opacity: 0;
          pointer-events: none;
        }

        .newspaper-view-title {
          margin: 8px 0 12px;
          color: var(--ink);
          font-family: Manrope, Inter, sans-serif;
          font-size: clamp(18px, 2vw, 26px);
          font-weight: 800;
          letter-spacing: -0.03em;
        }

        /* 왼쪽 컨트롤 패널 섹션 라벨 */
        .cat-ctrl-section {
          margin: 20px 0 12px;
          padding-top: 16px;
          border-top: 1px solid rgba(17, 19, 24, 0.09);
          font-size: 10px;
          font-weight: 700;
          letter-spacing: 0.08em;
          text-transform: uppercase;
          color: #6f7683;
        }

        .coin-guide {
          margin-top: 2px;
        }

        .coin-guide__hero {
          display: grid;
          grid-template-columns: minmax(0, 1.12fr) minmax(280px, 0.88fr);
          gap: 14px;
          align-items: stretch;
          margin-bottom: 12px;
        }

        .coin-guide__panel,
        .coin-guide-card,
        .coin-guide-step,
        .coin-guide-signal {
          border: 1px solid var(--line);
          border-radius: 8px;
          background: rgba(255, 255, 255, 0.62);
        }

        .coin-guide__panel {
          padding: 18px 18px 16px;
        }

        .coin-guide__eyebrow {
          margin: 0 0 8px;
          color: var(--muted);
          font-size: 10px;
          font-weight: 800;
          letter-spacing: 0;
          text-transform: uppercase;
        }

        .coin-guide__title {
          margin: 0;
          color: var(--ink);
          font-family: Manrope, Inter, sans-serif;
          font-size: clamp(21px, 2.2vw, 30px);
          line-height: 1.12;
          font-weight: 800;
          letter-spacing: 0;
          word-break: keep-all;
        }

        .coin-guide__lead {
          margin: 10px 0 0;
          color: var(--ink-soft);
          font-size: 13px;
          line-height: 1.65;
          letter-spacing: 0;
          word-break: keep-all;
        }

        .coin-guide__rules {
          display: grid;
          gap: 8px;
          height: 100%;
        }

        .coin-guide__rule {
          display: grid;
          grid-template-columns: 74px 1fr;
          gap: 10px;
          align-items: center;
          padding: 12px 14px;
          border: 1px solid var(--line);
          border-radius: 8px;
          background: rgba(255, 255, 255, 0.62);
        }

        .coin-guide__rule strong {
          color: var(--ink);
          font-size: 12px;
          font-weight: 800;
          letter-spacing: 0;
        }

        .coin-guide__rule span {
          color: var(--muted);
          font-size: 12px;
          line-height: 1.5;
          letter-spacing: 0;
          word-break: keep-all;
        }

        .coin-guide__section {
          margin-top: 16px;
        }

        .coin-guide__section-title {
          margin: 0 0 10px;
          color: var(--ink);
          font-size: 13px;
          font-weight: 800;
          letter-spacing: 0;
        }

        .coin-guide__flow {
          display: grid;
          grid-template-columns: repeat(5, minmax(0, 1fr));
          gap: 8px;
        }

        .coin-guide-step {
          min-height: 132px;
          padding: 13px 12px;
        }

        .coin-guide-step__num {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 22px;
          height: 22px;
          margin-bottom: 10px;
          border-radius: 999px;
          background: rgba(139, 151, 232, 0.16);
          color: #5868ce;
          font-size: 11px;
          font-weight: 800;
        }

        .coin-guide-step__title {
          margin: 0 0 6px;
          color: var(--ink);
          font-size: 12px;
          font-weight: 800;
          letter-spacing: 0;
        }

        .coin-guide-step__copy {
          margin: 0;
          color: var(--muted);
          font-size: 11px;
          line-height: 1.48;
          letter-spacing: 0;
          word-break: keep-all;
        }

        .coin-guide__cards {
          display: grid;
          grid-template-columns: repeat(5, minmax(0, 1fr));
          gap: 8px;
        }

        .coin-guide-card {
          min-height: 122px;
          padding: 12px;
        }

        .coin-guide-card__chip {
          display: inline-flex;
          align-items: center;
          height: 20px;
          margin-bottom: 8px;
          padding: 0 8px;
          border-radius: 999px;
          font-size: 10px;
          font-weight: 800;
          letter-spacing: 0;
        }

        .coin-guide-card__chip--core {
          background: rgba(139, 151, 232, 0.16);
          color: #5868ce;
        }

        .coin-guide-card__chip--flow {
          background: rgba(93, 177, 128, 0.14);
          color: #2f7a55;
        }

        .coin-guide-card__chip--risk {
          background: rgba(224, 82, 82, 0.11);
          color: #aa3838;
        }

        .coin-guide-card__chip--learn {
          background: rgba(220, 149, 67, 0.15);
          color: #8a5a1f;
        }

        .coin-guide-card__name {
          margin: 0 0 5px;
          color: var(--ink);
          font-size: 12px;
          font-weight: 800;
          letter-spacing: 0;
        }

        .coin-guide-card__desc {
          margin: 0;
          color: var(--muted);
          font-size: 11px;
          line-height: 1.48;
          letter-spacing: 0;
          word-break: keep-all;
        }

        .coin-guide__signals {
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 8px;
        }

        .coin-guide-signal {
          padding: 13px 14px;
        }

        .coin-guide-signal__label {
          margin: 0 0 6px;
          color: var(--ink);
          font-size: 12px;
          font-weight: 800;
          letter-spacing: 0;
        }

        .coin-guide-signal__text {
          margin: 0;
          color: var(--muted);
          font-size: 11px;
          line-height: 1.5;
          letter-spacing: 0;
          word-break: keep-all;
        }

        .coin-guide__footer {
          margin-top: 12px;
          padding: 11px 14px;
          border-radius: 8px;
          border: 1px solid rgba(220, 149, 67, 0.24);
          background: rgba(220, 149, 67, 0.09);
          color: #755124;
          font-size: 11px;
          line-height: 1.5;
          letter-spacing: 0;
          word-break: keep-all;
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

          .coin-guide__hero,
          .coin-guide__flow,
          .coin-guide__cards,
          .coin-guide__signals {
            grid-template-columns: 1fr;
          }

          .coin-guide-step,
          .coin-guide-card {
            min-height: auto;
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

    now = datetime.now(KST)
    if now.hour < 12:
        greeting = "좋은 아침입니다."
    elif now.hour < 18:
        greeting = "좋은 오후입니다."
    else:
        greeting = "좋은 저녁입니다."
    date_line = f"{now.year}년 {now.month}월 {now.day}일 {WEEKDAY_KO[now.weekday()]}요일"

    title = (
        f"{greeting} 오늘의 데이터를 준비해 두었어요."
        if mode == "stock"
        else "코인 시장을 공부합니다."
    )
    sub = (
        f"{date_line} — 시황 브리핑 · 개별 종목 · 테마 공부를 만들고 바로 복사하세요."
        if mode == "stock"
        else f"{date_line} — 시장 온도, 섹터 흐름, 개별 코인 구조를 대시보드로 공부합니다."
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
            color: rgba(255, 255, 255, 0.9) !important;
            font-size: 13px !important;
            font-weight: 700 !important;
            letter-spacing: 0.2em !important;
            cursor: pointer !important;
            transition: color 120ms ease !important;
            font-family: Inter, -apple-system, BlinkMacSystemFont, system-ui, sans-serif !important;
            transform: none !important;
            line-height: 1 !important;
        }}
        .st-key-mode_logo_toggle button p {{
            font-size: 13px !important;
            font-weight: 700 !important;
            letter-spacing: 0.2em !important;
            color: inherit !important;
            margin: 0 !important;
        }}
        .st-key-mode_logo_toggle button:hover {{
            color: #cba258 !important;
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
        <div class="cat-shell cat-shell--band">
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


def render_ctrl_section(label: str) -> None:
    """왼쪽 컨트롤 패널 내 섹션 구분 라벨"""
    from html import escape as _escape
    st.markdown(
        f'<p class="cat-ctrl-section">{_escape(label)}</p>',
        unsafe_allow_html=True,
    )


def render_note(message: str, tone: str = "info") -> None:
    cls = "cat-note--warn" if tone == "warn" else "cat-note--info"
    st.markdown(f'<div class="cat-note {cls}">{escape(message)}</div>', unsafe_allow_html=True)

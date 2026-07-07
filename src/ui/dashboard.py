from __future__ import annotations

import re
from html import escape

import plotly.graph_objects as go

from src.ui.dashboard_styles import DISPATCH_CSS


# ── 색상 팔레트 (앱과 동일 계열) ──────────────────────────
_BG = "#faf7f1"
_BLUE = "#6f8cf1"
_GREEN = "#4caf83"
_RED = "#e05252"
_AMBER = "#dc9543"
_TEXT = "#111318"
_MUTED = "#6f7683"
_LINE = "rgba(17,19,24,0.09)"

_PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, -apple-system, system-ui, sans-serif", color=_TEXT, size=11),
    margin=dict(l=0, r=0, t=8, b=0),
    showlegend=True,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=10)),
    xaxis=dict(showgrid=False, zeroline=False, color=_MUTED, tickfont=dict(size=10)),
    yaxis=dict(showgrid=True, gridcolor=_LINE, zeroline=False, color=_MUTED, tickfont=dict(size=10)),
)

# ── 헬퍼 ─────────────────────────────────────────────────────

def _sign_class(text: str) -> str:
    t = str(text or "")
    if any(c in t for c in ["+", "상회"]):
        return "up"
    if any(c in t for c in ["-", "하회"]):
        return "dn"
    return ""


def _parse_flow_num(text: str | None) -> float | None:
    if not text:
        return None
    sign = -1 if text.strip().startswith("-") else 1
    cleaned = re.sub(r"[^\d]", "", str(text))
    return sign * int(cleaned) if cleaned else None


def _parse_fin_amount(val: str | None) -> float | None:
    if not val:
        return None
    cleaned = re.sub(r"[^\d]", "", str(val))
    return int(cleaned) / 1_000_000_000_000 if cleaned else None


def _ma_dot(val: str | None) -> str:
    v = str(val or "")
    if "상회" in v:
        return "up"
    if "하회" in v:
        return "dn"
    return "near"


def _opinion_tag(text: str) -> str:
    t = text.upper()
    if any(w in t for w in ["BUY", "매수"]):
        return '<span class="tag tag-buy">BUY</span>'
    if any(w in t for w in ["SELL", "매도"]):
        return '<span class="tag tag-sell">SELL</span>'
    if any(w in t for w in ["HOLD", "중립", "보유"]):
        return '<span class="tag tag-hold">HOLD</span>'
    return ""


def _ticker_item(name: str, value: str, cls: str = "") -> str:
    val_cls = f"t-val {cls}" if cls else "t-val na"
    return f'<div class="ticker-item"><div class="t-name">{escape(name)}</div><div class="{val_cls}">{escape(str(value or "—"))}</div></div>'


def _column_html(column: dict | None, date_str: str) -> str:
    fallback = "OPENAI_API_KEY를 설정하면 AI 분석 칼럼이 여기에 생성됩니다."
    reason_messages = {
        "missing_api_key": "AI 칼럼: OPENAI_API_KEY가 설정되지 않았습니다.",
        "package_missing": "AI 칼럼: openai 패키지가 설치되지 않았습니다.",
        "api_error": "AI 칼럼: 생성 중 오류가 발생했습니다.",
    }
    if not column or not column.get("is_available"):
        message = reason_messages.get((column or {}).get("reason"), fallback)
        return f'<p class="no-col">{escape(message)}</p>'
    title = escape(column.get("title", ""))
    body = escape(column.get("body", ""))
    return f"""<div class="section-tag">MARKET INSIGHT</div>
<h2 class="column-title">{title}</h2>
<div class="byline">CAT STOCK AI Analysis · {escape(date_str)}</div>
<div class="col-body"><p class="column-copy">{body}</p></div>"""


def _date_notice_html(payload: dict) -> str:
    if not payload.get("is_adjusted"):
        return ""
    requested = escape(str(payload.get("requested_date") or ""))
    requested_weekday = escape(str(payload.get("requested_weekday") or ""))
    resolved = escape(str(payload.get("resolved_date") or payload.get("target_date") or ""))
    resolved_weekday = escape(str(payload.get("resolved_weekday") or ""))
    return (
        '<div class="date-notice">'
        f'<span>요청일 {requested} {requested_weekday}요일</span>'
        f'<strong>분석 기준일 {resolved} {resolved_weekday}요일</strong>'
        '<span>주말/휴장일은 최근 거래일 기준</span>'
        '</div>'
    )


def _news_grid3_html(news_items: list[dict], fallback_news: list[str]) -> str:
    if not news_items and fallback_news:
        news_items = [{"title": t, "url": "", "source": "", "date": ""} for t in fallback_news]
    if not news_items:
        return '<div class="news-empty">뉴스 데이터 없음</div>'
    cells = []
    for item in news_items:
        title = escape(str(item.get("title") or ""))
        url = str(item.get("url") or "")
        source = escape(str(item.get("source") or item.get("broker") or ""))
        src_html = f'<div class="nc-source">{source}</div>' if source else ""
        title_html = (
            f'<a href="{escape(url)}" target="_blank" rel="noopener">{title}</a>'
            if url else title
        )
        cells.append(f'<div class="news-cell">{src_html}<div class="nc-title">{title_html}</div></div>')
    return f'<div class="news-grid3">{"".join(cells)}</div>'


def _news_cards_html(news_items: list[dict], fallback_news: list[str]) -> str:
    if not news_items and fallback_news:
        news_items = [{"title": line, "source": "", "date": "", "url": ""} for line in fallback_news]

    if not news_items:
        return '<div class="news-empty">데이터 없음</div>'

    cards = []
    for item in news_items:
        title = escape(str(item.get("title") or "제목 없음"))
        meta = " · ".join(str(part) for part in [item.get("source"), item.get("date")] if part)
        meta_html = f'<div class="news-meta">{escape(meta)}</div>' if meta else ""
        url = str(item.get("url") or "")
        inner = f"{meta_html}<div class=\"news-title\">{title}</div>"
        if url:
            cards.append(
                f'<a class="news-card" href="{escape(url)}" target="_blank" rel="noopener noreferrer">'
                f'{inner}<div class="news-action">원문</div></a>'
            )
        else:
            cards.append(f'<div class="news-card">{inner}</div>')

    return f'<div class="news-grid">{"".join(cards)}</div>'


def _chart_empty(message: str) -> str:
    """데이터 없는 차트 자리 — 빈 캔버스 대신 한 줄로 접는다."""
    return f'<div class="chart-empty">{escape(message)}</div>'


def _fig_html(fig: go.Figure, first: bool = False) -> str:
    return fig.to_html(
        include_plotlyjs="cdn" if first else False,
        full_html=False,
        config={"displayModeBar": False, "responsive": True, "staticPlot": True},
    )


def _dispatch_wrap(page_title: str, masthead_name: str, masthead_sub: str, date_str: str, body: str) -> str:
    import datetime
    date_label = date_str or datetime.date.today().isoformat()
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(page_title)} · CAT STOCK DISPATCH</title>
<style>{DISPATCH_CSS}</style>
</head>
<body>
<div class="dispatch">
  <div class="masthead">
    <div class="masthead-meta">
      <span>CAT STOCK DISPATCH</span>
      <span>SEOUL · {escape(date_label)} · PREMIUM INSIGHT</span>
      <span>{escape(masthead_name)}</span>
    </div>
    <div class="masthead-name">{escape(masthead_name)}</div>
    <div class="masthead-sub">{escape(masthead_sub)}</div>
  </div>
{body}
</div>
</body>
</html>"""


def _wrap(title: str, eyebrow: str, date_str: str, body: str) -> str:
    return _dispatch_wrap(title, title, eyebrow, date_str, body)


# ══════════════════════════════════════════════════════════════
# 1. 개별 종목 대시보드
# ══════════════════════════════════════════════════════════════

def build_stock_dashboard(payload: dict) -> str:
    basics = payload["basics"]
    flows = payload["flows"]
    financials = payload["financials"]
    disclosures = payload["disclosures"]
    short_selling = payload["short_selling"]
    reports = payload.get("reports", [])
    naver_reports = flows.get("naver_reports", [])
    news_items = flows.get("news_items", [])
    news_text = flows.get("news", [])
    column = payload.get("column")
    date_str = payload.get("target_date", "")
    is_first = True

    name = basics.get("name", "종목")
    price = str(basics.get("price") or "—")
    change = str(basics.get("change_pct") or "—")
    mktcap = str(basics.get("market_cap") or "—")
    per = str(basics.get("per") or "—")
    pbr = str(basics.get("pbr") or "—")
    roe = str(basics.get("roe") or "—")
    year_hl = str(basics.get("year_high_low") or "—")
    consensus = str(short_selling.get("consensus_target_price") or "—")
    major = str(disclosures.get("major_shareholder_ratio") or "—")
    risks = disclosures.get("risk_flags", [])
    chg_cls = _sign_class(change)

    # ── 티커 바 ────────────────────────────────────────────────
    ticker = (
        _ticker_item("현재가", price)
        + _ticker_item("등락률", change, chg_cls)
        + _ticker_item("시가총액", mktcap)
        + _ticker_item("PER", per)
        + _ticker_item("PBR", pbr)
        + _ticker_item("52주 고저", year_hl)
    )
    ticker_html = f'<div class="ticker-bar">{ticker}</div>'

    # ── 이동평균선 배지 ────────────────────────────────────────
    ma = basics.get("ma_position", {})
    badges = ""
    for label, key in [("5일선", "ma5"), ("20일선", "ma20"), ("60일선", "ma60")]:
        val = ma.get(key) or "—"
        dot = _ma_dot(val)
        badges += f'<span class="badge"><span class="dot dot-{dot}"></span>{label} {escape(str(val))}</span>'
    ma_html = f'<div class="ma-row" style="margin-top:12px;margin-bottom:16px;">{badges}</div>'

    # ── 재무 차트 ──────────────────────────────────────────────
    fin_quarters = [r.get("quarter", "") for r in financials]
    fin_sales = [_parse_fin_amount(r.get("sales")) for r in financials]
    fin_op = [_parse_fin_amount(r.get("op_income")) for r in financials]
    fin_net = [_parse_fin_amount(r.get("net_income")) for r in financials]
    if any(v is not None for v in fin_sales):
        fin_layout = dict(**_PLOTLY_LAYOUT, height=220, barmode="group")
        fin_fig = go.Figure(layout=fin_layout)
        fin_fig.add_trace(go.Bar(name="매출", x=fin_quarters, y=fin_sales, marker_color="rgba(26,26,26,0.15)", width=0.25))
        fin_fig.add_trace(go.Bar(name="영업이익", x=fin_quarters, y=fin_op, marker_color="rgba(26,26,26,0.55)", width=0.25))
        fin_fig.add_trace(go.Bar(name="순이익", x=fin_quarters, y=fin_net, marker_color="#1a1a1a", width=0.25))
        fin_fig.update_yaxes(ticksuffix="조")
        fin_chart = _fig_html(fin_fig, first=is_first)
        is_first = False
    else:
        fin_chart = _chart_empty("재무 데이터 없음 — DART 연결 시 표시됩니다")

    # ── 수급 차트: 일별 20거래일 우선, 없으면 20일 합계 폴백 ────────
    kis_flow = payload.get("kis_flow", {})
    daily_flows = flows.get("daily_flows") or {}
    daily_foreign = daily_flows.get("foreign") or []
    daily_inst = daily_flows.get("institution") or []
    daily_dates = [str(d)[5:] for d in (daily_flows.get("dates") or [])]  # "2026.07.04" → "07.04"

    if any(v is not None for v in daily_foreign) or any(v is not None for v in daily_inst):
        def _to_man(values: list) -> list:
            return [None if v is None else v / 10_000 for v in values]

        flow_layout = dict(**_PLOTLY_LAYOUT, height=220, barmode="group", bargap=0.25)
        flow_fig = go.Figure(layout=flow_layout)
        flow_fig.add_trace(go.Bar(name="외국인", x=daily_dates, y=_to_man(daily_foreign), marker_color="#1a1a1a"))
        flow_fig.add_trace(go.Bar(name="기관", x=daily_dates, y=_to_man(daily_inst), marker_color="rgba(26,26,26,0.35)"))
        flow_fig.update_yaxes(ticksuffix="만주", zeroline=True, zerolinecolor="rgba(0,0,0,0.25)")
        flow_fig.update_xaxes(type="category", tickangle=-45)
        flow_eyebrow = "INVESTOR FLOW — DAILY, 20 SESSIONS (만주)"
        flow_chart = _fig_html(flow_fig, first=is_first)
        is_first = False
    else:
        foreign_raw = kis_flow.get("foreign_20d_krw") or flows.get("foreign_20d")
        inst_raw = kis_flow.get("institution_20d_krw") or flows.get("institution_20d")
        foreign_num = _parse_flow_num(foreign_raw) or 0
        inst_num = _parse_flow_num(inst_raw) or 0
        unit = "억" if kis_flow.get("foreign_20d_krw") else "주"
        flow_eyebrow = f"INVESTOR FLOW — 20 DAYS ({unit})"
        if foreign_num == 0 and inst_num == 0:
            flow_chart = _chart_empty("수급 데이터 없음")
        else:
            flow_layout = dict(**_PLOTLY_LAYOUT, height=200)
            flow_fig = go.Figure(layout=flow_layout)
            flow_vals = [foreign_num, inst_num]
            flow_colors = ["#cc2200" if v >= 0 else "#006633" for v in flow_vals]
            flow_fig.add_trace(go.Bar(
                x=["외국인", "기관"], y=flow_vals, marker_color=flow_colors,
                showlegend=False,
                text=[f"{v:+,.1f}{unit}" if v else "—" for v in flow_vals],
                textposition="outside",
            ))
            flow_chart = _fig_html(flow_fig, first=is_first)
            is_first = False

    # ── 사이드바: 핵심 지표 ────────────────────────────────────
    def metric(lbl: str, val: str, cls: str = "") -> str:
        val_cls = f"m-val {cls}" if cls else "m-val"
        return f'<div class="metric-row"><span class="m-lbl">{escape(lbl)}</span><span class="{val_cls}">{escape(val)}</span></div>'

    sb_metrics = (
        metric("현재가", price)
        + metric("등락률", change, chg_cls)
        + metric("시가총액", mktcap)
        + metric("PER", per)
        + metric("PBR", pbr)
        + metric("ROE", roe)
        + metric("52주 고저", year_hl)
        + metric("컨센서스 목표가", consensus, "up")
        + metric("대주주 지분율", major)
    )

    # ── 사이드바: 리포트 ───────────────────────────────────────
    def _rpt_rows_html(rpt_list: list[dict]) -> str:
        rows = []
        for r in rpt_list[:5]:
            title = escape(str(r.get("title") or ""))
            broker = escape(str(r.get("broker") or ""))
            date_r = escape(str(r.get("date") or ""))
            target = escape(str(r.get("target_price") or ""))
            opinion = str(r.get("opinion") or "")
            pdf = str(r.get("pdf_url") or r.get("detail_url") or "")
            tag = _opinion_tag(opinion)
            title_html = f'<a href="{escape(pdf)}" target="_blank">{title}</a>' if pdf else title
            meta = " · ".join(p for p in [broker, date_r] if p)
            target_html = f'<span class="rpt-meta up">{target}</span>' if target else ""
            rows.append(f'<div class="rpt-row"><div class="rpt-broker">{meta}</div>'
                        f'<div class="rpt-title">{tag} {title_html}</div>{target_html}</div>')
        return "".join(rows) if rows else '<div class="rpt-broker">데이터 없음</div>'

    all_reports = (
        [{"title": ln.split(" | ")[0], "broker": " | ".join(ln.split(" | ")[1:]), "pdf_url": ""} for ln in naver_reports]
        + [{"title": r.get("title",""), "broker": r.get("broker",""), "date": r.get("date",""),
            "target_price": r.get("target_price",""), "opinion": r.get("opinion",""),
            "pdf_url": r.get("pdf_url","")} for r in reports]
    )

    # ── 공시 ──────────────────────────────────────────────────
    disc_list = disclosures.get("disclosures", [])
    disc_html = "".join(f'<tr><td>{escape(d)}</td></tr>' for d in disc_list[:8]) if disc_list else '<tr><td class="disc-empty">데이터 없음</td></tr>'

    # ── 조립 ──────────────────────────────────────────────────
    sidebar = f"""<div class="sidebar">
  <div class="sb-section">
    <div class="sb-title">THE WATCHLIST</div>
    {sb_metrics}
  </div>
  <div class="sb-section">
    <div class="sb-title">ANALYST DESK</div>
    {_rpt_rows_html(all_reports)}
  </div>
  <div class="sb-section">
    <div class="sb-title">RISK FLAGS</div>
    <div style="font-family:'IBM Plex Mono',monospace;font-size:10px;color:#666;line-height:1.7;">
      {"<br>".join(escape(r) for r in risks) if risks else "이상 없음"}
    </div>
  </div>
</div>"""

    main_col = f"""<div class="main-col">
  {_column_html(column, date_str)}
  {ma_html}
  <div class="chart-eyebrow">QUARTERLY FINANCIALS (조원)</div>
  {fin_chart}
  <div class="chart-eyebrow">{flow_eyebrow}</div>
  {flow_chart}
</div>"""

    body = f"""
{ticker_html}
{_date_notice_html(payload)}
<div class="main-grid">
  {main_col}
  {sidebar}
</div>
<div class="rule"><div class="rule-line"></div><div class="rule-title">LATEST NEWS</div><div class="rule-line"></div></div>
{_news_grid3_html(news_items, news_text)}
<div class="rule"><div class="rule-line"></div><div class="rule-title">DISCLOSURES</div><div class="rule-line"></div></div>
<table class="disc-table"><tbody>{disc_html}</tbody></table>
"""

    return _dispatch_wrap(
        page_title=name,
        masthead_name=name,
        masthead_sub="INDIVIDUAL STOCK INTELLIGENCE REPORT · CAT STOCK",
        date_str=date_str,
        body=body,
    )


# ══════════════════════════════════════════════════════════════
# 2. 시황 브리핑 대시보드
# ══════════════════════════════════════════════════════════════

def build_market_dashboard(payload: dict) -> str:
    indices = payload.get("indices", {})
    macro = payload.get("global_macro", {})
    investor_flows = payload.get("investor_flows", {})
    leaders = payload.get("leaders", [])
    sectors = payload.get("sectors", [])
    events = payload.get("market_events", {})
    news_items = payload.get("news_items", [])
    market_reports = payload.get("market_reports", [])
    column = payload.get("column")
    date_str = payload.get("target_date", "")
    is_first = True

    kospi = indices.get("kospi", {})
    kosdaq = indices.get("kosdaq", {})

    # ── 티커 바 ────────────────────────────────────────────────
    def idx_cls(v: object) -> str:
        # change_pct는 숫자로 오면 "+"가 없어 _sign_class가 상승을 놓치므로 숫자를 우선 판정
        try:
            num = float(str(v).replace(",", "").replace("%", "").strip())
        except (TypeError, ValueError):
            return _sign_class(str(v))
        if num > 0:
            return "up"
        if num < 0:
            return "dn"
        return ""

    def signed_pct(v: object) -> str:
        try:
            return f"{float(str(v).replace(',', '')):+.2f}%"
        except (TypeError, ValueError):
            return f"{v}%" if v not in (None, "", "—") else "—"

    ticker = (
        _ticker_item("코스피", str(kospi.get("close") or "—"), idx_cls(kospi.get("change_pct")))
        + _ticker_item("등락", signed_pct(kospi.get("change_pct")), idx_cls(kospi.get("change_pct")))
        + _ticker_item("코스닥", str(kosdaq.get("close") or "—"), idx_cls(kosdaq.get("change_pct")))
        + _ticker_item("달러/원", str(macro.get("usdkrw") or "—"))
        + _ticker_item("나스닥", str(macro.get("nasdaq") or "—"), idx_cls(macro.get("nasdaq")))
        + _ticker_item("미10년물", str(macro.get("us10y") or "—"))
    )

    # ── 지수 흐름 차트 (최근 10거래일, 첫날 대비 %) ───────────────
    index_trend = payload.get("index_trend") or {}
    kospi_closes = [v for v in ((index_trend.get("kospi") or {}).get("closes") or []) if v is not None]
    kosdaq_closes = [v for v in ((index_trend.get("kosdaq") or {}).get("closes") or []) if v is not None]
    trend_block = ""
    if len(kospi_closes) >= 2 or len(kosdaq_closes) >= 2:
        def _pct_series(closes: list) -> list:
            base = closes[0]
            return [(v / base - 1) * 100 for v in closes]

        def _session_labels(n: int) -> list:
            return [f"D-{n - 1 - i}" if i < n - 1 else "당일" for i in range(n)]

        trend_layout = dict(**_PLOTLY_LAYOUT, height=200)
        trend_fig = go.Figure(layout=trend_layout)
        if len(kospi_closes) >= 2:
            trend_fig.add_trace(go.Scatter(
                name="코스피", x=_session_labels(len(kospi_closes)), y=_pct_series(kospi_closes),
                mode="lines+markers", line=dict(color="#1a1a1a", width=2), marker=dict(size=4),
            ))
        if len(kosdaq_closes) >= 2:
            trend_fig.add_trace(go.Scatter(
                name="코스닥", x=_session_labels(len(kosdaq_closes)), y=_pct_series(kosdaq_closes),
                mode="lines+markers", line=dict(color="#6f7683", width=2, dash="dot"), marker=dict(size=4),
            ))
        trend_fig.update_yaxes(ticksuffix="%", zeroline=True, zerolinecolor="rgba(0,0,0,0.25)")
        trend_chart = _fig_html(trend_fig, first=is_first)
        is_first = False
        trend_block = f'<div class="chart-eyebrow">INDEX TREND — 10 SESSIONS (CUMULATIVE %)</div>\n  {trend_chart}'

    # ── 거래대금 상위 차트 ─────────────────────────────────────
    leader_names = [item.get("name", "") for item in leaders[:10]]
    leader_tvr = []
    for item in leaders[:10]:
        try:
            leader_tvr.append(float(str(item.get("turnover_krw_billion") or 0).replace(",", "")))
        except Exception:
            leader_tvr.append(0)

    if leader_names:
        vol_layout = dict(**_PLOTLY_LAYOUT, height=260)
        vol_fig = go.Figure(layout=vol_layout)
        vol_fig.add_trace(go.Bar(
            x=leader_tvr[::-1], y=leader_names[::-1], orientation="h",
            marker_color="#1a1a1a", showlegend=False,
            text=[f"{v:,.0f}억" for v in leader_tvr[::-1]], textposition="outside",
        ))
        vol_fig.update_xaxes(ticksuffix="억")
        vol_chart = _fig_html(vol_fig, first=is_first)
        is_first = False
    else:
        vol_chart = _chart_empty("거래대금 데이터 없음")

    # ── 수급 차트 ──────────────────────────────────────────────
    summary = investor_flows.get("summary", {})
    flow_nums = []
    for key in ["foreign", "institution", "retail"]:
        try:
            v = summary.get(key)
            flow_nums.append(float(str(v).replace(",", "")) if v not in (None, "—") else 0)
        except Exception:
            flow_nums.append(0)
    if any(flow_nums):
        sup_layout = dict(**_PLOTLY_LAYOUT, height=220)
        sup_fig = go.Figure(layout=sup_layout)
        sup_fig.add_trace(go.Bar(
            x=["외국인", "기관", "개인"], y=flow_nums,
            marker_color=["#cc2200" if v >= 0 else "#006633" for v in flow_nums],
            showlegend=False,
            text=[f"{v:+,.0f}억" if v else "—" for v in flow_nums],
            textposition="outside",
        ))
        sup_fig.update_yaxes(ticksuffix="억")
        sup_chart = _fig_html(sup_fig, first=is_first)
        is_first = False
    else:
        sup_chart = _chart_empty("수급 데이터 없음")

    # ── 사이드바: 글로벌 지표 ─────────────────────────────────
    global_items = [
        ("다우", "dow"), ("S&P500", "sp500"), ("나스닥", "nasdaq"),
        ("달러/원", "usdkrw"), ("미10년물", "us10y"), ("WTI", "wti"),
        ("상해", "shanghai"), ("심천", "shenzhen"),
    ]
    gm_rows = ""
    for lbl, key in global_items:
        val = str(macro.get(key) or "—")
        cls = _sign_class(val)
        val_cls = f"gm-val {cls}" if cls else "gm-val na"
        gm_rows += f'<div class="gm-row"><span class="gm-name">{escape(lbl)}</span><span class="{val_cls}">{escape(val)}</span></div>'

    # ── 사이드바: 테마/섹터 ────────────────────────────────────
    sector_rows = ""
    for s in sorted(sectors, key=lambda x: abs(x.get("change_pct") or 0), reverse=True)[:10]:
        val = s.get("change_pct")
        val_str = f"{'+' if (val or 0) >= 0 else ''}{val:.2f}%" if val is not None else "—"
        cls = _sign_class(val_str)
        val_cls = f"gm-val {cls}" if cls else "gm-val na"
        sector_rows += f'<div class="gm-row"><span class="gm-name">{escape(s.get("name",""))}</span><span class="{val_cls}">{escape(val_str)}</span></div>'

    # ── 수급 상위 ──────────────────────────────────────────────
    def _flow_col(names: list, kind: str) -> str:
        cls = "buy" if kind == "buy" else "sell"
        items = "".join(f'<div class="flow-item {cls}">{escape(str(n))}</div>' for n in names[:5]) or "—"
        return items

    fb = investor_flows.get("foreign_top_buy", [])
    fs = investor_flows.get("foreign_top_sell", [])
    ib = investor_flows.get("institution_top_buy", [])
    is_ = investor_flows.get("institution_top_sell", [])

    flow_section = f"""<div class="flow2">
  <div class="flow-col">
    <div class="flow-title">외국인 순매수</div>{_flow_col(fb,"buy")}
    <div class="flow-title" style="margin-top:10px;">외국인 순매도</div>{_flow_col(fs,"sell")}
  </div>
  <div class="flow-col">
    <div class="flow-title">기관 순매수</div>{_flow_col(ib,"buy")}
    <div class="flow-title" style="margin-top:10px;">기관 순매도</div>{_flow_col(is_,"sell")}
  </div>
</div>"""

    # ── 등락률 상위 (지면에서는 상위 15개만, 나머지는 개수로 축약) ──
    def _mover_col(items: list, kind: str, limit: int) -> str:
        cls = "buy" if kind == "buy" else "sell"
        shown = items[:limit]
        html = "".join(f'<div class="flow-item {cls}">{escape(str(item))}</div>' for item in shown) or "—"
        rest = len(items) - len(shown)
        if rest > 0:
            html += f'<div class="flow-item" style="opacity:.55;">외 {rest}종목 (텍스트 출력에 전체 포함)</div>'
        return html

    movers_section = f"""<div class="flow2">
  <div class="flow-col">
    <div class="flow-title">당일 상승 상위</div>{_mover_col(events.get("new_highs", []), "buy", 15)}
  </div>
  <div class="flow-col">
    <div class="flow-title">당일 하락 상위</div>{_mover_col(events.get("new_lows", []), "sell", 15)}
  </div>
</div>"""

    sidebar = f"""<div class="sidebar">
  <div class="sb-section">
    <div class="sb-title">GLOBAL MARKETS</div>
    <div class="global-mini">{gm_rows}</div>
  </div>
  <div class="sb-section">
    <div class="sb-title">SECTOR · THEME</div>
    <div class="global-mini">{sector_rows if sector_rows else '<span class="disc-empty">데이터 없음</span>'}</div>
  </div>
  <div class="sb-section">
    <div class="sb-title">시장 이벤트</div>
    <div style="font-family:\'IBM Plex Mono\',monospace;font-size:10px;color:#444;line-height:1.8;">
      <div>상한가: {escape(', '.join(events.get('upper_limit', [])[:5]) or '—')}</div>
      <div>시간외: {escape(', '.join(events.get('after_hours_movers', [])[:3]) or '—')}</div>
    </div>
  </div>
</div>"""

    main_col = f"""<div class="main-col">
  {_column_html(column, date_str)}
  {trend_block}
  <div class="chart-eyebrow">TODAY'S TRADING LEADERS (억원)</div>
  {vol_chart}
  <div class="chart-eyebrow">INVESTOR NET BUY / SELL (억원)</div>
  {sup_chart}
  <div class="rule-thin"></div>
  {flow_section}
  <div class="chart-eyebrow">PRICE MOVERS</div>
  {movers_section}
</div>"""

    body = f"""
<div class="ticker-bar">{ticker}</div>
{_date_notice_html(payload)}
<div class="main-grid">
  {main_col}
  {sidebar}
</div>
<div class="rule"><div class="rule-line"></div><div class="rule-title">LATEST NEWS</div><div class="rule-line"></div></div>
{_news_grid3_html(news_items, [])}
<div class="rule"><div class="rule-line"></div><div class="rule-title">ANALYST REPORTS</div><div class="rule-line"></div></div>
{_news_grid3_html(market_reports, [])}
"""

    return _dispatch_wrap(
        page_title="시황 브리핑",
        masthead_name="KOSPI DISPATCH",
        masthead_sub="THE DAILY INTELLIGENCE FOR THE KOREAN CAPITAL MARKETS · CAT STOCK",
        date_str=date_str,
        body=body,
    )


# ══════════════════════════════════════════════════════════════
# 3. 테마 공부 대시보드
# ══════════════════════════════════════════════════════════════

def _theme_pct(value: object) -> float | None:
    try:
        return float(str(value).replace("%", "").replace("+", "").replace(",", ""))
    except (TypeError, ValueError):
        return None


def build_theme_dashboard(payload: dict) -> str:
    theme_name = payload.get("theme_name", "")
    stocks = payload.get("stocks") or []
    news_bundle = payload.get("news_bundle") or {}
    peer_bundle = payload.get("peer_bundle") or {}
    date_str = payload.get("target_date", "")

    # ── 티커 바: 테마 요약 ─────────────────────────────────────
    pcts = [p for p in (_theme_pct(s.get("change_pct")) for s in stocks) if p is not None]
    up_count = sum(1 for p in pcts if p > 0)
    down_count = sum(1 for p in pcts if p < 0)
    avg_pct = sum(pcts) / len(pcts) if pcts else None
    avg_str = f"{avg_pct:+.2f}%" if avg_pct is not None else "—"
    leader = max(stocks, key=lambda s: _theme_pct(s.get("change_pct")) or float("-inf")) if pcts else None
    ticker = (
        _ticker_item("테마", theme_name or "—")
        + _ticker_item("편입 종목", f"{len(stocks)}개" if stocks else "—")
        + _ticker_item("평균 등락", avg_str, _sign_class(avg_str))
        + _ticker_item("상승", f"{up_count}종목", "up" if up_count else "")
        + _ticker_item("하락", f"{down_count}종목", "dn" if down_count else "")
        + _ticker_item("주도주", str((leader or {}).get("name") or "—"))
    )
    ticker_html = f'<div class="ticker-bar">{ticker}</div>'

    # ── 등락률 차트 ────────────────────────────────────────────
    chart_stocks = sorted(
        [s for s in stocks if _theme_pct(s.get("change_pct")) is not None],
        key=lambda s: _theme_pct(s.get("change_pct")),
    )[-12:]
    chart_block = ""
    if chart_stocks:
        names = [str(s.get("name") or "") for s in chart_stocks]
        values = [_theme_pct(s.get("change_pct")) for s in chart_stocks]
        bar_layout = dict(**_PLOTLY_LAYOUT, height=max(200, 24 * len(names)))
        bar_fig = go.Figure(layout=bar_layout)
        bar_fig.add_trace(go.Bar(
            x=values, y=names, orientation="h",
            marker_color=["#cc2200" if v >= 0 else "#006633" for v in values],
            showlegend=False,
            text=[f"{v:+.2f}%" for v in values], textposition="outside",
        ))
        bar_fig.update_xaxes(ticksuffix="%", zeroline=True, zerolinecolor="rgba(0,0,0,0.25)")
        chart_block = (
            '<div class="chart-eyebrow">THEME MOVERS — DAILY CHANGE (%)</div>\n'
            + _fig_html(bar_fig, first=True)
        )

    # ── 종목 테이블 ────────────────────────────────────────────
    if stocks:
        rows = []
        for s in stocks:
            pct = _theme_pct(s.get("change_pct"))
            cls = "up" if (pct or 0) > 0 else ("dn" if (pct or 0) < 0 else "")
            rows.append(
                "<tr>"
                f"<td>{escape(str(s.get('name') or '—'))}</td>"
                f'<td class="num">{escape(str(s.get("market_cap") or "—"))}</td>'
                f'<td class="num">{escape(str(s.get("price") or "—"))}</td>'
                f'<td class="num {cls}">{escape(str(s.get("change_pct") or "—"))}</td>'
                f'<td class="num">{escape(str(s.get("per") or "—"))}</td>'
                f'<td class="num">{escape(str(s.get("pbr") or "—"))}</td>'
                "</tr>"
            )
        table_html = (
            '<table class="theme-table"><thead><tr>'
            "<th>종목</th><th>시가총액</th><th>현재가</th><th>등락률</th><th>PER</th><th>PBR</th>"
            f'</tr></thead><tbody>{"".join(rows)}</tbody></table>'
        )
    else:
        table_html = '<div class="news-empty">테마 종목 데이터 없음 — 테마명을 다시 확인해 주세요.</div>'

    # ── 사이드바: 뉴스/리포트/공시 ─────────────────────────────
    def _line_rows(lines: list, empty: str) -> str:
        items = "".join(f'<div class="rpt-row"><div class="rpt-title">{escape(str(line))}</div></div>' for line in lines[:8])
        return items or f'<div class="rpt-broker">{escape(empty)}</div>'

    sidebar = f"""<div class="sidebar">
  <div class="sb-section">
    <div class="sb-title">THEME WIRE</div>
    {_line_rows(news_bundle.get("news") or [], "관련 뉴스 없음")}
  </div>
  <div class="sb-section">
    <div class="sb-title">ANALYST DESK</div>
    {_line_rows(news_bundle.get("reports") or [], "리포트 없음")}
  </div>
  <div class="sb-section">
    <div class="sb-title">DISCLOSURES</div>
    {_line_rows(peer_bundle.get("disclosures") or [], "공시 없음")}
  </div>
</div>"""

    main_col = f"""<div class="main-col">
  {chart_block}
  <div class="chart-eyebrow">CONSTITUENTS</div>
  {table_html}
</div>"""

    body = f"""
{ticker_html}
<div class="main-grid">
  {main_col}
  {sidebar}
</div>
"""

    return _dispatch_wrap(
        page_title=theme_name or "테마 공부",
        masthead_name=theme_name or "THEME STUDY",
        masthead_sub="THEME INTELLIGENCE REPORT · CAT STOCK",
        date_str=date_str,
        body=body,
    )

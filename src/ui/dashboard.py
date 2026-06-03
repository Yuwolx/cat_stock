from __future__ import annotations

import re
from html import escape

import plotly.graph_objects as go


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

# ── 신문 스타일 CSS ─────────────────────────────────────────
_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,900;1,700&family=Crimson+Text:ital,wght@0,400;0,600;1,400&family=IBM+Plex+Mono:wght@400;500;700&display=swap');
*{margin:0;padding:0;box-sizing:border-box;}
body{background:#f4f0e6;font-family:'Crimson Text',Georgia,'Times New Roman',serif;color:#1a1a1a;padding:28px 20px 72px;}
.dispatch{max-width:1080px;margin:0 auto;}

/* ── MASTHEAD ── */
.masthead-meta{display:flex;justify-content:space-between;align-items:center;font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:.07em;text-transform:uppercase;border-top:2.5px solid #1a1a1a;border-bottom:1px solid #1a1a1a;padding:6px 0;margin-bottom:6px;}
.masthead-name{font-family:'Playfair Display',Georgia,serif;font-size:clamp(32px,5vw,56px);font-weight:900;letter-spacing:-.02em;text-transform:uppercase;text-align:center;line-height:1;margin:4px 0 6px;}
.masthead-sub{text-align:center;font-family:'IBM Plex Mono',monospace;font-size:9.5px;letter-spacing:.12em;text-transform:uppercase;border-top:1px solid #1a1a1a;border-bottom:3px solid #1a1a1a;padding:5px 0;margin-bottom:0;}

/* ── TICKER BAR ── */
.ticker-bar{display:flex;background:#1a1a1a;color:#f4f0e6;margin-bottom:18px;overflow:hidden;}
.ticker-item{flex:1;padding:9px 14px;border-right:1px solid rgba(255,255,255,.08);}
.ticker-item:last-child{border-right:0;}
.t-name{font-family:'IBM Plex Mono',monospace;font-size:9px;opacity:.55;text-transform:uppercase;letter-spacing:.07em;margin-bottom:3px;}
.t-val{font-family:'IBM Plex Mono',monospace;font-size:16px;font-weight:700;letter-spacing:-.01em;}
.t-val.up{color:#ff6b6b;}.t-val.dn{color:#51cf66;}.t-val.na{color:rgba(244,240,230,.4);}

/* ── MAIN GRID ── */
.main-grid{display:grid;grid-template-columns:1fr 260px;gap:24px;margin-bottom:0;}
.main-col{}

/* ── COLUMN SECTION ── */
.section-tag{display:inline-block;background:#1a1a1a;color:#f4f0e6;font-family:'IBM Plex Mono',monospace;font-size:9px;letter-spacing:.12em;text-transform:uppercase;padding:3px 9px;margin-bottom:10px;}
.column-title{font-family:'Playfair Display',Georgia,serif;font-size:clamp(20px,2.4vw,26px);font-weight:700;line-height:1.22;letter-spacing:-.01em;word-break:keep-all;margin-bottom:9px;}
.byline{font-family:'IBM Plex Mono',monospace;font-size:10px;color:#666;letter-spacing:.03em;border-bottom:1px solid #aaa;padding-bottom:10px;margin-bottom:12px;}
.col-body{font-size:16px;line-height:1.74;color:#222;}
.col-body p{margin-bottom:10px;}
.drop-cap::first-letter{float:left;font-family:'Playfair Display',serif;font-size:62px;line-height:.76;margin-right:7px;margin-top:5px;font-weight:700;}
.no-col{font-family:'IBM Plex Mono',monospace;font-size:11px;color:#999;font-style:italic;padding:10px 0 16px;border-bottom:1px solid #ccc;margin-bottom:14px;}

/* ── RULE DIVIDERS ── */
.rule{display:flex;align-items:center;gap:12px;margin:20px 0 12px;}
.rule-title{font-family:'Playfair Display',serif;font-size:14px;font-weight:700;text-transform:uppercase;white-space:nowrap;letter-spacing:.02em;}
.rule-line{flex:1;height:1px;background:#1a1a1a;}
.rule-thin{border-top:1px solid #ccc;margin:16px 0;}

/* ── CHART SECTIONS ── */
.chart-eyebrow{font-family:'IBM Plex Mono',monospace;font-size:9px;letter-spacing:.10em;text-transform:uppercase;color:#666;border-top:1px solid #ccc;padding-top:10px;margin-bottom:8px;margin-top:18px;}

/* ── SIDEBAR ── */
.sidebar{border-left:1px solid #ccc;padding-left:18px;}
.sb-section{margin-bottom:22px;}
.sb-title{font-family:'Playfair Display',serif;font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:.03em;border-bottom:2px solid #1a1a1a;padding-bottom:4px;margin-bottom:10px;}
.metric-row{display:flex;justify-content:space-between;align-items:baseline;padding:5px 0;border-bottom:1px solid rgba(0,0,0,.07);}
.metric-row:last-child{border-bottom:0;}
.m-lbl{font-family:'IBM Plex Mono',monospace;font-size:10px;color:#666;letter-spacing:.02em;}
.m-val{font-family:'IBM Plex Mono',monospace;font-size:12px;font-weight:700;letter-spacing:-.01em;}
.m-val.up{color:#cc2200;}.m-val.dn{color:#006633;}

/* ── REPORT ROWS ── */
.rpt-row{padding:7px 0;border-bottom:1px solid rgba(0,0,0,.07);}
.rpt-row:last-child{border-bottom:0;}
.rpt-broker{font-family:'IBM Plex Mono',monospace;font-size:9px;color:#888;text-transform:uppercase;letter-spacing:.04em;margin-bottom:2px;}
.rpt-title{font-size:12px;font-weight:600;line-height:1.42;word-break:keep-all;margin-bottom:2px;}
.rpt-title a{color:#1a1a1a;text-decoration:none;}
.rpt-title a:hover{text-decoration:underline;color:#cc2200;}
.rpt-meta{font-family:'IBM Plex Mono',monospace;font-size:10px;color:#888;}
.rpt-meta.up{color:#cc2200;}

/* ── TAGS ── */
.tag{display:inline-block;padding:1px 6px;font-family:'IBM Plex Mono',monospace;font-size:9px;font-weight:700;border:1px solid;}
.tag-buy{border-color:#cc2200;color:#cc2200;}
.tag-hold{border-color:#cc7700;color:#cc7700;}
.tag-sell{border-color:#006633;color:#006633;}

/* ── NEWS GRID ── */
.news-grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:0;border:1px solid #ccc;margin-bottom:20px;}
.news-cell{padding:11px 14px;border-right:1px solid #ccc;border-bottom:1px solid #ccc;}
.news-cell:nth-child(3n){border-right:0;}
.news-cell:nth-last-child(-n+3){border-bottom:0;}
.nc-source{font-family:'IBM Plex Mono',monospace;font-size:9px;color:#888;text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px;}
.nc-title{font-size:13px;font-weight:600;line-height:1.45;word-break:keep-all;}
.nc-title a{color:#1a1a1a;text-decoration:none;}
.nc-title a:hover{text-decoration:underline;color:#cc2200;}
.news-empty{font-family:'IBM Plex Mono',monospace;font-size:11px;color:#aaa;padding:12px 0;}

/* ── DISCLOSURE / TABLE ── */
.disc-table{width:100%;border-collapse:collapse;margin-bottom:20px;}
.disc-table td{font-size:12px;padding:7px 0;border-bottom:1px solid rgba(0,0,0,.07);color:#333;line-height:1.5;}
.disc-table tr:last-child td{border-bottom:0;}
.disc-empty{font-family:'IBM Plex Mono',monospace;font-size:11px;color:#aaa;padding:8px 0;}

/* ── GLOBAL MINI GRID ── */
.global-mini{display:grid;grid-template-columns:1fr 1fr;gap:0;}
.gm-row{display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid rgba(0,0,0,.07);}
.gm-row:last-child{border-bottom:0;}
.gm-name{font-family:'IBM Plex Mono',monospace;font-size:10px;color:#666;}
.gm-val{font-family:'IBM Plex Mono',monospace;font-size:11px;font-weight:700;}
.gm-val.up{color:#cc2200;}.gm-val.dn{color:#006633;}

/* ── FLOW TOP TABLE ── */
.flow2{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:20px;}
.flow-col{}
.flow-title{font-family:'IBM Plex Mono',monospace;font-size:9px;letter-spacing:.08em;text-transform:uppercase;color:#888;margin-bottom:6px;}
.flow-item{font-size:13px;padding:4px 0;border-bottom:1px solid rgba(0,0,0,.06);}
.flow-item.buy::before{content:"▲ ";color:#cc2200;font-size:10px;}
.flow-item.sell::before{content:"▼ ";color:#006633;font-size:10px;}

/* ── MA BADGES ── */
.ma-row{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:4px;}
.badge{display:inline-flex;align-items:center;gap:5px;padding:4px 10px;border:1px solid #ccc;font-size:11px;font-family:'IBM Plex Mono',monospace;}
.dot{width:7px;height:7px;border-radius:50%;}
.dot-up{background:#cc2200;}.dot-near{background:#cc7700;}.dot-dn{background:#006633;}

@media(max-width:768px){.main-grid{grid-template-columns:1fr;}.sidebar{border-left:0;padding-left:0;border-top:2px solid #1a1a1a;padding-top:16px;}.news-grid3{grid-template-columns:repeat(2,1fr);}.global-mini{grid-template-columns:1fr;}.flow2{grid-template-columns:1fr;}.ticker-bar{flex-wrap:wrap;}}
"""


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
    fallback = "ANTHROPIC_API_KEY를 설정하면 AI 분석 칼럼이 여기에 생성됩니다."
    reason_messages = {
        "missing_api_key": "AI 칼럼: ANTHROPIC_API_KEY가 설정되지 않았습니다.",
        "package_missing": "AI 칼럼: anthropic 패키지가 설치되지 않았습니다.",
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
<div class="col-body"><p class="drop-cap">{body}</p></div>"""


def _news_grid3_html(news_items: list[dict], fallback_news: list[str]) -> str:
    if not news_items and fallback_news:
        news_items = [{"title": t, "url": "", "source": "", "date": ""} for t in fallback_news]
    if not news_items:
        return '<div class="news-empty">뉴스 데이터 없음</div>'
    cells = []
    for item in news_items:
        title = escape(str(item.get("title") or ""))
        url = str(item.get("url") or "")
        source = escape(str(item.get("source") or ""))
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


def _fig_html(fig: go.Figure, first: bool = False) -> str:
    return fig.to_html(
        include_plotlyjs=first,
        full_html=False,
        config={"displayModeBar": False, "responsive": True},
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
<style>{_CSS}</style>
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
    fin_layout = dict(**_PLOTLY_LAYOUT, height=220, barmode="group")
    fin_fig = go.Figure(layout=fin_layout)
    if any(v is not None for v in fin_sales):
        fin_fig.add_trace(go.Bar(name="매출", x=fin_quarters, y=fin_sales, marker_color="rgba(26,26,26,0.15)", width=0.25))
        fin_fig.add_trace(go.Bar(name="영업이익", x=fin_quarters, y=fin_op, marker_color="rgba(26,26,26,0.55)", width=0.25))
        fin_fig.add_trace(go.Bar(name="순이익", x=fin_quarters, y=fin_net, marker_color="#1a1a1a", width=0.25))
    fin_fig.update_yaxes(ticksuffix="조")
    fin_chart = _fig_html(fin_fig, first=is_first)
    is_first = False

    # ── 수급 차트 ──────────────────────────────────────────────
    kis_flow = payload.get("kis_flow", {})
    foreign_raw = kis_flow.get("foreign_20d_krw") or flows.get("foreign_20d")
    inst_raw = kis_flow.get("institution_20d_krw") or flows.get("institution_20d")
    foreign_num = _parse_flow_num(foreign_raw) or 0
    inst_num = _parse_flow_num(inst_raw) or 0
    flow_layout = dict(**_PLOTLY_LAYOUT, height=200)
    flow_fig = go.Figure(layout=flow_layout)
    flow_vals = [foreign_num, inst_num]
    flow_colors = ["#cc2200" if v >= 0 else "#006633" for v in flow_vals]
    unit = "억" if kis_flow.get("foreign_20d_krw") else "주"
    flow_fig.add_trace(go.Bar(
        x=["외국인", "기관"], y=flow_vals, marker_color=flow_colors,
        showlegend=False,
        text=[f"{v:+,.1f}{unit}" if v else "—" for v in flow_vals],
        textposition="outside",
    ))
    flow_chart = _fig_html(flow_fig, first=False)

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
  <div class="chart-eyebrow">INVESTOR FLOW — 20 DAYS ({unit})</div>
  {flow_chart}
</div>"""

    body = f"""
{ticker_html}
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
    disclosures = payload.get("disclosures", [])
    sectors = payload.get("sectors", [])
    events = payload.get("market_events", {})
    column = payload.get("column")
    date_str = payload.get("target_date", "")
    is_first = True

    kospi = indices.get("kospi", {})
    kosdaq = indices.get("kosdaq", {})

    # ── 티커 바 ────────────────────────────────────────────────
    def idx_cls(v: object) -> str:
        return _sign_class(str(v))

    ticker = (
        _ticker_item("코스피", str(kospi.get("close") or "—"), idx_cls(kospi.get("change_pct")))
        + _ticker_item("등락", f"{kospi.get('change_pct','—')}%", idx_cls(kospi.get("change_pct")))
        + _ticker_item("코스닥", str(kosdaq.get("close") or "—"), idx_cls(kosdaq.get("change_pct")))
        + _ticker_item("달러/원", str(macro.get("usdkrw") or "—"))
        + _ticker_item("나스닥", str(macro.get("nasdaq") or "—"), idx_cls(macro.get("nasdaq")))
        + _ticker_item("미10년물", str(macro.get("us10y") or "—"))
    )

    # ── 거래대금 상위 차트 ─────────────────────────────────────
    leader_names = [item.get("name", "") for item in leaders[:10]]
    leader_tvr = []
    for item in leaders[:10]:
        try:
            leader_tvr.append(float(str(item.get("turnover_krw_billion") or 0).replace(",", "")))
        except Exception:
            leader_tvr.append(0)

    vol_layout = dict(**_PLOTLY_LAYOUT, height=260)
    vol_fig = go.Figure(layout=vol_layout)
    if leader_names:
        vol_fig.add_trace(go.Bar(
            x=leader_tvr[::-1], y=leader_names[::-1], orientation="h",
            marker_color="#1a1a1a", showlegend=False,
            text=[f"{v:,.0f}억" for v in leader_tvr[::-1]], textposition="outside",
        ))
    vol_fig.update_xaxes(ticksuffix="억")
    vol_chart = _fig_html(vol_fig, first=is_first)
    is_first = False

    # ── 수급 차트 ──────────────────────────────────────────────
    summary = investor_flows.get("summary", {})
    flow_nums = []
    for key in ["foreign", "institution", "retail"]:
        try:
            v = summary.get(key)
            flow_nums.append(float(str(v).replace(",", "")) if v not in (None, "—") else 0)
        except Exception:
            flow_nums.append(0)
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
    sup_chart = _fig_html(sup_fig, first=False)

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

    # ── 공시 ──────────────────────────────────────────────────
    disc_html = "".join(f'<tr><td>{escape(str(d))}</td></tr>' for d in disclosures[:10]) if disclosures else '<tr><td class="disc-empty">데이터 없음</td></tr>'

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
  <div class="chart-eyebrow">TODAY'S TRADING LEADERS (억원)</div>
  {vol_chart}
  <div class="chart-eyebrow">INVESTOR NET BUY / SELL (억원)</div>
  {sup_chart}
  <div class="rule-thin"></div>
  {flow_section}
</div>"""

    body = f"""
<div class="ticker-bar">{ticker}</div>
<div class="main-grid">
  {main_col}
  {sidebar}
</div>
<div class="rule"><div class="rule-line"></div><div class="rule-title">DISCLOSURES</div><div class="rule-line"></div></div>
<table class="disc-table"><tbody>{disc_html}</tbody></table>
"""

    return _dispatch_wrap(
        page_title="시황 브리핑",
        masthead_name="KOSPI DISPATCH",
        masthead_sub="THE DAILY INTELLIGENCE FOR THE KOREAN CAPITAL MARKETS · CAT STOCK",
        date_str=date_str,
        body=body,
    )


# ══════════════════════════════════════════════════════════════
# 3. 테마 공부 대시보드 (데이터 연결 전 플레이스홀더)
# ══════════════════════════════════════════════════════════════

def build_theme_dashboard(payload: dict) -> str:
    theme_name = payload.get("theme_name", "")
    parts = ["""
<div class="tbl-card">
  <div class="sec-ttl">준비 중</div>
  <p style="font-size:13px;color:#6f7683;padding:12px 0;">테마 공부 대시보드는 실데이터 연결 후 제공됩니다.</p>
</div>"""]
    return _wrap(
        title=theme_name,
        eyebrow="테마 공부",
        date_str=payload.get("target_date", ""),
        body="\n".join(parts),
    )

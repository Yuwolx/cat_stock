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

# ── 공통 CSS ────────────────────────────────────────────────
_CSS = """
*{margin:0;padding:0;box-sizing:border-box;}
body{background:#fdfbf7;font-family:-apple-system,BlinkMacSystemFont,'Inter',system-ui,sans-serif;color:#111318;padding:36px 28px 72px;}
.db{max-width:1200px;margin:0 auto;}
.hdr{margin-bottom:28px;padding-bottom:20px;border-bottom:1px solid rgba(17,19,24,0.09);}
.hdr-eye{font-size:10px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#6f7683;margin-bottom:6px;}
.hdr-title{font-size:30px;font-weight:800;letter-spacing:-.04em;}
.hdr-sub{font-size:12px;color:#6f7683;margin-top:4px;}
.metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:20px;}
.card{background:#fff;border:1px solid rgba(17,19,24,0.09);border-radius:12px;padding:16px 18px;}
.card-lbl{font-size:10px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:#6f7683;margin-bottom:6px;}
.card-val{font-size:20px;font-weight:700;letter-spacing:-.02em;}
.card-val.up{color:#e05252;}
.card-val.dn{color:#4caf83;}
.card-sub{font-size:11px;color:#6f7683;margin-top:3px;}
.ma-row{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:20px;}
.badge{display:inline-flex;align-items:center;gap:6px;padding:5px 12px;border-radius:999px;font-size:11px;font-weight:600;border:1px solid rgba(17,19,24,0.09);background:#fff;}
.dot{width:7px;height:7px;border-radius:50%;}
.dot-up{background:#4caf83;}.dot-near{background:#dc9543;}.dot-dn{background:#e05252;}
.charts2{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:20px;}
.charts1{margin-bottom:20px;}
.chart-card{background:#fff;border:1px solid rgba(17,19,24,0.09);border-radius:12px;padding:20px 20px 12px;}
.chart-ttl{font-size:10px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:#6f7683;margin-bottom:10px;}
.tbl-card{background:#fff;border:1px solid rgba(17,19,24,0.09);border-radius:12px;padding:20px;margin-bottom:16px;}
.sec-ttl{font-size:10px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:#6f7683;margin-bottom:12px;}
table{width:100%;border-collapse:collapse;}
th{font-size:10px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;color:#6f7683;text-align:left;padding:0 8px 8px 0;border-bottom:1px solid rgba(17,19,24,0.09);}
td{font-size:12px;color:#303743;padding:8px 8px 8px 0;border-bottom:1px solid rgba(17,19,24,0.05);vertical-align:top;line-height:1.5;}
td.sm{font-size:11px;color:#6f7683;}
tr:last-child td{border-bottom:0;}
.tag{display:inline-block;padding:2px 7px;border-radius:999px;font-size:10px;font-weight:600;}
.tag-buy{background:rgba(76,175,131,.12);color:#2e7d5b;}
.tag-hold{background:rgba(220,149,67,.14);color:#8a5a1f;}
.tag-sell{background:rgba(224,82,82,.10);color:#b03030;}
.check3{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:20px;}
.ck{background:#fff;border:1px solid rgba(17,19,24,0.09);border-radius:12px;padding:14px 16px;}
.ck-lbl{font-size:10px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:#6f7683;margin-bottom:4px;}
.ck-val{font-size:13px;font-weight:600;color:#111318;}
.empty{color:#b0b8c1;font-size:12px;padding:8px 0;}
.global-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px;margin-bottom:20px;}
.g-card{background:#fff;border:1px solid rgba(17,19,24,0.09);border-radius:10px;padding:12px 14px;}
.g-name{font-size:10px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:#6f7683;margin-bottom:4px;}
.g-val{font-size:16px;font-weight:700;letter-spacing:-.02em;}
.g-val.up{color:#e05252;}.g-val.dn{color:#4caf83;}
.top-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:20px;}
@media(max-width:768px){.charts2,.top-grid,.check3{grid-template-columns:1fr;}.metrics{grid-template-columns:repeat(2,1fr);}}
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


def _fig_html(fig: go.Figure, first: bool = False) -> str:
    return fig.to_html(
        include_plotlyjs=first,
        full_html=False,
        config={"displayModeBar": False, "responsive": True},
    )


def _wrap(title: str, eyebrow: str, date_str: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)}</title>
<style>{_CSS}</style>
</head>
<body>
<div class="db">
<div class="hdr">
  <p class="hdr-eye">{escape(eyebrow)}</p>
  <h1 class="hdr-title">{escape(title)}</h1>
  <p class="hdr-sub">{escape(date_str)}</p>
</div>
{body}
</div>
</body>
</html>"""


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
    news = flows.get("news", [])

    name = basics.get("name", "")
    parts = []
    is_first_chart = True

    # ── 핵심 지표 카드 ─────────────────────────────────────────
    price = basics.get("price", "—")
    change = basics.get("change_pct", "—")
    turnover = basics.get("turnover_krw_billion")
    turnover_str = f"{int(turnover):,}억" if turnover else "—"
    mktcap = basics.get("market_cap", "—")
    per = basics.get("per", "—")
    pbr = basics.get("pbr", "—")
    roe = basics.get("roe", "—")

    chg_cls = _sign_class(str(change))
    cards_html = f"""
<div class="metrics">
  <div class="card"><div class="card-lbl">현재가</div><div class="card-val">{escape(str(price))}</div></div>
  <div class="card"><div class="card-lbl">등락률</div><div class="card-val {chg_cls}">{escape(str(change))}</div></div>
  <div class="card"><div class="card-lbl">거래대금</div><div class="card-val">{turnover_str}</div></div>
  <div class="card"><div class="card-lbl">시가총액</div><div class="card-val">{escape(str(mktcap))}</div></div>
  <div class="card"><div class="card-lbl">PER</div><div class="card-val">{escape(str(per))}</div><div class="card-sub">PBR {escape(str(pbr))} | ROE {escape(str(roe))}</div></div>
</div>"""
    parts.append(cards_html)

    # ── 이동평균선 배지 ────────────────────────────────────────
    ma = basics.get("ma_position", {})
    badges = ""
    for label, key in [("5일선", "ma5"), ("20일선", "ma20"), ("60일선", "ma60")]:
        val = ma.get(key) or "—"
        dot = _ma_dot(val)
        badges += f'<span class="badge"><span class="dot dot-{dot}"></span>{label} {escape(str(val))}</span>'
    parts.append(f'<div class="ma-row">{badges}</div>')

    # ── 재무 차트 + 수급 차트 ────────────────────────────────────
    fin_quarters = [r.get("quarter", "") for r in financials]
    fin_sales = [_parse_fin_amount(r.get("sales")) for r in financials]
    fin_op = [_parse_fin_amount(r.get("op_income")) for r in financials]
    fin_net = [_parse_fin_amount(r.get("net_income")) for r in financials]

    fin_fig = go.Figure(layout=dict(**_PLOTLY_LAYOUT, height=240, barmode="group"))
    if any(v is not None for v in fin_sales):
        fin_fig.add_trace(go.Bar(name="매출", x=fin_quarters, y=fin_sales, marker_color="rgba(111,140,241,0.7)", width=0.25))
        fin_fig.add_trace(go.Bar(name="영업이익", x=fin_quarters, y=fin_op, marker_color=_BLUE, width=0.25))
        fin_fig.add_trace(go.Bar(name="순이익", x=fin_quarters, y=fin_net, marker_color="rgba(76,175,131,0.8)", width=0.25))
    fin_fig.update_yaxes(ticksuffix="조")

    foreign_num = _parse_flow_num(flows.get("foreign_20d"))
    institution_num = _parse_flow_num(flows.get("institution_20d"))
    flow_fig = go.Figure(layout=dict(**_PLOTLY_LAYOUT, height=240))
    flow_names = ["외국인", "기관"]
    flow_vals = [foreign_num or 0, institution_num or 0]
    flow_colors = [_RED if v >= 0 else _GREEN for v in flow_vals]
    flow_fig.add_trace(go.Bar(
        x=flow_names, y=flow_vals,
        marker_color=flow_colors,
        showlegend=False,
        text=[f"{int(v):+,}주" if v else "—" for v in flow_vals],
        textposition="outside",
    ))
    flow_fig.update_yaxes(ticksuffix="주")

    fin_html = _fig_html(fin_fig, first=is_first_chart)
    is_first_chart = False
    flow_html = _fig_html(flow_fig, first=False)

    parts.append(f"""
<div class="charts2">
  <div class="chart-card"><div class="chart-ttl">분기별 재무 요약 (조원)</div>{fin_html}</div>
  <div class="chart-card"><div class="chart-ttl">외국인·기관 20일 누적 수급</div>{flow_html}</div>
</div>""")

    # ── 추가 체크 ────────────────────────────────────────────────
    consensus = short_selling.get("consensus_target_price", "—")
    major = disclosures.get("major_shareholder_ratio", "—")
    risks = disclosures.get("risk_flags", [])
    risk_str = ", ".join(risks) if risks else "—"
    parts.append(f"""
<div class="check3">
  <div class="ck"><div class="ck-lbl">컨센서스 목표가</div><div class="ck-val">{escape(str(consensus or '—'))}</div></div>
  <div class="ck"><div class="ck-lbl">대주주 지분율</div><div class="ck-val">{escape(str(major or '—'))}</div></div>
  <div class="ck"><div class="ck-lbl">리스크 체크</div><div class="ck-val">{escape(risk_str)}</div></div>
</div>""")

    # ── 공시 ─────────────────────────────────────────────────────
    disc_list = disclosures.get("disclosures", [])
    disc_rows = "".join(f"<tr><td>{escape(d)}</td></tr>" for d in disc_list) if disc_list else '<tr><td class="empty">데이터 없음</td></tr>'
    parts.append(f"""
<div class="tbl-card">
  <div class="sec-ttl">최근 공시</div>
  <table><thead><tr><th>내용</th></tr></thead><tbody>{disc_rows}</tbody></table>
</div>""")

    # ── 최근 뉴스 ────────────────────────────────────────────────
    news_rows = "".join(f"<tr><td>{escape(n)}</td></tr>" for n in news) if news else '<tr><td class="empty">데이터 없음</td></tr>'
    parts.append(f"""
<div class="tbl-card">
  <div class="sec-ttl">최근 뉴스</div>
  <table><thead><tr><th>제목</th></tr></thead><tbody>{news_rows}</tbody></table>
</div>""")

    # ── 네이버 리포트 ────────────────────────────────────────────
    if naver_reports:
        nr_rows = ""
        for line in naver_reports:
            parts_line = line.split(" | ")
            title_part = escape(parts_line[0])
            meta_part = escape(" | ".join(parts_line[1:])) if len(parts_line) > 1 else ""
            tag = _opinion_tag(line)
            nr_rows += f"<tr><td>{title_part} {tag}</td><td class='sm'>{meta_part}</td></tr>"
        parts.append(f"""
<div class="tbl-card">
  <div class="sec-ttl">네이버 리포트</div>
  <table><thead><tr><th style="width:70%">제목</th><th>증권사 / 의견 / 목표가</th></tr></thead><tbody>{nr_rows}</tbody></table>
</div>""")

    # ── fnguide 리포트 ────────────────────────────────────────────
    if reports:
        rpt_rows = ""
        for r in reports:
            title = escape(r.get("title", ""))
            broker = escape(r.get("broker", ""))
            date_str = escape(r.get("date", ""))
            summary = escape(r.get("summary", ""))
            rpt_rows += f"<tr><td><div>{title}</div><div class='sm'>{summary}</div></td><td class='sm'>{broker}<br>{date_str}</td></tr>"
        report_date = payload.get("report_date", "")
        parts.append(f"""
<div class="tbl-card">
  <div class="sec-ttl">fnguide 리포트 ({escape(report_date)})</div>
  <table><thead><tr><th style="width:75%">제목 / 요약</th><th>증권사</th></tr></thead><tbody>{rpt_rows}</tbody></table>
</div>""")

    return _wrap(
        title=name,
        eyebrow="개별 종목 분석",
        date_str=payload.get("target_date", ""),
        body="\n".join(parts),
    )


# ══════════════════════════════════════════════════════════════
# 2. 시황 브리핑 대시보드
# ══════════════════════════════════════════════════════════════

def build_market_dashboard(payload: dict) -> str:
    indices = payload.get("indices", {})
    global_macro = payload.get("global_macro", {})
    investor_flows = payload.get("investor_flows", {})
    leaders = payload.get("leaders", [])
    disclosures = payload.get("disclosures", [])

    parts = []
    is_first_chart = True

    # ── 지수 카드 ────────────────────────────────────────────────
    kospi = indices.get("kospi", {})
    kosdaq = indices.get("kosdaq", {})
    idx_html = '<div class="metrics">'
    for label, idx in [("코스피", kospi), ("코스닥", kosdaq)]:
        close = idx.get("close", "—")
        chg = idx.get("change_pct", "—")
        tvr = idx.get("turnover_trillion_krw", "—")
        pt = idx.get("change_points", "—")
        cls = _sign_class(str(chg))
        idx_html += f"""<div class="card">
  <div class="card-lbl">{label}</div>
  <div class="card-val {cls}">{escape(str(close))}</div>
  <div class="card-sub">등락 {escape(str(chg))}% | {escape(str(pt))}pt | 거래대금 {escape(str(tvr))}조</div>
</div>"""
    idx_html += "</div>"
    parts.append(idx_html)

    # ── 글로벌 지표 카드 ─────────────────────────────────────────
    global_items = [
        ("다우", "dow"), ("S&P500", "sp500"), ("나스닥", "nasdaq"),
        ("달러/원", "usdkrw"), ("미10년물", "us10y"), ("WTI", "wti"),
        ("상해", "shanghai"),
    ]
    g_html = '<div class="global-grid">'
    for label, key in global_items:
        val = global_macro.get(key, "—")
        cls = _sign_class(str(val))
        g_html += f'<div class="g-card"><div class="g-name">{label}</div><div class="g-val {cls}">{escape(str(val or "—"))}</div></div>'
    g_html += "</div>"
    parts.append(g_html)

    # ── 거래대금 상위 차트 + 수급 차트 ──────────────────────────
    leader_names = [item.get("name", "") for item in leaders[:10]]
    leader_tvr = []
    for item in leaders[:10]:
        t = item.get("turnover_krw_billion")
        try:
            leader_tvr.append(float(str(t).replace(",", "")) if t else 0)
        except Exception:
            leader_tvr.append(0)

    vol_fig = go.Figure(layout=dict(**_PLOTLY_LAYOUT, height=300))
    if leader_names:
        vol_fig.add_trace(go.Bar(
            x=leader_tvr[::-1], y=leader_names[::-1],
            orientation="h",
            marker_color=_BLUE,
            showlegend=False,
            text=[f"{v:,.0f}억" for v in leader_tvr[::-1]],
            textposition="outside",
        ))
    vol_fig.update_layout(margin=dict(l=0, r=60, t=8, b=0))
    vol_fig.update_xaxes(ticksuffix="억")

    summary = investor_flows.get("summary", {})
    flow_names = ["외국인", "기관", "개인"]
    flow_vals_raw = [summary.get("foreign"), summary.get("institution"), summary.get("retail")]
    flow_nums = []
    for v in flow_vals_raw:
        try:
            flow_nums.append(float(str(v).replace(",", "")) if v not in (None, "—", "연결 예정") else 0)
        except Exception:
            flow_nums.append(0)
    flow_colors = [_RED if v >= 0 else _GREEN for v in flow_nums]

    sup_fig = go.Figure(layout=dict(**_PLOTLY_LAYOUT, height=300))
    sup_fig.add_trace(go.Bar(
        x=flow_names, y=flow_nums,
        marker_color=flow_colors,
        showlegend=False,
        text=[f"{v:+,.0f}억" if v else "—" for v in flow_nums],
        textposition="outside",
    ))
    sup_fig.update_yaxes(ticksuffix="억")

    vol_html = _fig_html(vol_fig, first=is_first_chart)
    is_first_chart = False
    sup_html = _fig_html(sup_fig, first=False)

    parts.append(f"""
<div class="charts2">
  <div class="chart-card"><div class="chart-ttl">거래대금 상위 (억원)</div>{vol_html}</div>
  <div class="chart-card"><div class="chart-ttl">외국인·기관·개인 수급 요약 (억원)</div>{sup_html}</div>
</div>""")

    # ── 외국인/기관 순매수 상위 ──────────────────────────────────
    fb = investor_flows.get("foreign_top_buy", [])
    fs = investor_flows.get("foreign_top_sell", [])
    ib = investor_flows.get("institution_top_buy", [])
    is_ = investor_flows.get("institution_top_sell", [])

    def _flow_table(buy_list: list, sell_list: list, label: str) -> str:
        buy_rows = "".join(f"<tr><td>▲ {escape(str(x))}</td></tr>" for x in buy_list) or '<tr><td class="empty">—</td></tr>'
        sell_rows = "".join(f"<tr><td>▼ {escape(str(x))}</td></tr>" for x in sell_list) or '<tr><td class="empty">—</td></tr>'
        return f"""<div class="tbl-card">
  <div class="sec-ttl">{label} 순매수/순매도 상위</div>
  <table><thead><tr><th>순매수</th></tr></thead><tbody>{buy_rows}</tbody></table>
  <table style="margin-top:10px"><thead><tr><th>순매도</th></tr></thead><tbody>{sell_rows}</tbody></table>
</div>"""

    parts.append(f'<div class="top-grid">{_flow_table(fb, fs, "외국인")}{_flow_table(ib, is_, "기관")}</div>')

    # ── 공시 ─────────────────────────────────────────────────────
    disc_rows = "".join(f"<tr><td>{escape(str(d))}</td></tr>" for d in disclosures) if disclosures else '<tr><td class="empty">데이터 없음</td></tr>'
    parts.append(f"""
<div class="tbl-card">
  <div class="sec-ttl">주요 공시</div>
  <table><thead><tr><th>내용</th></tr></thead><tbody>{disc_rows}</tbody></table>
</div>""")

    return _wrap(
        title="시황 브리핑",
        eyebrow="Market Briefing",
        date_str=payload.get("target_date", ""),
        body="\n".join(parts),
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

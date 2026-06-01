from __future__ import annotations

from html import escape


def _fmt_pct(value: object) -> str:
    if value is None:
        return "-"
    try:
        return f"{float(value):+.2f}%"
    except (TypeError, ValueError):
        return str(value)


def _pct_class(value: object) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "flat"
    if number > 0:
        return "up"
    if number < 0:
        return "down"
    return "flat"


def _fmt_usd(value: object) -> str:
    if value is None:
        return "-"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if number >= 1_000_000_000_000:
        return f"${number / 1_000_000_000_000:.2f}T"
    if number >= 1_000_000_000:
        return f"${number / 1_000_000_000:.1f}B"
    if number >= 1_000_000:
        return f"${number / 1_000_000:.1f}M"
    if number >= 1:
        return f"${number:,.2f}"
    return f"${number:.6f}"


def _fmt_krw(value: object) -> str:
    if value is None:
        return "-"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if number >= 1_000_000_000_000:
        return f"{number / 1_000_000_000_000:.2f}조"
    if number >= 100_000_000:
        return f"{number / 100_000_000:.0f}억"
    return f"{number:,.0f}원"


def _series_values(rows: object) -> list[float]:
    values: list[float] = []
    if not isinstance(rows, (list, tuple)):
        return values
    for row in rows:
        if not isinstance(row, (list, tuple)) or len(row) < 2:
            continue
        try:
            values.append(float(row[1]))
        except (TypeError, ValueError):
            continue
    return values


def _series_change_pct(rows: object) -> float | None:
    values = _series_values(rows)
    if len(values) < 2 or values[0] == 0:
        return None
    return ((values[-1] / values[0]) - 1) * 100


def _sparkline_svg(rows: object, stroke: str = "#6f8cf1", fill: str = "rgba(111, 140, 241, 0.10)") -> str:
    values = _series_values(rows)
    if len(values) < 2:
        return '<div class="coin-chart-empty">차트 데이터 없음</div>'

    min_value = min(values)
    max_value = max(values)
    span = max(max_value - min_value, 0.0000001)
    sampled = values[-34:]
    bars = []
    for value in sampled:
        height = 18 + ((value - min_value) / span) * 62
        bars.append(f'<i style="height:{height:.1f}px"></i>')
    return f'<div class="coin-chart-bars" aria-label="chart">{"".join(bars)}</div>'


def _chart_card(title: str, chart: dict, series_key: str = "prices", value_label: str = "") -> str:
    rows = chart.get(series_key) if isinstance(chart, dict) else []
    values = _series_values(rows)
    change = _series_change_pct(rows)
    latest = values[-1] if values else None
    return f"""
    <div class="coin-chart-card">
      <div class="coin-chart-card__top">
        <div>
          <p class="coin-chart-card__label">{escape(title)}</p>
          <p class="coin-chart-card__value">{escape(value_label or _fmt_usd(latest))}</p>
        </div>
        <span class="{_pct_class(change)}">{escape(_fmt_pct(change))}</span>
      </div>
      {_sparkline_svg(rows)}
    </div>
    """


def _mini_data_row(label: str, value: str, sub: str = "", tone: str = "flat") -> str:
    return f"""
    <div class="coin-mini-row">
      <div><strong>{escape(label)}</strong><span>{escape(sub)}</span></div>
      <em class="{tone}">{escape(value)}</em>
    </div>
    """


def _metric(label: str, value: str, sub: str = "", tone: str = "flat") -> str:
    return f"""
    <div class="coin-metric">
      <div class="coin-metric__label">{escape(label)}</div>
      <div class="coin-metric__value {tone}">{escape(value)}</div>
      <div class="coin-metric__sub">{escape(sub)}</div>
    </div>
    """


def _coin_row(row: dict) -> str:
    return f"""
    <tr>
      <td>#{escape(str(row.get("market_cap_rank") or "-"))}</td>
      <td><strong>{escape(str(row.get("name") or "-"))}</strong><span>{escape(str(row.get("symbol") or "").upper())}</span></td>
      <td>{escape(_fmt_usd(row.get("current_price")))}</td>
      <td class="{_pct_class(row.get("price_change_percentage_24h"))}">{escape(_fmt_pct(row.get("price_change_percentage_24h")))}</td>
      <td>{escape(_fmt_usd(row.get("market_cap")))}</td>
    </tr>
    """


def _upbit_row(row: dict, rank: int) -> str:
    name = row.get("korean_name") or row.get("symbol") or row.get("market") or "-"
    market = row.get("market") or "-"
    warning = "주의" if row.get("warning") else ""
    return f"""
    <tr>
      <td>{rank}</td>
      <td><strong>{escape(str(name))}</strong><span>{escape(str(market))}</span></td>
      <td>{escape(_fmt_krw(row.get("trade_price")))}</td>
      <td class="{_pct_class(row.get("change_pct"))}">{escape(_fmt_pct(row.get("change_pct")))}</td>
      <td>{escape(_fmt_krw(row.get("acc_trade_price_24h")))}</td>
      <td>{escape(warning)}</td>
    </tr>
    """


def _protocol_row(row: dict, rank: int) -> str:
    chains = ", ".join((row.get("chains") or [])[:2])
    return f"""
    <tr>
      <td>{rank}</td>
      <td><strong>{escape(str(row.get("name") or "-"))}</strong><span>{escape(str(row.get("category") or "-"))}</span></td>
      <td>{escape(_fmt_usd(row.get("tvl")))}</td>
      <td class="{_pct_class(row.get("change_1d"))}">{escape(_fmt_pct(row.get("change_1d")))}</td>
      <td>{escape(chains or "-")}</td>
    </tr>
    """


def _fee_row(row: dict, rank: int) -> str:
    return f"""
    <tr>
      <td>{rank}</td>
      <td><strong>{escape(str(row.get("name") or "-"))}</strong><span>{escape(str(row.get("category") or "-"))}</span></td>
      <td>{escape(_fmt_usd(row.get("total24h")))}</td>
      <td>{escape(_fmt_usd(row.get("total7d")))}</td>
    </tr>
    """


def _category_card(row: dict) -> str:
    change = row.get("market_cap_change_24h")
    return f"""
    <div class="coin-sector">
      <div class="coin-sector__name">{escape(str(row.get("name") or "-"))}</div>
      <div class="coin-sector__change {_pct_class(change)}">{escape(_fmt_pct(change))}</div>
      <div class="coin-sector__sub">시총 {escape(_fmt_usd(row.get("market_cap")))}</div>
    </div>
    """


def build_coin_market_dashboard(payload: dict) -> str:
    global_market = payload.get("global_market", {})
    majors = payload.get("majors", {})
    btc = majors.get("bitcoin", {})
    eth = majors.get("ethereum", {})
    fear_greed = payload.get("fear_greed", {})
    regime = payload.get("regime", {})
    upbit_leaders = payload.get("upbit_leaders", [])
    top_coins = payload.get("top_coins", [])
    categories = payload.get("categories", [])
    charts = payload.get("charts", {})
    stablecoins = payload.get("stablecoins", {})
    top_protocols = payload.get("top_protocols", [])
    fees = payload.get("fees", {})

    cards = [
        _metric(
            "총 코인 시총",
            _fmt_usd(global_market.get("total_market_cap_usd")),
            f"24h {_fmt_pct(global_market.get('market_cap_change_24h_pct'))}",
            _pct_class(global_market.get("market_cap_change_24h_pct")),
        ),
        _metric("24h 거래대금", _fmt_usd(global_market.get("total_volume_usd")), "글로벌 전체"),
        _metric("BTC 도미넌스", _fmt_pct(global_market.get("btc_dominance")), "BTC 중심 장세 확인"),
        _metric("ETH/BTC", f"{float(payload.get('eth_btc_ratio')):.4f}" if payload.get("eth_btc_ratio") else "-", "ETH가 BTC보다 강한지"),
        _metric(
            "공포탐욕",
            str(fear_greed.get("value") or "-"),
            str(fear_greed.get("classification") or "-"),
        ),
        _metric(
            "스테이블코인",
            _fmt_usd(stablecoins.get("total_circulating_usd")),
            f"7d {_fmt_pct(stablecoins.get('change_7d_pct'))}",
            _pct_class(stablecoins.get("change_7d_pct")),
        ),
        _metric(
            "김치 프리미엄",
            _fmt_pct(payload.get("kimchi_premium_pct")),
            f"USD/KRW {payload.get('usdkrw') or '-'}",
            _pct_class(payload.get("kimchi_premium_pct")),
        ),
    ]

    major_cards = [
        _metric(
            "BTC",
            _fmt_usd(btc.get("current_price")),
            f"24h {_fmt_pct(btc.get('price_change_percentage_24h'))} · 7d {_fmt_pct(btc.get('price_change_percentage_7d_in_currency'))}",
            _pct_class(btc.get("price_change_percentage_24h")),
        ),
        _metric(
            "ETH",
            _fmt_usd(eth.get("current_price")),
            f"24h {_fmt_pct(eth.get('price_change_percentage_24h'))} · 7d {_fmt_pct(eth.get('price_change_percentage_7d_in_currency'))}",
            _pct_class(eth.get("price_change_percentage_24h")),
        ),
    ]

    upbit_rows = "".join(_upbit_row(row, idx + 1) for idx, row in enumerate(upbit_leaders[:8]))
    top_rows = "".join(_coin_row(row) for row in top_coins[:10])
    sector_cards = "".join(_category_card(row) for row in categories[:8])
    protocol_rows = "".join(_protocol_row(row, idx + 1) for idx, row in enumerate(top_protocols[:6]))
    fee_rows = "".join(_fee_row(row, idx + 1) for idx, row in enumerate((fees.get("protocols") or [])[:6]))
    stable_asset_rows = "".join(
        _mini_data_row(
            str(row.get("symbol") or row.get("name") or "-"),
            _fmt_usd(row.get("circulating_usd")),
            f"7d {_fmt_pct(row.get('change_7d_pct'))}",
            _pct_class(row.get("change_7d_pct")),
        )
        for row in (stablecoins.get("top_assets") or [])[:4]
    )
    stable_chain_rows = "".join(
        _mini_data_row(str(row.get("name") or "-"), _fmt_usd(row.get("circulating_usd")), "체인별 스테이블")
        for row in (stablecoins.get("top_chains") or [])[:4]
    )

    return f"""
    <style>
      .coin-market {{
        display: grid;
        gap: 12px;
        color: #111318;
        font-family: Inter, -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
      }}
      .coin-market * {{ box-sizing: border-box; }}
      .coin-market__head {{
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 12px;
        padding: 16px 18px;
        border: 1px solid rgba(17, 19, 24, 0.09);
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.62);
      }}
      .coin-market__eyebrow {{
        margin: 0 0 6px;
        color: #6f7683;
        font-size: 10px;
        font-weight: 800;
        letter-spacing: 0;
        text-transform: uppercase;
      }}
      .coin-market__title {{
        margin: 0;
        color: #111318;
        font-size: 22px;
        line-height: 1.16;
        font-weight: 800;
        letter-spacing: 0;
      }}
      .coin-market__time {{
        margin: 6px 0 0;
        color: #6f7683;
        font-size: 11px;
        line-height: 1.4;
      }}
      .coin-regime {{
        min-width: 144px;
        padding: 10px 12px;
        border: 1px solid rgba(139, 151, 232, 0.22);
        border-radius: 8px;
        background: rgba(139, 151, 232, 0.10);
      }}
      .coin-regime__label {{
        margin: 0 0 5px;
        color: #5868ce;
        font-size: 12px;
        font-weight: 800;
      }}
      .coin-regime__copy {{
        margin: 0;
        color: #5f6775;
        font-size: 11px;
        line-height: 1.45;
      }}
      .coin-metrics {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(132px, 1fr));
        gap: 8px;
      }}
      .coin-metric,
      .coin-panel,
      .coin-sector {{
        border: 1px solid rgba(17, 19, 24, 0.09);
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.62);
      }}
      .coin-metric {{
        min-height: 92px;
        padding: 13px 14px;
      }}
      .coin-metric__label {{
        margin-bottom: 8px;
        color: #6f7683;
        font-size: 10px;
        font-weight: 800;
        letter-spacing: 0;
      }}
      .coin-metric__value {{
        color: #111318;
        font-size: 18px;
        font-weight: 800;
        letter-spacing: 0;
      }}
      .coin-metric__sub {{
        margin-top: 5px;
        color: #6f7683;
        font-size: 11px;
        line-height: 1.35;
      }}
      .up {{ color: #b93d3d !important; }}
      .down {{ color: #2f7a55 !important; }}
      .flat {{ color: #303743 !important; }}
      .coin-grid-2 {{
        display: grid;
        grid-template-columns: 1fr 1.25fr;
        gap: 10px;
      }}
      .coin-panel {{
        overflow: hidden;
      }}
      .coin-panel__title {{
        margin: 0;
        padding: 13px 14px 10px;
        color: #111318;
        font-size: 13px;
        font-weight: 800;
        letter-spacing: 0;
        border-bottom: 1px solid rgba(17, 19, 24, 0.07);
      }}
      .coin-panel__body {{
        padding: 10px;
      }}
      .coin-major-grid {{
        display: grid;
        gap: 8px;
      }}
      .coin-chart-grid {{
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 8px;
      }}
      .coin-chart-card {{
        min-height: 138px;
        padding: 12px;
        border: 1px solid rgba(17, 19, 24, 0.09);
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.62);
      }}
      .coin-chart-card__top {{
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 8px;
        margin-bottom: 7px;
      }}
      .coin-chart-card__label {{
        margin: 0 0 4px;
        color: #6f7683;
        font-size: 10px;
        font-weight: 800;
      }}
      .coin-chart-card__value {{
        margin: 0;
        color: #111318;
        font-size: 14px;
        font-weight: 800;
      }}
      .coin-chart-card__top span {{
        font-size: 12px;
        font-weight: 800;
      }}
      .coin-chart-bars {{
        height: 88px;
        display: flex;
        align-items: flex-end;
        gap: 3px;
        padding-top: 8px;
        border-top: 1px solid rgba(17, 19, 24, 0.05);
      }}
      .coin-chart-bars i {{
        flex: 1 1 0;
        min-width: 2px;
        border-radius: 999px 999px 0 0;
        background: linear-gradient(180deg, rgba(111, 140, 241, 0.78), rgba(93, 177, 128, 0.50));
      }}
      .coin-chart-empty {{
        height: 88px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #8a929e;
        font-size: 11px;
      }}
      .coin-liquidity-grid {{
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 8px;
      }}
      .coin-mini-list {{
        display: grid;
        gap: 7px;
      }}
      .coin-mini-row {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
        padding: 9px 10px;
        border: 1px solid rgba(17, 19, 24, 0.07);
        border-radius: 8px;
        background: rgba(250, 247, 241, 0.72);
      }}
      .coin-mini-row strong {{
        display: block;
        color: #111318;
        font-size: 11px;
      }}
      .coin-mini-row span {{
        display: block;
        margin-top: 3px;
        color: #8a929e;
        font-size: 10px;
      }}
      .coin-mini-row em {{
        flex-shrink: 0;
        color: #303743;
        font-style: normal;
        font-size: 11px;
        font-weight: 800;
        text-align: right;
      }}
      .coin-table-wrap {{
        overflow-x: auto;
      }}
      .coin-table {{
        width: 100%;
        min-width: 0;
        table-layout: fixed;
        border-collapse: collapse;
      }}
      .coin-table th {{
        padding: 0 8px 8px 0;
        border-bottom: 1px solid rgba(17, 19, 24, 0.09);
        color: #6f7683;
        font-size: 10px;
        font-weight: 800;
        text-align: left;
        overflow-wrap: anywhere;
      }}
      .coin-table td {{
        padding: 9px 8px 9px 0;
        border-bottom: 1px solid rgba(17, 19, 24, 0.05);
        color: #303743;
        font-size: 11px;
        line-height: 1.35;
        vertical-align: top;
        overflow-wrap: anywhere;
      }}
      .coin-table tr:last-child td {{ border-bottom: 0; }}
      .coin-table strong {{
        display: block;
        color: #111318;
        font-size: 11px;
      }}
      .coin-table span {{
        display: block;
        margin-top: 3px;
        color: #8a929e;
        font-size: 10px;
      }}
      .coin-sectors {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
        gap: 8px;
      }}
      .coin-sector {{
        padding: 12px;
      }}
      .coin-sector__name {{
        min-height: 30px;
        color: #111318;
        font-size: 11px;
        font-weight: 800;
        line-height: 1.35;
      }}
      .coin-sector__change {{
        margin-top: 8px;
        font-size: 15px;
        font-weight: 800;
      }}
      .coin-sector__sub {{
        margin-top: 4px;
        color: #6f7683;
        font-size: 10px;
      }}
      .coin-questions {{
        margin: 0;
        padding: 0;
        list-style: none;
        display: grid;
        gap: 7px;
      }}
      .coin-questions li {{
        padding: 9px 10px;
        border: 1px solid rgba(220, 149, 67, 0.20);
        border-radius: 8px;
        background: rgba(220, 149, 67, 0.08);
        color: #755124;
        font-size: 11px;
        line-height: 1.45;
      }}
      @media(max-width: 980px) {{
        .coin-market__head,
        .coin-grid-2,
        .coin-chart-grid,
        .coin-liquidity-grid {{
          grid-template-columns: 1fr;
          display: grid;
        }}
      }}
    </style>
    <section class="coin-market">
      <div class="coin-market__head">
        <div>
          <p class="coin-market__eyebrow">Coin Market Dashboard</p>
          <h2 class="coin-market__title">오늘 코인 시장을 먼저 읽습니다</h2>
          <p class="coin-market__time">{escape(str(payload.get("target_datetime") or ""))}</p>
        </div>
        <div class="coin-regime">
          <p class="coin-regime__label">{escape(str(regime.get("label") or "관망"))}</p>
          <p class="coin-regime__copy">{escape(str(regime.get("message") or ""))}</p>
        </div>
      </div>

      <div class="coin-metrics">
        {"".join(cards)}
      </div>

      <div class="coin-panel">
        <h3 class="coin-panel__title">BTC / ETH / 도미넌스 30일 흐름</h3>
        <div class="coin-panel__body coin-chart-grid">
          {_chart_card("BTC 가격", charts.get("bitcoin") or {})}
          {_chart_card("ETH 가격", charts.get("ethereum") or {})}
          {_chart_card("BTC 도미넌스 (근사)", charts.get("dominance") or {}, value_label=f"{float(global_market.get('btc_dominance') or 0):.1f}%" if global_market.get('btc_dominance') else "-")}
        </div>
      </div>

      <div class="coin-grid-2">
        <div class="coin-panel">
          <h3 class="coin-panel__title">BTC / ETH 기준 자산</h3>
          <div class="coin-panel__body coin-major-grid">
            {"".join(major_cards)}
          </div>
        </div>
        <div class="coin-panel">
          <h3 class="coin-panel__title">업비트 KRW 거래대금 상위</h3>
          <div class="coin-panel__body coin-table-wrap">
            <table class="coin-table">
              <thead><tr><th>#</th><th>코인</th><th>가격</th><th>24h</th><th>거래대금</th><th>주의</th></tr></thead>
              <tbody>{upbit_rows or '<tr><td colspan="6">데이터 없음</td></tr>'}</tbody>
            </table>
          </div>
        </div>
      </div>

      <div class="coin-panel">
        <h3 class="coin-panel__title">글로벌 시총 상위</h3>
        <div class="coin-panel__body coin-table-wrap">
          <table class="coin-table">
            <thead><tr><th>순위</th><th>코인</th><th>가격</th><th>24h</th><th>시총</th></tr></thead>
            <tbody>{top_rows or '<tr><td colspan="5">데이터 없음</td></tr>'}</tbody>
          </table>
        </div>
      </div>

      <div class="coin-panel">
        <h3 class="coin-panel__title">섹터 온도</h3>
        <div class="coin-panel__body coin-sectors">
          {sector_cards or '<div class="coin-sector">데이터 없음</div>'}
        </div>
      </div>

      <div class="coin-grid-2">
        <div class="coin-panel">
          <h3 class="coin-panel__title">스테이블코인 유동성</h3>
          <div class="coin-panel__body coin-liquidity-grid">
            <div class="coin-mini-list">{stable_asset_rows or '<div class="coin-chart-empty">자산 데이터 없음</div>'}</div>
            <div class="coin-mini-list">{stable_chain_rows or '<div class="coin-chart-empty">체인 데이터 없음</div>'}</div>
          </div>
        </div>
        <div class="coin-panel">
          <h3 class="coin-panel__title">프로토콜 수수료 상위</h3>
          <div class="coin-panel__body coin-table-wrap">
            <table class="coin-table">
              <thead><tr><th>#</th><th>프로토콜</th><th>24h</th><th>7d</th></tr></thead>
              <tbody>{fee_rows or '<tr><td colspan="4">데이터 없음</td></tr>'}</tbody>
            </table>
          </div>
        </div>
      </div>

      <div class="coin-panel">
        <h3 class="coin-panel__title">DeFi TVL 상위</h3>
        <div class="coin-panel__body coin-table-wrap">
          <table class="coin-table">
            <thead><tr><th>#</th><th>프로토콜</th><th>TVL</th><th>24h</th><th>체인</th></tr></thead>
            <tbody>{protocol_rows or '<tr><td colspan="5">데이터 없음</td></tr>'}</tbody>
          </table>
        </div>
      </div>

      <div class="coin-panel">
        <h3 class="coin-panel__title">오늘의 공부 질문</h3>
        <div class="coin-panel__body">
          <ul class="coin-questions">
            <li>BTC가 오르는 장인지, 알트까지 퍼지는 장인지 도미넌스로 확인하기</li>
            <li>업비트 거래대금 상위와 글로벌 시총 상위가 같은지 비교하기</li>
            <li>김치 프리미엄이 높다면 국내 수급 과열인지 의심하기</li>
          </ul>
        </div>
      </div>
    </section>
    """


def build_coin_market_empty_state() -> str:
    return """
    <div class="cat-output-shell">
      <div class="cat-output-placeholder">
        시황 불러오기 버튼을 누르면 BTC, ETH, 도미넌스, 공포탐욕지수, 업비트 거래대금, 김치 프리미엄이 여기에 표시됩니다.
      </div>
    </div>
    """


def _fmt_number(value: object) -> str:
    if value is None:
        return "-"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if number >= 1_000_000_000:
        return f"{number / 1_000_000_000:.2f}B"
    if number >= 1_000_000:
        return f"{number / 1_000_000:.2f}M"
    return f"{number:,.0f}"


def _detail_item(label: str, value: str, help_text: str = "") -> str:
    return f"""
    <div class="coin-detail-item">
      <div class="coin-detail-item__label">{escape(label)}</div>
      <div class="coin-detail-item__value">{escape(value)}</div>
      <div class="coin-detail-item__help">{escape(help_text)}</div>
    </div>
    """


def _chip(label: str) -> str:
    return f'<span class="coin-detail-chip">{escape(label)}</span>'


def build_coin_detail_dashboard(payload: dict) -> str:
    basics = payload.get("basics", {})
    market = payload.get("market", {})
    supply = payload.get("supply", {})
    upbit = payload.get("upbit", {})
    risk = payload.get("risk", {})
    project = payload.get("project", {})
    community = payload.get("community", {})
    developer = payload.get("developer", {})
    price_chart = payload.get("price_chart", {})
    defi_protocol = payload.get("defi_protocol", {})
    futures = payload.get("futures", {})
    risk_flags = payload.get("risk_flags", [])

    categories = "".join(_chip(item) for item in (project.get("categories") or [])[:6])
    description = project.get("description") or "프로젝트 설명 데이터가 아직 없습니다."

    metrics = [
        _metric("현재가", _fmt_usd(market.get("current_price_usd")), f"KRW {_fmt_krw(market.get('current_price_krw'))}"),
        _metric("24h", _fmt_pct(market.get("change_24h_pct")), "단기 방향", _pct_class(market.get("change_24h_pct"))),
        _metric("7d", _fmt_pct(market.get("change_7d_pct")), "주간 흐름", _pct_class(market.get("change_7d_pct"))),
        _metric("30d", _fmt_pct(market.get("change_30d_pct")), "월간 흐름", _pct_class(market.get("change_30d_pct"))),
        _metric("시가총액", _fmt_usd(market.get("market_cap_usd")), "코인의 전체 크기"),
        _metric("FDV", _fmt_usd(market.get("fdv_usd")), f"FDV/MC {risk.get('fdv_to_mcap') or '-'}"),
        _metric("24h 거래량", _fmt_usd(market.get("volume_usd")), f"Vol/MC {risk.get('volume_to_mcap') or '-'}"),
        _metric("ATH 대비", _fmt_pct(market.get("ath_change_pct")), f"ATH {_fmt_usd(market.get('ath_usd'))}", _pct_class(market.get("ath_change_pct"))),
    ]

    supply_items = [
        _detail_item("유통량", _fmt_number(supply.get("circulating_supply")), "현재 시장에 풀린 물량"),
        _detail_item("총공급량", _fmt_number(supply.get("total_supply")), "현재까지 발행된 전체 물량"),
        _detail_item("최대공급량", _fmt_number(supply.get("max_supply")), "최종적으로 발행될 수 있는 상한"),
    ]

    if upbit.get("is_listed"):
        upbit_body = f"""
        <div class="coin-detail-upbit">
          {_detail_item("마켓", str(upbit.get("market") or "-"), str(upbit.get("korean_name") or ""))}
          {_detail_item("현재가", _fmt_krw(upbit.get("trade_price")), "업비트 KRW 기준")}
          {_detail_item("24h", _fmt_pct(upbit.get("change_pct")), "국내 거래소 등락")}
          {_detail_item("거래대금", _fmt_krw(upbit.get("acc_trade_price_24h")), "24시간 누적")}
          {_detail_item("김치 프리미엄", _fmt_pct(upbit.get("kimchi_premium_pct")), f"USD/KRW {payload.get('usdkrw') or '-'}")}
          {_detail_item("유의/주의", "주의" if upbit.get("warning") else "없음", "업비트 market_event 기준")}
        </div>
        """
    else:
        upbit_body = """
        <div class="coin-detail-empty">업비트 KRW 마켓 상장 정보가 없거나 조회에 실패했습니다.</div>
        """

    risk_items = [
        _detail_item("FDV/시총", str(risk.get("fdv_to_mcap") or "-"), "높을수록 향후 희석 위험을 더 확인"),
        _detail_item("거래량/시총", str(risk.get("volume_to_mcap") or "-"), "단기 관심과 회전율 확인"),
        _detail_item("김치 프리미엄", _fmt_pct(upbit.get("kimchi_premium_pct")), "국내 가격이 글로벌보다 비싼지 확인"),
        _detail_item("ATH 대비", _fmt_pct(market.get("ath_change_pct")), "고점 대비 현재 위치"),
    ]

    risk_flag_items = [
        f"""
        <div class="coin-risk-flag coin-risk-flag--{escape(str(item.get("level") or "warn"))}">
          <strong>{escape(str(item.get("label") or "-"))}</strong>
          <span>{escape(str(item.get("message") or ""))}</span>
        </div>
        """
        for item in risk_flags
    ]

    community_items = [
        _detail_item("Twitter", _fmt_number(community.get("twitter_followers")), "팔로워 수"),
        _detail_item("Reddit", _fmt_number(community.get("reddit_subscribers")), "구독자 수"),
        _detail_item("GitHub stars", _fmt_number(developer.get("stars")), "개발 관심도"),
        _detail_item("4주 commits", _fmt_number(developer.get("commit_count_4_weeks")), "최근 개발 활동"),
    ]

    links = []
    if project.get("homepage"):
        links.append(f'<a href="{escape(project["homepage"])}" target="_blank">홈페이지</a>')
    if project.get("whitepaper"):
        links.append(f'<a href="{escape(project["whitepaper"])}" target="_blank">백서</a>')
    if project.get("twitter"):
        links.append(f'<span>@{escape(project["twitter"])}</span>')

    if defi_protocol:
        fees_items = ""
        if defi_protocol.get("fees_24h") is not None:
            fees_items = (
                _detail_item("24h 수수료", _fmt_usd(defi_protocol.get("fees_24h")), "프로토콜 수수료 수입")
                + _detail_item("7d 수수료", _fmt_usd(defi_protocol.get("fees_7d")), "7일 누적")
            )
        defi_body = f"""
        <div class="coin-detail-upbit">
          {_detail_item("프로토콜", str(defi_protocol.get("name") or "-"), str(defi_protocol.get("category") or ""))}
          {_detail_item("TVL", _fmt_usd(defi_protocol.get("tvl")), "DefiLlama 기준")}
          {_detail_item("24h TVL", _fmt_pct(defi_protocol.get("change_1d")), "단기 예치금 변화")}
          {_detail_item("7d TVL", _fmt_pct(defi_protocol.get("change_7d")), "주간 예치금 변화")}
          {fees_items}
        </div>
        """
    else:
        defi_body = """
        <div class="coin-detail-empty">DefiLlama에서 이 코인과 직접 매핑되는 프로토콜을 찾지 못했습니다.</div>
        """

    if futures.get("is_available"):
        futures_body = f"""
        <div class="coin-detail-upbit">
          {_detail_item("마켓", str(futures.get("symbol") or "-"), "Binance USD-M")}
          {_detail_item("최근 펀딩비", _fmt_pct(futures.get("latest_funding_rate_pct")), "양수면 롱이 숏에게 비용 지불")}
          {_detail_item("연율 환산", _fmt_pct(futures.get("annualized_funding_pct")), "최근 평균 펀딩비 단순 환산")}
          {_detail_item("OI 변화", _fmt_pct(futures.get("open_interest_change_24h_pct")), "24시간 미결제약정 변화")}
          {_detail_item("OI 규모", _fmt_usd(futures.get("open_interest_value_usd")), "선물 포지션 명목 규모")}
          {_detail_item("상태", str(futures.get("warning") or "-"), "학습용 과열 체크")}
        </div>
        """
    else:
        futures_body = """
        <div class="coin-detail-empty">Binance USD-M 선물 데이터를 찾지 못했습니다.</div>
        """

    return f"""
    <style>
      .coin-detail {{
        display: grid;
        gap: 12px;
        color: #111318;
        font-family: Inter, -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
      }}
      .coin-detail * {{ box-sizing: border-box; }}
      .coin-detail-head,
      .coin-detail-panel,
      .coin-detail-item {{
        border: 1px solid rgba(17, 19, 24, 0.09);
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.62);
      }}
      .coin-detail-head {{
        display: grid;
        grid-template-columns: 1fr auto;
        gap: 14px;
        align-items: start;
        padding: 17px 18px;
      }}
      .coin-detail-head__eyebrow {{
        margin: 0 0 6px;
        color: #6f7683;
        font-size: 10px;
        font-weight: 800;
        text-transform: uppercase;
      }}
      .coin-detail-head__title {{
        margin: 0;
        font-size: 23px;
        line-height: 1.16;
        font-weight: 800;
      }}
      .coin-detail-rank {{
        padding: 9px 11px;
        border-radius: 8px;
        background: rgba(139, 151, 232, 0.12);
        color: #5868ce;
        font-size: 12px;
        font-weight: 800;
      }}
      .coin-detail-chips {{
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        margin-top: 11px;
      }}
      .coin-detail-chip {{
        display: inline-flex;
        align-items: center;
        height: 22px;
        padding: 0 9px;
        border-radius: 999px;
        background: rgba(93, 177, 128, 0.13);
        color: #2f7a55;
        font-size: 10px;
        font-weight: 800;
      }}
      .coin-detail-metrics {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(132px, 1fr));
        gap: 8px;
      }}
      .coin-detail-chart {{
        padding: 10px;
      }}
      .coin-chart-card {{
        min-height: 138px;
        padding: 12px;
        border: 1px solid rgba(17, 19, 24, 0.09);
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.62);
      }}
      .coin-chart-card__top {{
        display: flex;
        justify-content: space-between;
        gap: 8px;
        margin-bottom: 7px;
      }}
      .coin-chart-card__label {{
        margin: 0 0 4px;
        color: #6f7683;
        font-size: 10px;
        font-weight: 800;
      }}
      .coin-chart-card__value {{
        margin: 0;
        color: #111318;
        font-size: 14px;
        font-weight: 800;
      }}
      .coin-chart-card__top span {{
        font-size: 12px;
        font-weight: 800;
      }}
      .coin-chart-bars {{
        height: 88px;
        display: flex;
        align-items: flex-end;
        gap: 3px;
        padding-top: 8px;
        border-top: 1px solid rgba(17, 19, 24, 0.05);
      }}
      .coin-chart-bars i {{
        flex: 1 1 0;
        min-width: 2px;
        border-radius: 999px 999px 0 0;
        background: linear-gradient(180deg, rgba(111, 140, 241, 0.78), rgba(93, 177, 128, 0.50));
      }}
      .coin-chart-empty {{
        height: 88px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #8a929e;
        font-size: 11px;
      }}
      .coin-detail .coin-metric {{
        min-height: 92px;
        padding: 13px 14px;
        border: 1px solid rgba(17, 19, 24, 0.09);
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.62);
      }}
      .coin-detail .coin-metric__label {{
        margin-bottom: 8px;
        color: #6f7683;
        font-size: 10px;
        font-weight: 800;
      }}
      .coin-detail .coin-metric__value {{
        color: #111318;
        font-size: 18px;
        font-weight: 800;
        letter-spacing: 0;
      }}
      .coin-detail .coin-metric__sub {{
        margin-top: 5px;
        color: #6f7683;
        font-size: 11px;
        line-height: 1.35;
      }}
      .coin-detail .up {{ color: #b93d3d !important; }}
      .coin-detail .down {{ color: #2f7a55 !important; }}
      .coin-detail .flat {{ color: #303743 !important; }}
      .coin-detail-grid {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
      }}
      .coin-detail-panel {{
        overflow: hidden;
      }}
      .coin-detail-panel__title {{
        margin: 0;
        padding: 13px 14px 10px;
        border-bottom: 1px solid rgba(17, 19, 24, 0.07);
        font-size: 13px;
        font-weight: 800;
      }}
      .coin-detail-panel__body {{
        display: grid;
        gap: 8px;
        padding: 10px;
      }}
      .coin-detail-panel__copy {{
        margin: 0;
        padding: 12px 14px 14px;
        color: #303743;
        font-size: 12px;
        line-height: 1.65;
        word-break: keep-all;
      }}
      .coin-detail-item {{
        padding: 11px 12px;
      }}
      .coin-detail-item__label {{
        margin-bottom: 5px;
        color: #6f7683;
        font-size: 10px;
        font-weight: 800;
      }}
      .coin-detail-item__value {{
        color: #111318;
        font-size: 14px;
        font-weight: 800;
        overflow-wrap: anywhere;
      }}
      .coin-detail-item__help {{
        margin-top: 5px;
        color: #6f7683;
        font-size: 10px;
        line-height: 1.35;
      }}
      .coin-detail-upbit {{
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 8px;
      }}
      .coin-detail-empty {{
        padding: 18px;
        color: #6f7683;
        font-size: 12px;
        text-align: center;
      }}
      .coin-risk-flags {{
        display: grid;
        gap: 8px;
      }}
      .coin-risk-flag {{
        padding: 10px 12px;
        border: 1px solid rgba(220, 149, 67, 0.22);
        border-radius: 8px;
        background: rgba(220, 149, 67, 0.08);
      }}
      .coin-risk-flag--ok {{
        border-color: rgba(93, 177, 128, 0.22);
        background: rgba(93, 177, 128, 0.09);
      }}
      .coin-risk-flag--risk {{
        border-color: rgba(185, 61, 61, 0.22);
        background: rgba(185, 61, 61, 0.07);
      }}
      .coin-risk-flag strong {{
        display: block;
        color: #111318;
        font-size: 11px;
        font-weight: 800;
      }}
      .coin-risk-flag span {{
        display: block;
        margin-top: 4px;
        color: #6f7683;
        font-size: 11px;
        line-height: 1.45;
      }}
      .coin-detail-links {{
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        padding: 0 14px 14px;
      }}
      .coin-detail-links a,
      .coin-detail-links span {{
        color: #0066cc;
        font-size: 11px;
        font-weight: 700;
        text-decoration: none;
      }}
      .coin-detail-questions {{
        margin: 0;
        padding: 0;
        list-style: none;
        display: grid;
        gap: 7px;
      }}
      .coin-detail-questions li {{
        padding: 9px 10px;
        border: 1px solid rgba(220, 149, 67, 0.20);
        border-radius: 8px;
        background: rgba(220, 149, 67, 0.08);
        color: #755124;
        font-size: 11px;
        line-height: 1.45;
      }}
      @media(max-width: 980px) {{
        .coin-detail-head,
        .coin-detail-grid,
        .coin-detail-upbit {{
          grid-template-columns: 1fr;
        }}
      }}
    </style>
    <section class="coin-detail">
      <div class="coin-detail-head">
        <div>
          <p class="coin-detail-head__eyebrow">Single Coin Study</p>
          <h2 class="coin-detail-head__title">{escape(str(basics.get("name") or "-"))} ({escape(str(basics.get("symbol") or "-"))})</h2>
          <div class="coin-detail-chips">{categories or _chip("카테고리 없음")}</div>
        </div>
        <div class="coin-detail-rank">Rank #{escape(str(basics.get("market_cap_rank") or "-"))}</div>
      </div>

      <div class="coin-detail-metrics">
        {"".join(metrics)}
      </div>

      <div class="coin-detail-panel">
        <h3 class="coin-detail-panel__title">90일 가격 / 거래량 흐름</h3>
        <div class="coin-detail-chart" style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;">
          {_chart_card("가격 (90일)", price_chart, series_key="prices")}
          {_chart_card("거래량 (90일)", price_chart, series_key="total_volumes")}
        </div>
      </div>

      <div class="coin-detail-grid">
        <div class="coin-detail-panel">
          <h3 class="coin-detail-panel__title">공급 구조</h3>
          <div class="coin-detail-panel__body">{"".join(supply_items)}</div>
        </div>
        <div class="coin-detail-panel">
          <h3 class="coin-detail-panel__title">업비트 KRW</h3>
          <div class="coin-detail-panel__body">{upbit_body}</div>
        </div>
      </div>

      <div class="coin-detail-grid">
        <div class="coin-detail-panel">
          <h3 class="coin-detail-panel__title">리스크 체크</h3>
          <div class="coin-detail-panel__body">{"".join(risk_items)}</div>
        </div>
        <div class="coin-detail-panel">
          <h3 class="coin-detail-panel__title">커뮤니티 / 개발</h3>
          <div class="coin-detail-panel__body">{"".join(community_items)}</div>
        </div>
      </div>

      <div class="coin-detail-grid">
        <div class="coin-detail-panel">
          <h3 class="coin-detail-panel__title">온체인 / DeFi</h3>
          <div class="coin-detail-panel__body">{defi_body}</div>
        </div>
        <div class="coin-detail-panel">
          <h3 class="coin-detail-panel__title">파생상품 과열</h3>
          <div class="coin-detail-panel__body">{futures_body}</div>
        </div>
      </div>

      <div class="coin-detail-panel">
        <h3 class="coin-detail-panel__title">위험 신호 요약</h3>
        <div class="coin-detail-panel__body coin-risk-flags">{"".join(risk_flag_items)}</div>
      </div>

      <div class="coin-detail-panel">
        <h3 class="coin-detail-panel__title">프로젝트 설명</h3>
        <p class="coin-detail-panel__copy">{escape(description)}</p>
        <div class="coin-detail-links">{"".join(links)}</div>
      </div>

      <div class="coin-detail-panel">
        <h3 class="coin-detail-panel__title">오늘의 공부 질문</h3>
        <div class="coin-detail-panel__body">
          <ul class="coin-detail-questions">
            <li>이 코인의 핵심 수요가 수수료, 담보, 스테이킹, 밈, 거버넌스 중 무엇인지 설명하기</li>
            <li>가격 상승이 거래량 증가를 동반했는지 확인하기</li>
            <li>FDV가 시총보다 크다면 앞으로 어떤 희석 이벤트가 있을지 찾아보기</li>
            <li>업비트 가격과 글로벌 가격이 크게 다르면 국내 수급 과열인지 확인하기</li>
          </ul>
        </div>
      </div>
    </section>
    """


def build_coin_detail_empty_state() -> str:
    return """
    <div class="cat-output-shell">
      <div class="cat-output-placeholder">
        코인명이나 심볼을 입력하고 분석 버튼을 누르면 가격, 차트, 시총, FDV, 공급 구조, 업비트 수급, 온체인, 파생상품, 공부 질문이 여기에 표시됩니다.
      </div>
    </div>
    """


def _sector_row(row: dict, rank: int) -> str:
    return f"""
    <tr>
      <td>{rank}</td>
      <td><strong>{escape(str(row.get("name") or "-"))}</strong><span>{escape(str(row.get("id") or ""))}</span></td>
      <td class="{_pct_class(row.get("market_cap_change_24h"))}">{escape(_fmt_pct(row.get("market_cap_change_24h")))}</td>
      <td>{escape(_fmt_usd(row.get("market_cap")))}</td>
      <td>{escape(_fmt_usd(row.get("volume_24h")))}</td>
    </tr>
    """


def _sector_coin_row(row: dict) -> str:
    return f"""
    <tr>
      <td><strong>{escape(str(row.get("sector") or "-"))}</strong></td>
      <td><strong>{escape(str(row.get("name") or "-"))}</strong><span>{escape(str(row.get("symbol") or "").upper())}</span></td>
      <td>{escape(str(row.get("market_cap_rank") or "-"))}</td>
      <td>{escape(_fmt_usd(row.get("current_price")))}</td>
      <td class="{_pct_class(row.get("price_change_percentage_24h"))}">{escape(_fmt_pct(row.get("price_change_percentage_24h")))}</td>
      <td>{escape(_fmt_usd(row.get("market_cap")))}</td>
    </tr>
    """


def _playbook_card(row: dict) -> str:
    return f"""
    <div class="coin-playbook">
      <div class="coin-playbook__name">{escape(str(row.get("name") or "-"))}</div>
      <p>{escape(str(row.get("what") or ""))}</p>
      <dl>
        <dt>볼 것</dt>
        <dd>{escape(str(row.get("watch") or "-"))}</dd>
        <dt>조심할 것</dt>
        <dd>{escape(str(row.get("risk") or "-"))}</dd>
      </dl>
    </div>
    """


def build_coin_sector_dashboard(payload: dict) -> str:
    categories = payload.get("categories", [])
    representative = payload.get("representative_coins", [])
    strongest = payload.get("strongest_sector", {})
    weakest = payload.get("weakest_sector", {})
    playbooks = payload.get("playbooks", [])
    top_protocols = payload.get("top_protocols", [])
    fees = payload.get("fees", {})
    stablecoins = payload.get("stablecoins", {})

    heat_cards = "".join(_category_card(row) for row in categories[:12])
    sector_rows = "".join(_sector_row(row, idx + 1) for idx, row in enumerate(categories[:12]))
    coin_rows = "".join(_sector_coin_row(row) for row in representative[:18])
    playbook_cards = "".join(_playbook_card(row) for row in playbooks[:8])
    protocol_rows = "".join(_protocol_row(row, idx + 1) for idx, row in enumerate(top_protocols[:8]))
    fee_rows = "".join(_fee_row(row, idx + 1) for idx, row in enumerate((fees.get("protocols") or [])[:6]))
    stable_rows = "".join(
        _mini_data_row(
            str(row.get("symbol") or row.get("name") or "-"),
            _fmt_usd(row.get("circulating_usd")),
            f"7d {_fmt_pct(row.get('change_7d_pct'))}",
            _pct_class(row.get("change_7d_pct")),
        )
        for row in (stablecoins.get("top_assets") or [])[:5]
    )

    return f"""
    <style>
      .coin-sector-study {{
        display: grid;
        gap: 12px;
        color: #111318;
        font-family: Inter, -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
      }}
      .coin-sector-study * {{ box-sizing: border-box; }}
      .coin-sector-head,
      .coin-sector-panel,
      .coin-playbook {{
        border: 1px solid rgba(17, 19, 24, 0.09);
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.62);
      }}
      .coin-sector-head {{
        display: grid;
        grid-template-columns: 1fr minmax(220px, 0.45fr);
        gap: 14px;
        align-items: stretch;
        padding: 17px 18px;
      }}
      .coin-sector-head__eyebrow {{
        margin: 0 0 6px;
        color: #6f7683;
        font-size: 10px;
        font-weight: 800;
        text-transform: uppercase;
      }}
      .coin-sector-head__title {{
        margin: 0;
        font-size: 23px;
        line-height: 1.16;
        font-weight: 800;
      }}
      .coin-sector-head__time {{
        margin: 7px 0 0;
        color: #6f7683;
        font-size: 11px;
      }}
      .coin-sector-summary {{
        display: grid;
        gap: 8px;
      }}
      .coin-sector-summary__box {{
        padding: 10px 12px;
        border: 1px solid rgba(139, 151, 232, 0.20);
        border-radius: 8px;
        background: rgba(139, 151, 232, 0.10);
      }}
      .coin-sector-summary__label {{
        margin: 0 0 4px;
        color: #6f7683;
        font-size: 10px;
        font-weight: 800;
      }}
      .coin-sector-summary__value {{
        margin: 0;
        color: #111318;
        font-size: 13px;
        font-weight: 800;
      }}
      .coin-sector-heat {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(142px, 1fr));
        gap: 8px;
      }}
      .coin-sector-study .coin-sector {{
        min-height: 112px;
        padding: 12px;
        border: 1px solid rgba(17, 19, 24, 0.09);
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.62);
      }}
      .coin-sector-study .coin-sector__name {{
        min-height: 32px;
        color: #111318;
        font-size: 11px;
        font-weight: 800;
        line-height: 1.38;
        word-break: keep-all;
      }}
      .coin-sector-study .coin-sector__change {{
        margin-top: 8px;
        font-size: 15px;
        font-weight: 800;
      }}
      .coin-sector-study .coin-sector__sub {{
        margin-top: 4px;
        color: #6f7683;
        font-size: 10px;
      }}
      .coin-sector-panel {{
        overflow: hidden;
      }}
      .coin-sector-panel__title {{
        margin: 0;
        padding: 13px 14px 10px;
        border-bottom: 1px solid rgba(17, 19, 24, 0.07);
        font-size: 13px;
        font-weight: 800;
      }}
      .coin-sector-panel__body {{
        padding: 10px;
      }}
      .coin-sector-grid-2 {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
      }}
      .coin-mini-list {{
        display: grid;
        gap: 7px;
      }}
      .coin-mini-row {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
        padding: 9px 10px;
        border: 1px solid rgba(17, 19, 24, 0.07);
        border-radius: 8px;
        background: rgba(250, 247, 241, 0.72);
      }}
      .coin-mini-row strong {{
        display: block;
        color: #111318;
        font-size: 11px;
      }}
      .coin-mini-row span {{
        display: block;
        margin-top: 3px;
        color: #8a929e;
        font-size: 10px;
      }}
      .coin-mini-row em {{
        flex-shrink: 0;
        color: #303743;
        font-style: normal;
        font-size: 11px;
        font-weight: 800;
        text-align: right;
      }}
      .coin-sector-table-wrap {{
        overflow-x: auto;
      }}
      .coin-sector-table {{
        width: 100%;
        min-width: 0;
        table-layout: fixed;
        border-collapse: collapse;
      }}
      .coin-sector-table th {{
        padding: 0 8px 8px 0;
        border-bottom: 1px solid rgba(17, 19, 24, 0.09);
        color: #6f7683;
        font-size: 10px;
        font-weight: 800;
        text-align: left;
      }}
      .coin-sector-table td {{
        padding: 9px 8px 9px 0;
        border-bottom: 1px solid rgba(17, 19, 24, 0.05);
        color: #303743;
        font-size: 11px;
        line-height: 1.35;
        vertical-align: top;
        overflow-wrap: anywhere;
      }}
      .coin-sector-table tr:last-child td {{ border-bottom: 0; }}
      .coin-sector-table strong {{
        display: block;
        color: #111318;
        font-size: 11px;
      }}
      .coin-sector-table span {{
        display: block;
        margin-top: 3px;
        color: #8a929e;
        font-size: 10px;
      }}
      .coin-playbooks {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
        gap: 8px;
      }}
      .coin-playbook {{
        padding: 13px 14px;
      }}
      .coin-playbook__name {{
        margin-bottom: 7px;
        color: #111318;
        font-size: 12px;
        font-weight: 800;
      }}
      .coin-playbook p {{
        margin: 0 0 10px;
        color: #303743;
        font-size: 11px;
        line-height: 1.55;
        word-break: keep-all;
      }}
      .coin-playbook dl {{
        display: grid;
        gap: 4px;
        margin: 0;
      }}
      .coin-playbook dt {{
        color: #6f7683;
        font-size: 10px;
        font-weight: 800;
      }}
      .coin-playbook dd {{
        margin: 0 0 6px;
        color: #303743;
        font-size: 11px;
        line-height: 1.45;
      }}
      .coin-sector-study .up {{ color: #b93d3d !important; }}
      .coin-sector-study .down {{ color: #2f7a55 !important; }}
      .coin-sector-study .flat {{ color: #303743 !important; }}
      @media(max-width: 980px) {{
        .coin-sector-head {{
          grid-template-columns: 1fr;
        }}
        .coin-sector-grid-2 {{
          grid-template-columns: 1fr;
        }}
      }}
    </style>
    <section class="coin-sector-study">
      <div class="coin-sector-head">
        <div>
          <p class="coin-sector-head__eyebrow">Sector Study</p>
          <h2 class="coin-sector-head__title">섹터별로 시장을 나눠 봅니다</h2>
          <p class="coin-sector-head__time">{escape(str(payload.get("target_datetime") or ""))}</p>
        </div>
        <div class="coin-sector-summary">
          <div class="coin-sector-summary__box">
            <p class="coin-sector-summary__label">강한 섹터</p>
            <p class="coin-sector-summary__value">{escape(str(strongest.get("name") or "-"))} {escape(_fmt_pct(strongest.get("market_cap_change_24h")))}</p>
          </div>
          <div class="coin-sector-summary__box">
            <p class="coin-sector-summary__label">약한 섹터</p>
            <p class="coin-sector-summary__value">{escape(str(weakest.get("name") or "-"))} {escape(_fmt_pct(weakest.get("market_cap_change_24h")))}</p>
          </div>
        </div>
      </div>

      <div class="coin-sector-panel">
        <h3 class="coin-sector-panel__title">섹터 히트맵</h3>
        <div class="coin-sector-panel__body coin-sector-heat">
          {heat_cards or '<div class="coin-sector">데이터 없음</div>'}
        </div>
      </div>

      <div class="coin-sector-panel">
        <h3 class="coin-sector-panel__title">섹터 순위</h3>
        <div class="coin-sector-panel__body coin-sector-table-wrap">
          <table class="coin-sector-table">
            <thead><tr><th>#</th><th>섹터</th><th>24h</th><th>시총</th><th>거래대금</th></tr></thead>
            <tbody>{sector_rows or '<tr><td colspan="5">데이터 없음</td></tr>'}</tbody>
          </table>
        </div>
      </div>

      <div class="coin-sector-panel">
        <h3 class="coin-sector-panel__title">섹터별 대표 코인</h3>
        <div class="coin-sector-panel__body coin-sector-table-wrap">
          <table class="coin-sector-table">
            <thead><tr><th>섹터</th><th>코인</th><th>순위</th><th>가격</th><th>24h</th><th>시총</th></tr></thead>
            <tbody>{coin_rows or '<tr><td colspan="6">데이터 없음</td></tr>'}</tbody>
          </table>
        </div>
      </div>

      <div class="coin-sector-grid-2">
        <div class="coin-sector-panel">
          <h3 class="coin-sector-panel__title">DeFi TVL 상위</h3>
          <div class="coin-sector-panel__body coin-sector-table-wrap">
            <table class="coin-sector-table">
              <thead><tr><th>#</th><th>프로토콜</th><th>TVL</th><th>24h</th><th>체인</th></tr></thead>
              <tbody>{protocol_rows or '<tr><td colspan="5">데이터 없음</td></tr>'}</tbody>
            </table>
          </div>
        </div>
        <div class="coin-sector-panel">
          <h3 class="coin-sector-panel__title">수수료 상위 프로토콜</h3>
          <div class="coin-sector-panel__body coin-sector-table-wrap">
            <table class="coin-sector-table">
              <thead><tr><th>#</th><th>프로토콜</th><th>24h</th><th>7d</th></tr></thead>
              <tbody>{fee_rows or '<tr><td colspan="4">데이터 없음</td></tr>'}</tbody>
            </table>
          </div>
        </div>
      </div>

      <div class="coin-sector-panel">
        <h3 class="coin-sector-panel__title">스테이블코인 공급</h3>
        <div class="coin-sector-panel__body coin-mini-list">
          {_mini_data_row("전체 시총", _fmt_usd(stablecoins.get("total_circulating_usd")), f"7d {_fmt_pct(stablecoins.get('change_7d_pct'))}", _pct_class(stablecoins.get("change_7d_pct")))}
          {stable_rows or '<div class="coin-mini-row"><div><strong>데이터 없음</strong><span>-</span></div><em>-</em></div>'}
        </div>
      </div>

      <div class="coin-sector-panel">
        <h3 class="coin-sector-panel__title">섹터별 공부 포인트</h3>
        <div class="coin-sector-panel__body coin-playbooks">
          {playbook_cards or '<div class="coin-playbook">데이터 없음</div>'}
        </div>
      </div>
    </section>
    """


def build_coin_sector_empty_state() -> str:
    return """
    <div class="cat-output-shell">
      <div class="cat-output-placeholder">
        섹터 불러오기 버튼을 누르면 섹터 히트맵, 섹터별 대표 코인, 공부 포인트가 여기에 표시됩니다.
      </div>
    </div>
    """

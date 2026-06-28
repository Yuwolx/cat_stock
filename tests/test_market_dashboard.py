from src.ui.dashboard import build_market_dashboard, build_stock_dashboard


def _market_payload() -> dict:
    return {
        "target_date": "2026-06-03",
        "indices": {
            "kospi": {"close": 9000, "change_pct": "+1.2"},
            "kosdaq": {"close": 1000, "change_pct": "-0.3"},
        },
        "global_macro": {"usdkrw": "1,350", "nasdaq": "+0.5%"},
        "investor_flows": {"summary": {"foreign": 100, "institution": -50, "retail": -50}},
        "leaders": [{"name": "삼성전자", "turnover_krw_billion": 1000}],
        "sectors": [],
        "market_events": {"new_highs": [], "new_lows": [], "upper_limit": [], "after_hours_movers": []},
        "column": {"is_available": False, "reason": "missing_api_key"},
        "news_items": [
            {
                "title": "코스피 강세 지속",
                "url": "https://n.news.naver.com/mnews/article/018/0006296662",
                "source": "이데일리",
                "date": "2026-06-03",
            }
        ],
        "market_reports": [
            {
                "title": "Daily 신한생각",
                "url": "https://finance.naver.com/research/market_info_read.naver?nid=36261&page=1",
                "broker": "신한투자증권",
                "date": "26.06.04",
            }
        ],
    }


def _stock_payload() -> dict:
    return {
        "target_date": "2026-06-03",
        "basics": {
            "name": "삼성전자",
            "price": "78,500",
            "change_pct": "+1.2%",
            "market_cap": "468조",
            "per": "18.4",
            "pbr": "1.5",
            "roe": "12.8%",
            "year_high_low": "88,000 / 61,500",
            "ma_position": {"ma5": "상회", "ma20": "근접", "ma60": "하회"},
        },
        "flows": {
            "foreign_20d": "+1,245주",
            "institution_20d": "-342주",
            "news": ["뉴스"],
            "news_items": [],
            "naver_reports": [],
        },
        "financials": [
            {
                "quarter": "2026Q1",
                "sales": "74000000000000",
                "op_income": "6500000000000",
                "net_income": "5800000000000",
            }
        ],
        "disclosures": {"disclosures": ["공시"], "major_shareholder_ratio": "20%", "risk_flags": ["CB 없음"]},
        "short_selling": {"consensus_target_price": "91,000원"},
        "reports": [],
        "column": {"is_available": False, "reason": "missing_api_key"},
    }


def test_market_dashboard_includes_latest_news_links() -> None:
    html = build_market_dashboard(_market_payload())

    assert "LATEST NEWS" in html
    assert "코스피 강세 지속" in html
    assert 'href="https://n.news.naver.com/mnews/article/018/0006296662"' in html
    assert "ANALYST REPORTS" in html
    assert "Daily 신한생각" in html
    assert "신한투자증권" in html
    assert 'href="https://finance.naver.com/research/market_info_read.naver?nid=36261&amp;page=1"' in html


def test_plotly_dashboards_use_cdn_without_heavy_inline_bundle() -> None:
    market_html = build_market_dashboard(_market_payload())
    stock_html = build_stock_dashboard(_stock_payload())

    for html in (market_html, stock_html):
        assert "https://cdn.plot.ly/" in html
        assert html.count("https://cdn.plot.ly/") == 1
        assert len(html) < 200_000


def test_plotly_dashboards_disable_chart_interaction_for_mobile_scroll() -> None:
    market_html = build_market_dashboard(_market_payload())
    stock_html = build_stock_dashboard(_stock_payload())

    for html in (market_html, stock_html):
        assert '"staticPlot": true' in html
        assert "touch-action:pan-y" in html
        assert ".plotly-graph-div" in html
        assert "overflow-x:hidden" in html


def test_dashboard_shows_adjusted_trading_date_notice() -> None:
    payload = {
        **_market_payload(),
        "requested_date": "2026-06-28",
        "target_date": "2026-06-26",
        "resolved_date": "2026-06-26",
        "requested_weekday": "일",
        "resolved_weekday": "금",
        "is_adjusted": True,
    }

    html = build_market_dashboard(payload)

    assert "요청일 2026-06-28 일요일" in html
    assert "분석 기준일 2026-06-26 금요일" in html

from src.ui.dashboard import build_market_dashboard


def test_market_dashboard_includes_latest_news_links() -> None:
    html = build_market_dashboard(
        {
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
        }
    )

    assert "LATEST NEWS" in html
    assert "코스피 강세 지속" in html
    assert 'href="https://n.news.naver.com/mnews/article/018/0006296662"' in html

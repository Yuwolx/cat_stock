from src.formatters.market_formatter import format_market_briefing


def test_market_formatter_includes_sections() -> None:
    payload = {
        "target_date": "2026-05-29",
        "is_mock_data": True,
        "indices": {
            "kospi": {"close": 2640.0, "change_pct": 1.0, "turnover_trillion_krw": 10, "change_points": 20},
            "kosdaq": {"close": 840.0, "change_pct": -0.5, "turnover_trillion_krw": 8, "change_points": -4},
        },
        "global_macro": {
            "dow": "+0.1%",
            "sp500": "+0.2%",
            "nasdaq": "+0.3%",
            "usdkrw": "1360.0",
            "us10y": "4.4%",
            "wti": "$77",
            "shanghai": "-0.1%",
            "shenzhen": "+0.1%",
        },
        "leaders": [{"name": "삼성전자", "price": "79,000", "change_pct": 1.2, "turnover_krw_billion": 1000}],
        "investor_flows": {
            "summary": {"foreign": 100, "institution": 50, "retail": -150},
            "by_market": {
                "kospi": {"foreign": 90, "institution": 40, "retail": -130},
                "kosdaq": {"foreign": 10, "institution": 10, "retail": -20},
            },
            "foreign_top_buy": ["삼성전자"],
            "foreign_top_sell": ["A"],
            "institution_top_buy": ["B"],
            "institution_top_sell": ["C"],
        },
        "derivatives": {
            "futures_foreign_net": 10,
            "futures_institution_net": -10,
            "program_arbitrage": 20,
            "program_non_arbitrage": -5,
            "program_by_market": {
                "kospi": {"arbitrage": 18, "non_arbitrage": -4, "total": 14},
                "kosdaq": {"arbitrage": 2, "non_arbitrage": -1, "total": 1},
            },
        },
        "market_events": {
            "new_highs": ["A"],
            "new_lows": ["B"],
            "upper_limit": ["C"],
            "after_hours_movers": ["D +3%"],
            "rising_over_5pct": [
                {"name": "테스트종목", "market": "KOSPI", "price": "12,300", "change_pct": 6.03}
            ],
        },
    }

    result = format_market_briefing(payload)

    assert "[시황 브리핑 데이터 - 2026-05-29]" in result
    assert "■ 한국 지수" in result
    assert "■ 주요 공시" not in result
    assert "공시" not in result
    assert "코스피 수급 외국인 90억" in result
    assert "프로그램 코스닥 차익 2억" in result
    assert "5% 이상 상승 종목 (KOSPI) 테스트종목 | 현재가 12,300 | 등락률 +6.03%" in result

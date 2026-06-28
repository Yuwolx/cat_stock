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
        "leaders": [{"name": "삼성전자", "price": "79,000", "change_pct": 1.2, "turnover_krw_billion": 121726.1}],
        "investor_flows": {
            "summary": {"foreign": -67087.0, "institution": 50.0, "retail": -150},
            "by_market": {
                "kospi": {"foreign": 90.0, "institution": 40, "retail": -130},
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
            "futures_contract_code": "A01606",
            "futures_warning": None,
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
        "news_items": [
            {
                "title": "코스피 강세 지속",
                "url": "https://n.news.naver.com/mnews/article/018/0006296662",
                "source": "이데일리",
                "date": "2026-06-03 17:15:09",
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

    result = format_market_briefing(payload)

    assert "[시황 브리핑 데이터 - 2026-05-29]" in result
    assert "■ 한국 지수" in result
    assert "■ 주요 공시" not in result
    assert "공시" not in result
    assert "거래대금 12.2조" in result
    assert "순매수 요약 외국인 -6.7조" in result
    assert "코스피 수급 외국인 90억" in result
    assert "코스피200 선물 근월물 코드 A01606" not in result
    assert "코스피200 선물" not in result
    assert "선물 수급" not in result
    assert "선물 수급 경고" not in result
    assert "프로그램 코스닥 차익 2억" in result
    assert "당일 상승 상위" not in result
    assert "5% 이상 상승 종목 (KOSPI) 테스트종목 | 현재가 12,300 | 등락률 +6.03%" in result
    assert "■ 주요 뉴스" in result
    assert "코스피 강세 지속 (이데일리, 2026-06-03 17:15:09)" in result
    assert "  링크: https://n.news.naver.com/mnews/article/018/0006296662" in result
    assert "■ 증권사 리포트" in result
    assert "Daily 신한생각 (신한투자증권, 26.06.04)" in result
    assert "  링크: https://finance.naver.com/research/market_info_read.naver?nid=36261&page=1" in result


def test_market_formatter_shows_adjusted_trading_date_notice() -> None:
    payload = {
        "requested_date": "2026-06-28",
        "target_date": "2026-06-26",
        "resolved_date": "2026-06-26",
        "requested_weekday": "일",
        "resolved_weekday": "금",
        "is_adjusted": True,
        "is_mock_data": False,
        "indices": {
            "kospi": {"close": None, "change_pct": None, "turnover_trillion_krw": None, "change_points": None},
            "kosdaq": {"close": None, "change_pct": None, "turnover_trillion_krw": None, "change_points": None},
        },
        "global_macro": {
            "dow": None,
            "sp500": None,
            "nasdaq": None,
            "usdkrw": None,
            "us10y": None,
            "wti": None,
            "shanghai": None,
            "shenzhen": None,
        },
        "leaders": [],
        "investor_flows": {
            "summary": {"foreign": None, "institution": None, "retail": None},
            "by_market": {},
            "foreign_top_buy": [],
            "foreign_top_sell": [],
            "institution_top_buy": [],
            "institution_top_sell": [],
        },
        "derivatives": {
            "program_arbitrage": None,
            "program_non_arbitrage": None,
            "program_by_market": {},
        },
        "market_events": {
            "new_lows": [],
            "upper_limit": [],
            "after_hours_movers": [],
            "rising_over_5pct": [],
        },
    }

    result = format_market_briefing(payload)

    assert "[시황 브리핑 데이터 - 2026-06-26]" in result
    assert "요청일: 2026-06-28 일요일" in result
    assert "분석 기준일: 2026-06-26 금요일" in result

from src.formatters.stock_formatter import format_stock_report


def test_stock_formatter_includes_stock_name() -> None:
    payload = {
        "target_date": "2026-05-29",
        "report_date": "2026-05-29 ~ 2026-05-29",
        "is_mock_data": True,
        "basics": {
            "name": "삼성전자",
            "price": "78,500",
            "change_pct": "+1.82%",
            "turnover_krw_billion": 842,
            "market_cap": "46.8조",
            "year_high_low": "88,000 / 61,500",
            "per": "18.4",
            "pbr": "1.52",
            "roe": "12.8%",
            "ma_position": {"ma5": "상회", "ma20": "상회", "ma60": "근접"},
        },
        "flows": {
            "foreign_20d": "+1,245주",
            "institution_20d": "-342주",
            "news": ["뉴스"],
        },
        "reports": [],
        "financials": [{"quarter": "2026Q1", "sales": "10", "op_income": "2", "net_income": "1"}],
        "disclosures": {
            "disclosures": ["공시"],
            "major_shareholder_ratio": "20%",
            "risk_flags": ["CB 없음"],
        },
        "short_selling": {"short_balance_ratio": "1.84%", "consensus_target_price": "91,000원"},
    }

    result = format_stock_report(payload)

    assert "[개별 종목 분석 - 삼성전자 - 2026-05-29]" in result
    assert "■ 기본 정보" in result
    assert "■ 최근 공시" in result
    assert "공시" in result
    assert "컨센서스 목표가 91,000원" in result

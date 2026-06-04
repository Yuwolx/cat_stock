from src.formatters.coin_detail_formatter import format_coin_detail_report


def test_coin_detail_formatter_includes_risk_and_learning_sections() -> None:
    payload = {
        "target_datetime": "2026-05-31 18:00 KST",
        "basics": {"id": "bitcoin", "name": "Bitcoin", "symbol": "BTC", "market_cap_rank": 1},
        "market": {
            "current_price_usd": 100_000,
            "change_24h_pct": 1.2,
            "change_7d_pct": -2.4,
            "change_30d_pct": 8.3,
            "market_cap_usd": 2_000_000_000_000,
            "fdv_usd": 2_100_000_000_000,
            "volume_usd": 50_000_000_000,
            "ath_usd": 110_000,
            "ath_change_pct": -9.0,
        },
        "supply": {"circulating_supply": 20_000_000, "total_supply": 20_000_000, "max_supply": 21_000_000},
        "upbit": {
            "is_listed": True,
            "market": "KRW-BTC",
            "trade_price": 150_000_000,
            "change_pct": 1.1,
            "acc_trade_price_24h": 500_000_000_000,
            "kimchi_premium_pct": 1.8,
            "warning": False,
        },
        "risk": {"fdv_to_mcap": "1.05x", "volume_to_mcap": "0.03x"},
        "project": {"categories": ["Layer 1"], "description": "Bitcoin description"},
    }

    result = format_coin_detail_report(payload)

    assert "[개별 코인 공부 - Bitcoin - 2026-05-31 18:00 KST]" in result
    assert "■ 리스크 체크" in result
    assert "■ 공부 질문" in result
    assert "김치 프리미엄 +1.80%" in result


def test_coin_detail_formatter_marks_missing_values_plainly() -> None:
    payload = {
        "target_datetime": "2026-05-31 18:00 KST",
        "basics": {"id": "bitcoin", "name": "Bitcoin", "symbol": "BTC", "market_cap_rank": None},
        "market": {
            "current_price_usd": None,
            "change_24h_pct": None,
            "change_7d_pct": None,
            "change_30d_pct": None,
            "market_cap_usd": None,
            "fdv_usd": None,
            "volume_usd": None,
            "ath_usd": None,
            "ath_change_pct": None,
        },
        "supply": {"circulating_supply": None, "total_supply": None, "max_supply": None},
        "upbit": {"is_listed": False, "kimchi_premium_pct": None, "warning": None},
        "risk": {"fdv_to_mcap": None, "volume_to_mcap": None},
        "project": {"categories": []},
        "defi_protocol": {"name": None, "tvl": None, "change_1d": None, "change_7d": None},
        "futures": {"is_available": True, "symbol": "BTCUSDT", "latest_funding_rate_pct": None},
        "risk_flags": [{"label": None, "message": None}],
    }

    result = format_coin_detail_report(payload)

    assert "연결 예정" not in result
    assert "None" not in result
    assert "현재가 —" in result
    assert "카테고리 —" in result

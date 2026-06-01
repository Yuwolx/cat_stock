from src.formatters.coin_market_formatter import format_coin_market_briefing


def test_coin_market_formatter_includes_learning_sections() -> None:
    payload = {
        "target_datetime": "2026-05-31 17:00 KST",
        "global_market": {
            "total_market_cap_usd": 2_500_000_000_000,
            "total_volume_usd": 110_000_000_000,
            "market_cap_change_24h_pct": 1.5,
            "btc_dominance": 53.2,
            "eth_dominance": 16.1,
        },
        "majors": {
            "bitcoin": {
                "current_price": 100_000,
                "price_change_percentage_24h": 1.1,
                "price_change_percentage_7d_in_currency": 4.2,
            },
            "ethereum": {
                "current_price": 4_000,
                "price_change_percentage_24h": -0.5,
                "price_change_percentage_7d_in_currency": 2.3,
            },
        },
        "fear_greed": {"value": 62, "classification": "Greed"},
        "kimchi_premium_pct": 1.8,
        "usdkrw": "1,360.00",
        "regime": {"label": "위험 선호", "message": "시장 전체가 강합니다."},
        "upbit_leaders": [
            {
                "korean_name": "비트코인",
                "symbol": "BTC",
                "market": "KRW-BTC",
                "trade_price": 136_000_000,
                "change_pct": 1.2,
                "acc_trade_price_24h": 500_000_000_000,
            }
        ],
        "top_coins": [{"name": "Bitcoin", "symbol": "btc", "market_cap_rank": 1, "current_price": 100_000, "price_change_percentage_24h": 1.1, "market_cap": 2_000_000_000_000}],
        "categories": [{"name": "Layer 1", "market_cap_change_24h": 1.0, "market_cap": 1_500_000_000_000}],
    }

    result = format_coin_market_briefing(payload)

    assert "[코인 시황 대시보드 - 2026-05-31 17:00 KST]" in result
    assert "■ 시장 온도" in result
    assert "■ 업비트 KRW 거래대금 상위" in result
    assert "■ 오늘의 공부 질문" in result
    assert "김치 프리미엄 +1.80%" in result

from src.formatters.coin_sector_formatter import format_coin_sector_report


def test_coin_sector_formatter_includes_heatmap_and_playbook() -> None:
    payload = {
        "target_datetime": "2026-05-31 18:30 KST",
        "categories": [
            {"name": "Layer 1", "market_cap_change_24h": 1.5, "market_cap": 2_000_000_000_000, "volume_24h": 30_000_000_000}
        ],
        "representative_coins": [
            {
                "sector": "Layer 1",
                "name": "Bitcoin",
                "symbol": "btc",
                "market_cap_rank": 1,
                "current_price": 100_000,
                "price_change_percentage_24h": 1.2,
            }
        ],
        "strongest_sector": {"name": "Layer 1", "market_cap_change_24h": 1.5},
        "weakest_sector": {"name": "Meme", "market_cap_change_24h": -2.1},
        "playbooks": [{"name": "Layer 1", "watch": "수수료", "risk": "장애"}],
    }

    result = format_coin_sector_report(payload)

    assert "[코인 섹터 공부 - 2026-05-31 18:30 KST]" in result
    assert "■ 섹터 히트맵" in result
    assert "■ 대표 코인" in result
    assert "■ 섹터별 공부 포인트" in result

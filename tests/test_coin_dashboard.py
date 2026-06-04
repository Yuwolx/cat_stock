from src.ui.coin_dashboard import build_coin_detail_dashboard, build_coin_sector_dashboard


def test_coin_detail_dashboard_hides_raw_none_values() -> None:
    html = build_coin_detail_dashboard(
        {
            "target_datetime": "2026-06-04 18:00 KST",
            "basics": {"name": None, "symbol": None, "market_cap_rank": None},
            "market": {
                "current_price_usd": None,
                "current_price_krw": None,
                "change_24h_pct": None,
                "change_7d_pct": None,
                "change_30d_pct": None,
                "market_cap_usd": None,
                "fdv_usd": None,
                "volume_usd": None,
                "ath_change_pct": None,
                "ath_usd": None,
            },
            "supply": {"circulating_supply": None, "total_supply": None, "max_supply": None},
            "upbit": {"is_listed": True, "market": None, "korean_name": None, "warning": None},
            "risk": {"fdv_to_mcap": None, "volume_to_mcap": None},
            "project": {"categories": [None], "description": None},
            "community": {"twitter_followers": None, "reddit_subscribers": None},
            "developer": {"stars": None, "commit_count_4_weeks": None},
            "price_chart": {"prices": [], "total_volumes": []},
            "defi_protocol": {"name": None, "category": None, "tvl": None, "change_1d": None, "change_7d": None},
            "futures": {"is_available": True, "symbol": None, "warning": None},
            "risk_flags": [{"label": None, "message": None}],
            "usdkrw": None,
        }
    )

    assert "None" not in html
    assert "—" in html


def test_coin_sector_dashboard_hides_raw_none_values() -> None:
    html = build_coin_sector_dashboard(
        {
            "target_datetime": "2026-06-04 18:00 KST",
            "categories": [{"id": None, "name": None, "market_cap_change_24h": None, "market_cap": None, "volume_24h": None}],
            "representative_coins": [
                {
                    "sector": None,
                    "name": None,
                    "symbol": None,
                    "market_cap_rank": None,
                    "current_price": None,
                    "price_change_percentage_24h": None,
                    "market_cap": None,
                }
            ],
            "strongest_sector": {},
            "weakest_sector": {},
            "playbooks": [{"name": None, "what": None, "watch": None, "risk": None}],
            "top_protocols": [{"name": None, "category": None, "tvl": None, "change_1d": None}],
            "fees": {"protocols": [{"name": None, "category": None, "total24h": None, "total7d": None}]},
            "stablecoins": {"top_assets": [{"symbol": None, "name": None, "circulating_usd": None, "change_7d_pct": None}]},
        }
    )

    assert "None" not in html
    assert "—" in html

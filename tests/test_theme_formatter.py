from src.formatters.theme_formatter import format_theme_report


def test_theme_formatter_includes_theme_name() -> None:
    payload = {
        "target_date": "2026-05-29",
        "is_mock_data": True,
        "theme_name": "HBM",
        "stocks": [
            {
                "name": "한미반도체",
                "market_cap": "17조",
                "price": "100,000",
                "change_pct": "+1.0%",
                "per": "30",
                "pbr": "4",
            }
        ],
        "news_bundle": {"news": ["뉴스"], "reports": ["리포트"]},
        "peer_bundle": {"disclosures": ["공시"], "global_peers": ["NVIDIA"]},
    }

    result = format_theme_report(payload)

    assert "[테마 공부 - HBM - 2026-05-29]" in result
    assert "■ 글로벌 피어" in result

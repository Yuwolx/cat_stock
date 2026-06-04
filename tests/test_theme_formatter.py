from src.formatters.theme_formatter import format_theme_report


def test_theme_formatter_includes_theme_name() -> None:
    payload = {
        "target_date": "2026-05-29",
        "is_mock_data": True,
        "theme_name": "HBM",
        "stocks": [
            {
                "name": "하나마이크론",
                "market_cap": "1.7조",
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


def test_theme_formatter_hides_empty_per_pbr_values() -> None:
    payload = {
        "target_date": "2026-05-29",
        "is_mock_data": False,
        "theme_name": "HBM",
        "stocks": [
            {
                "name": "테스트",
                "market_cap": "3조 5,680억원",
                "price": "100,000",
                "change_pct": "+1.0%",
                "per": None,
                "pbr": "",
            }
        ],
        "news_bundle": {"news": [], "reports": []},
        "peer_bundle": {"disclosures": [], "global_peers": []},
    }

    result = format_theme_report(payload)

    assert "시총 3조 5,680억원" in result
    assert "PER — | PBR —" in result
    assert "None" not in result

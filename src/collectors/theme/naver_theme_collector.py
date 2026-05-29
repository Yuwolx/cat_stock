from __future__ import annotations


def get_theme_stocks(theme_name: str, use_mock_data: bool = True) -> list[dict]:
    if use_mock_data:
        return [
            {
                "name": "하나마이크론",
                "market_cap": "1.7조",
                "price": "164,200",
                "change_pct": "+3.1%",
                "per": "34.2",
                "pbr": "6.8",
            },
            {
                "name": "ISC",
                "market_cap": "1.9조",
                "price": "72,800",
                "change_pct": "-1.4%",
                "per": "19.3",
                "pbr": "2.7",
            },
        ]
    return []

from src.ui import pages


def test_market_missing_data_warning_does_not_include_disclosures(monkeypatch) -> None:
    messages: list[str] = []
    monkeypatch.setattr(pages, "render_note", lambda message, tone="info": messages.append(message))

    pages._render_missing_data_warnings(
        {
            "investor_flows": {},
            "global_macro": {"dow": None, "sp500": None},
            "sectors": [],
        },
        "market",
    )

    assert messages
    assert "DART 공시" not in messages[0]


def test_stock_missing_data_warning_keeps_disclosures(monkeypatch) -> None:
    messages: list[str] = []
    monkeypatch.setattr(pages, "render_note", lambda message, tone="info": messages.append(message))

    pages._render_missing_data_warnings(
        {
            "basics": {"price": "70,000"},
            "flows": {"foreign_20d": "+1주"},
            "disclosures": {"disclosures": []},
            "financials": [{"quarter": "2026Q1"}],
        },
        "stock",
    )

    assert messages == ["수집 실패 항목: DART 공시 (API 키 확인 필요)"]

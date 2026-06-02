from __future__ import annotations

from bs4 import BeautifulSoup

from src.collectors.market import naver_market_collector as collector


def test_parse_rise_fall_rows_extracts_structured_fields(monkeypatch) -> None:
    html = """
    <table class="type_2">
      <tr>
        <td>1</td>
        <td><a class="tltle" href="/item/main.naver?code=123456">테스트종목</a></td>
        <td>12,300</td>
        <td>상승 700</td>
        <td>+6.03%</td>
        <td>1,200,000</td>
      </tr>
    </table>
    """

    monkeypatch.setattr(collector, "_fetch_soup", lambda url: BeautifulSoup(html, "html.parser"))

    rows = collector._parse_rise_fall_rows("https://example.com", market="KOSPI")

    assert rows == [
        {
            "name": "테스트종목",
            "code": "123456",
            "market": "KOSPI",
            "price": "12,300",
            "change_text": "상승 700",
            "change_pct": 6.03,
            "change_pct_text": "+6.03%",
        }
    ]


def test_get_rising_stocks_over_threshold_filters_and_sorts(monkeypatch) -> None:
    def fake_parse(url: str, market: str | None = None) -> list[dict]:
        if "sosok=0" in url:
            return [
                {"name": "A", "code": "000001", "market": market, "price": "1,000", "change_pct": 4.99},
                {"name": "B", "code": "000002", "market": market, "price": "2,000", "change_pct": 7.1},
            ]
        return [
            {"name": "C", "code": "000003", "market": market, "price": "3,000", "change_pct": 9.5},
        ]

    monkeypatch.setattr(collector, "_parse_rise_fall_rows", fake_parse)

    result = collector.get_rising_stocks_over_threshold(
        threshold_pct=5.0,
        limit=10,
        max_pages=1,
        use_mock_data=False,
    )

    assert [item["name"] for item in result] == ["C", "B"]

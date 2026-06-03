from __future__ import annotations

import logging

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


def test_get_market_event_lists_collects_rankings_with_page_two(monkeypatch) -> None:
    called_urls: list[str] = []

    def rows(prefix: str, start: int, count: int, sign: int) -> list[dict]:
        return [
            {
                "name": f"{prefix}{idx}",
                "code": f"{start + idx:06d}",
                "market": "KOSPI",
                "price": "1,000",
                "change_pct": sign * float(100 - idx),
                "change_pct_text": f"{sign * float(100 - idx):+.2f}%",
            }
            for idx in range(count)
        ]

    def fake_parse(url: str, market: str | None = None) -> list[dict]:
        called_urls.append(url)
        is_page_two = "page=2" in url
        if "sise_rise" in url:
            if "sosok=0" in url:
                return rows("상승코스피", 100000 if not is_page_two else 200000, 30, 1)
            return rows("상승코스닥", 300000 if not is_page_two else 400000, 10 if not is_page_two else 0, 1)
        if "sise_fall" in url:
            if "sosok=0" in url:
                return rows("하락코스피", 500000 if not is_page_two else 600000, 12, -1)
            return rows("하락코스닥", 700000 if not is_page_two else 800000, 8 if not is_page_two else 0, -1)
        return []

    monkeypatch.setattr(collector, "_parse_rise_fall_rows", fake_parse)
    monkeypatch.setattr(collector, "get_home_market_snapshot", lambda use_mock_data=False: {"upper_limit": []})
    monkeypatch.setattr(collector, "_parse_nxt_movers", lambda limit=10: [])
    monkeypatch.setattr(collector, "get_rising_stocks_over_threshold", lambda use_mock_data=False: [])

    result = collector.get_market_event_lists("2026-06-03", use_mock_data=False)

    assert len(result["new_highs"]) == 50
    assert len(result["new_lows"]) == 20
    assert any("sise_rise.naver?sosok=0&page=2" in url for url in called_urls)
    assert any("sise_fall.naver?sosok=0&page=2" in url for url in called_urls)


def test_parse_market_news_items_includes_title_url_source_and_date() -> None:
    html = """
    <ul class="newsList">
      <li class="block1">
        <dl>
          <dd class="articleSubject">
            <a href="/news/news_read.naver?article_id=0006296662&office_id=018&mode=mainnews">
              코스피 강세 지속
            </a>
          </dd>
          <dd class="articleSummary">
            요약은 쓰지 않는다.
            <span class="press">이데일리</span>
            <span class="bar">|</span>
            <span class="wdate">2026-06-03 17:15:09</span>
          </dd>
        </dl>
      </li>
    </ul>
    """

    result = collector._parse_market_news_items(BeautifulSoup(html, "html.parser"), limit=12)

    assert result == [
        {
            "title": "코스피 강세 지속",
            "url": "https://n.news.naver.com/mnews/article/018/0006296662",
            "source": "이데일리",
            "date": "2026-06-03 17:15:09",
        }
    ]


def test_market_news_url_from_href_falls_back_to_finance_url() -> None:
    assert collector._market_news_url_from_href("/news/news_read.naver?mode=mainnews") == (
        "https://finance.naver.com/news/news_read.naver?mode=mainnews"
    )


def test_get_market_news_logs_empty_parser(monkeypatch, caplog) -> None:
    monkeypatch.setattr(collector, "_fetch_soup", lambda url, encoding=None: BeautifulSoup("<html></html>", "html.parser"))

    with caplog.at_level(logging.WARNING):
        result = collector.get_market_news(use_mock_data=False)

    assert result == []
    assert "market_news" in caplog.text

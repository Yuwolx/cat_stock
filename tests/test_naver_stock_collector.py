from types import SimpleNamespace

from bs4 import BeautifulSoup

from src.collectors.stock import naver_stock_collector as collector
from src.collectors.stock.naver_stock_collector import _news_url_from_href, _parse_news_items, _parse_news_rows, _to_number


def test_to_number_preserves_negative_arrow() -> None:
    assert _to_number("▼1,234") == -1234.0


def test_to_number_preserves_positive_arrow() -> None:
    assert _to_number("▲1,234") == 1234.0


def test_to_number_returns_none_for_empty_text() -> None:
    assert _to_number("") is None


def test_parse_news_rows_includes_source_and_date_once() -> None:
    html = """
    <table>
      <tr>
        <td class="title"><a href="/item/news_read.naver?article_id=0000130547&office_id=586&code=005930">삼성전자 AI 반도체 공급 확대</a></td>
        <td class="info">서울경제</td>
        <td class="date">2026.06.01 15:44</td>
      </tr>
      <tr>
        <td class="title"><a href="/item/news_read.naver?article_id=0000130547&office_id=586&code=005930">삼성전자 AI 반도체 공급 확대</a></td>
        <td class="info">서울경제</td>
        <td class="date">2026.06.01 15:44</td>
      </tr>
    </table>
    """

    result = _parse_news_rows(BeautifulSoup(html, "html.parser"), limit=6)

    assert result == [
        "삼성전자 AI 반도체 공급 확대 (서울경제, 2026.06.01 15:44)\n"
        "  링크: https://n.news.naver.com/mnews/article/586/0000130547"
    ]


def test_parse_news_items_includes_reader_url() -> None:
    html = """
    <table>
      <tr>
        <td class="title"><a href="/item/news_read.naver?article_id=0000130547&office_id=586&code=005930">삼성전자 AI 반도체 공급 확대</a></td>
        <td class="info">서울경제</td>
        <td class="date">2026.06.01 15:44</td>
      </tr>
    </table>
    """

    result = _parse_news_items(BeautifulSoup(html, "html.parser"), limit=6)

    assert result == [
        {
            "title": "삼성전자 AI 반도체 공급 확대",
            "source": "서울경제",
            "date": "2026.06.01 15:44",
            "url": "https://n.news.naver.com/mnews/article/586/0000130547",
        }
    ]


def test_news_url_from_href_falls_back_to_finance_url() -> None:
    assert _news_url_from_href("/item/news_read.naver?code=005930") == (
        "https://finance.naver.com/item/news_read.naver?code=005930"
    )


def test_get_stock_investor_flows_uses_code_fallback_for_news(monkeypatch) -> None:
    news_items = [
        {
            "title": "삼성전자 AI 반도체 공급 확대",
            "source": "서울경제",
            "date": "2026.06.01 15:44",
            "url": "https://n.news.naver.com/mnews/article/586/0000130547",
        }
    ]

    monkeypatch.setattr(collector, "_find_stock_row", lambda stock_name: None)
    monkeypatch.setattr(collector, "get_stock_code", lambda stock_name: "005930")
    monkeypatch.setattr(collector, "_parse_investor_flow_table", lambda code: SimpleNamespace(empty=True))
    monkeypatch.setattr(collector, "_parse_report_rows", lambda code, limit=5: [])
    monkeypatch.setattr(collector, "_parse_news_items_by_code", lambda code, limit=6: news_items)

    result = collector.get_stock_investor_flows("삼성전자", use_mock_data=False)

    assert result["news_items"] == news_items
    assert result["news"] == [
        "삼성전자 AI 반도체 공급 확대 (서울경제, 2026.06.01 15:44)\n"
        "  링크: https://n.news.naver.com/mnews/article/586/0000130547"
    ]

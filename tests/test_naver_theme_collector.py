import logging

from bs4 import BeautifulSoup

from src.collectors.theme import naver_theme_collector as collector


def test_find_theme_no_uses_current_sise_group_detail_links(monkeypatch) -> None:
    html = """
    <a href="/sise/sise_group_detail.naver?type=theme&no=49">인터넷 대표주</a>
    <a href="/sise/sise_group_detail.naver?type=theme&no=497">토스(toss)</a>
    """
    monkeypatch.setattr(collector, "_fetch_soup", lambda url: BeautifulSoup(html, "html.parser"))

    assert collector._find_theme_no("인터넷 대표주") == "49"


def test_parse_stock_valuation_from_naver_main(monkeypatch) -> None:
    html = """
    <div><em id="_market_sum">3조 5,680</em> 억원</div>
    <em id="_per">24.35</em>
    <em id="_pbr">1.42</em>
    """
    monkeypatch.setattr(collector, "_fetch_soup", lambda url: BeautifulSoup(html, "html.parser"))

    assert collector._parse_stock_valuation("035420") == {
        "market_cap": "3조 5,680억원",
        "per": "24.35",
        "pbr": "1.42",
    }


def test_parse_theme_detail_enriches_market_cap_per_pbr(monkeypatch) -> None:
    html = """
    <table class="type_5">
      <tr>
        <td><a href="/item/main.naver?code=035420">NAVER</a></td>
        <td>테마 편입 사유 NAVER 인터넷 검색포털</td>
        <td>280,500</td>
        <td>상승 9,000</td>
        <td class="red">3.31%</td>
      </tr>
    </table>
    """
    monkeypatch.setattr(collector, "_fetch_soup", lambda url: BeautifulSoup(html, "html.parser"))
    monkeypatch.setattr(
        collector,
        "_parse_stock_valuation",
        lambda code: {"market_cap": "44조 31억원", "per": "24.35", "pbr": "1.42"},
    )

    assert collector._parse_theme_detail("49") == [
        {
            "name": "NAVER",
            "price": "280,500",
            "change_pct": "+3.31%",
            "market_cap": "44조 31억원",
            "per": "24.35",
            "pbr": "1.42",
        }
    ]


def test_find_theme_no_logs_when_theme_links_disappear(monkeypatch, caplog) -> None:
    monkeypatch.setattr(collector, "_fetch_soup", lambda url: BeautifulSoup("<html></html>", "html.parser"))

    with caplog.at_level(logging.WARNING):
        result = collector._find_theme_no("인터넷 대표주")

    assert result is None
    assert "theme_list" in caplog.text

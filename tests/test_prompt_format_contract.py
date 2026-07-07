"""프롬프트 텍스트 포맷 계약 테스트.

생성되는 텍스트는 외부 프롬프트 템플릿이 섹션 제목으로 참조하는 사실상의 API다.
섹션 제목·순서·헤더 형식을 바꾸면 템플릿 쪽 워크플로가 조용히 깨지므로,
포맷을 의도적으로 바꿀 때만 이 테스트를 함께 수정할 것.
"""

from src.formatters.market_formatter import format_market_briefing
from src.formatters.stock_formatter import format_stock_report
from src.formatters.theme_formatter import format_theme_report

MARKET_SECTION_TITLES = [
    "한국 지수",
    "글로벌/매크로",
    "거래대금 상위",
    "테마/그룹 등락",
    "외국인/기관 수급",
    "파생/프로그램 매매",
    "시장 이벤트",
    "주요 뉴스",
    "증권사 리포트",
]

STOCK_SECTION_TITLES = [
    "기본 정보",
    "이동평균선 위치",
    "수급",
    "재무 요약",
    "최근 공시",
    "최근 뉴스",
    "네이버 리포트",
    "증권사 리포트 (2026-05-29 ~ 2026-05-29)",
    "추가 체크",
]

THEME_SECTION_TITLES = [
    "테마 관련 종목",
    "최근 관련 뉴스",
    "관련 공시",
    "증권사 리포트 요약",
]


def _section_titles(text: str) -> list[str]:
    return [line[2:].strip() for line in text.splitlines() if line.startswith("■ ")]


def _full_market_payload() -> dict:
    return {
        "target_date": "2026-05-29",
        "is_mock_data": False,
        "collector_status": {
            key: {"status": "ok", "error": None}
            for key in [
                "indices",
                "global_macro",
                "leaders",
                "sectors",
                "investor_flows",
                "derivatives",
                "market_events",
                "news_items",
                "market_reports",
            ]
        },
        "indices": {
            "kospi": {"close": 2640.0, "change_pct": 1.0, "turnover_trillion_krw": 10, "change_points": 20},
            "kosdaq": {"close": 840.0, "change_pct": -0.5, "turnover_trillion_krw": 8, "change_points": -4},
        },
        "global_macro": {
            "dow": "+0.1%",
            "sp500": "+0.2%",
            "nasdaq": "+0.3%",
            "usdkrw": "1360.0",
            "us10y": "4.4%",
            "wti": "$77",
            "shanghai": "-0.1%",
            "shenzhen": "+0.1%",
        },
        "leaders": [{"name": "삼성전자", "price": "79,000", "change_pct": 1.2, "turnover_krw_billion": 121726.1}],
        "sectors": [{"name": "반도체", "change_pct": 1.2}],
        "investor_flows": {
            "summary": {"foreign": -67087.0, "institution": 50.0, "retail": -150},
            "by_market": {
                "kospi": {"foreign": 90.0, "institution": 40, "retail": -130},
                "kosdaq": {"foreign": 10, "institution": 10, "retail": -20},
            },
            "foreign_top_buy": ["삼성전자"],
            "foreign_top_sell": ["A"],
            "institution_top_buy": ["B"],
            "institution_top_sell": ["C"],
        },
        "derivatives": {
            "program_arbitrage": 20,
            "program_non_arbitrage": -5,
            "program_by_market": {
                "kospi": {"arbitrage": 18, "non_arbitrage": -4, "total": 14},
                "kosdaq": {"arbitrage": 2, "non_arbitrage": -1, "total": 1},
            },
        },
        "market_events": {
            "new_highs": ["A"],
            "new_lows": ["B"],
            "upper_limit": ["C"],
            "after_hours_movers": ["D +3%"],
            "rising_over_5pct": [
                {"name": "테스트종목", "market": "KOSPI", "price": "12,300", "change_pct": 6.03}
            ],
        },
        "news_items": [
            {"title": "코스피 강세", "url": "https://example.com/1", "source": "이데일리", "date": "2026-05-29"}
        ],
        "market_reports": [
            {"title": "데일리", "url": "https://example.com/2", "broker": "신한투자증권", "date": "26.05.29"}
        ],
    }


def _full_stock_payload() -> dict:
    return {
        "target_date": "2026-05-29",
        "report_date": "2026-05-29 ~ 2026-05-29",
        "is_mock_data": False,
        "basics": {
            "name": "삼성전자",
            "price": "78,500",
            "change_pct": "+1.82%",
            "turnover_krw_billion": 842,
            "market_cap": "46.8조",
            "year_high_low": "88,000 / 61,500",
            "per": "18.4",
            "pbr": "1.52",
            "roe": "12.8%",
            "ma_position": {"ma5": "상회", "ma20": "상회", "ma60": "근접"},
        },
        "flows": {
            "foreign_20d": "+1,245주",
            "institution_20d": "-342주",
            "news": ["뉴스"],
            "naver_reports": ["리포트"],
        },
        "reports": [],
        "financials": [{"quarter": "2026Q1", "sales": "20.0조", "op_income": "35000.0억", "net_income": "1"}],
        "disclosures": {
            "disclosures": ["공시"],
            "major_shareholder_ratio": "20%",
            "risk_flags": ["CB 없음"],
        },
        "short_selling": {
            "short_balance_ratio": "미제공",
            "short_sale_volume_ratio": "1.84%",
            "consensus_target_price": "91,000원",
        },
    }


def _full_theme_payload() -> dict:
    return {
        "target_date": "2026-05-29",
        "is_mock_data": False,
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
        "peer_bundle": {"disclosures": ["공시"], "global_peers": []},
    }


def test_market_section_titles_are_locked() -> None:
    result = format_market_briefing(_full_market_payload())

    assert result.splitlines()[0] == "[시황 브리핑 데이터 - 2026-05-29]"
    assert _section_titles(result) == MARKET_SECTION_TITLES


def test_stock_section_titles_are_locked() -> None:
    result = format_stock_report(_full_stock_payload())

    assert result.splitlines()[0] == "[개별 종목 분석 - 삼성전자 - 2026-05-29]"
    assert _section_titles(result) == STOCK_SECTION_TITLES


def test_theme_section_titles_are_locked() -> None:
    result = format_theme_report(_full_theme_payload())

    assert result.splitlines()[0] == "[테마 공부 - HBM - 2026-05-29]"
    assert _section_titles(result) == THEME_SECTION_TITLES


def test_full_payload_has_no_data_status_section() -> None:
    for text in [
        format_market_briefing(_full_market_payload()),
        format_stock_report(_full_stock_payload()),
        format_theme_report(_full_theme_payload()),
    ]:
        assert "데이터 수집 안내" not in text


def test_market_collector_failure_is_stated_in_text() -> None:
    payload = _full_market_payload()
    payload["collector_status"]["investor_flows"] = {"status": "error", "error": "boom"}
    payload["collector_status"]["market_reports"] = {"status": "empty", "error": None}

    result = format_market_briefing(payload)

    assert "■ 데이터 수집 안내" in result
    assert "외국인/기관 수급 (수집 오류)" in result
    assert "증권사 리포트 (빈 결과)" in result
    assert "추정하거나 일반론으로 채우지 말고" in result


def test_stock_missing_data_is_stated_in_text() -> None:
    payload = _full_stock_payload()
    payload["basics"]["price"] = None
    payload["financials"] = []

    result = format_stock_report(payload)

    assert "■ 데이터 수집 안내" in result
    assert "기본 시세 (종목명 확인 필요)" in result
    assert "재무 요약 (API 키 확인 필요)" in result


def test_theme_missing_data_is_stated_in_text() -> None:
    payload = _full_theme_payload()
    payload["stocks"] = []
    payload["news_bundle"]["news"] = []

    result = format_theme_report(payload)

    assert "■ 데이터 수집 안내" in result
    assert "테마 관련 종목 (테마명 재확인)" in result
    assert "관련 뉴스" in result

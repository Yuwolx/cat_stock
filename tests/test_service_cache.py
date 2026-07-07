from src.services import market_service, theme_service
from tests.test_stock_parallel_service import _date_context


def _patch_market_collectors(monkeypatch, calls: list[str]) -> None:
    def counted(name, value):
        def collector(*args, **kwargs):
            calls.append(name)
            return value

        return collector

    # 모든 수집기를 '정상(비어있지 않음)'으로 — 저장 가능 조건을 만족시키기 위함
    monkeypatch.setattr(market_service, "resolve_stock_trading_date", lambda target_date: _date_context("2026-06-03"))
    monkeypatch.setattr(market_service, "get_market_indices", counted("indices", {"kospi": {"close": 1.0}}))
    monkeypatch.setattr(market_service, "get_korean_index_trend", counted("index_trend", {"kospi": {"closes": [1.0, 2.0]}}))
    monkeypatch.setattr(market_service, "get_global_macro_snapshot", counted("macro", {"dow": "+1%"}))
    monkeypatch.setattr(market_service, "get_trading_value_leaders", counted("leaders", [{"name": "A"}]))
    monkeypatch.setattr(market_service, "get_sector_changes", counted("sectors", [{"name": "반도체", "change_pct": 1.2}]))
    monkeypatch.setattr(market_service, "get_investor_flows", counted("flows", {"summary": {"foreign": 1}}))
    monkeypatch.setattr(market_service, "get_derivatives_snapshot", counted("derivatives", {"program_total": 1}))
    monkeypatch.setattr(market_service, "get_market_event_lists", counted("events", {"new_highs": ["A"]}))
    monkeypatch.setattr(market_service, "get_market_news", counted("news", [{"title": "뉴스"}]))
    monkeypatch.setattr(market_service, "get_market_reports", counted("reports", [{"title": "리포트"}]))
    monkeypatch.setattr(market_service, "generate_market_column", lambda payload: {"is_available": False, "reason": "x"})
    monkeypatch.setattr(market_service, "format_market_briefing", lambda payload: "market text")
    monkeypatch.setattr(market_service, "save_output_text", lambda prefix, target_date, text: "/tmp/market.txt")


def test_market_briefing_is_cached_within_ttl(monkeypatch) -> None:
    calls: list[str] = []
    _patch_market_collectors(monkeypatch, calls)

    first = market_service.generate_market_briefing("2026-06-03", use_mock_data=False)
    count_after_first = len(calls)
    second = market_service.generate_market_briefing("2026-06-03", use_mock_data=False)

    assert count_after_first > 0
    assert len(calls) == count_after_first  # 두 번째 호출은 수집기를 다시 부르지 않음
    assert second is first


def test_market_briefing_cache_is_per_date(monkeypatch) -> None:
    calls: list[str] = []
    _patch_market_collectors(monkeypatch, calls)
    # 날짜별 캐시 검증이므로 resolve가 요청일을 그대로 반영해야 한다
    monkeypatch.setattr(market_service, "resolve_stock_trading_date", lambda target_date: _date_context(target_date))

    market_service.generate_market_briefing("2026-06-03", use_mock_data=False)
    count_after_first = len(calls)
    market_service.generate_market_briefing("2026-06-04", use_mock_data=False)

    assert len(calls) == count_after_first * 2


def test_theme_report_is_cached_within_ttl(monkeypatch) -> None:
    calls: list[str] = []

    monkeypatch.setattr(theme_service, "get_theme_stocks", lambda name, use_mock_data=False: calls.append("stocks") or [])
    monkeypatch.setattr(theme_service, "get_theme_news", lambda name, use_mock_data=False: {"news": [], "reports": []})
    monkeypatch.setattr(
        theme_service,
        "get_theme_peers",
        lambda name, api_key="", use_mock_data=False: {"disclosures": [], "global_peers": []},
    )
    monkeypatch.setattr(theme_service, "format_theme_report", lambda payload: "theme text")
    monkeypatch.setattr(theme_service, "save_output_text", lambda prefix, target_date, text: "/tmp/theme.txt")

    theme_service.generate_theme_report("HBM", use_mock_data=False)
    theme_service.generate_theme_report("HBM", use_mock_data=False)

    assert calls == ["stocks"]

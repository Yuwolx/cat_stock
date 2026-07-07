from types import SimpleNamespace

from src.services import market_service, stock_service


def _date_context(day: str, *, requested: str = None, adjusted: bool = False) -> dict:
    requested_day = requested or day
    return {
        "requested_date": requested_day,
        "target_date": day,
        "resolved_date": day,
        "requested_weekday": "수",
        "resolved_weekday": "수",
        "is_adjusted": adjusted,
        "basis": "test",
        "resolved_label": f"{day} 수요일",
        "date_note": f"분석 기준일: {day} 수요일",
    }


def test_market_parallel_payload_matches_sequential_result(monkeypatch) -> None:
    indices = {"kospi": {"close": 1}, "kosdaq": {"close": 2}}
    index_trend = {"kospi": {"closes": [1.0, 2.0]}, "kosdaq": {"closes": [3.0, 4.0]}}
    macro = {"dow": "+1%"}
    leaders = [{"name": "A"}]
    sectors = [{"name": "반도체", "change_pct": 1.2}]
    flows = {"summary": {"foreign": 1, "institution": 2, "retail": 3}}
    derivatives = {"futures_foreign_net": None, "futures_institution_net": None, "program_total": 4}
    events = {"new_highs": ["A"], "new_lows": [], "upper_limit": [], "after_hours_movers": [], "rising_over_5pct": []}
    news_items = [{"title": "시장 뉴스", "url": "https://n.news.naver.com/mnews/article/001/0000000001", "source": "연합", "date": "2026-06-03"}]
    market_reports = [{"title": "시황 리포트", "url": "https://finance.naver.com/research/market_info_read.naver?nid=1&page=1", "broker": "증권사", "date": "26.06.04"}]
    column = {"is_available": False, "reason": "missing_api_key", "title": None, "body": None}
    date_context = _date_context("2026-06-03")

    monkeypatch.setattr(market_service, "resolve_stock_trading_date", lambda target_date: date_context)
    monkeypatch.setattr(market_service, "get_market_indices", lambda target_date, use_mock_data=False: indices)
    monkeypatch.setattr(market_service, "get_korean_index_trend", lambda target_date, use_mock_data=False: index_trend)
    monkeypatch.setattr(market_service, "get_global_macro_snapshot", lambda target_date, use_mock_data=False: macro)
    monkeypatch.setattr(market_service, "get_trading_value_leaders", lambda target_date, use_mock_data=False: leaders)
    monkeypatch.setattr(market_service, "get_sector_changes", lambda use_mock_data=False: sectors)
    monkeypatch.setattr(market_service, "get_investor_flows", lambda target_date, use_mock_data=False: flows)
    monkeypatch.setattr(market_service, "get_derivatives_snapshot", lambda target_date, use_mock_data=False: derivatives.copy())
    monkeypatch.setattr(market_service, "get_market_event_lists", lambda target_date, use_mock_data=False: events)
    monkeypatch.setattr(market_service, "get_market_news", lambda use_mock_data=False: news_items)
    monkeypatch.setattr(market_service, "get_market_reports", lambda use_mock_data=False: market_reports)
    monkeypatch.setattr(market_service, "generate_market_column", lambda payload: column)
    monkeypatch.setattr(market_service, "format_market_briefing", lambda payload: "market text")
    monkeypatch.setattr(market_service, "save_output_text", lambda prefix, target_date, text: "/tmp/market.txt")

    result = market_service.generate_market_briefing("2026-06-03", use_mock_data=False)

    assert result["payload"] == {
        **date_context,
        "is_mock_data": False,
        "indices": indices,
        "index_trend": index_trend,
        "global_macro": macro,
        "leaders": leaders,
        "sectors": sectors,
        "investor_flows": flows,
        "derivatives": derivatives,
        "market_events": events,
        "news_items": news_items,
        "market_reports": market_reports,
        "collector_status": {
            "indices": {"status": "ok", "error": None},
            "index_trend": {"status": "ok", "error": None},
            "global_macro": {"status": "ok", "error": None},
            "leaders": {"status": "ok", "error": None},
            "sectors": {"status": "ok", "error": None},
            "investor_flows": {"status": "ok", "error": None},
            "derivatives": {"status": "ok", "error": None},
            "market_events": {"status": "ok", "error": None},
            "news_items": {"status": "ok", "error": None},
            "market_reports": {"status": "ok", "error": None},
        },
        "column": column,
    }
    assert "disclosures" not in result["payload"]


def test_market_parallel_collector_failure_keeps_remaining_payload(monkeypatch) -> None:
    def broken_sectors(use_mock_data=False):
        raise RuntimeError("sector failed")

    monkeypatch.setattr(market_service, "resolve_stock_trading_date", lambda target_date: _date_context("2026-06-03"))
    monkeypatch.setattr(market_service, "get_market_indices", lambda target_date, use_mock_data=False: {"kospi": {}})
    monkeypatch.setattr(market_service, "get_korean_index_trend", lambda target_date, use_mock_data=False: {})
    monkeypatch.setattr(market_service, "get_global_macro_snapshot", lambda target_date, use_mock_data=False: {"dow": "+1%"})
    monkeypatch.setattr(market_service, "get_trading_value_leaders", lambda target_date, use_mock_data=False: [{"name": "A"}])
    monkeypatch.setattr(market_service, "get_sector_changes", broken_sectors)
    monkeypatch.setattr(market_service, "get_investor_flows", lambda target_date, use_mock_data=False: {"summary": {}})
    monkeypatch.setattr(market_service, "get_derivatives_snapshot", lambda target_date, use_mock_data=False: {"program_total": 1})
    monkeypatch.setattr(market_service, "get_market_event_lists", lambda target_date, use_mock_data=False: {"new_highs": []})
    monkeypatch.setattr(market_service, "get_market_news", lambda use_mock_data=False: [])
    monkeypatch.setattr(market_service, "get_market_reports", lambda use_mock_data=False: [])
    monkeypatch.setattr(market_service, "generate_market_column", lambda payload: {"is_available": False, "reason": "x"})
    monkeypatch.setattr(market_service, "format_market_briefing", lambda payload: "market text")
    monkeypatch.setattr(market_service, "save_output_text", lambda prefix, target_date, text: "/tmp/market.txt")

    payload = market_service.generate_market_briefing("2026-06-03", use_mock_data=False)["payload"]

    assert payload["leaders"] == [{"name": "A"}]
    assert payload["sectors"] == []
    assert payload["collector_status"]["sectors"]["status"] == "error"
    assert "sector failed" in payload["collector_status"]["sectors"]["error"]


def test_market_parallel_keeps_derivatives_without_unsupported_kis_overlay(monkeypatch) -> None:
    derivatives = {
        "futures_foreign_net": None,
        "futures_institution_net": -1,
        "program_total": 4,
    }

    monkeypatch.setattr(market_service, "resolve_stock_trading_date", lambda target_date: _date_context("2026-06-03"))
    monkeypatch.setattr(market_service, "get_market_indices", lambda target_date, use_mock_data=False: {"kospi": {}})
    monkeypatch.setattr(market_service, "get_korean_index_trend", lambda target_date, use_mock_data=False: {})
    monkeypatch.setattr(market_service, "get_global_macro_snapshot", lambda target_date, use_mock_data=False: {})
    monkeypatch.setattr(market_service, "get_trading_value_leaders", lambda target_date, use_mock_data=False: [])
    monkeypatch.setattr(market_service, "get_sector_changes", lambda use_mock_data=False: [])
    monkeypatch.setattr(market_service, "get_investor_flows", lambda target_date, use_mock_data=False: {"summary": {}})
    monkeypatch.setattr(market_service, "get_derivatives_snapshot", lambda target_date, use_mock_data=False: derivatives.copy())
    monkeypatch.setattr(market_service, "get_market_event_lists", lambda target_date, use_mock_data=False: {"new_highs": []})
    monkeypatch.setattr(market_service, "get_market_news", lambda use_mock_data=False: [])
    monkeypatch.setattr(market_service, "get_market_reports", lambda use_mock_data=False: [])
    monkeypatch.setattr(market_service, "generate_market_column", lambda payload: {"is_available": False, "reason": "x"})
    monkeypatch.setattr(market_service, "format_market_briefing", lambda payload: "market text")
    monkeypatch.setattr(market_service, "save_output_text", lambda prefix, target_date, text: "/tmp/market.txt")

    payload = market_service.generate_market_briefing("2026-06-03", use_mock_data=False)["payload"]

    assert payload["derivatives"]["futures_foreign_net"] is None
    assert payload["derivatives"]["futures_institution_net"] == -1


def test_market_weekend_request_collects_resolved_trading_date(monkeypatch) -> None:
    collected_dates: list[str] = []
    date_context = _date_context("2026-06-26", requested="2026-06-28", adjusted=True)

    def record_date(target_date, use_mock_data=False):
        collected_dates.append(target_date)
        return {"kospi": {}, "kosdaq": {}}

    monkeypatch.setattr(market_service, "resolve_stock_trading_date", lambda target_date: date_context)
    monkeypatch.setattr(market_service, "get_market_indices", record_date)
    monkeypatch.setattr(market_service, "get_korean_index_trend", lambda target_date, use_mock_data=False: {})
    monkeypatch.setattr(market_service, "get_global_macro_snapshot", lambda target_date, use_mock_data=False: {})
    monkeypatch.setattr(market_service, "get_trading_value_leaders", lambda target_date, use_mock_data=False: [])
    monkeypatch.setattr(market_service, "get_sector_changes", lambda use_mock_data=False: [])
    monkeypatch.setattr(market_service, "get_investor_flows", lambda target_date, use_mock_data=False: {"summary": {}})
    monkeypatch.setattr(market_service, "get_derivatives_snapshot", lambda target_date, use_mock_data=False: {"program_total": 1})
    monkeypatch.setattr(market_service, "get_market_event_lists", lambda target_date, use_mock_data=False: {"new_highs": []})
    monkeypatch.setattr(market_service, "get_market_news", lambda use_mock_data=False: [])
    monkeypatch.setattr(market_service, "get_market_reports", lambda use_mock_data=False: [])
    monkeypatch.setattr(market_service, "generate_market_column", lambda payload: {"is_available": False, "reason": "x"})
    monkeypatch.setattr(market_service, "format_market_briefing", lambda payload: "market text")
    monkeypatch.setattr(market_service, "save_output_text", lambda prefix, target_date, text: f"/tmp/{target_date}.txt")

    result = market_service.generate_market_briefing("2026-06-28", use_mock_data=False)

    assert collected_dates == ["2026-06-26"]
    assert result["payload"]["requested_date"] == "2026-06-28"
    assert result["payload"]["target_date"] == "2026-06-26"


def test_stock_parallel_payload_matches_sequential_result_and_primes_kis(monkeypatch) -> None:
    calls: list[str] = []
    basics = {"name": "삼성전자", "price": "70,000", "ma_position": {}}
    flows = {"foreign_20d": "+1주", "institution_20d": "-1주", "news": [], "news_items": [], "naver_reports": []}
    financials = [{"quarter": "2026Q1", "sales": "1", "op_income": "2", "net_income": "3"}]
    disclosures = {"disclosures": ["공시"], "major_shareholder_ratio": "10%", "risk_flags": []}
    naver_snapshot = {"short_balance_ratio": "1.00%", "consensus_target_price": "90,000원"}
    kis_flow = {"foreign_20d_krw": "+10.0억", "institution_20d_krw": "-5.0억"}
    reports = [{"title": "리포트"}]
    column = {"is_available": True, "reason": "ok", "title": "제목", "body": "본문"}

    monkeypatch.setattr(
        stock_service,
        "get_settings",
        lambda: SimpleNamespace(dart_api_key="dart-key", kis_app_key="kis-key", kis_app_secret="kis-secret"),
    )
    monkeypatch.setattr(stock_service, "resolve_stock_trading_date", lambda value=None: _date_context(value or "2026-06-03"))
    monkeypatch.setattr(stock_service, "get_stock_code", lambda stock_name: calls.append("code") or "005930")
    monkeypatch.setattr(stock_service, "get_token", lambda app_key, app_secret: calls.append("token") or "token")
    monkeypatch.setattr(stock_service, "get_stock_basics", lambda stock_name, use_mock_data=False: basics)
    monkeypatch.setattr(stock_service, "get_stock_investor_flows", lambda stock_name, use_mock_data=False: flows)
    monkeypatch.setattr(
        stock_service,
        "get_financial_summary",
        lambda stock_name, api_key="", use_mock_data=False: financials,
    )
    monkeypatch.setattr(
        stock_service,
        "get_stock_disclosures",
        lambda stock_name, api_key="", use_mock_data=False: disclosures,
    )
    monkeypatch.setattr(stock_service, "get_short_selling_snapshot", lambda stock_name, use_mock_data=False: naver_snapshot)
    monkeypatch.setattr(stock_service, "get_fnguide_reports", lambda code, from_date, to_date: reports)
    monkeypatch.setattr(
        stock_service,
        "get_stock_investor_flow_krw",
        lambda code, app_key, app_secret: calls.append("kis_flow") or kis_flow,
    )
    monkeypatch.setattr(
        stock_service,
        "get_short_selling_ratio",
        lambda code, app_key, app_secret: calls.append("kis_short") or "2.00%",
    )
    monkeypatch.setattr(stock_service, "generate_stock_column", lambda payload: column)
    monkeypatch.setattr(stock_service, "format_stock_report", lambda payload: "stock text")
    monkeypatch.setattr(stock_service, "save_output_text", lambda prefix, target_date, text: "/tmp/stock.txt")

    result = stock_service.generate_stock_report("삼성전자", "2026-06-01", "2026-06-03", use_mock_data=False)

    assert calls[:2] == ["code", "token"]
    assert calls.count("token") == 1
    assert result["payload"] == {
        **_date_context("2026-06-03"),
        "report_date": "2026-06-01 ~ 2026-06-03",
        "requested_report_date": "2026-06-01 ~ 2026-06-03",
        "is_mock_data": False,
        "basics": basics,
        "flows": flows,
        "financials": financials,
        "disclosures": disclosures,
        "short_selling": {
            "short_balance_ratio": "미제공",
            "short_sale_volume_ratio": "2.00%",
            "consensus_target_price": "90,000원",
        },
        "kis_flow": kis_flow,
        "reports": reports,
        "column": column,
    }


def test_stock_parallel_collector_failure_keeps_remaining_payload(monkeypatch) -> None:
    def broken_financials(stock_name, api_key="", use_mock_data=False):
        raise RuntimeError("dart failed")

    flows = {"foreign_20d": "+1주", "institution_20d": "-1주", "news": [], "news_items": [], "naver_reports": []}

    monkeypatch.setattr(
        stock_service,
        "get_settings",
        lambda: SimpleNamespace(dart_api_key="", kis_app_key="", kis_app_secret=""),
    )
    monkeypatch.setattr(stock_service, "resolve_stock_trading_date", lambda value=None: _date_context(value or "2026-06-03"))
    monkeypatch.setattr(stock_service, "get_stock_code", lambda stock_name: "005930")
    monkeypatch.setattr(stock_service, "get_stock_basics", lambda stock_name, use_mock_data=False: {"name": stock_name})
    monkeypatch.setattr(stock_service, "get_stock_investor_flows", lambda stock_name, use_mock_data=False: flows)
    monkeypatch.setattr(stock_service, "get_financial_summary", broken_financials)
    monkeypatch.setattr(
        stock_service,
        "get_stock_disclosures",
        lambda stock_name, api_key="", use_mock_data=False: {"disclosures": [], "major_shareholder_ratio": None, "risk_flags": []},
    )
    monkeypatch.setattr(
        stock_service,
        "get_short_selling_snapshot",
        lambda stock_name, use_mock_data=False: {"short_balance_ratio": None, "consensus_target_price": None},
    )
    monkeypatch.setattr(stock_service, "get_fnguide_reports", lambda code, from_date, to_date: [])
    monkeypatch.setattr(stock_service, "generate_stock_column", lambda payload: {"is_available": False, "reason": "x"})
    monkeypatch.setattr(stock_service, "format_stock_report", lambda payload: "stock text")
    monkeypatch.setattr(stock_service, "save_output_text", lambda prefix, target_date, text: "/tmp/stock.txt")

    payload = stock_service.generate_stock_report("삼성전자", use_mock_data=False)["payload"]

    assert payload["flows"] == flows
    assert payload["financials"] == []

from types import SimpleNamespace

from src.services import market_service, stock_service


def test_market_parallel_payload_matches_sequential_result(monkeypatch) -> None:
    indices = {"kospi": {"close": 1}, "kosdaq": {"close": 2}}
    macro = {"dow": "+1%"}
    leaders = [{"name": "A"}]
    sectors = [{"name": "반도체", "change_pct": 1.2}]
    flows = {"summary": {"foreign": 1, "institution": 2, "retail": 3}}
    derivatives = {"futures_foreign_net": None, "futures_institution_net": None, "program_total": 4}
    events = {"new_highs": ["A"], "new_lows": [], "upper_limit": [], "after_hours_movers": [], "rising_over_5pct": []}
    disclosures = ["A: 공시"]
    column = {"is_available": False, "reason": "missing_api_key", "title": None, "body": None}

    monkeypatch.setattr(
        market_service,
        "get_settings",
        lambda: SimpleNamespace(dart_api_key="dart-key", kis_app_key="", kis_app_secret=""),
    )
    monkeypatch.setattr(market_service, "get_market_indices", lambda target_date, use_mock_data=False: indices)
    monkeypatch.setattr(market_service, "get_global_macro_snapshot", lambda target_date, use_mock_data=False: macro)
    monkeypatch.setattr(market_service, "get_trading_value_leaders", lambda target_date, use_mock_data=False: leaders)
    monkeypatch.setattr(market_service, "get_sector_changes", lambda use_mock_data=False: sectors)
    monkeypatch.setattr(market_service, "get_investor_flows", lambda target_date, use_mock_data=False: flows)
    monkeypatch.setattr(market_service, "get_derivatives_snapshot", lambda target_date, use_mock_data=False: derivatives.copy())
    monkeypatch.setattr(market_service, "get_market_event_lists", lambda target_date, use_mock_data=False: events)
    monkeypatch.setattr(
        market_service,
        "get_major_disclosures",
        lambda target_date, api_key="", use_mock_data=False: disclosures,
    )
    monkeypatch.setattr(market_service, "generate_market_column", lambda payload: column)
    monkeypatch.setattr(market_service, "format_market_briefing", lambda payload: "market text")
    monkeypatch.setattr(market_service, "save_output_text", lambda prefix, target_date, text: "/tmp/market.txt")

    result = market_service.generate_market_briefing("2026-06-03", use_mock_data=False)

    assert result["payload"] == {
        "target_date": "2026-06-03",
        "is_mock_data": False,
        "indices": indices,
        "global_macro": macro,
        "leaders": leaders,
        "sectors": sectors,
        "investor_flows": flows,
        "derivatives": derivatives,
        "market_events": events,
        "disclosures": disclosures,
        "column": column,
    }


def test_market_parallel_collector_failure_keeps_remaining_payload(monkeypatch) -> None:
    def broken_sectors(use_mock_data=False):
        raise RuntimeError("sector failed")

    monkeypatch.setattr(
        market_service,
        "get_settings",
        lambda: SimpleNamespace(dart_api_key="", kis_app_key="", kis_app_secret=""),
    )
    monkeypatch.setattr(market_service, "get_market_indices", lambda target_date, use_mock_data=False: {"kospi": {}})
    monkeypatch.setattr(market_service, "get_global_macro_snapshot", lambda target_date, use_mock_data=False: {"dow": "+1%"})
    monkeypatch.setattr(market_service, "get_trading_value_leaders", lambda target_date, use_mock_data=False: [{"name": "A"}])
    monkeypatch.setattr(market_service, "get_sector_changes", broken_sectors)
    monkeypatch.setattr(market_service, "get_investor_flows", lambda target_date, use_mock_data=False: {"summary": {}})
    monkeypatch.setattr(market_service, "get_derivatives_snapshot", lambda target_date, use_mock_data=False: {"program_total": 1})
    monkeypatch.setattr(market_service, "get_market_event_lists", lambda target_date, use_mock_data=False: {"new_highs": []})
    monkeypatch.setattr(market_service, "get_major_disclosures", lambda target_date, api_key="", use_mock_data=False: [])
    monkeypatch.setattr(market_service, "generate_market_column", lambda payload: {"is_available": False, "reason": "x"})
    monkeypatch.setattr(market_service, "format_market_briefing", lambda payload: "market text")
    monkeypatch.setattr(market_service, "save_output_text", lambda prefix, target_date, text: "/tmp/market.txt")

    payload = market_service.generate_market_briefing("2026-06-03", use_mock_data=False)["payload"]

    assert payload["leaders"] == [{"name": "A"}]
    assert payload["sectors"] == []


def test_market_parallel_primes_kis_and_applies_overlay_after_derivatives(monkeypatch) -> None:
    calls: list[str] = []
    derivatives = {
        "futures_foreign_net": None,
        "futures_institution_net": -1,
        "program_total": 4,
    }

    monkeypatch.setattr(
        market_service,
        "get_settings",
        lambda: SimpleNamespace(dart_api_key="", kis_app_key="kis-key", kis_app_secret="kis-secret"),
    )
    monkeypatch.setattr(market_service, "get_token", lambda app_key, app_secret: calls.append("token") or "token")
    monkeypatch.setattr(market_service, "get_market_indices", lambda target_date, use_mock_data=False: {"kospi": {}})
    monkeypatch.setattr(market_service, "get_global_macro_snapshot", lambda target_date, use_mock_data=False: {})
    monkeypatch.setattr(market_service, "get_trading_value_leaders", lambda target_date, use_mock_data=False: [])
    monkeypatch.setattr(market_service, "get_sector_changes", lambda use_mock_data=False: [])
    monkeypatch.setattr(market_service, "get_investor_flows", lambda target_date, use_mock_data=False: {"summary": {}})
    monkeypatch.setattr(market_service, "get_derivatives_snapshot", lambda target_date, use_mock_data=False: derivatives.copy())
    monkeypatch.setattr(market_service, "get_market_event_lists", lambda target_date, use_mock_data=False: {"new_highs": []})
    monkeypatch.setattr(market_service, "get_major_disclosures", lambda target_date, api_key="", use_mock_data=False: [])
    monkeypatch.setattr(
        market_service,
        "get_futures_investor_flow",
        lambda app_key, app_secret: calls.append("kis_futures") or {
            "futures_foreign_net": 100,
            "futures_institution_net": None,
        },
    )
    monkeypatch.setattr(market_service, "generate_market_column", lambda payload: {"is_available": False, "reason": "x"})
    monkeypatch.setattr(market_service, "format_market_briefing", lambda payload: "market text")
    monkeypatch.setattr(market_service, "save_output_text", lambda prefix, target_date, text: "/tmp/market.txt")

    payload = market_service.generate_market_briefing("2026-06-03", use_mock_data=False)["payload"]

    assert calls == ["token", "kis_futures"]
    assert payload["derivatives"]["futures_foreign_net"] == 100
    assert payload["derivatives"]["futures_institution_net"] == -1


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
    monkeypatch.setattr(stock_service, "today_kst_string", lambda: "2026-06-03")
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
        "target_date": "2026-06-03",
        "report_date": "2026-06-01 ~ 2026-06-03",
        "is_mock_data": False,
        "basics": basics,
        "flows": flows,
        "financials": financials,
        "disclosures": disclosures,
        "short_selling": {"short_balance_ratio": "2.00%", "consensus_target_price": "90,000원"},
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
    monkeypatch.setattr(stock_service, "today_kst_string", lambda: "2026-06-03")
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

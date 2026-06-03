from pytest import approx

from src.collectors.coin import binance_futures_client as client


def test_get_futures_risk_parses_funding_and_open_interest(monkeypatch) -> None:
    def fake_get_json(path, params=None):
        if path == "/fapi/v1/fundingRate":
            return [
                {"fundingRate": "0.0001", "markPrice": "100.0"},
                {"fundingRate": "0.0003", "markPrice": "110.0"},
            ]
        if path == "/fapi/v1/openInterest":
            return {"openInterest": "1234.5"}
        if path == "/futures/data/openInterestHist":
            return [
                {"sumOpenInterestValue": "1000"},
                {"sumOpenInterestValue": "1200"},
            ]
        raise AssertionError(path)

    monkeypatch.setattr(client, "_get_json", fake_get_json)

    result = client.get_futures_risk("btc", use_mock_data=False)

    assert result["symbol"] == "BTCUSDT"
    assert result["contract_type"] == "PERPETUAL"
    assert result["contract_label"] == "USD-M 무기한 선물"
    assert result["is_available"] is True
    assert result["mark_price_usd"] == 110.0
    assert result["latest_funding_rate_pct"] == 0.03
    assert result["avg_funding_rate_pct"] == approx(0.02)
    assert result["annualized_funding_pct"] == approx(21.9)
    assert result["open_interest"] == 1234.5
    assert result["open_interest_value_usd"] == 1200.0
    assert result["open_interest_change_24h_pct"] == approx(20.0)
    assert result["warning"] == "OI 급증 주의"


def test_get_futures_risk_marks_empty_success_response_unavailable(monkeypatch) -> None:
    def fake_get_json(path, params=None):
        if path == "/fapi/v1/fundingRate":
            return []
        if path == "/fapi/v1/openInterest":
            return {}
        if path == "/futures/data/openInterestHist":
            return []
        raise AssertionError(path)

    monkeypatch.setattr(client, "_get_json", fake_get_json)

    result = client.get_futures_risk("unknown", use_mock_data=False)

    assert result["symbol"] == "UNKNOWNUSDT"
    assert result["contract_type"] == "PERPETUAL"
    assert result["is_available"] is False
    assert result["latest_funding_rate_pct"] is None
    assert result["open_interest_value_usd"] is None
    assert result["warning"] == "데이터 없음"

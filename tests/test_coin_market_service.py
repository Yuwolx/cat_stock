from src.services.coin_market_service import generate_coin_market_report


def test_coin_market_report_does_not_emit_approximate_dominance_chart() -> None:
    result = generate_coin_market_report(use_mock_data=True)

    assert "dominance" not in result["payload"]["charts"]

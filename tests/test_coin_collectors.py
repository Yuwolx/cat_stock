import pytest

from src.collectors.coin import defillama_client


def test_find_protocol_for_coin_mock_uses_mock_fees(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_live_fees() -> dict:
        raise AssertionError("mock mode should not call live DefiLlama fees")

    monkeypatch.setattr(defillama_client, "_get_fees_live", fail_live_fees)

    result = defillama_client.find_protocol_for_coin("aave", symbol="AAVE", name="Aave", use_mock_data=True)

    assert result is not None
    assert result["name"] == "Aave"
    assert result["fees_24h"] == 2_100_000
    assert result["fees_7d"] == 15_000_000

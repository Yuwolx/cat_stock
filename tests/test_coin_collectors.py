import pytest

from src.collectors.coin import coingecko_client, defillama_client


def test_find_protocol_for_coin_mock_uses_mock_fees(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_live_fees() -> dict:
        raise AssertionError("mock mode should not call live DefiLlama fees")

    monkeypatch.setattr(defillama_client, "_get_fees_live", fail_live_fees)

    result = defillama_client.find_protocol_for_coin("aave", symbol="AAVE", name="Aave", use_mock_data=True)

    assert result is not None
    assert result["name"] == "Aave"
    assert result["fees_24h"] == 2_100_000
    assert result["fees_7d"] == 15_000_000


def test_coingecko_rate_limit_sets_status(monkeypatch: pytest.MonkeyPatch) -> None:
    class Response:
        status_code = 429
        headers = {"retry-after": "0"}

        @staticmethod
        def raise_for_status() -> None:
            raise RuntimeError("429")

    monkeypatch.setattr(coingecko_client.requests, "get", lambda *args, **kwargs: Response())
    monkeypatch.setattr(coingecko_client.time, "sleep", lambda seconds: None)
    coingecko_client.reset_coingecko_status()

    assert coingecko_client.get_coin_markets(use_mock_data=False) == []
    assert coingecko_client.get_coingecko_status()["rate_limited"] is True

from src.collectors.coin import upbit_client
from src.utils.ttl_cache import clear_ttl_cache


def test_coin_http_client_uses_ttl_cache(monkeypatch) -> None:
    calls: list[str] = []

    class Response:
        @staticmethod
        def raise_for_status() -> None:
            return None

        @staticmethod
        def json() -> dict:
            return {"ok": True}

    def fake_get(url: str, params: dict, headers: dict, timeout: int) -> Response:
        calls.append(url)
        return Response()

    clear_ttl_cache()
    monkeypatch.setattr(upbit_client.requests, "get", fake_get)

    assert upbit_client._get_json("/market/all", params={"isDetails": "true"}) == {"ok": True}
    assert upbit_client._get_json("/market/all", params={"isDetails": "true"}) == {"ok": True}
    assert len(calls) == 1

from src.collectors.stock import kis_stock_collector as collector


def test_get_short_selling_ratio_uses_verified_daily_short_sale_field(monkeypatch) -> None:
    calls: list[dict] = []

    def fake_kis_get(path: str, tr_id: str, params: dict, app_key: str, app_secret: str) -> dict:
        calls.append({"path": path, "tr_id": tr_id, "params": params})
        return {"output2": [{"stck_bsop_date": "20260603", "ssts_vol_rlim": "1.23"}]}

    monkeypatch.setattr(collector, "kis_get", fake_kis_get)

    result = collector.get_short_selling_ratio("005930", "app", "secret")

    assert result == "1.23%"
    assert calls == [
        {
            "path": "/uapi/domestic-stock/v1/quotations/daily-short-sale",
            "tr_id": "FHPST04830000",
            "params": {
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": "005930",
                "FID_INPUT_DATE_1": "",
                "FID_INPUT_DATE_2": "",
            },
        }
    ]


def test_get_short_selling_ratio_ignores_unverified_balance_fields(monkeypatch) -> None:
    monkeypatch.setattr(
        collector,
        "kis_get",
        lambda *args, **kwargs: {"output2": [{"ssts_rto": "9.99", "loan_bal_rto": "8.88"}]},
    )

    assert collector.get_short_selling_ratio("005930", "app", "secret") is None

from __future__ import annotations

from src.collectors.kis_client import kis_get


def get_futures_investor_flow(app_key: str, app_secret: str) -> dict:
    """
    코스피200 선물 투자자별 매매동향 (KIS API).
    반환: { futures_foreign_net, futures_institution_net }  단위: 계약 수
    """
    try:
        data = kis_get(
            path="/uapi/domestic-futureoption/v1/quotations/inquire-futures-investor",
            tr_id="FHKST01010400",
            params={
                "FID_COND_MRKT_DIV_CODE": "F",
                "FID_INPUT_ISCD": "101W09",  # 코스피200 선물 근월물 (매월 갱신 필요)
            },
            app_key=app_key,
            app_secret=app_secret,
        )
        output = data.get("output")
        if not output:
            return {"futures_foreign_net": None, "futures_institution_net": None}

        row = output[0] if isinstance(output, list) else output
        def _to_int(val: str | None) -> int | None:
            if not val:
                return None
            try:
                return int(val)
            except (ValueError, TypeError):
                return None

        return {
            "futures_foreign_net": _to_int(row.get("frgn_ntby_qty") or row.get("frgn_net_qty")),
            "futures_institution_net": _to_int(row.get("orgn_ntby_qty") or row.get("orgn_net_qty")),
        }
    except Exception:
        return {"futures_foreign_net": None, "futures_institution_net": None}

from __future__ import annotations

from src.collectors.kis_client import kis_get


def _to_billion(raw: str | None) -> str | None:
    """원 단위 문자열 → 억 원 (소수점 1자리)"""
    if not raw:
        return None
    try:
        val = int(raw)
    except (ValueError, TypeError):
        return None
    billion = round(val / 1_0000_0000, 1)
    sign = "+" if billion >= 0 else ""
    return f"{sign}{billion:,.1f}억"


def get_stock_investor_flow_krw(
    code: str,
    app_key: str,
    app_secret: str,
    market: str = "J",
) -> dict:
    """
    당일 투자자별 순매수 금액 (KIS API).
    market: "J"=KOSPI, "Q"=KOSDAQ (코드가 6자리면 자동 판단 불가 → 기본 J)
    반환: { foreign_today, institution_today, retail_today }  모두 억 원 문자열
    """
    try:
        data = kis_get(
            path="/uapi/domestic-stock/v1/quotations/investor",
            tr_id="FHKST01010300",
            params={
                "FID_COND_MRKT_DIV_CODE": market,
                "FID_INPUT_ISCD": code,
            },
            app_key=app_key,
            app_secret=app_secret,
        )
        output = data.get("output")
        if not output:
            return {"foreign_today": None, "institution_today": None, "retail_today": None}

        # output이 리스트인 경우 첫 항목(당일)
        row = output[0] if isinstance(output, list) else output
        return {
            "foreign_today": _to_billion(row.get("frgn_ntby_amt")),
            "institution_today": _to_billion(row.get("orgn_ntby_amt")),
            "retail_today": _to_billion(row.get("prsn_ntby_amt")),
        }
    except Exception:
        return {"foreign_today": None, "institution_today": None, "retail_today": None}


def get_short_selling_ratio(
    code: str,
    app_key: str,
    app_secret: str,
) -> str | None:
    """공매도 잔고 비율 (KIS API 대차잔고 기준)"""
    try:
        data = kis_get(
            path="/uapi/domestic-stock/v1/quotations/short-sale",
            tr_id="HHKDB669100C0",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": code,
                "FID_INPUT_DATE_1": "",
                "FID_INPUT_DATE_2": "",
                "FID_PERIOD_DIV_CODE": "D",
            },
            app_key=app_key,
            app_secret=app_secret,
        )
        output = data.get("output")
        if not output:
            return None
        row = output[0] if isinstance(output, list) else output

        # 대차잔고비율 또는 공매도비율 필드 탐색
        for field in ("ssts_rto", "short_sale_rto", "loan_bal_rto", "stln_rto"):
            val = row.get(field)
            if val and val not in ("", "0", "0.00"):
                try:
                    return f"{float(val):.2f}%"
                except ValueError:
                    pass
        return None
    except Exception:
        return None

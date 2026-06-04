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
    days: int = 20,
) -> dict:
    """
    최근 N일 투자자별 순매수 금액 누적 (KIS API FHKST01010900).
    - 단위: 백만 원 → 억 원 변환 (÷100)
    - 반환: { foreign_20d_krw, institution_20d_krw, foreign_today_krw, institution_today_krw }
    """
    try:
        data = kis_get(
            path="/uapi/domestic-stock/v1/quotations/inquire-investor",
            tr_id="FHKST01010900",
            params={
                "FID_COND_MRKT_DIV_CODE": market,
                "FID_INPUT_ISCD": code,
            },
            app_key=app_key,
            app_secret=app_secret,
        )
        rows = data.get("output", [])
        if not rows:
            return {"foreign_20d_krw": None, "institution_20d_krw": None,
                    "foreign_today_krw": None, "institution_today_krw": None}

        # 최신순 정렬 (이미 최신이 앞에 있지만 보장)
        recent = rows[:days]

        def _sum_billion(field: str) -> str | None:
            total = 0
            for r in recent:
                try:
                    total += int(r.get(field) or 0)
                except (ValueError, TypeError):
                    pass
            # 백만 원 → 억 원
            val = round(total / 100, 1)
            sign = "+" if val >= 0 else ""
            return f"{sign}{val:,.1f}억"

        def _today_billion(field: str) -> str | None:
            if not rows:
                return None
            return _to_billion(str(int(rows[0].get(field) or 0) * 1_000_000))

        return {
            "foreign_20d_krw": _sum_billion("frgn_ntby_tr_pbmn"),
            "institution_20d_krw": _sum_billion("orgn_ntby_tr_pbmn"),
            "foreign_today_krw": _to_billion(str(int(rows[0].get("frgn_ntby_tr_pbmn") or 0) * 1_000_000)),
            "institution_today_krw": _to_billion(str(int(rows[0].get("orgn_ntby_tr_pbmn") or 0) * 1_000_000)),
        }
    except Exception:
        return {"foreign_20d_krw": None, "institution_20d_krw": None,
                "foreign_today_krw": None, "institution_today_krw": None}


def get_short_selling_ratio(
    code: str,
    app_key: str,
    app_secret: str,
) -> str | None:
    """공매도 거래량 비중 (KIS 국내주식 공매도 일별추이).

    KIS 공식 샘플 기준:
    - [국내주식] 시세분석 > 국내주식 공매도 일별추이[국내주식-134]
    - path: /uapi/domestic-stock/v1/quotations/daily-short-sale
    - tr_id: FHPST04830000
    - verified field: ssts_vol_rlim (공매도 거래량 비중)

    개별 종목의 "공매도 잔고 비율"을 검증된 필드로 제공하는 엔드포인트는 확인되지 않아
    잔고 비율처럼 가공하지 않는다.
    """
    try:
        data = kis_get(
            path="/uapi/domestic-stock/v1/quotations/daily-short-sale",
            tr_id="FHPST04830000",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": code,
                "FID_INPUT_DATE_1": "",
                "FID_INPUT_DATE_2": "",
            },
            app_key=app_key,
            app_secret=app_secret,
        )
        rows = data.get("output2") or []
        if not rows:
            return None

        row = rows[0] if isinstance(rows, list) else rows
        val = row.get("ssts_vol_rlim") if isinstance(row, dict) else None
        if val in (None, ""):
            return None
        try:
            return f"{float(str(val).replace(',', '')):.2f}%"
        except ValueError:
            return None
        return None
    except Exception:
        return None

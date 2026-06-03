from __future__ import annotations

from functools import lru_cache
from io import BytesIO
from zipfile import ZipFile

import requests

from src.collectors.kis_client import kis_get


INDEX_FUTURE_MASTER_URL = "https://new.real.download.dws.co.kr/common/master/fo_idx_code_mts.mst.zip"


@lru_cache(maxsize=1)
def get_kospi200_nearest_future_code() -> str | None:
    """KOSPI200 지수선물 근월물 단축코드 조회.

    KIS 공식 종목 마스터(fo_idx_code_mts.mst) 기준:
    - 상품종류 1: 지수선물
    - 월물구분코드 1: 최근월물
    - 기초자산 단축코드 2001 / 기초자산 명 KOSPI200
    """
    response = requests.get(INDEX_FUTURE_MASTER_URL, timeout=20)
    response.raise_for_status()
    with ZipFile(BytesIO(response.content)) as archive:
        master_name = archive.namelist()[0]
        lines = archive.read(master_name).decode("cp949").splitlines()

    for line in lines:
        cols = [part.strip() for part in line.split("|")]
        if len(cols) < 9:
            continue
        product_type, short_code, _, _, _, _, month_code, underlying_code, underlying_name = cols[:9]
        if (
            product_type == "1"
            and month_code == "1"
            and underlying_code == "2001"
            and underlying_name.upper() == "KOSPI200"
        ):
            return short_code
    return None


def get_futures_investor_flow(app_key: str, app_secret: str) -> dict:
    """
    코스피200 선물 투자자별 매매동향 (KIS API).
    반환: { futures_foreign_net, futures_institution_net }  단위: 계약 수
    """
    contract_code: str | None = None
    try:
        contract_code = get_kospi200_nearest_future_code()
        if not contract_code:
            return {
                "futures_foreign_net": None,
                "futures_institution_net": None,
                "futures_contract_code": None,
                "futures_warning": "KOSPI200 선물 근월물 코드를 찾지 못했습니다.",
            }

        data = kis_get(
            path="/uapi/domestic-futureoption/v1/quotations/inquire-futures-investor",
            tr_id="FHKST01010400",
            params={
                "FID_COND_MRKT_DIV_CODE": "F",
                "FID_INPUT_ISCD": contract_code,
            },
            app_key=app_key,
            app_secret=app_secret,
        )
        output = data.get("output")
        if not output:
            return {
                "futures_foreign_net": None,
                "futures_institution_net": None,
                "futures_contract_code": contract_code,
                "futures_warning": "KIS 선물 투자자 수급 응답이 비어 있습니다.",
            }

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
            "futures_contract_code": contract_code,
            "futures_warning": None,
        }
    except Exception:
        return {
            "futures_foreign_net": None,
            "futures_institution_net": None,
            "futures_contract_code": contract_code,
            "futures_warning": "KIS 선물 투자자 수급 조회에 실패했습니다.",
        }

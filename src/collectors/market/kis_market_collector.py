from __future__ import annotations

from functools import lru_cache
from io import BytesIO
from zipfile import ZipFile

import requests


INDEX_FUTURE_MASTER_URL = "https://new.real.download.dws.co.kr/common/master/fo_idx_code_mts.mst.zip"
FUTURES_INVESTOR_FLOW_UNSUPPORTED_WARNING = (
    "KIS 국내선물옵션 공식 API에 코스피200 선물 투자자별 매매동향 엔드포인트가 없어 미제공입니다."
)


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
    코스피200 선물 투자자별 매매동향.

    KIS 공식 개발자센터/공식 샘플 기준 국내선물옵션 공개 REST API는
    주문/계좌, 기본시세, 실시간시세 범주만 제공하며, 투자자별 매매동향 시세 엔드포인트는 없다.
    따라서 검증되지 않은 path/TR_ID로 값을 추정하지 않고 미제공으로 반환한다.

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

        return {
            "futures_foreign_net": None,
            "futures_institution_net": None,
            "futures_contract_code": contract_code,
            "futures_warning": FUTURES_INVESTOR_FLOW_UNSUPPORTED_WARNING,
        }
    except Exception:
        return {
            "futures_foreign_net": None,
            "futures_institution_net": None,
            "futures_contract_code": contract_code,
            "futures_warning": "KIS 선물 투자자 수급 조회에 실패했습니다.",
        }

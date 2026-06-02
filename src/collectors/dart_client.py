from __future__ import annotations

import io
import re
import zipfile
from datetime import datetime, timedelta
from functools import lru_cache
from xml.etree import ElementTree

import requests


BASE_URL = "https://opendart.fss.or.kr/api"
TIMEOUT_SECONDS = 20
DART_API_KEY_LENGTH = 40


def _normalize_name(value: str) -> str:
    return re.sub(r"\s+", "", value or "").upper()


def _validate_api_key(api_key: str) -> str:
    key = (api_key or "").strip()
    if not key:
        raise RuntimeError("DART_API_KEY가 비어 있습니다.")
    if len(key) != DART_API_KEY_LENGTH or not key.isalnum():
        raise RuntimeError(
            "DART_API_KEY는 OpenDART에서 발급받은 40자리 인증키만 입력해야 합니다. "
            ".env에 URL, 파라미터, 중복된 'DART_API_KEY='가 들어가지 않았는지 확인하세요."
        )
    return key


def _safe_get_json(endpoint: str, params: dict) -> dict:
    if "crtfc_key" in params:
        params = {**params, "crtfc_key": _validate_api_key(params["crtfc_key"])}

    response = requests.get(
        f"{BASE_URL}/{endpoint}",
        params=params,
        timeout=TIMEOUT_SECONDS,
        headers={"User-Agent": "jin-stock/0.1"},
    )
    response.raise_for_status()
    data = response.json()
    status = data.get("status")
    if status in {None, "000"}:
        return data
    if status == "013":
        return {"status": status, "message": data.get("message"), "list": []}
    raise RuntimeError(f"DART API error {status}: {data.get('message', 'unknown error')}")


@lru_cache(maxsize=4)
def get_corp_code_index(api_key: str) -> list[dict]:
    api_key = _validate_api_key(api_key)
    response = requests.get(
        f"{BASE_URL}/corpCode.xml",
        params={"crtfc_key": api_key},
        timeout=TIMEOUT_SECONDS,
        headers={"User-Agent": "jin-stock/0.1"},
    )
    response.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        xml_name = archive.namelist()[0]
        xml_bytes = archive.read(xml_name)

    root = ElementTree.fromstring(xml_bytes)
    records: list[dict] = []
    for item in root.findall("list"):
        corp_name = (item.findtext("corp_name") or "").strip()
        stock_code = (item.findtext("stock_code") or "").strip()
        corp_code = (item.findtext("corp_code") or "").strip()
        if not corp_name or not corp_code:
            continue
        records.append(
            {
                "corp_name": corp_name,
                "corp_code": corp_code,
                "stock_code": stock_code,
                "corp_name_normalized": _normalize_name(corp_name),
            }
        )
    return records


def find_corp_by_name(name: str, api_key: str) -> dict | None:
    target = _normalize_name(name)
    if not target:
        return None

    records = get_corp_code_index(api_key)
    exact = next((item for item in records if item["corp_name_normalized"] == target), None)
    if exact:
        return exact

    partial = next(
        (
            item
            for item in records
            if target in item["corp_name_normalized"] or item["corp_name_normalized"] in target
        ),
        None,
    )
    return partial


def list_disclosures(
    api_key: str,
    start_date: str,
    end_date: str,
    corp_code: str | None = None,
    corp_cls: str | None = None,
    page_count: int = 10,
    last_reprt_at: str = "Y",
) -> list[dict]:
    params = {
        "crtfc_key": api_key,
        "bgn_de": start_date,
        "end_de": end_date,
        "page_count": page_count,
        "page_no": 1,
        "sort": "date",
        "sort_mth": "desc",
        "last_reprt_at": last_reprt_at,
    }
    if corp_code:
        params["corp_code"] = corp_code
    if corp_cls:
        params["corp_cls"] = corp_cls
    data = _safe_get_json("list.json", params)
    return data.get("list", [])


def get_single_company_major_accounts(
    api_key: str,
    corp_code: str,
    business_year: int,
    report_code: str,
) -> list[dict]:
    data = _safe_get_json(
        "fnlttSinglAcnt.json",
        {
            "crtfc_key": api_key,
            "corp_code": corp_code,
            "bsns_year": business_year,
            "reprt_code": report_code,
        },
    )
    return data.get("list", [])


def get_major_shareholding_reports(api_key: str, corp_code: str) -> list[dict]:
    data = _safe_get_json(
        "majorstock.json",
        {
            "crtfc_key": api_key,
            "corp_code": corp_code,
        },
    )
    return data.get("list", [])


def get_executive_major_shareholders(api_key: str, corp_code: str) -> list[dict]:
    data = _safe_get_json(
        "elestock.json",
        {
            "crtfc_key": api_key,
            "corp_code": corp_code,
        },
    )
    return data.get("list", [])


def recent_date_range(days: int = 30) -> tuple[str, str]:
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    return start_date.strftime("%Y%m%d"), end_date.strftime("%Y%m%d")

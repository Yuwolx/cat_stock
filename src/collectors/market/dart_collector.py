from __future__ import annotations

from src.collectors.dart_client import list_disclosures


def get_major_disclosures(
    target_date: str,
    api_key: str = "",
    use_mock_data: bool = True,
) -> list[str]:
    if use_mock_data or not api_key:
        return [
            "삼성전자: 시설투자 관련 공시 점검 필요",
            "현대차: 자사주 관련 공시 여부 확인 필요",
            "셀트리온: 합병/지배구조 이슈 공시 점검 필요",
        ]

    date_key = target_date.replace("-", "")
    try:
        items = list_disclosures(
            api_key=api_key,
            start_date=date_key,
            end_date=date_key,
            page_count=12,
            last_reprt_at="Y",
        )
    except Exception as exc:
        return [f"DART 조회 실패: {exc}"]

    if not items:
        return ["당일 조회된 주요 공시가 없습니다."]

    return [f"{item['corp_name']}: {item['report_nm']} ({item['rcept_dt']})" for item in items[:10]]

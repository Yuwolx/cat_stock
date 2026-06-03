from __future__ import annotations


def get_theme_peers(theme_name: str, api_key: str = "", use_mock_data: bool = True) -> dict:
    if use_mock_data:
        return {
            "disclosures": [f"{theme_name}: 관련 상장사 공시 추가 확인 필요"],
            "global_peers": ["NVIDIA", "TSMC", "ASML"],
        }

    # 글로벌 피어는 아직 신뢰 가능한 실데이터 매핑 경로가 없다.
    # 고정 샘플을 실데이터처럼 노출하지 않고 미연결 상태를 빈 값으로 보낸다.
    return {"disclosures": [], "global_peers": []}

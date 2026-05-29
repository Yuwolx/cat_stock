from __future__ import annotations


def get_theme_peers(theme_name: str, api_key: str = "", use_mock_data: bool = True) -> dict:
    if use_mock_data or not api_key:
        return {
            "disclosures": [f"{theme_name}: 관련 상장사 공시 추가 확인 필요"],
            "global_peers": ["NVIDIA", "TSMC", "ASML"],
        }
    return {"disclosures": [], "global_peers": []}

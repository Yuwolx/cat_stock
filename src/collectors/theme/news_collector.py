from __future__ import annotations


def get_theme_news(theme_name: str, use_mock_data: bool = True) -> dict:
    if use_mock_data:
        return {
            "news": [
                f"{theme_name}: 최근 2주간 수급 집중 뉴스",
                f"{theme_name}: 글로벌 정책 수혜 기대 뉴스",
            ],
            "reports": [
                f"{theme_name}: 업황 회복 기대 리포트",
                f"{theme_name}: 밸류체인 재평가 리포트",
            ],
        }
    return {"news": [], "reports": []}

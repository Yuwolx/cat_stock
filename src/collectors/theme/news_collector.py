from __future__ import annotations

import logging

import requests
from bs4 import BeautifulSoup


HEADERS = {"User-Agent": "Mozilla/5.0"}
logger = logging.getLogger(__name__)


def _search_naver_news(query: str, limit: int = 8) -> list[str]:
    try:
        response = requests.get(
            "https://search.naver.com/search.naver",
            params={"where": "news", "query": query},
            headers=HEADERS,
            timeout=20,
        )
        response.raise_for_status()
        response.encoding = response.apparent_encoding or response.encoding
        soup = BeautifulSoup(response.text, "html.parser")

        items: list[str] = []
        seen: set[str] = set()
        for anchor in soup.select("a[href]"):
            href = anchor.get("href", "")
            text = " ".join(anchor.stripped_strings)
            if not href.startswith("https://"):
                continue
            if "search.naver.com" in href or "help.naver.com" in href or "channelPromotion" in href:
                continue
            if "n.news.naver.com" in href:
                continue
            if len(text) < 14 or len(text) > 90:
                continue
            if href in seen:
                continue
            seen.add(href)
            items.append(text)
            if len(items) >= limit:
                break
        if not items:
            logger.warning("Naver parser returned 0 rows: theme_news (%s)", query)
        return items
    except Exception as exc:
        logger.warning("Naver parser failed: theme_news (%s)", exc)
        return []


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

    news = _search_naver_news(theme_name, limit=8)
    return {"news": news, "reports": []}

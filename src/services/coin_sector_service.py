from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from src.collectors.coin.coingecko_client import (
    get_category_markets,
    get_coingecko_status,
    get_coin_markets,
    reset_coingecko_status,
)
from src.collectors.coin.defillama_client import get_fees_overview, get_stablecoin_snapshot, get_top_protocols
from src.formatters.coin_sector_formatter import format_coin_sector_report
from src.utils.date_utils import KST, today_kst_string
from src.utils.file_utils import save_output_text


SECTOR_PLAYBOOKS = {
    "layer-1": {
        "label": "Layer 1",
        "what": "블록체인 자체의 보안, 수수료, 처리량, 개발자 생태계를 경쟁합니다.",
        "watch": "활성 주소, 수수료, 개발자, 생태계 앱 수",
        "risk": "기술 장애, 과도한 밸류에이션, 생태계 유동성 이탈",
    },
    "smart-contract-platform": {
        "label": "Smart Contract Platform",
        "what": "앱과 토큰이 올라가는 기본 인프라입니다.",
        "watch": "TVL, 수수료, 배포 앱, 거래량",
        "risk": "사용량 없이 인프라 서사만 강한 경우",
    },
    "decentralized-finance-defi": {
        "label": "DeFi",
        "what": "예치, 대출, 거래, 파생상품을 온체인에서 처리합니다.",
        "watch": "TVL, fees, revenue, 대출/거래량",
        "risk": "해킹, 유동성 이탈, 인센티브 의존",
    },
    "meme-token": {
        "label": "Meme",
        "what": "커뮤니티와 유동성이 가격의 핵심 동력입니다.",
        "watch": "거래대금, 보유자 분산, 커뮤니티 지속성",
        "risk": "급등락, 내부자 물량, 유동성 급감",
    },
    "artificial-intelligence": {
        "label": "AI",
        "what": "AI 인프라, 데이터, 에이전트, 컴퓨팅 서사를 다룹니다.",
        "watch": "실제 제품, 매출, 파트너십, 네트워크 사용량",
        "risk": "AI 이름만 붙은 테마성 상승",
    },
    "stablecoins": {
        "label": "Stablecoin",
        "what": "시장 안의 대기 자금과 결제 인프라 역할을 합니다.",
        "watch": "시총, 발행/상환, 체인별 분포",
        "risk": "준비금, 규제, 디페깅",
    },
    "exchange-based-tokens": {
        "label": "Exchange Token",
        "what": "거래소 수익, 수수료 할인, 소각 정책과 연결됩니다.",
        "watch": "거래소 점유율, 수익, 소각, 규제",
        "risk": "거래소 사고, 규제, 수익 의존",
    },
    "oracle": {
        "label": "Oracle",
        "what": "온체인 앱에 외부 데이터를 연결합니다.",
        "watch": "파트너십, 데이터 요청량, 수수료",
        "risk": "데이터 신뢰성, 경쟁 프로토콜",
    },
}


def _strip_html(value: str | None) -> str:
    if not value:
        return ""
    without_tags = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", without_tags).strip()[:420]


def _fallback_playbook(category_id: str, name: str, content: str) -> dict:
    return {
        "id": category_id,
        "name": name,
        "what": content or "이 섹터가 어떤 문제를 해결하는지, 대표 코인이 실제로 쓰이는지 확인합니다.",
        "watch": "시총, 거래대금, 대표 코인 동반 강도",
        "risk": "섹터명만 보고 추격하지 말고 실제 사용량과 유동성을 확인",
    }


def _build_playbook(category: dict) -> dict:
    category_id = category.get("id") or ""
    base = SECTOR_PLAYBOOKS.get(category_id)
    if base:
        return {"id": category_id, "name": base["label"], "what": base["what"], "watch": base["watch"], "risk": base["risk"]}
    return _fallback_playbook(category_id, category.get("name") or "-", _strip_html(category.get("content")))


def _fallback_categories() -> list[dict]:
    return [
        {
            "id": category_id,
            "name": data["label"],
            "market_cap": None,
            "market_cap_change_24h": None,
            "volume_24h": None,
            "content": data["what"],
            "top_3_coins_id": [],
        }
        for category_id, data in SECTOR_PLAYBOOKS.items()
    ]


def _representative_coins(categories: list[dict], coin_map: dict[str, dict]) -> list[dict]:
    rows = []
    seen = set()
    for category in categories[:10]:
        sector_name = category.get("name") or "-"
        for coin_id in category.get("top_3_coins_id") or []:
            key = (sector_name, coin_id)
            if key in seen:
                continue
            seen.add(key)
            coin = dict(coin_map.get(coin_id, {"id": coin_id, "name": coin_id, "symbol": coin_id}))
            coin["sector"] = sector_name
            rows.append(coin)
    return rows[:24]


def _future_result(futures: dict[str, object], key: str, default: object) -> object:
    try:
        return futures[key].result()
    except Exception:
        return default


def generate_coin_sector_report(use_mock_data: bool = False) -> dict:
    reset_coingecko_status()
    target_date = today_kst_string()
    target_datetime = datetime.now(KST).strftime("%Y-%m-%d %H:%M KST")
    categories = get_category_markets(limit=16, use_mock_data=use_mock_data)
    if not categories:
        categories = _fallback_categories()

    top_coin_ids: list[str] = []
    for category in categories[:10]:
        for coin_id in category.get("top_3_coins_id") or []:
            if coin_id not in top_coin_ids:
                top_coin_ids.append(coin_id)

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            "coin_rows": executor.submit(
                get_coin_markets,
                top_coin_ids,
                per_page=max(len(top_coin_ids), 1),
                use_mock_data=use_mock_data,
            )
            if top_coin_ids
            else None,
            "top_protocols": executor.submit(get_top_protocols, limit=8, use_mock_data=use_mock_data),
            "fees": executor.submit(get_fees_overview, limit=6, use_mock_data=use_mock_data),
            "stablecoins": executor.submit(get_stablecoin_snapshot, limit=5, use_mock_data=use_mock_data),
        }

    coin_rows = _future_result(futures, "coin_rows", []) if top_coin_ids else []
    coin_map = {row.get("id"): row for row in coin_rows}
    representative = _representative_coins(categories, coin_map)
    top_protocols = _future_result(futures, "top_protocols", [])
    fees = _future_result(futures, "fees", {})
    stablecoins = _future_result(futures, "stablecoins", {})

    sorted_by_change = sorted(
        [item for item in categories if item.get("market_cap_change_24h") is not None],
        key=lambda row: row.get("market_cap_change_24h") or 0,
        reverse=True,
    )

    payload = {
        "target_date": target_date,
        "target_datetime": target_datetime,
        "is_mock_data": use_mock_data,
        "categories": categories,
        "representative_coins": representative,
        "strongest_sector": sorted_by_change[0] if sorted_by_change else {},
        "weakest_sector": sorted_by_change[-1] if sorted_by_change else {},
        "playbooks": [_build_playbook(category) for category in categories[:10]],
        "top_protocols": top_protocols,
        "fees": fees,
        "stablecoins": stablecoins,
    }
    coingecko_status = get_coingecko_status()
    payload["source_status"] = {"coingecko": coingecko_status}
    payload["data_warnings"] = (
        ["CoinGecko rate limit으로 일부 데이터가 비었을 수 있습니다."] if coingecko_status.get("rate_limited") else []
    )
    text = format_coin_sector_report(payload)
    path = save_output_text("coin_sector", target_date, text)
    return {"text": text, "path": path, "payload": payload}

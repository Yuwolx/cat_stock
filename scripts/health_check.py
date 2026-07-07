"""크롤링 수집기 아침 점검 스크립트.

GitHub Actions(.github/workflows/health-check.yml)가 평일 아침마다 실행한다.
네이버 페이지 개편 등으로 수집기가 깨졌는지 사용자가 쓰기 전에 확인하는 용도.
하나라도 실패하면 종료 코드 1 → 워크플로 실패 → GitHub이 이메일로 알린다.

API 키가 필요 없는 수집기(네이버/KRX/글로벌)만 점검한다.
테마 수집기는 네이버 테마 목록이 등락률순으로 바뀌어 특정 테마가
1페이지에 없을 수 있고, 그 경우 오탐이 나므로 점검 대상에서 제외한다.
"""

from __future__ import annotations

import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from src.collectors.market.global_collector import get_global_macro_snapshot, get_korean_index_trend
from src.collectors.market.krx_collector import (
    get_derivatives_snapshot,
    get_investor_flows,
    get_market_indices,
)
from src.collectors.market.naver_market_collector import (
    get_market_event_lists,
    get_market_news,
    get_market_reports,
    get_sector_changes,
    get_trading_value_leaders,
)
from src.collectors.stock.naver_stock_collector import (
    get_stock_basics,
    get_stock_investor_flows,
)
from src.utils.date_utils import resolve_stock_trading_date

CHECK_STOCK_NAME = "삼성전자"


def _is_empty(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, (list, tuple, set)):
        return len(value) == 0
    if isinstance(value, dict):
        if not value:
            return True
        return all(_is_empty(item) for item in value.values())
    return False


def main() -> int:
    target_date = resolve_stock_trading_date()["target_date"]
    print(f"점검 기준일: {target_date}\n")

    checks = [
        ("시황: 한국 지수 (KRX)", lambda: get_market_indices(target_date, use_mock_data=False)),
        ("시황: 외국인/기관 수급 (KRX)", lambda: get_investor_flows(target_date, use_mock_data=False)),
        ("시황: 파생/프로그램 (KRX)", lambda: get_derivatives_snapshot(target_date, use_mock_data=False)),
        ("시황: 거래대금 상위 (네이버)", lambda: get_trading_value_leaders(target_date, use_mock_data=False)),
        ("시황: 테마/그룹 등락 (네이버)", lambda: get_sector_changes(use_mock_data=False)),
        ("시황: 시장 이벤트 (네이버)", lambda: get_market_event_lists(target_date, use_mock_data=False)),
        ("시황: 시장 뉴스 (네이버)", lambda: get_market_news(use_mock_data=False)),
        ("시황: 증권사 리포트 (네이버)", lambda: get_market_reports(use_mock_data=False)),
        ("시황: 글로벌 지표", lambda: get_global_macro_snapshot(target_date, use_mock_data=False)),
        ("시황: 지수 흐름 (네이버)", lambda: get_korean_index_trend(target_date, use_mock_data=False)),
        (f"종목: 기본 정보 (네이버, {CHECK_STOCK_NAME})", lambda: get_stock_basics(CHECK_STOCK_NAME, use_mock_data=False)),
        (f"종목: 수급/뉴스 (네이버, {CHECK_STOCK_NAME})", lambda: get_stock_investor_flows(CHECK_STOCK_NAME, use_mock_data=False)),
    ]

    failures: list[str] = []
    for name, run in checks:
        started = time.monotonic()
        try:
            data = run()
        except Exception:
            print(f"[오류]     {name}")
            traceback.print_exc()
            failures.append(f"{name}: 예외 발생")
            continue

        elapsed = time.monotonic() - started
        if _is_empty(data):
            print(f"[비어있음] {name} ({elapsed:.1f}s)")
            failures.append(f"{name}: 빈 결과")
        else:
            print(f"[정상]     {name} ({elapsed:.1f}s)")

    print()
    if failures:
        print(f"실패 {len(failures)}건 / 전체 {len(checks)}건:")
        for item in failures:
            print(f"  - {item}")
        return 1

    print(f"전체 {len(checks)}건 모두 정상.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

# 작업 지시: P0-3 주식 모드 수집 병렬화
> 상태: 완료 — 커밋 5831f77 (주식 수집 병렬화)

발행: 관리자 / 수행: 개발자
브랜치: develop (main 직접 작업 금지)
근거: docs/CODE_REVIEW.md P0-3

## 문제

`market_service.generate_market_briefing()`와 `stock_service.generate_stock_report()`는
네이버/DART/fnguide/KIS 호출이 대부분 순차다. 코인 서비스는 이미
`ThreadPoolExecutor` + `_future_result(futures, key, default)` 패턴으로 병렬화돼 있다.
같은 패턴을 주식 쪽에 적용한다.

## 요구 결과

### 1. 공통 헬퍼 재사용
`coin_market_service._future_result`와 동일한 예외 격리 패턴을 쓴다.
중복이면 `src/utils/`로 추출해도 좋다(선택). 한 수집 실패가 전체를 죽이면 안 된다.

### 2. market_service.generate_market_briefing 병렬화
다음 7개는 서로 독립이므로 `ThreadPoolExecutor`로 동시 실행:
`get_market_indices`, `get_global_macro_snapshot`, `get_trading_value_leaders`,
`get_sector_changes`, `get_investor_flows`, `get_market_event_lists`, `get_major_disclosures`.
`get_derivatives_snapshot`도 포함. KIS 선물 보강 로직은 derivatives 결과 확정 후 적용(기존 동작 유지).

### 3. stock_service.generate_stock_report 병렬화
**순서 의존성 주의**: `get_stock_code(stock_name)`로 `code`를 먼저 구한 뒤,
그 결과에 의존하는 호출들을 병렬화한다.
독립 그룹(병렬): `get_stock_basics`, `get_stock_investor_flows`,
`get_financial_summary`, `get_stock_disclosures`, `get_short_selling_snapshot`,
`get_fnguide_reports`(code 필요), KIS 수급/공매도(code+키 필요).
`generate_stock_column`은 payload 완성 후 마지막 단계 유지.

### 4. KIS 토큰 race 방지 (중요)
KIS 호출 여러 개를 동시에 처음 던지면 토큰이 동시 발급될 수 있다.
KIS는 토큰 발급 횟수 제한이 있다(과거에 막힌 적 있음).
→ **병렬 제출 직전에 토큰을 1회 선발급**(`get_token(app_key, app_secret)` 한 번 호출)해
파일/메모리 캐시를 채운 뒤 병렬 호출에 들어갈 것.

## 검증 (필수)

- 병렬화 전후 payload **키 구성과 값이 동일**해야 한다.
  같은 입력으로 순차 결과와 병렬 결과를 비교하는 회귀 테스트 또는 수동 비교.
- 수집 1개를 강제 실패시켜도 나머지가 채워지고 앱이 죽지 않는지 확인.
- `.venv/bin/python3 -m pytest` 전체 통과.
- 실제 1회 실행해 시황/종목 생성이 정상 동작하고 체감 속도가 줄었는지 확인.

## 주의

- main 푸시 금지. develop 커밋만.
- 병렬화는 "값 보강 로직(예: KIS가 네이버 None을 덮어쓰는 부분)"의 순서를 깨면 안 된다.
  수집은 병렬, **병합/덮어쓰기는 결과 취합 후** 순차로.

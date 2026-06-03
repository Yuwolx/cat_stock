# 작업 지시: 시황 브리핑 개편 (공시 제거 + 등락률 상위 확대)

발행: 관리자 / 수행: 개발자
브랜치: develop (main 직접 작업 금지)
근거: 프로젝트 주인 오더

## 오더 요약
1. **시황 브리핑에서 공시 섹션 완전 제거** (개별 종목 DART 공시는 유지)
2. **등락률 상위: 상승 50개 + 하락 20개** (코스피+코스닥 합산)
3. 뉴스는 제목+링크 현행 유지 (요약 작업 안 함 — 변경 없음)

---

## 1. 시황 공시 제거

**개별 종목(build_stock_dashboard, stock_service)의 공시는 절대 건드리지 말 것.**
시황 경로만 제거한다.

대상:
- `src/services/market_service.py`: executor의 `disclosures` 제출 + payload의 `disclosures` 제거. 안 쓰게 되는 `get_major_disclosures` import도 정리.
- `src/formatters/market_formatter.py`: `section("주요 공시", ...)` 라인 제거.
- `src/ui/dashboard.py` `build_market_dashboard`: 공시 섹션(DISCLOSURES rule + disc-table) 제거. **build_stock_dashboard의 공시는 유지.**
- `src/ui/pages.py` `_render_missing_data_warnings`: market 분기의 공시 누락 경고 제거.
- `market_column` 프롬프트엔 공시 없음 → 작업 불필요(확인만).

## 2. 등락률 상위 상승 50 / 하락 20

대상: `src/collectors/market/naver_market_collector.py` `get_market_event_lists`
- `daily_highs`: 코스피+코스닥 합산 **상위 50개**
- `daily_lows`: 코스피+코스닥 합산 **상위 20개**

**확인 필수**: `sise_rise.naver?sosok=N` 한 페이지가 50개를 주는지.
부족하면 `&page=2` 페이지네이션으로 채울 것. 한 페이지 종목 수를 실제로 찍어보고 결정.

표시부도 개수 맞춰 확대:
- `src/formatters/market_formatter.py`: 상승/하락 상위 출력 개수 (현재 잘려 있으면 50/20 반영)
- `src/ui/dashboard.py` `build_market_dashboard`: 사이드바/본문의 상승·하락 목록 개수

## 검증
- 시황 생성 시 공시가 TXT/HTML/경고 어디에도 안 나오는지.
- 개별 종목 분석의 공시는 그대로 나오는지 (회귀 금지).
- 등락률 상승 실제 50개, 하락 20개 수집되는지 실행으로 확인 (`get_market_event_lists` 직접 호출해 len 출력).
- `.venv/bin/python3 -m pytest` 전체 통과. 공시 관련 테스트가 있으면 시황용만 정리.

## 주의
- main 푸시 금지. develop 커밋만.
- 50개 수집이 느려지면 시황 병렬화(P0-3)와 충돌하지 않게 기존 executor 안에서 처리.

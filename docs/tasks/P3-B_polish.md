# 작업 지시: 3순위 완성도 다듬기 묶음

발행: 관리자 / 수행: 개발자
브랜치: develop (main 직접 작업 금지)
우선순위: 3순위(되어 있는데 다듬으면 좋은 것)

항목별 한 커밋. 자잘한 표기/중복/점검 묶음.

## 1. 테마 종목 표기 정리
관리자 실측 출력 예: `시총 3조 5,680 억원`, `PER None`.
- 시총 표기에서 불필요한 공백/단위 중복 정리 → `3조 5,680억원` 형태.
  (`naver_theme_collector._parse_stock_valuation`의 market_cap 추출부)
- `PER None` / `PBR None`처럼 값이 없을 때 `None` 문자열이 그대로 노출됨
  → 포맷터(`theme_formatter`)에서 없으면 `—`로. TXT/대시보드 양쪽.
- 수용: 테마 출력에 `None`/이상한 공백 없음.

## 2. `_format_news_item` 중복 제거
- 현재 `market_formatter.py`와 `naver_stock_collector.py` 두 곳에 거의 동일 정의.
- 공용 위치(`src/utils/` 또는 한 곳)로 통일하고 양쪽이 같은 함수를 쓰게.
- 수용: 정의 1곳, 종목/시황 뉴스 출력 동일 유지.

## 3. 코인 개별·섹터 None 전수 점검 (D-3 잔여)
- 실제 코인(BTC, SOL 등)으로 `generate_coin_detail_report` / `generate_coin_sector_report` 호출,
  payload에서 None으로 비는 지표를 찾는다.
- 원래 없는 값이면 대시보드에서 `—` 표기, 수집 실패면 사유 표기(정직성 원칙).
- `None`이 사용자 화면에 문자열로 노출되는 곳이 없게.
- 수용: 코인 개별/섹터 화면에 raw `None` 노출 0건.

## 4. 수집 실패 메타데이터 종목 확장 (B-1 잔여, 선택)
- 시황만 status 메타데이터가 있고 종목은 아직 빈 값 추정 기반.
- 여력 되면 종목도 동일 패턴 적용. 시간 없으면 1~3만 하고 보고.

## 검증
- 테마/코인 실제 출력에 `None` 문자열·깨진 표기 없는지 실호출 확인.
- `.venv/bin/python3 -m pytest` 전체 통과. 표기 관련 테스트 보강.

## 주의
- main 푸시 금지. develop 커밋만.
- 표기만 다듬는 것이므로 데이터 값/로직을 바꾸지 말 것.

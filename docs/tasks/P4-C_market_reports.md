# 작업 지시: 시황에 네이버 증권 데일리 리포트 추가

발행: 관리자 / 수행: 개발자
브랜치: develop (main 직접 작업 금지)
근거: 주인 지시 — 시황에도 네이버 증권 리포트(데일리 시황 섹션)를 뉴스처럼 제목+링크로

## 목표
시황 브리핑에 **네이버 리서치 시황정보 데일리 리포트**를 뉴스 섹션처럼 추가.
fnguide(종목 리포트)는 건드리지 않음 — 유저 설정 기간대로 유지.

## 출처 (실측 확인됨)
- `https://finance.naver.com/research/market_info_list.naver` (인코딩 euc-kr)
- `table.type_1 tr` 행에서: 제목(a), 증권사, 날짜 제공. 30건 수준.
- 제목 링크 href에서 상세/PDF URL 추출 — 종목 리포트의
  `naver_stock_collector._parse_report_rows`(detail_url/pdf_url) 패턴 참고.

## 요구 결과

### 1. 수집기 (naver_market_collector.py)
- `get_market_reports(limit=10)` 추가.
- 반환: `[{"title", "broker", "date", "url"}]` — 뉴스 `news_items`와 유사 스키마.
  url은 리포트 상세 또는 PDF 링크(절대경로). 없으면 빈 문자열.
- 실패 시 빈 리스트(예외 격리). 파서 0건이면 로깅 경고(기존 패턴).

### 2. market_service 연결
- 기존 `ThreadPoolExecutor`에 `market_reports` 수집 추가.
- payload에 `"market_reports": [...]`.

### 3. 표시 (뉴스와 동일 톤, TXT + 대시보드 둘 다)
- `market_formatter.py`: "증권사 리포트" 섹션 추가 — `제목 (증권사, 날짜)` + 링크 줄.
  뉴스의 `format_news_item` 재사용 가능하면 재사용(같은 스키마라면).
- `dashboard.py build_market_dashboard`: 뉴스 그리드처럼 리포트 섹션 추가
  (제목+증권사 표시, 클릭 시 링크 이동). LATEST NEWS 아래에 ANALYST REPORTS 같은 섹션.

## 검증
- 시황 생성 시 TXT/대시보드에 증권사 리포트 제목+링크가 뜨고 클릭 이동되는지.
- `get_market_reports()` 직접 호출해 건수/url 확인.
- 종목 fnguide 리포트는 영향 없는지(회귀).
- `.venv/bin/python3 -m pytest` 전체 통과.

## 주의
- main 푸시 금지. develop 커밋만.
- 뉴스/리포트 스키마가 같으면 `news_formatting` 공용 함수 재사용해 중복 만들지 말 것.

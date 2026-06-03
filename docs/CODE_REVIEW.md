# 코드 리뷰 및 개선 백로그

최종 업데이트: 2026년 6월 3일
작성 기준: 현재 `main` 브랜치 코드

이 문서는 과거 코드 리뷰에서 이미 해결된 지적은 지우고, 지금도 실제 품질에 영향을 주는 항목만 남긴 관리용 리뷰 문서입니다.

## 결론

현재 구조는 유지보수 가능한 편입니다. UI, 서비스, 수집기, 포맷터가 분리되어 있고 주식/코인 기능도 같은 패턴으로 확장되고 있습니다.

다만 아직 운영 품질 관점에서 중요한 위험이 남아 있습니다.

- 네이버 HTML 파싱 의존도가 높아 페이지 구조 변경에 취약합니다.
- 서비스 레이어가 수집 실패 원인을 구조화해서 들고 있지 않습니다.
- 새로 들어온 AI 칼럼 기능은 유용하지만 실패 이유가 조용히 사라지고 테스트가 부족합니다.
- 주식 모드 수집은 아직 대부분 순차 실행이라 느릴 수 있습니다.
- 테마 공부는 아직 데이터 깊이가 얕습니다.

## 과거 리뷰에서 삭제한 항목

아래 항목은 예전 문서에 남아 있었지만 현재 코드 기준으로 더 이상 핵심 이슈가 아니므로 본문에서 제거했습니다.

| 과거 지적 | 현재 상태 |
| --- | --- |
| 개별 종목 기본 정보 실데이터 미구현 | `naver_stock_collector.get_stock_basics()` 실데이터 연결 |
| 테마/뉴스 컬렉터 전체 mock 상태 | 테마 종목과 뉴스 수집 연결 |
| CAT COIN 플레이스홀더만 존재 | 코인 시황, 개별 코인, 섹터, 학습 노트 대시보드 구현 |
| DART 잘못된 키가 ZIP 파싱 오류로 터짐 | 40자리 키 검증과 사용자 친화적 실패 메시지 추가 |
| `_to_number()` 하락 화살표 파싱 오류 | 테스트로 음수/양수 화살표 처리 검증 |
| 최근 뉴스가 단순 검색 기반 | 네이버 금융 종목 뉴스 탭 기반 제목/언론사/시간/링크 구조화 |
| 5% 이상 상승 종목 없음 | 네이버 등락률 상위에서 +5% 이상 종목 수집 추가 |

## 현재 강점

| 영역 | 좋은 점 |
| --- | --- |
| 구조 | `ui -> service -> collector -> formatter` 흐름이 명확함 |
| 설정 | `.env` 기반 설정을 `settings.py`에서 집중 관리 |
| DART | 키 형식 검증, 공시/재무/대주주 지분율 연결 |
| KIS | 키가 있으면 수급 금액/공매도/선물 수급 보강 |
| 뉴스 | TXT는 헤드라인, HTML은 링크 카드로 분리 |
| 코인 | CoinGecko, Upbit, DeFiLlama, Binance futures를 공부용 대시보드로 연결 |
| 테스트 | 포맷터, DART 키 검증, 네이버 파서, 코인 수집기 일부 테스트 존재 |

## P0: 지금 가장 먼저 봐야 할 것

### 1. AI 칼럼 기능의 실패 이유가 사라짐

파일:

- `src/services/column_service.py`
- `src/services/market_service.py`
- `src/services/stock_service.py`

현재 `generate_market_column()`과 `generate_stock_column()`은 Anthropic API가 없거나 실패하면 `None`을 반환합니다. UI는 칼럼이 없는 상태만 알 수 있고, 왜 없는지는 알 수 없습니다.

문제:

- API 키 없음
- 패키지 미설치
- 모델명 오류
- 네트워크 실패
- 할당량/결제 문제

이 모든 경우가 같은 `None`입니다.

개선:

- `{"is_available": false, "reason": "missing_api_key"}` 같은 구조화된 결과 반환
- UI에서 "AI 칼럼 생성 안 됨: API 키 없음"처럼 표시
- `column_service` 단위 테스트 추가
- Anthropic 호출 타임아웃/최대 재시도 정책 명시

### 2. 서비스 레이어에 수집 실패 메타데이터가 없음

현재 앱은 일부 실패를 UI에서 추정해 경고합니다. 예를 들어 결과가 비어 있으면 "DART 공시 확인 필요" 같은 메시지를 보여줍니다.

문제는 실제 실패 원인이 payload에 구조화되어 있지 않다는 점입니다.

개선:

- 각 collector 호출 결과를 `data`, `source`, `status`, `error`, `fetched_at` 구조로 감싸기
- UI는 빈 값 추정보다 `status`를 보고 경고 표시
- TXT에는 필요 이상으로 에러를 넣지 않고 HTML/경고 영역에서 설명

### 3. 주식 모드 수집이 여전히 느릴 수 있음

코인 서비스는 `ThreadPoolExecutor`를 적극 사용합니다. 반면 주식 시황/종목 분석은 네이버, DART, fnguide, KIS 호출이 대부분 순차로 진행됩니다.

개선:

- `market_service.generate_market_briefing()` 병렬화
- `stock_service.generate_stock_report()`에서 DART/네이버/fnguide/KIS 병렬화
- 같은 종목/날짜 반복 조회에는 짧은 TTL 캐시 적용

## P1: 데이터 신뢰도와 유지보수

### 4. 네이버 HTML 파싱 의존도

네이버 금융 HTML은 공식 API가 아니므로 구조가 바뀌면 파서가 깨질 수 있습니다.

현재 특히 주의할 곳:

- `src/collectors/market/naver_market_collector.py`
- `src/collectors/stock/naver_stock_collector.py`
- `src/collectors/theme/naver_theme_collector.py`

개선:

- 주요 파서마다 fixture 기반 테스트 추가
- selector 실패 시 빈 리스트만 반환하지 말고 source status에 실패 이유 저장
- 네이버 페이지 구조 변경 시 확인할 "스모크 체크 스크립트" 작성

### 5. DART corpCode 캐시가 프로세스 생애에 묶임

`get_corp_code_index()`는 `lru_cache`로 프로세스 내 캐시됩니다. 서버 재시작 후에는 다시 다운로드하며, 장시간 떠 있는 서버에서는 최신 corpCode 반영이 늦을 수 있습니다.

개선:

- `output/.dart_corp_code_cache.json` 같은 파일 캐시 추가
- 일 단위 TTL 적용
- 캐시 생성/만료 로그 추가

### 6. 테마 공부 데이터가 아직 얕음

현재 테마 공부는 테마 종목과 뉴스 중심입니다. 공부용으로는 괜찮지만 AI가 투자 포인트를 깊게 정리하기에는 부족합니다.

추가하면 좋은 데이터:

- 테마 종목별 시가총액
- 테마 종목별 PER/PBR
- 최근 공시
- 대표 글로벌 피어
- 테마 내 대장주/후발주 구분

## P2: UI/문서/운영 품질

### 7. CSS/HTML이 Python 파일에 많이 들어 있음

`src/ui/components.py`, `src/ui/dashboard.py`, `src/ui/coin_dashboard.py`에 CSS와 HTML 문자열이 큽니다.

당장 문제는 아니지만, 디자인이 계속 바뀌면 유지보수가 어려워집니다.

개선:

- 자주 바뀌는 스타일은 `static/` CSS 파일로 분리 검토
- 컴포넌트별 HTML 생성 함수를 더 작게 나누기
- 화면 회귀 확인용 Playwright 스크린샷 테스트 검토

### 8. 환경변수 문서화 유지

현재 주요 환경변수:

- `DART_API_KEY`
- `KIS_APP_KEY`
- `KIS_APP_SECRET`
- `ANTHROPIC_API_KEY`

README와 데이터 흐름 가이드에는 현재 반영되어 있습니다. 새 외부 API 키나 선택 기능을 추가할 때 이 목록도 같이 갱신해야 합니다.

### 9. 테스트 우선순위

다음 테스트가 필요합니다.

| 테스트 | 이유 |
| --- | --- |
| `column_service` API 키 없음/실패/정상 응답 | AI 칼럼 기능 회귀 방지 |
| market/stock service 부분 실패 | 일부 collector 실패 시 전체 생성 유지 확인 |
| 네이버 HTML fixture 테스트 확대 | 페이지 구조 변경 감지 |
| DART corpCode 캐시 테스트 | 잘못된 키/네트워크 실패/캐시 사용 확인 |
| 대시보드 HTML 스모크 테스트 | 생성 HTML이 비어 있지 않은지 확인 |

## 남겨둘 운영 메모

- `.env` 수정 후에는 Streamlit 서버 재시작이 필요합니다. `get_settings()`가 process cache를 사용하기 때문입니다.
- DART 당일 공시는 새벽/장 전에는 없을 수 있습니다. `013 조회된 데이터 없음`은 오류가 아닙니다.
- KIS 키가 없으면 수급 금액/선물 수급/공매도 보강이 비어 있을 수 있습니다.
- AI 칼럼은 데이터 분석 보조용입니다. 원자료가 비어 있으면 칼럼 품질도 낮아집니다.

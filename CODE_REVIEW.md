# Code Review — Jin Stock AI Research

> **Reviewer**: Claude Sonnet 4.6  
> **Date**: 2026-05-29  
> **Scope**: Full codebase (`src/`, `app.py`, `tests/`, config)  
> **Stack**: Python 3.11+, Streamlit 1.45, BeautifulSoup4, FinanceDataReader, DART OpenAPI

---

## Executive Summary

아키텍처 설계는 명확하고 레이어 분리가 잘 되어 있습니다. 그러나 **실데이터 레이어의 약 60%가 mock/stub 상태**이고, 서비스·컬렉터 레이어 전반에 걸쳐 예외가 조용히 삼켜지는 패턴이 반복됩니다. UI는 Apple 미학을 따르지만 코드 밀도 대비 HTML/CSS 부피가 과도합니다. 아래 지적 사항은 심각도 순으로 정렬되어 있습니다.

---

## 1. 아키텍처

### 1.1 강점

| 항목 | 평가 |
|------|------|
| 레이어 분리 | UI → Service → Collector → Formatter → Utils 흐름이 명확 |
| 타입 힌트 | 모든 모듈에 `from __future__ import annotations` + 명시적 반환 타입 적용 |
| 설정 집중화 | `get_settings()` + `@lru_cache` 로 설정 단일 관리 |
| Mock/Real 전환 | `use_mock_data` 파라미터로 테스트와 실서비스를 깔끔하게 분리 |
| 출력 일관성 | `section()` / `format_list()` 유틸로 텍스트 포맷 통일 |
| 타임존 안전 | `zoneinfo.ZoneInfo("Asia/Seoul")` 로 KST 명시 처리 |

### 1.2 구조적 우려 사항

**① 서비스 계층에 오케스트레이션만 있고 에러 경계가 없음**

`generate_market_briefing()`은 7개 컬렉터를 순차 호출합니다. 하나라도 예외를 던지면 전체 briefing 생성이 실패합니다. 각 컬렉터가 내부에서 `try/except` 하지만, 서비스 레이어에는 타임아웃이나 부분 실패 처리가 없습니다.

```python
# src/services/market_service.py — 현재
payload = {
    "indices": get_market_indices(...),   # 실패 → None
    "global_macro": get_global_macro_snapshot(...),  # 실패 → None
    ...
}
text = format_market_briefing(payload)  # None이 섞인 payload를 그대로 포맷터에 전달
```

포맷터가 `None`을 처리하지 못하면 런타임 에러가 발생합니다. 실제로 `market_formatter.py`의 일부 섹션은 `None` guard 없이 `str(value)` 를 호출합니다.

**② 수평 의존성 (Collector → Collector)**

`krx_collector.py`의 `get_investor_flows()`와 `get_derivatives_snapshot()`이 `naver_market_collector.get_home_market_snapshot()`을 직접 import합니다. Collector 레이어 내부에 수평 의존이 생기면 테스트와 교체가 어려워집니다. 이 로직은 `market_service.py`에서 조합하는 것이 맞습니다.

**③ `@lru_cache`가 process-level 캐시임을 인지해야 함**

`get_settings()`의 `@lru_cache(maxsize=1)`은 프로세스 생애 동안 고정됩니다. Streamlit은 단일 프로세스에서 여러 세션을 처리하므로 환경변수를 런타임에 바꿔도 반영되지 않습니다. 개발 환경에서 `.env`를 수정하면 재시작이 필요함을 문서화해야 합니다.

---

## 2. 데이터 레이어 (`src/collectors/`)

### 2.1 현황 매핑

| 컬렉터 | 실데이터 연결 | 비고 |
|--------|-------------|------|
| `krx_collector.get_market_indices()` | ✅ Live | Naver Finance HTML 파싱 |
| `krx_collector.get_investor_flows()` | ⚠️ Partial | 상위 목록만, 수급 합계(foreign/institution/retail)는 `None` |
| `krx_collector.get_derivatives_snapshot()` | ⚠️ Partial | 프로그램 차익만, 선물 수급은 `None` |
| `naver_market_collector.get_trading_value_leaders()` | ✅ Live | |
| `naver_market_collector.get_market_event_lists()` | ✅ Live | |
| `global_collector.get_global_macro_snapshot()` | ✅ Live | FinanceDataReader |
| `dart_collector.get_major_disclosures()` | ✅ Live | DART OpenAPI |
| `naver_stock_collector.get_stock_basics()` | ❌ Stub | 항상 `None` 반환 (real mode에서도) |
| `dart_stock_collector.get_financial_summary()` | ✅ Live | |
| `dart_stock_collector.get_recent_disclosures()` | ✅ Live | |
| `short_selling_collector` | ❌ Stub | mock 데이터만 |
| `naver_theme_collector` | ❌ Stub | mock 데이터만 |
| `news_collector` | ❌ Stub | mock 데이터만 |
| `peer_collector` | ❌ Stub | mock 데이터만 |

### 2.2 구체적 버그 위험

**`naver_stock_collector.get_stock_basics()` 실데이터 미연결**

```python
# src/collectors/stock/naver_stock_collector.py
def get_stock_basics(stock_name: str, use_mock_data: bool = True) -> dict | None:
    if use_mock_data:
        return { ... }   # mock 반환
    # real mode: 아무것도 없음 — 함수가 None을 반환함
    # stock_formatter.py는 이 값이 None이면 섹션 전체를 건너뜀
    return None  # ← 이게 의도인지 실수인지 코드만으로는 불명확
```

주석이나 `# TODO`도 없어서 의도적 미구현인지 빠진 코드인지 알 수 없습니다.

**`_to_number()` 의 `-` 처리 모호성**

```python
def _to_number(text: str) -> float | None:
    cleaned = re.sub(r"[^\d.-]", "", text or "")
```

`"▼1,234.5"` 같은 입력에서 `"▼"` 는 제거되지만 `-`가 앞에 없으면 양수로 파싱됩니다. 하락 값이 양수로 들어갈 수 있습니다.

**`_parse_index_page()` 의 셀렉터 취약성**

```python
now_value = _to_number(soup.select_one("#now_value").get_text(strip=True))
```

`#now_value`가 없으면 `AttributeError` 발생. `try/except` 없이 호출하면 전체 briefing 생성 실패로 연결됩니다. (외부 `get_market_indices`의 try/except 가 잡긴 하지만, 에러 로그가 없어 디버깅이 어렵습니다.)

**DART corp code 캐시 invalidation 없음**

```python
@lru_cache(maxsize=4)
def _get_corp_code_index() -> dict[str, str]:
    ...
```

DART의 `corpCode.xml`은 주기적으로 업데이트됩니다. 프로세스 재시작 전까지 stale 데이터를 사용합니다. 일별 invalidation 또는 TTL이 필요합니다.

---

## 3. 서비스 레이어 (`src/services/`)

### 3.1 로깅 부재

서비스 함수에 로그가 전혀 없습니다.

```python
# market_service.py — 현재
def generate_market_briefing(target_date: str, ...) -> dict:
    payload = { "indices": get_market_indices(...), ... }
    text = format_market_briefing(payload)
    path = save_output_text(...)
    return {"text": text, "path": path, "payload": payload}
```

어떤 컬렉터가 실패했는지, 얼마나 걸렸는지 알 방법이 없습니다. `src/utils/logger.py`가 있음에도 서비스 레이어에서 사용하지 않습니다.

### 3.2 직렬 호출 성능 문제

7개 컬렉터가 모두 순차 실행됩니다. Naver Finance와 DART API의 네트워크 레이턴시를 고려하면 총 소요 시간이 10-20초에 이를 수 있습니다. `asyncio` 또는 `concurrent.futures.ThreadPoolExecutor`로 병렬화하면 체감 속도가 크게 개선됩니다.

---

## 4. 포맷터 레이어 (`src/formatters/`)

### 4.1 `None` 방어 코드 산발적 적용

`market_formatter.py`의 일부 섹션은 `None` 체크를 합니다:

```python
if indices.get("kospi", {}).get("close") is None:
    lines.append("KOSPI 지수 데이터 없음")
```

하지만 다른 섹션은 그냥 `str(value)` 를 호출합니다. 일관된 `display_value()` 유틸 함수가 `text_utils.py`에 있음에도 포맷터마다 다르게 처리합니다.

### 4.2 하드코딩된 제한값

```python
# dart_client.py
disclosures = api.list(corp_code=code, bgn_de=start_str, end_de=today_str, page_count=10)
# dart_stock_collector.py
period_codes = ["11013", "11012", "11014", "11011"]  # 최근 4분기/반기/연간
```

이 값들이 여러 파일에 산재해 있습니다. `settings.py`에서 중앙 관리하는 것이 좋습니다.

---

## 5. UI 레이어 (`src/ui/`)

### 5.1 `components.py`의 구조 문제

- **CSS 740줄이 Python 파일에 인라인으로 삽입됨**: 유지보수가 어렵고, Python 포맷터(`black`)가 CSS 들여쓰기를 건드릴 위험이 있습니다.
- **닫히지 않는 HTML div**: `render_output_panel()`이 `<div class="apple-output-shell">` 를 열고 나서 Streamlit 위젯을 삽입하고 `</div>`를 닫습니다. 이는 Streamlit의 각 `st.markdown()` 호출이 독립 컴포넌트로 렌더되는 방식과 충돌하며 DOM이 깨질 수 있습니다.
- **데코레이티브 섹션이 너무 많음**: Hero tile + Feature band + Sub-nav + Section intro 가 실제 생성기 위에 쌓여 있어 핵심 기능까지 스크롤이 필요합니다.
- **Hero tile의 CTA가 가짜임**: `<div class="apple-pill">Generate</div>` 는 클릭할 수 없는 div입니다. 실제 버튼처럼 보여 사용자 혼란 가능.

### 5.2 입력 유효성 검사 누락

```python
stock_name = st.text_input("종목명", placeholder="예: 삼성전자")
if trigger:
    if not stock_name.strip():
        render_note("종목명을 먼저 입력해주세요.", tone="warn")
    else:
        result = generate_stock_report(stock_name.strip(), ...)
```

빈 문자열 체크는 있지만 특수문자, SQL-like 인젝션, 지나치게 긴 입력에 대한 처리가 없습니다. DART API에 악성 문자가 전달될 수 있습니다.

### 5.3 세션 스테이트 누적

페이지 전환 시 이전 결과가 session_state에 남아 있습니다. `market_result`를 보다가 `stock`으로 탭을 전환해도 이전 market 결과가 session_state에 상주합니다. 이는 메모리 문제보다는 혼란을 줄 수 있습니다.

---

## 6. 테스트

### 6.1 현황

```
tests/
├── test_market_formatter.py   # 8개 테스트
├── test_stock_formatter.py    # 섹션 헤더 존재 여부만 검증
└── test_theme_formatter.py    # 동일
```

### 6.2 빠진 것들

| 미테스트 영역 | 위험도 |
|-------------|--------|
| 컬렉터 레이어 (모든 네트워크 로직) | 높음 |
| 서비스 레이어 (생성 플로우 전체) | 높음 |
| `None` payload 로 포맷터 호출 시 동작 | 높음 |
| DART client corp code 매핑 실패 케이스 | 중간 |
| 날짜 파싱 엣지케이스 (주말, 공휴일) | 중간 |
| `_to_number()` 하락값 파싱 | 낮음 |

현재 테스트는 "포맷터가 특정 문자열을 결과에 포함하는가"만 검증하며, `None`이 섞인 실제 데이터 시나리오를 커버하지 않습니다.

---

## 7. 보안

### 7.1 API 키 노출 위험 낮음 (양호)

- `.env.example` 제공, `.gitignore` 패턴 존재
- Railway 환경변수로 주입하는 구조

### 7.2 스크래핑 User-Agent 고정

```python
HEADERS = {"User-Agent": "Mozilla/5.0"}
```

모든 요청이 동일한 UA를 사용합니다. Naver Finance 측에서 차단하면 모든 컬렉터가 한 번에 실패합니다. UA 풀을 두거나 최소한 더 구체적인 UA 문자열을 사용해야 합니다.

### 7.3 `unsafe_allow_html=True` 사용 전반

모든 HTML 삽입에 `escape()` 가 적용되어 XSS 위험은 낮습니다. 단, `render_output_panel`의 `result_text`는 escape 없이 `st.text_area`에 전달됩니다 — text_area는 HTML이 아니므로 문제없습니다.

---

## 8. 성능

### 8.1 중복 네트워크 호출

`get_home_market_snapshot()`이 `get_investor_flows()`와 `get_derivatives_snapshot()` 양쪽에서 호출됩니다. 두 함수가 같은 Naver 홈 페이지를 두 번 스크래핑합니다.

### 8.2 FinanceDataReader 매 실행마다 14일치 데이터 fetch

```python
# global_collector.py
for symbol, label in SYMBOLS.items():
    df = fdr.DataReader(symbol, start_date)  # 14일치 매번 다운로드
```

결과를 `st.cache_data(ttl=3600)` 로 캐싱하면 동일 날짜 재실행 시 빠릅니다.

### 8.3 DART corp code XML 다운로드 (수백 KB)

매 실행 시 `corpCode.xml.zip`을 다운로드합니다. `lru_cache`로 프로세스 내 캐싱은 되지만, 프로세스 재시작마다 다시 다운로드합니다. 파일 캐시(로컬 디스크)를 추가하면 콜드스타트가 빨라집니다.

---

## 9. 우선순위별 개선 권고

### P0 — 즉시 수정 (버그/데이터 신뢰성)

1. **`_to_number()` 하락값 파싱 버그 수정**: `▼1,234` 패턴에서 음수를 올바르게 추출하도록 수정
2. **포맷터의 `None` guard 통일**: `display_value()` 유틸 함수를 모든 포맷터에 일관되게 적용
3. **스크래퍼 셀렉터에 `AttributeError` 방어 추가**: `select_one()` 결과를 무조건 `.get_text()` 하지 않도록

### P1 — 단기 (안정성/디버깅)

4. **서비스 레이어 로깅 추가**: 각 컬렉터 소요시간, 성공/실패 여부를 `logger.info()` 로 기록
5. **컬렉터 병렬화**: `ThreadPoolExecutor`로 7개 market 컬렉터를 동시 실행 (예상 개선: 10초 → 3초)
6. **`get_home_market_snapshot()` 중복 호출 제거**: `market_service.py`에서 한 번만 호출하고 결과를 두 컬렉터에 전달
7. **입력 유효성 강화**: 종목명 최대 길이 제한, 허용 문자 whitelist 적용

### P2 — 중기 (기능 완성)

8. **`get_stock_basics()` 실데이터 연결**: 네이버 종목 페이지 파싱 구현 (현재 real mode에서도 `None` 반환)
9. **`FinanceDataReader` 결과 캐싱**: `@st.cache_data(ttl=3600)` 적용
10. **DART corp code 파일 캐시**: 로컬 디스크에 당일 캐시 저장

### P3 — 장기 (품질/확장성)

11. **컬렉터 유닛 테스트 추가**: mock HTTP response로 파싱 로직 검증
12. **`None` payload 포맷터 통합 테스트 추가**: 실제 real mode 실패 시나리오 커버
13. **CSS를 별도 파일로 분리**: `static/styles.css` 또는 Streamlit theme 활용
14. **Collector 간 수평 의존 제거**: `krx_collector`에서 `naver_market_collector` import 제거

---

## 부록: 파일별 요약

| 파일 | 라인수 | 품질 | 주요 이슈 |
|------|--------|------|-----------|
| `app.py` | 5 | ✅ | — |
| `src/config/settings.py` | 37 | ✅ | lru_cache process-scope 주의 |
| `src/collectors/market/krx_collector.py` | 112 | ⚠️ | 수평 의존, 하락값 파싱 |
| `src/collectors/market/naver_market_collector.py` | ~200 | ⚠️ | 셀렉터 AttributeError 위험 |
| `src/collectors/market/global_collector.py` | ~80 | ✅ | 캐싱 없음 |
| `src/collectors/market/dart_collector.py` | ~60 | ✅ | — |
| `src/collectors/stock/naver_stock_collector.py` | ~80 | ❌ | real mode 미구현 |
| `src/collectors/stock/dart_stock_collector.py` | ~120 | ✅ | — |
| `src/collectors/stock/short_selling_collector.py` | ~30 | ❌ | 전체 stub |
| `src/services/market_service.py` | 39 | ⚠️ | 로깅 없음, 순차 실행 |
| `src/services/stock_service.py` | ~50 | ⚠️ | 로깅 없음 |
| `src/formatters/market_formatter.py` | ~150 | ⚠️ | None guard 산발적 |
| `src/ui/components.py` | 740 | ⚠️ | 인라인 CSS, 가짜 CTA |
| `src/ui/pages.py` | 285 | ⚠️ | 데코레이티브 섹션 과다 |
| `tests/` | ~90 | ⚠️ | 컬렉터/서비스 미커버 |

# 작업 지시: 시황 대시보드에 시장 뉴스(제목+링크) 추가

발행: 관리자 / 수행: 개발자
브랜치: develop (main 직접 작업 금지)
근거: 프로젝트 주인 오더 — 대시보드에 기사 제목·링크 제공 (제미나이 입력용)

## 현황
- 개별 종목 대시보드: 뉴스 제목+링크 이미 렌더됨(LATEST NEWS). 손대지 말 것.
- **시황 대시보드: 시장 뉴스가 아예 없음.** 수집기·서비스·표시 전부 신규.

## 요구 결과

### 1. 시장 뉴스 수집기
`src/collectors/market/naver_market_collector.py`에 함수 추가 (예: `get_market_news`).
- 출처: `https://finance.naver.com/news/mainnews.naver` (인코딩 euc-kr)
- 셀렉터: `.articleSubject a` (제목+href). 실제로 찍어보고 확정.
- href는 상대경로(`/news/news_read.naver?...`)이므로 절대 URL로 변환.
  종목 뉴스의 `_news_url_from_href` 패턴이 재사용 가능한지 확인, 안 되면 별도 변환.
- 반환: `[{"title", "url", "source", "date"}]` — 종목 뉴스 `news_items`와 **같은 스키마**
  (대시보드 `_news_grid3_html` 그대로 재사용 위함). source/date 없으면 빈 문자열.
- 요약은 수집하지 않는다(주인 지시: 제목+링크면 충분).
- limit 12개 정도. 실패 시 빈 리스트(예외 격리).

### 2. market_service 연결
`generate_market_briefing`의 기존 `ThreadPoolExecutor`에 `market_news` 수집을 추가.
payload에 `"news_items": [...]` 키로 넣는다. (P0-3 병렬 구조 안에서)

### 3. build_market_dashboard 표시
종목 대시보드와 동일하게 LATEST NEWS 섹션 추가:
```
<div class="rule">...LATEST NEWS...</div>
{_news_grid3_html(news_items, [])}
```
위치는 본문 하단(기존 공시 자리 비었으니 그 부근). `_news_grid3_html` 재사용.

### 4. TXT에도 제목+링크 (주인 추가 지시)
뉴스는 **TXT와 대시보드 둘 다** 들어가야 한다. 제목+링크 필수.

- `_format_news_item` (naver_stock_collector): 현재 "제목 (언론사, 날짜)"로 링크가 빠짐.
  → 링크를 붙인다. 예: `제목 (언론사, 날짜)\n  링크URL` 또는 `제목 — URL`.
  이 함수는 종목 TXT에 바로 반영되므로 **개별 종목 TXT 뉴스에도 링크가 생긴다**.
- 시황 포맷터(`market_formatter.py`): 시장 뉴스 섹션을 추가해 제목+링크 출력.
  (공시 섹션 제거된 자리에 "주요 뉴스" 섹션)

## 검증
- 시황: TXT에 뉴스 제목+링크가 있고, 대시보드에도 떠서 클릭 시 이동하는지.
- 종목: TXT 뉴스에 링크가 새로 붙는지(기존 제목/언론사 유지), 대시보드는 그대로인지.
- `get_market_news()` 직접 호출해 len과 url 출력.
- `.venv/bin/python3 -m pytest` 전체 통과. 뉴스 포맷 테스트 있으면 링크 포함으로 갱신.

## 주의
- main 푸시 금지. develop 커밋만.
- TXT 링크는 한 줄에 길어지므로 줄바꿈/구분자로 가독성 확보. 제미나이 입력용이니 URL이 깨지지 않게.

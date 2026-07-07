# cat_stock

한국 증시 데이터를 수집해서 ChatGPT / Gemini에 바로 붙여넣을 수 있는 분석용 텍스트를 만드는 웹앱입니다.

**서비스 주소: https://catstock-production.up.railway.app**

## 현재 상태

- 시황 브리핑 생성
- 개별 종목 분석 생성
- 테마 공부 텍스트 생성 (종목·뉴스 실데이터 연결)
- 화면에서 바로 복사 가능
- `.txt` 다운로드 가능
- 대시보드 HTML 다운로드 및 미리보기
  - 종목/시황 대시보드 HTML은 Plotly CDN을 사용하므로 열람 시 인터넷 연결이 필요합니다.
- AI 칼럼 생성 (OpenAI API 키가 있을 때)
- CAT COIN 모드 스위처 (로고 클릭 전환 / 공부용 대시보드)
- 과거 거래일 브리핑 SQLite 저장 — 한 번 생성한 지난 날짜는 재크롤링 없이 즉시 서빙
- Railway 배포 완료

## 현재 연결된 실데이터

### 시황 브리핑
- 코스피 / 코스닥 지수, 등락률, 거래대금, 전일대비
- 거래대금 상위 종목
- 외국인 / 기관 / 개인 수급 요약
- 외국인 / 기관 순매수·순매도 상위
- 프로그램 차익 / 비차익 / 전체
- 상한가 종목
- 업종별 등락률
- 당일 상승 / 하락 상위
- 5% 이상 상승 종목
- 시간외 단일가 급등락 (부분 연결)
- DART 주요 공시
- 글로벌 지표 — 다우, S&P500, 나스닥, 달러/원, 미국 10년물, WTI, 상해, 심천

### 개별 종목 분석
- 현재가, 등락률, 거래대금, 시가총액
- 52주 고저, PER, PBR, ROE
- 5일 / 20일 / 60일선 위치
- 외국인 / 기관 최근 20일 누적 수급 (주 수 기준)
- 최근 뉴스 헤드라인 / 원문 링크
- 증권사 리포트 (네이버 + fnguide 요약)
- 컨센서스 목표가
- 최근 공시
- 최근 재무 요약 (매출/영업이익/순이익 4기간)
- 대주주 지분율
- 재무 위험 체크 (CB/BW/유증 키워드)

### 테마 공부
- 테마 관련 종목 목록 (현재가·등락률)
- 테마 관련 최근 뉴스

## 아직 안 된 것

- 코스피200 선물 외국인 / 기관 순매수
- 시황 브리핑 증권사 리포트
- 개별 종목 공매도 잔고 비율
- 개별 종목 수급 금액 기준 전환 (현재 주 수)
- 테마 공시 / 글로벌 피어 / 시총·밸류 데이터
- 52주 신고가 / 신저가 전용 URL 기반 수집

## 실행

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## 환경 변수

`.env.example`를 참고해서 `.env` 파일을 만들면 됩니다.

- `DART_API_KEY`
- `KIS_APP_KEY`
- `KIS_APP_SECRET`
- `OPENAI_API_KEY`
- `OUTPUT_DIR`
- `APP_TITLE`

## 배포

`railway.json`이 포함되어 있어서 Railway에 바로 올릴 수 있습니다.  
main 브랜치에 push하면 자동 배포됩니다.

- 운영 주소: https://catstock-production.up.railway.app

### 과거 브리핑 저장 유지 (볼륨)

과거 거래일 리포트는 `OUTPUT_DIR`의 `cat_stock.db`(SQLite)에 저장됩니다.
Railway 컨테이너 디스크는 재배포 때 초기화되므로, 저장분을 유지하려면
서비스에 **볼륨을 마운트**해야 합니다:

1. Railway 대시보드 → cat_stock 서비스 → 우클릭(또는 Settings) → **Attach Volume**
2. Mount path: `/app/output`
3. 환경 변수 `OUTPUT_DIR=/app/output` 설정 (기본값 `output`은 상대 경로라 마운트 경로와 다를 수 있음)

볼륨 없이도 동작은 하며, 재배포 시점에 저장분만 사라집니다.

## 참고 문서

- [문서 목차](docs/README.md)
- [앱 데이터 흐름 가이드](docs/앱_데이터_흐름_가이드.md)
- [현재 연결된 실데이터 목록](docs/현재_연결된_실데이터_목록.md)
- [요구사항 요약](docs/요구사항_요약.md)
- [진행계획 및 파일구조](docs/진행계획_및_파일구조.md)
- [CAT COIN 기획서](docs/CAT_COIN_기획서.md)
- [서비스 품질 평가](docs/서비스_품질_냉철한_평가.md)

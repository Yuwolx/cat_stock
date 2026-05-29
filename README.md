# cat_stock

한국 증시 데이터를 수집해서 ChatGPT / Gemini에 바로 붙여넣을 수 있는 분석용 텍스트를 만드는 웹앱입니다.

## 현재 상태

- 시황 브리핑 생성
- 개별 종목 분석 생성
- 테마 공부 텍스트 생성
- 화면에서 바로 복사 가능
- `.txt` 다운로드 가능
- Railway 배포 가능

## 현재 연결된 실데이터

### 시황 브리핑
- 코스피 / 코스닥 지수, 등락률, 거래대금, 전일대비
- 거래대금 상위 종목
- 외국인 / 기관 / 개인 수급 요약
- 외국인 / 기관 순매수·순매도 상위
- 프로그램 차익 / 비차익 / 전체
- 상한가 종목
- DART 주요 공시
- 글로벌 지표
  - 다우
  - S&P500
  - 나스닥
  - 달러/원
  - 미국 10년물
  - WTI
  - 중국 상해

### 개별 종목 분석
- 현재가
- 등락률
- 거래대금
- 시가총액
- 52주 고저
- PER / PBR / ROE
- 5일 / 20일 / 60일선 위치
- 외국인 / 기관 최근 20일 누적 수급
- 최근 뉴스
- 증권사 리포트
- 컨센서스 목표가
- 최근 공시
- 최근 재무 요약
- 대주주 지분율

## 아직 안 된 것

- 시황 브리핑
  - 업종별 등락
  - 52주 신고가 / 신저가
  - 시간외 단일가 급등락
  - 코스피200 선물 외국인 / 기관 순매수
  - 중국 심천 지수
  - 증권사 리포트
- 개별 종목 분석
  - 공매도 잔고 비율
  - 재무 위험 체크 자동화
- 테마 공부
  - 실데이터 연결 전

## 실행

### PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

### Git Bash

```bash
python -m venv .venv
source .venv/Scripts/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## 환경 변수

`.env.example`를 참고해서 `.env` 파일을 만들면 됩니다.

- `DART_API_KEY`
- `OUTPUT_DIR`
- `APP_TITLE`

## 배포

`railway.json`이 포함되어 있어서 Railway에 바로 올릴 수 있습니다.

## 참고 문서

- [현재_연결된_실데이터_목록.md](C:/Users/SSAFY/Desktop/cat_stock/현재_연결된_실데이터_목록.md)
- [요구사항_요약.md](C:/Users/SSAFY/Desktop/cat_stock/요구사항_요약.md)
- [진행계획_및_파일구조.md](C:/Users/SSAFY/Desktop/cat_stock/진행계획_및_파일구조.md)

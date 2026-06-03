# 작업 지시: AI 칼럼 생성 LLM을 Claude → OpenAI(GPT)로 전환

발행: 관리자 / 수행: 개발자
브랜치: develop (main 직접 작업 금지)
근거: 프로젝트 주인 오더 — 금일 리포트 생성은 GPT API 사용

## 목표
`column_service.py`의 칼럼 생성 백엔드를 기존 Claude 계열 호출에서 OpenAI로 교체한다.
**P0-1에서 만든 실패 사유 구조(`is_available`/`reason`)는 그대로 유지**한다. LLM 호출부만 교체.

## 변경

### 1. settings (`src/config/settings.py`)
- 기존 AI API 키 설정 → `openai_api_key`로 교체 (env: `OPENAI_API_KEY`).
- 코인 등 다른 곳에서 기존 AI API 키 설정을 안 쓰는지 grep 확인 후 제거.

### 2. .env.example
- 기존 AI API 키 줄을 `OPENAI_API_KEY=`로 교체.

### 3. requirements.txt
- 기존 Claude SDK 제거, `openai` 추가.

### 4. column_service.py
- 기존 LLM 호출부 → `_call_gpt`로 교체. OpenAI SDK 사용.
- reason 매핑 유지: `missing_api_key` / `package_missing`(`import openai` 실패) / `api_error` / `ok`.
- 타임아웃 명시(20초 수준).
- 모델: 최신 경량 모델(예: `gpt-4o-mini`) 사용. 정확한 모델명은 개발자가 현재 사용 가능한 것으로 확정.
- 프롬프트 내용/톤(경제신문 칼럼, 제목 --- 본문)은 그대로 유지.
- `generate_stock_column` / `generate_market_column` 반환 스키마 변경 없음.

### 5. UI/문서 문구
- `dashboard.py` `_column_html`의 `missing_api_key` 안내 문구를 OpenAI 기준으로:
  "AI 칼럼: OPENAI_API_KEY가 설정되지 않았습니다." / `package_missing`: "openai 패키지가 설치되지 않았습니다."
- byline "CAT STOCK AI Analysis"는 유지.

### 6. 테스트 (tests/test_column_service.py)
- 기존 제공자 전제 테스트를 openai 기준으로 갱신. 키 없을 때 `reason="missing_api_key"` 확인은 그대로 유지(네트워크 호출 없이).

## 검증
- 키 없는 상태: 대시보드가 "OPENAI_API_KEY 미설정" 안내를 예외 없이 렌더.
- `.venv/bin/python3 -m pytest` 전체 통과.
- (키 있으면) 실제 칼럼 1회 생성해 제목/본문 분리가 정상인지 확인.

## 주의
- main 푸시 금지. develop 커밋만.
- P0-1의 구조화된 실패 처리 로직을 깨지 말 것 — LLM 교체로 인한 회귀 금지.

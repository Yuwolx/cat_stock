# 작업 지시: P0-1 AI 칼럼 실패 이유 구조화

발행: 관리자 / 수행: 개발자
브랜치: develop (main 직접 작업 금지)
근거: docs/CODE_REVIEW.md P0-1

## 문제

`column_service.py`의 LLM 호출부, `generate_stock_column`, `generate_market_column`이
실패 시 모두 `None`을 반환한다. 키 없음 / 패키지 없음 / API 오류가 구분되지 않아
UI는 "왜 칼럼이 없는지" 표시하지 못한다.

## 요구 결과

### 1. column_service.py

LLM 호출부 반환을 `dict`로 변경:

```
{"text": str | None, "reason": "ok" | "missing_api_key" | "package_missing" | "api_error"}
```

- 키 없음 → `{"text": None, "reason": "missing_api_key"}`
- `import openai` 실패 → `package_missing`
- API 호출 예외 → `api_error` (예외 메시지는 로깅만, 사용자 노출 X)
- 성공 → `{"text": ..., "reason": "ok"}`

OpenAI 클라이언트에 타임아웃 명시.

`generate_stock_column` / `generate_market_column` 반환을 **항상 dict**로:

```
{"is_available": bool, "reason": str, "title": str | None, "body": str | None}
```

- 성공: `is_available=True, reason="ok"`, 기존 title/body
- 실패: `is_available=False, reason=<위 reason>`, title/body는 None

### 2. dashboard.py `_column_html`

`column` dict의 `is_available`/`reason`을 보고 분기. reason별 한국어 안내:

- `missing_api_key`: "AI 칼럼: OPENAI_API_KEY가 설정되지 않았습니다."
- `package_missing`: "AI 칼럼: openai 패키지가 설치되지 않았습니다."
- `api_error`: "AI 칼럼: 생성 중 오류가 발생했습니다."
- 그 외/None: 기존 기본 안내

성공 시 기존 칼럼 렌더링 유지.

### 3. 테스트 (tests/test_column_service.py 신규)

- 키 없을 때 `is_available=False, reason="missing_api_key"` 확인 (네트워크 호출 없이)
- `_split_title_body`가 `---` 있는/없는 입력 둘 다 처리하는지

## 검증

`.venv/bin/python3 -m pytest tests/test_column_service.py` 통과,
키 없는 상태에서 대시보드 빌드가 예외 없이 안내문을 렌더링하는지 확인.

## 주의

- main 푸시 금지. develop 커밋만.
- 기존 호출부(market_service/stock_service)는 항상 dict를 받으므로 None 가드 불필요해짐 — 확인해서 정리.

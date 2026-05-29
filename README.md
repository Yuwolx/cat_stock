# cat_stock

한국 증시 데이터를 수집해서 AI 채팅창에 바로 붙여넣을 수 있는 텍스트를 만드는 웹앱입니다.

## 현재 범위

- 시황 브리핑 생성
- 개별 종목 분석 생성
- 테마 공부용 텍스트 생성
- 화면에서 바로 복사 가능
- TXT 다운로드 가능
- DART 일부 실데이터 연결
- 시황 브리핑 실데이터 1차 연결
- 개별 종목 분석 실데이터 일부 연결

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

`.env.example`을 참고해서 `.env` 파일을 만들면 됩니다.

- `DART_API_KEY`
- `USE_MOCK_DATA`
- `OUTPUT_DIR`

## 배포

`railway.json`이 포함되어 있어 Railway 배포를 바로 진행할 수 있습니다.

## 남은 작업

1. 시황 브리핑 남은 항목 연결
2. 개별 종목 분석 보강
3. 테마 공부 실데이터 연결
4. 배포 환경 검증

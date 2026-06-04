# 작업 지시: 대시보드 HTML 경량화 (plotly 4.8MB)

발행: 관리자 / 수행: 개발자
브랜치: develop (main 직접 작업 금지)
근거: 배포 후 관리자 실측 — 종목/시황 대시보드 HTML 4.8MB

## 문제
- `build_stock_dashboard` / `build_market_dashboard` 결과 HTML이 **약 4.8MB**.
- 원인: `dashboard.py` `_fig_html`가 `include_plotlyjs=first`로 plotly.js(~3.5MB)를 인라인.
- 코인 대시보드는 22KB(plotly 미사용)라 일관성도 없음.
- 사용자가 "대시보드 HTML" 다운로드 시 무겁고, 미리보기 렌더도 느림.

## 결정 포인트 (개발자가 확인 후 택1, 애매하면 관리자에게 질의)
1. **CDN 방식** `include_plotlyjs="cdn"` → HTML ~50KB. 단 **열 때 인터넷 필요**(오프라인 열람 불가).
2. **오프라인 유지 + 1회만 인라인**: plotly.js를 문서 전체에서 정확히 1번만 포함하도록 보장하고,
   현재 정말 1회인지 점검(4.8MB면 중복 의심). 1회여도 3.5MB는 남음.

→ 권고: 대시보드는 "AI에 붙여넣을 자료를 받아 보는" 용도라 **CDN(1번)이 현실적**.
   오프라인 열람이 꼭 필요하다는 근거가 없으면 CDN으로.

## 요구 결과
- 종목/시황 대시보드 HTML 용량을 수십 KB 수준으로 축소.
- 차트는 그대로 렌더(시각 동일). 다운로드/미리보기 정상.
- 코인 대시보드와 차트 처리 방식을 가능하면 통일.

## 검증
- `build_stock_dashboard`/`build_market_dashboard` 결과 `len()`을 출력해 축소 확인(목표 < 200KB).
- 실제 대시보드 미리보기/다운로드가 차트 포함 정상 렌더되는지 확인.
- `.venv/bin/python3 -m pytest` 전체 통과.

## 주의
- main 푸시 금지. develop 커밋만.
- CDN 택하면 README/문서에 "대시보드 HTML 열람 시 인터넷 필요" 한 줄 명시.

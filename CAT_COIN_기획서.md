# CAT COIN - 공부용 코인 대시보드 기획서

> 작성일: 2026-05-31
> 작업 브랜치: `develop`
> 핵심 방향: CAT STOCK은 프롬프트에 넣기 좋은 텍스트 생성 도구, CAT COIN은 내가 코인을 공부하기 위한 대시보드 도구.

---

## 1. 한 줄 정의

> CAT COIN은 매수/매도 신호를 주는 앱이 아니라, "왜 이 코인이 움직였는지"를 스스로 설명할 수 있게 도와주는 공부용 대시보드다.

CAT STOCK의 핵심 산출물이 텍스트라면, CAT COIN의 핵심 산출물은 화면이다.
텍스트 출력은 보조 기능으로 남기되, 메인은 차트, 지표 카드, 섹터 히트맵, 학습 질문, 위험 체크리스트다.

---

## 2. CAT STOCK과 CAT COIN의 차이

| 구분 | CAT STOCK | CAT COIN |
|---|---|---|
| 주 목적 | AI 프롬프트에 붙여넣기 좋은 텍스트 생성 | 코인 시장을 공부하기 위한 시각적 대시보드 |
| 핵심 화면 | 입력 영역 + 텍스트 출력 박스 | 지표 카드 + 차트 + 섹터/코인 비교 |
| 결과물 | 시황 브리핑 TXT, 종목 분석 TXT | 대시보드, 학습 노트, 관찰 질문 |
| 사용 흐름 | 생성 -> 복사 -> 프롬프트 활용 | 시장 보기 -> 원인 추적 -> 개별 코인 공부 -> 메모 |
| UX 톤 | 정리된 문서 | 공부방, 리서치 노트, 관찰 도구 |

---

## 3. 공부 흐름

초보자가 코인을 볼 때 가장 자주 놓치는 것은 "가격이 올랐다/내렸다" 이후의 질문이다. CAT COIN은 아래 순서로 생각하게 만든다.

1. 지금 시장 전체가 위험 선호인지 위험 회피인지 본다.
2. BTC와 ETH가 시장을 끌고 있는지, 알트코인이 따라오는지 본다.
3. 한국 거래소에서만 과열된 움직임인지 확인한다.
4. 어떤 섹터가 강한지, 그 섹터가 실제로 무엇을 하는지 공부한다.
5. 개별 코인의 가격, 유동성, 공급 구조, 프로젝트 지표, 파생상품 과열을 분해한다.
6. 오늘 배운 내용을 한 줄 가설과 반증 조건으로 남긴다.

이 흐름 때문에 CAT COIN은 "좋은 코인 추천"이 아니라 "좋은 질문을 던지는 화면"이어야 한다.

---

## 4. 전체 화면 구조

### 상단

```
CAT STOCK / CAT COIN 토글
현재 모드: CAT COIN
오늘의 시장 상태 요약: 위험 선호 / 중립 / 위험 회피 / 알트 과열 관찰
마지막 업데이트 시각
```

### 메인 탭

| 탭 | 역할 | 핵심 질문 |
|---|---|---|
| 처음 가이드 | 코인을 모르는 사람을 위한 읽는 순서와 용어 설명 | 어떤 순서로 봐야 덜 헷갈리나? |
| 코인 시황 | 전체 시장 온도와 유동성 확인 | 지금 코인 시장은 어떤 국면인가? |
| 개별 코인 | 한 코인을 구조적으로 뜯어보기 | 이 코인은 왜 움직이고 무엇을 확인해야 하나? |
| 섹터 공부 | 코인을 테마가 아니라 산업 구조로 보기 | 이 섹터는 뭘 해결하고 어떤 지표를 봐야 하나? |
| 학습 노트 | 관찰 내용 저장 | 오늘 배운 것을 내 언어로 설명할 수 있나? |

초기 MVP는 `처음 가이드`, `코인 시황`, `개별 코인`, `섹터 공부`, `학습 노트` 5개 탭으로 시작한다.

---

## 5. 코인 시황 대시보드

### 목적

시장 전체가 강한지, 일부 코인만 튀는지, 한국에서만 과열인지, 유동성이 들어오는지 확인한다.

### 상단 핵심 카드

| 카드 | 데이터 | 공부 포인트 |
|---|---|---|
| 총 코인 시가총액 | CoinGecko `/global` | 코인 시장 전체 크기와 전일 대비 변화 |
| 24h 거래대금 | CoinGecko `/global` | 가격 상승이 거래량을 동반하는지 |
| BTC 가격/수익률 | CoinGecko `/coins/markets` | 시장 기준 자산의 방향 |
| ETH 가격/수익률 | CoinGecko `/coins/markets` | 스마트컨트랙트 생태계의 방향 |
| BTC 도미넌스 | CoinGecko `/global` | 돈이 BTC에 몰리는지, 알트로 퍼지는지 |
| ETH/BTC 비율 | CoinGecko 가격 데이터로 계산 | ETH가 BTC 대비 강한지 |
| 공포탐욕지수 | Alternative.me `/fng/` | 심리 과열/공포 확인 |
| 스테이블코인 시총 | DefiLlama `/stablecoins` | 시장 대기 자금의 큰 방향 |
| 김치 프리미엄 | Upbit BTC KRW + BTC USD + USD/KRW | 한국 거래소 과열 여부 |

### 차트와 테이블

| 영역 | 표현 | 이유 |
|---|---|---|
| BTC/ETH 7일/30일 가격 차트 | 라인 차트 | 기준 자산 방향 확인 |
| BTC 도미넌스 vs 알트 breadth | 라인/막대 | BTC 장인지 알트 장인지 학습 |
| 업비트 KRW 거래대금 Top 10 | 테이블 | 한국 개인 자금이 몰리는 코인 확인 |
| 글로벌 시총 Top 20 | 테이블 | 전체 시장 리더 확인 |
| 24h/7d 상승률 Top 10 | 테이블 | 단기 과열 후보 확인 |
| 섹터 히트맵 | 카드 그리드 | 어떤 서사가 시장을 끄는지 확인 |
| 스테이블코인 시총 추이 | 라인 차트 | 유동성 증가/감소 확인 |

### 시장 국면 라벨

정답을 단정하지 않고, 조건 기반으로 학습용 라벨을 붙인다.

| 라벨 | 예시 조건 | 화면 문구 |
|---|---|---|
| 위험 선호 | BTC/ETH 상승, 거래대금 증가, 공포탐욕 중립 이상 | "자금이 시장에 들어오는 국면으로 보입니다." |
| 위험 회피 | BTC 하락, 도미넌스 상승, 알트 약세 | "알트보다 BTC 방어력이 중요한 국면입니다." |
| 알트 확산 | BTC 횡보, 도미넌스 하락, 섹터 다수 상승 | "테마/섹터별 확산을 관찰할 구간입니다." |
| 한국 과열 | 김치 프리미엄 상승, 업비트 거래대금 집중 | "한국 거래소 수급이 가격을 밀 수 있는 구간입니다." |
| 관망 | 가격/거래량/심리가 엇갈림 | "방향보다 기준 자산 확인이 우선입니다." |

---

## 6. 개별 코인 대시보드

### 목적

"이 코인 올랐네"에서 끝내지 않고, 가격, 유동성, 공급, 사용처, 위험 요인을 분해한다.

### 입력

- 코인명, 심볼, CoinGecko ID 검색
- 한글 별칭 우선 지원: 비트코인, 이더리움, 솔라나, 리플 등 자주 쓰는 이름은 내부 사전으로 보정
- 검색 실패 시 CoinGecko `/search` 결과를 후보로 보여주기

### 화면 구성

| 영역 | 데이터 | 공부 포인트 |
|---|---|---|
| 기본 카드 | 가격, 24h/7d/30d 수익률, 시총, FDV, 거래량 | 가격보다 시총/FDV/거래량을 같이 보는 습관 |
| 공급 구조 | 유통량, 총공급량, 최대공급량 | 희소성, 인플레이션, 희석 위험 |
| ATH/ATL | 최고가 대비 하락률, 최저가 대비 상승률 | 지금 위치가 역사적으로 어디인지 |
| 가격/거래량 차트 | 7일/30일/90일 | 상승이 거래량을 동반했는지 |
| 거래소/유동성 | CoinGecko ticker, Upbit 상장 여부 | 특정 거래소 의존도와 한국 수급 |
| 프로젝트 정보 | 카테고리, 설명, 공식 링크 | 코인이 실제로 무엇을 하는지 |
| 개발/커뮤니티 | CoinGecko developer/community data | 활동이 있는 프로젝트인지 |
| DeFi 지표 | DefiLlama TVL, fees, revenue | 프로토콜이면 실제 사용량 확인 |
| 파생상품 | Binance funding rate, open interest | 레버리지 과열 여부 |
| 위험 체크 | 고FDV/저유통, 거래량 급증, 김치 프리미엄, 유의종목 | 초보자가 놓치기 쉬운 리스크 |

### 학습 카드

개별 코인 화면 하단에는 "판단"이 아니라 "공부 질문"을 보여준다.

```
오늘의 관찰
- 가격은 올랐는데 거래량도 같이 늘었나?
- 글로벌 거래소와 업비트 중 어디서 더 강한가?
- 이 코인의 핵심 수요는 수수료, 스테이킹, 담보, 밈, 거버넌스 중 무엇인가?
- FDV가 시총보다 지나치게 크면 앞으로 어떤 희석 위험이 있나?
- 이 가설이 틀렸다고 말해줄 데이터는 무엇인가?
```

---

## 7. 섹터 공부 대시보드

### 목적

코인을 이름으로만 외우지 않고, 섹터별로 무엇을 해결하는지, 어떤 지표를 봐야 하는지 익힌다.

### 기본 섹터

| 섹터 | 공부해야 할 핵심 |
|---|---|
| Layer 1 | 보안, 처리량, 수수료, 개발자 생태계 |
| Layer 2 | 확장성, 수수료 절감, TVL, 브릿지 유동성 |
| DeFi | TVL, fees, revenue, 사용자 예치/차입 수요 |
| DEX | 거래량, 수수료, 유동성 깊이 |
| Stablecoin | 시총, 체인별 분포, 발행/상환 추세 |
| AI | 실제 제품/수요와 단순 서사의 구분 |
| DePIN | 실물 인프라 수요와 토큰 인센티브 구조 |
| RWA | 온체인 자산 규모, 규제/수익원 |
| Meme | 커뮤니티, 거래량, 유동성, 급락 리스크 |
| Gaming/NFT | 활성 사용자, 거래량, 지속 가능한 경제 |
| Exchange Token | 거래소 점유율, 수수료 할인, 소각/수익 연동 |
| Oracle | 데이터 수요, 파트너십, 네트워크 사용량 |

### 화면 구성

| 영역 | 표현 | 데이터 소스 |
|---|---|---|
| 섹터 히트맵 | 24h/7d 수익률, 시총, 거래대금 | CoinGecko `/coins/categories` |
| 섹터별 대표 코인 | Top 3-10 코인 | CoinGecko category + `/coins/markets` |
| 섹터 설명 카드 | 이 섹터가 해결하는 문제 | 내부 설명 + CoinGecko category content |
| DeFi 섹터 상세 | TVL, fees, revenue | DefiLlama |
| 스테이블코인 상세 | 총 시총, 체인별 분포 | DefiLlama stablecoins |
| 학습 질문 | 섹터별 체크리스트 | 내부 룰 |

---

## 8. 학습 노트

MVP에서는 자동 저장 없이 "오늘의 학습 노트 TXT" 다운로드만 제공한다. 이후에는 세션 단위 저장을 붙인다.

### 노트 템플릿

```
[CAT COIN 학습 노트 - YYYY-MM-DD HH:mm]

1. 오늘 시장 국면
- 위험 선호 / 위험 회피 / 알트 확산 / 한국 과열 / 관망

2. 가장 강한 섹터
- 섹터:
- 강한 이유로 보이는 데이터:

3. 오늘 본 코인
- 코인:
- 상승/하락 원인 가설:
- 반증 조건:

4. 다음에 확인할 것
- 지표:
- 자료:
```

---

## 9. 데이터 소스

| 소스 | 사용 범위 | 인증/비용 | 비고 |
|---|---|---|---|
| CoinGecko API | 글로벌 시총, BTC/ETH, 코인 목록, 가격, 시총, 거래량, 카테고리, 코인 상세 | 무료 Demo API 키 우선, 유료 플랜 선택 가능 | 핵심 시장 데이터 |
| Upbit Quotation API | KRW 마켓 목록, 현재가, 캔들, 호가, 거래대금 상위, 유의/주의 정보 | 공개 시세 API, 인증 불필요 | 한국 거래소 수급과 김치 프리미엄 |
| Alternative.me Fear & Greed | 공포탐욕지수 | 무료, attribution 필요 | 심리 지표 |
| DefiLlama Free API | TVL, 체인별 TVL, 스테이블코인, DEX volume, fees/revenue, yields | 무료, 인증 불필요 | DeFi/온체인 공부용 |
| Binance USD-M Futures API | funding rate, open interest | 공개 엔드포인트 | 파생상품 과열 참고용, 선택 기능 |
| 기존 FinanceDataReader/yfinance | USD/KRW, 나스닥, 미국 10년물, DXY 등 | 기존 프로젝트 재사용 | 코인 매크로 배경 |

### 참고 링크

- CoinGecko API: https://docs.coingecko.com/reference/introduction
- CoinGecko `/global`: https://docs.coingecko.com/v3.0.1/reference/crypto-global
- CoinGecko `/coins/markets`: https://docs.coingecko.com/reference/coins-markets
- CoinGecko `/coins/{id}`: https://docs.coingecko.com/v3.0.1/reference/coins-id
- CoinGecko `/coins/categories`: https://docs.coingecko.com/reference/coins-categories
- Upbit Quotation REST API: https://global-docs.upbit.com/docs/upbit-quotation-restful-api
- Upbit market list: https://docs.upbit.com/kr/v1.5.9/reference/%EB%A7%88%EC%BC%93-%EC%BD%94%EB%93%9C-%EC%A1%B0%ED%9A%8C
- Upbit candles: https://docs.upbit.com/kr/reference/list-candles-days
- Upbit rate limits: https://docs.upbit.com/kr/reference/rate-limits
- Alternative.me Fear & Greed API: https://alternative.me/crypto/fear-and-greed-index/
- DefiLlama API: https://api-docs.defillama.com/
- Binance funding rate: https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Get-Funding-Rate-History
- Binance open interest: https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Open-Interest

---

## 10. 계산 지표

### 김치 프리미엄

```
김치 프리미엄 =
(업비트 BTC 원화 가격 / (CoinGecko BTC USD 가격 * USD/KRW)) - 1
```

BTC를 기본으로 계산하고, 개별 코인 화면에서는 해당 코인이 Upbit KRW 마켓에 있을 때만 별도 계산한다.

### 거래량 강도

```
거래량 강도 =
현재 24h 거래량 / 최근 30일 평균 24h 거래량
```

초기에는 CoinGecko 30일 market chart로 계산한다. API 호출량이 부담되면 Top 20과 선택 코인에만 적용한다.

### 시총 대비 거래량

```
Volume / Market Cap
```

단기 관심이 큰지 보는 보조 지표다. 높다고 좋은 코인이라는 뜻은 아니며, 과열/회전율 관찰용으로만 사용한다.

### FDV 희석 비율

```
FDV / Market Cap
```

값이 높을수록 향후 토큰 발행/언락으로 기존 보유자가 희석될 수 있다. 데이터가 없으면 표시하지 않는다.

### 파생상품 과열

```
Funding Rate + Open Interest 변화
```

펀딩이 높고 OI가 빠르게 늘면 롱 과열 가능성을 경고한다. 이것도 매도 신호가 아니라 "주의해서 공부할 지점"이다.

---

## 11. 코드 구조 제안

현재 구조를 유지하되, 코인 기능은 별도 하위 폴더로 나눈다.

```
src/
├── collectors/
│   ├── market/                   # 주식 시황 기존
│   ├── stock/                    # 개별 종목 기존
│   ├── theme/                    # 테마 기존
│   └── coin/                     # 신규
│       ├── coingecko_client.py
│       ├── upbit_client.py
│       ├── alternative_client.py
│       ├── defillama_client.py
│       └── binance_futures_client.py
├── services/
│   ├── coin_market_service.py
│   ├── coin_detail_service.py
│   └── coin_sector_service.py
├── formatters/
│   └── coin_study_note_formatter.py
└── ui/
    ├── coin_dashboard.py
    ├── components.py
    └── pages.py
```

### 원칙

- `formatter`는 메인이 아니다. 텍스트는 학습 노트 다운로드용으로만 둔다.
- `coin_dashboard.py`가 CAT COIN의 핵심 렌더링 책임을 가진다.
- 각 API 클라이언트는 raw JSON을 너무 일찍 문자열로 바꾸지 말고, service에서 학습용 payload로 정규화한다.
- API 호출은 `@st.cache_data` 또는 서비스 레벨 캐시로 감싼다.
- 무료 API만으로 MVP를 만들고, 유료/Pro 데이터는 명확히 선택 기능으로 표시한다.

---

## 12. 구현 단계

### Phase 0 - 기획 확정과 UI 방향 정리

- [x] CAT COIN을 텍스트 중심에서 대시보드 중심으로 재정의
- [x] 데이터 소스와 학습 흐름 정리
- [x] 처음 보는 사람을 위한 앱 내 가이드 탭 추가
- [x] 현재 플레이스홀더 문구를 대시보드 중심으로 수정

### Phase 1 - 코인 시황 MVP

- [x] `coingecko_client.py`: `/global`, `/coins/markets`, `/coins/categories`
- [x] `upbit_client.py`: KRW 마켓, 현재가, 거래대금 상위
- [x] `alternative_client.py`: Fear & Greed
- [x] USD/KRW 재사용
- [x] 김치 프리미엄 계산
- [x] `coin_market_service.py`
- [x] `coin_dashboard.py`: 핵심 카드, BTC/ETH, 업비트 Top 10, 글로벌 시총 상위, 섹터 온도
- [x] 학습 질문 카드
- [x] BTC/ETH 가격 차트
- [ ] 도미넌스 추이 차트

### Phase 2 - 개별 코인 MVP

- [x] CoinGecko 검색/ID 매핑
- [x] 코인 기본 지표, 공급 구조, ATH/ATL
- [x] 90일 가격 차트
- [ ] 거래량 차트
- [x] Upbit 상장 여부와 KRW 거래대금
- [x] 학습 노트 TXT 다운로드

### Phase 3 - 섹터 공부 MVP

- [x] CoinGecko category 목록
- [x] 섹터 히트맵
- [x] 섹터별 대표 코인 테이블
- [x] 섹터별 공부 포인트 카드

### Phase 4 - DeFi/온체인 확장

- [x] DefiLlama protocols/TVL
- [x] DefiLlama fees/revenue
- [x] DefiLlama stablecoins
- [x] DeFi 코인 상세 화면에 TVL 연결
- [ ] DeFi 코인 상세 화면에 개별 fees/revenue 연결

### Phase 5 - 파생상품/위험 확장

- [x] Binance funding rate
- [x] Binance open interest
- [x] 레버리지 과열 경고
- [x] 고FDV/저유통, 김치 프리미엄, 거래소 주의 플래그 위험 체크
- [ ] 거래소 집중도 위험 체크

---

## 13. UI 방향

### 대시보드 톤

- 주식 쪽보다 더 "관찰판" 느낌으로 간다.
- 큰 히어로 대신 촘촘한 지표 카드와 차트를 우선한다.
- 버튼보다 탭, 필터, 드롭다운, 토글 중심으로 만든다.
- `복사` 버튼은 보조 기능이다. CAT COIN의 메인 CTA는 `데이터 새로고침`, `학습 노트 저장`, `섹터 비교`다.

### 필수 상태

| 상태 | 표시 |
|---|---|
| 로딩 | API별로 어떤 데이터를 가져오는지 짧게 표시 |
| 부분 실패 | 실패한 소스만 경고하고 나머지 대시보드는 표시 |
| API 제한 | 캐시된 데이터 시각과 재시도 안내 |
| 데이터 없음 | "없는 데이터"와 "아직 연결하지 않은 데이터"를 구분 |
| 위험 경고 | 투자 조언이 아니라 학습용 주의 문구로 표시 |

---

## 14. API/캐시 정책

| 데이터 | 권장 TTL | 이유 |
|---|---:|---|
| CoinGecko 글로벌/Top coins | 60-180초 | 시장 데이터는 빠르게 변함 |
| Upbit ticker/orderbook | 30-60초 | 한국 거래대금과 프리미엄 확인 |
| Fear & Greed | 6-12시간 | 일 단위 지표 |
| CoinGecko category | 5-15분 | 섹터 변화는 초 단위 필요 없음 |
| DefiLlama TVL/fees/stablecoins | 15-60분 | 온체인 지표는 상대적으로 느림 |
| Binance funding/OI | 1-5분 | 파생상품 과열 참고 |

API 제한에 걸리면 화면 전체를 죽이지 말고, 캐시된 데이터와 "마지막 갱신"을 보여준다.

---

## 15. 리스크와 대응

| 리스크 | 영향 | 대응 |
|---|---|---|
| CoinGecko 무료 한도/키 정책 변경 | 핵심 데이터 장애 | Demo API 키 환경변수화, 캐시 강화 |
| Upbit rate limit | 한국 수급 데이터 누락 | 요청 배치, ticker/all 우선 검토, TTL 적용 |
| 코인명 중복 | 잘못된 코인 조회 | 검색 후보 목록과 market cap rank 표시 |
| 김치 프리미엄 계산 오차 | 과열 판단 왜곡 | USD/KRW 출처와 계산 시각 표시 |
| DefiLlama 프로토콜 매핑 실패 | DeFi 지표 누락 | 수동 매핑 테이블 + 실패 시 숨김 |
| 파생상품 데이터 과해석 | 잘못된 매매 판단 | "학습용 보조 지표" 문구 고정 |
| 유료 데이터 유혹 | 비용 증가 | MVP는 무료 API만 사용, Pro 기능은 별도 승인 후 |

---

## 16. 완료 기준

첫 배포 기준으로 사용자가 아래 질문에 답할 수 있어야 한다.

- 지금 시장은 위험 선호인가, 위험 회피인가?
- BTC가 강한가, ETH/알트가 강한가?
- 한국 거래소에서만 과열된 코인이 있는가?
- 오늘 강한 섹터는 무엇이고, 그 섹터는 실제로 무엇을 해결하는가?
- 내가 고른 코인의 시총, FDV, 거래량, 공급 구조는 어떤 상태인가?
- 이 코인에 대해 다음으로 확인해야 할 데이터는 무엇인가?

이 질문에 답할 수 있으면 CAT COIN MVP는 성공이다.

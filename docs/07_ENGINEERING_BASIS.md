# 엔지니어링 계산 툴 — 산정 기준·표준·백데이터

> 이 문서는 `backend/app/services/engineering_basis.py` 에서 생성됩니다.
> 플랫폼 UI: [엔지니어링 검토] → [📐 산정 기준·표준 근거] 탭과 동일 내용.

## 와이어로프 안전율·수명 예측
**용도**: 권상 로프의 법규 안전율 검증과 굽힘피로 기반 교체주기 산정 (DR·PM 주기 설정용)

### 수식
- **줄당 장력**: `S = (W_load + W_carriage) × g × φ_dyn ÷ n_falls ÷ η_sheave^n + W_rope×g`
  - φ_dyn: 동적계수(기동·제동 충격), 로프 자중은 양정×단위중량(≈0.0045·d² kg/m) 가산
- **최소파단력**: `F_min = K × d² × R0 / 1000  [kN]`
  - EN 12385-4 의 로프 구조별 최소파단력 계수 K 사용
- **안전율**: `SF = F_min / S   (합격: SF ≥ 5.0)`
  - 산업안전보건규칙 제163조 — 화물 직접지지 5 이상, 사람 탑승 10 이상
- **폐기도달 굽힘수**: `N = 300,000 × (D/d ÷ 25)^2.5 × (SF ÷ 5)² × k_env × k_rope`
  - Feyrer 굽힘피로 시험 경향(장력·D/d 민감도)을 반영한 보수적 간이식. 기준점: D/d=25, SF=5, 청정환경, 6스트랜드 로프에서 3×10⁵ 굽힘(문헌 시험 데이터 차수)
- **수명(년)**: `Life = N ÷ (n_sheave×2+1) ÷ (cycles/day × days/year),  계획교체 = Life × 0.8`

### 파라미터·계수 출처

| 기호 | 항목 | 값 | 출처 |
|------|------|-----|------|
| `K` | 최소파단력 계수 | 6×19: 0.330 / 6×36WS: 0.356 / 8×19: 0.293 / 회전저항: 0.318 | EN 12385-4 (Steel wire ropes — Stranded ropes) |
| `R0` | 소선 인장강도 | 1770 / 1960 N/mm² | EN 12385-4 로프 등급 |
| `SF 기준` | 요구 안전율 | 화물 직접지지 5 / 사람 탑승 10 / 훅·샤클 3 / 기타 4 | 산업안전보건규칙 제163조 |
| `k_env` | 환경계수 | 청정 1.0 / 일반 0.85 / 분진 0.65 / 부식성 0.45 | 플랫폼 보수 추정치 — ISO 4309 환경별 점검주기 강화 취지 반영, 실측 보정 대상 |
| `k_rope` | 로프구조 계수 | 일반 1.0 / 회전저항 0.6 | 회전저항 로프의 굽힘피로 수명 단축 시험 결과 (Mechanics & Industry 2017 등) |
| `지수` | D/d^2.5, SF² | D/d 민감도 2.5승, 장력 민감도 2승(SF 환산) | Feyrer 수명식의 경향 단순화 — 장력은 원식에서 S^-3 차수이나 SF 환산·보수화하여 2승 적용 |

**폐기/관리 기준** — 사용금지(법규 제166조): 한 꼬임 소선 10% 이상 단선, 직경 7% 초과 감소, 킹크·심한 변형·부식. ISO 4309: 6d/30d 구간 가시 단선수(RCN·M등급별 표), 단선 클러스터는 즉시 폐기 검토.

**적용 한계** — 간이식이므로 ±50% 오차 가능 — 신규 설비는 보수값으로 시작하고 실측 단선 추세·교체 실적으로 N0·지수를 보정(베이지안 업데이트)할 것. 다층권 드럼 크로스오버 마모는 별도 가중 필요.

**참고 문헌·표준**
- K. Feyrer, Wire Ropes: Tension, Endurance, Reliability (Springer)
- [Discard fatigue life of stranded steel wire rope (Mechanics & Industry, 2017)](https://www.mechanics-industry.org/articles/meca/pdf/2017/02/mi160060.pdf)
- [ISO 4309:2017 Cranes — Wire ropes — Care, inspection and discard](https://www.iso.org/standard/66759.html)
- [산업안전보건기준에 관한 규칙 제163·166조 (국가법령정보센터)](https://law.go.kr/LSW/lsInfoP.do?lsiSeq=272927)

## 베어링 L10 수명
**용도**: 구동부 베어링 정격수명 검증 (DR 설계 검증·교체주기 산정)

### 수식
- **기본 정격수명**: `L10h = 10⁶ / (60·N) × (C/P)^p   [h]`
  - p = 3 (볼베어링), 10/3 (롤러베어링). 90% 신뢰도(10% 는 그 전에 피로 박리)

### 파라미터·계수 출처

| 기호 | 항목 | 값 | 출처 |
|------|------|-----|------|
| `C` | 기본 동정격하중 | 베어링 카탈로그 값 | 제조사 (ISO 281 산정) |
| `P` | 등가 동하중 | 레디얼+액시얼 합성, 충격계수 반영 | ISO 281 |
| `p` | 수명지수 | 볼 3 / 롤러 10/3 | ISO 281:2007 |

**폐기/관리 기준** — 진동 속도(ISO 10816/20816 존 기준)·온도 트렌드 DRIFT 가 박리 진행의 선행지표 — FDC 병행 감시.

**적용 한계** — L10 은 통계수명 — 윤활 열화·오염·고온 시 수명계수(aISO)로 추가 감소하나 본 툴은 미반영(보수적 운영 필요). 그리스 주입주기 관리가 실수명을 지배.

**참고 문헌·표준**
- ISO 281:2007 Rolling bearings — Dynamic load ratings and rating life
- ISO 20816 (기계 진동 평가 — 구 ISO 10816)

## 배터리(LiFePO4) 수명·SOH
**용도**: AGV/AMR/OHT 배터리 교체주기·SOH 추정

### 수식
- **DOD 보정 사이클**: `N_adj = N_rated × (80 / DOD)^1.1`
  - 정격(80% DOD 기준) 대비 실 운용 DOD 보정 — 제조사 DOD-사이클 곡선 회귀
- **수명**: `Life = min(N_adj ÷ (cycles/day × 365), 캘린더수명)`
  - 사이클 수명과 캘린더(시간 경과) 수명 중 짧은 쪽
- **SOH**: `SOH ≈ 100 − 20 × (경과년 / 수명)   (EOL = SOH 80%)`
  - 선형 열화 가정 — BMS 실측 SOH 로 대체 권장

### 파라미터·계수 출처

| 기호 | 항목 | 값 | 출처 |
|------|------|-----|------|
| `N_rated` | 정격 사이클 | LFP 3,000~5,000 @ 80% DOD (EOL 80%) | 제조사 공통 데이터 (EcoTree/Grepow/Ufine 등) |
| `DOD-사이클` | 방전심도 의존성 | 100% DOD: 2,000~3,000 / 50%: 5,000~7,000 / 10%: ~14,000 | LFP 제조사 사이클 시험 데이터 |
| `온도한계` | FDC 감시 임계 | 워닝 45°C / 알람 55°C | 고온 캘린더 열화 가속 — 제조사 권고 운용범위 |

**폐기/관리 기준** — SOH 80% 도달 시 교체(EOL). 운용 SOC 윈도우 20~80% 권장.

**적용 한계** — 지수 1.1 은 LFP 곡선의 보수 회귀값 — NCM 등 타 화학계는 별도 곡선 필요. 고온·고율 방전 가속 미반영.

**참고 문헌·표준**
- [EcoTree Lithium — LiFePO4 Cycle Life & Durability](https://ecotreelithium.co.uk/news/lifepo4-battery-cycle-life-and-durability/)
- [Grepow — What is DOD for LiFePO4](https://www.grepow.com/blog/what-is-dod-for-lifepo4-batteries.html)

## 휠 마모 안전연수
**용도**: 주행휠(STK/OHT/AGV) 잔여수명 — 실측 마모율 기반

### 수식
- **잔여수명**: `Life = (D_now − D_limit) / wear_rate × k_safety`
  - k_safety 0.8: 편마모·가속마모 불확실성 여유

### 파라미터·계수 출처

| 기호 | 항목 | 값 | 출처 |
|------|------|-----|------|
| `D_limit` | 마모한계경 | 제조사 도면값 (통상 신품경 −5~10%) | 제조사/DIN 15070 계열 |
| `wear_rate` | 연간 마모율 | PM 실측(비전 DIMENSION) 추세로 산정 | 자사 측정 데이터 |
| `경도` | 휠 경도 기준 | 최소 300HB, 고듀티 350~400HB | DIN 15070 계열 권고 |

**폐기/관리 기준** — 마모한계경 도달, 편마모/플랜지 마모 과다, 답면 박리·크랙. 구동휠 좌우 직경차는 CMAA 기준 관리.

**적용 한계** — 선형 마모 가정 — 레일 상태 악화·과하중 시 가속 마모 미반영. 비전 측정 주기 단축으로 추세 감시.

**참고 문헌·표준**
- DIN 15070 (크레인 휠) / DIN 15071 (베어링)
- [Extending Crane Wheel and Rail Life](https://www.linkedin.com/pulse/extending-crane-wheel-rail-life-aleksandar-miljevic)

## 모터 용량 산정 (주행/권상)
**용도**: DR 단계 구동 모터 용량 적정성 검증

### 수식
- **주행**: `F = m·g·μ + m·a,   P = F·v / η / 1000   [kW]`
  - μ: 주행저항계수(휠/레일 0.01~0.02), 가속분은 피크로 별도 평가
- **권상**: `P = m·g·v / η / 1000   [kW]  (+ 가속분 피크)`
- **선정**: `P_motor = max(P_steady × SF, P_peak) → 표준 용량 절상`
  - 표준 용량 계열: 0.4/0.75/1.5/2.2/3.7/5.5/7.5/11/15/18.5/22/30/37/45/55/75/90/110 kW (KS C IEC 60034 계열)

### 파라미터·계수 출처

| 기호 | 항목 | 값 | 출처 |
|------|------|-----|------|
| `μ` | 주행저항계수 | 강휠/강레일 0.01~0.02 (기본 0.015) | 크레인 설계 실무 표준값 |
| `η` | 기계효율 | 감속기+휠 0.85 (기본) | 감속기 1단 0.95~0.97 누적 |
| `SF` | 서비스팩터 | 1.2 (기본) | 듀티·기동빈도 여유 |

**적용 한계** — 인버터 구동 시 피크는 과부하율(150%/60s)로 흡수 가능 — 별도 확인. 권상용은 제동저항 용량·브레이크 토크(정격 1.5배) 함께 검토. 경사·풍하중 미반영.

**참고 문헌·표준**
- KS C IEC 60034 (회전기기) — 표준 출력 계열

## 컨베이어 구동 출력
**용도**: 벨트 컨베이어 모터 용량 개산

### 수식
- **필요동력**: `P = [μ·g·M_moving·v + Q·g·H] / η × SF / 1000   [kW]`
  - M_moving: 벨트·롤러 등 이동질량 + 벨트 위 체류 화물질량(Q·L/v), Q: 반송율 kg/s, H: 양정

### 파라미터·계수 출처

| 기호 | 항목 | 값 | 출처 |
|------|------|-----|------|
| `μ` | 마찰계수 | 롤러 지지 벨트 0.02~0.04 (기본 0.03) | CEMA Belt Book 마찰계수 범위 |
| `η` | 구동효율 | 0.85 (기본) | 감속기·체인 전동 누적 |

**적용 한계** — CEMA 정식 산정(부속 저항·테이크업·트리퍼 등) 대비 개산식 — 정밀 설계는 제조사 프로그램/CEMA Belt Book 7th 로 검증.

**참고 문헌·표준**
- [CEMA Belt Book 7th Edition — Conveyor Equipment Manufacturers Association](https://www.cemanet.org/)
- [CKIT — Conveyor Idlers: Rating and Bearing Life (L10@500rpm 기준)](https://www.ckit.co.za/secure/tech-focus/idlers/idlers.htm)

## 리프 체인 안전율·신율 수명
**용도**: 리프터/마스트 체인 교체시점 예측 (신율 실측 추세 기반)

### 수식
- **안전율**: `SF = MBL / S_line,   S_line = (W_load+W_carr)·g·φ ÷ n_chain`
  - 법규(제163조): 화물 직접지지 체인 SF 5 이상
- **잔여수명**: `t_2% = (2.0 − e_now) / e_rate,   t_3% = (3.0 − e_now) / e_rate`
  - e_now: 현재 신율%, e_rate: 신율 진행률 %/년 (PM 실측 이력 회귀)

### 파라미터·계수 출처

| 기호 | 항목 | 값 | 출처 |
|------|------|-----|------|
| `신율 한계` | 교체 기준 | 2% 도달: 3개월 내 교체계획 / 3% 이상: 즉시 교체·사용금지 | FLTA Technical Bulletin / SAFed (영국·네덜란드는 2% 한계) |
| `강도손실` | 신율-강도 관계 | 신율 3% ≈ 파단강도 15% 손실 | FLTA |
| `측정법` | 신율 측정 | 하중 건 상태, 12피치 표점거리, 풀리 통과 구간 다점 측정 | 체인 제조사 공통 지침 |

**폐기/관리 기준** — 신율 3% 이상, 플레이트 균열, 핀 회전 흔적(윤활 부족), 부식.

**적용 한계** — 무윤활 시 신율 진행 3~5배 가속 — 진행률은 급유 상태 유지 전제. 선형 진행 가정.

**참고 문헌·표준**
- [FLTA Technical Bulletin — Inspection of Leaf Chains](https://www.cdforktrucksltd.co.uk/siteDocuments/flta-lift-chain-technical-bulletin.pdf)
- [SAFed — Leaf Chain Elongation Rejection Criteria](https://www.safed.co.uk/publications-home/tc2-machinery-lift-crane/policy-statements-for-download/41-fork-lift-truck-order-picker-leaf-chain-elongation-rejection-criteria/file)

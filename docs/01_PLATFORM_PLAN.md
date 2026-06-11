# FA 물류설비 Operation Platform — 기획 및 구축 파이프라인

## 1. 목적

FA 물류설비(STK, OHT, Conveyor, AGV, Lifter 등)의 **전 생애주기(Design Review → 제작 → 셋업 →
Install Parameter → 운영 PM/BM → 폐기)** 를 단일 플랫폼에서 관리하고, FDC·비전 측정·엔지니어링
계산을 연계하여 **예지보전 기반의 설비 운영 체계**를 구축한다. 한 법인에서 확보한
Lesson & Learn 을 전 법인으로 확산하는 운영 표준 플랫폼을 지향한다.

## 2. 핵심 기능 (요구사항 매핑)

| # | 요구 기능 | 플랫폼 모듈 |
|---|-----------|-------------|
| 1 | PM 점검항목 표준화 | **PM Standard**: 설비 모델별 표준 점검항목(점검방법·판정기준·주기) 마스터, PM 오더/실적 |
| 2 | PM/BM 상태 비전 측정 | **Vision Inspection**: 이미지 업로드 → 마모율/치수/부식/정렬 자동 측정, PM 결과 자동 판정 연계 |
| 3 | DR→제작→셋업→Install Param→PM/BM 이력 | **Lifecycle**: 설비별 단계 이력 타임라인, Install Parameter 버전 이력 |
| 4 | 스페어파츠 관리/선정 기초자료 | **Spare Parts**: 재고/입출고, 모델별 BOM, MTBF·리드타임 기반 권장재고 산출 |
| 5 | 엔지니어링 검토 | **Engineering**: 배터리 수명, 와이어로프 안전율 기반 수명, 베어링 L10, 휠 안전연수 계산기 |
| 6 | FDC 연계 | **FDC**: 센서 데이터 수집 API, 룰 기반 이상감지/분류(Fault Detection & Classification), 알람→BM 연계 |
| 7 | Lesson&Learn 다법인 확산 | **L&L**: 등록 → 법인별 전파(통보/검토/적용) 상태 매트릭스, 표준(PM 항목) 반영 추적 |

## 3. 시스템 구성

```
┌────────────────────────── Frontend (React + TypeScript + Vite) ──────────────────────────┐
│ Dashboard │ 설비/이력 │ PM표준/오더 │ BM │ Vision │ Parts │ Engineering │ FDC │ L&L      │
└───────────────────────────────────────┬───────────────────────────────────────────────────┘
                                        │ REST (JSON) /api/v1
┌───────────────────────────────────────┴───────────────────────────────────────────────────┐
│ Backend (FastAPI)                                                                          │
│  Routers: equipment·pm·bm·parts·engineering·fdc·vision·lessons·meta                        │
│  Services: engineering(수명계산) · vision(이미지 분석) · fdc(룰 엔진)                        │
│  ORM: SQLAlchemy ─ SQLite(개발) / PostgreSQL(운영 전환)                                     │
└───────────────────────────────────────┬───────────────────────────────────────────────────┘
                                        │
   설비 PLC/센서 게이트웨이 ──► POST /api/v1/fdc/ingest (배치 수집, 운영 시 MQTT/Kafka 대체)
```

## 4. 구축 파이프라인 (로드맵)

### Phase 0 — 기반 구축 (본 저장소, 완료)
- 모노레포 구성(backend / frontend / docs), 데이터 모델 설계, REST API v1
- 전 모듈 동작 가능한 풀 패키지 + 데모 시드 데이터

### Phase 1 — 사내 파일럿 (1~2개월)
- 1개 라인 대상 설비 마스터/PM 표준 실데이터 입력, PM 오더 운영 시작
- DB를 PostgreSQL 로 전환, 사내 SSO 연동(현 토큰 인증 대체)
- 비전 측정: 현장 카메라 이미지로 레시피(픽셀-mm 캘리브레이션, 판정 한계) 튜닝

### Phase 2 — FDC 실연계 + 예지보전 (2~4개월)
- 설비 게이트웨이(PLC/IoT) → MQTT/Kafka → FDC ingest 파이프라인 구축
- 룰 기반 감지를 통계/ML 모델(EWMA, Isolation Forest 등)로 고도화
- FDC 알람 → PM 오더 자동 생성(Condition Based Maintenance)

### Phase 3 — 다법인 확산 (4~6개월)
- 법인(Site)별 권한/데이터 분리, L&L 전파 워크플로우 의무화
- 표준 PM 항목 중앙 배포 → 법인별 적용률 KPI 대시보드
- 다국어(한/영/중) UI

### Phase 4 — 고도화 (6개월~)
- 비전: 딥러닝 기반 결함 분류(전이학습), 엣지 추론
- 엔지니어링 수명모델에 실측 데이터 피드백(잔존수명 RUL 보정)
- 스페어파츠 발주 자동화(ERP 연계)

## 5. KPI

- PM 준수율, MTBF/MTTR, BM 건수·다운타임, FDC 알람 → 사전조치 전환율,
  스페어파츠 결품률, L&L 법인 적용률

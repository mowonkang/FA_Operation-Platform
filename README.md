# FA Operation Platform

FA 물류설비(STK·OHT·Conveyor·AGV 등) **전 생애주기 운영 플랫폼** — Design Review부터 제작·셋업·
Install Parameter·PM·BM까지의 이력 관리, PM 점검항목 표준화, 비전 기반 상태 측정, 스페어파츠,
엔지니어링 수명 검토, FDC 연계, Lesson & Learn 다법인 확산을 하나의 패키지로 제공합니다.

## 주요 기능

| 모듈 | 내용 |
|------|------|
| **대시보드** | PM 준수율, BM 미결, FDC 알람, 재고부족, L&L 적용률 KPI |
| **설비 / 이력** | 설비 마스터, DR→제작→셋업→PM/BM 생애주기 타임라인, Install Parameter 버전 이력 |
| **PM** | 모델별 표준 점검항목(방법·판정기준·주기), 주기 기반 오더 자동생성, 측정값 자동판정 |
| **BM** | 고장 보고→원인/조치→파츠 재고 자동차감, FDC 알람·L&L 연계 |
| **비전 측정** | 이미지 업로드 → 마모율·부식률·치수·정렬 자동 측정, PM 한계값으로 자동 OK/NG 판정 |
| **스페어 파츠** | 재고/입출고, 모델별 BOM, MTBF·리드타임 기반 권장재고(선정 기초자료) |
| **엔지니어링 검토** | 와이어로프 안전율/수명, 베어링 L10, 배터리 SOH/수명, 휠 마모 안전연수 계산기 |
| **FDC** | 센서 데이터 수집 API, 룰 기반 이상감지/분류(레벨·스파이크·드리프트), 알람→BM 전환 |
| **Lesson & Learn** | 등록 시 전 법인 자동 전파, 법인별 적용 상태 매트릭스, PM 표준 반영 추적 |
| **워크플로우** | DR·셋업 안정화·알람 조치·BM·PM·제어 변경·시스템 이슈 7종 표준 절차, DR 데이터팩(운영 이력 → 차기 설계 환류) |
| **지식 DB** | 물류설비 엔지니어링 지식 17건(ISO/FEM/DIN/법규/논문 출처 포함), 카테고리·검색 |
| **와이어로프 PRO** | 가반하중·체결방식 기반 안전율(법규)·Feyrer 수명 예측, D/d·직경·줄수 민감도 인터랙티브 차트 |

문서: [기획/파이프라인](docs/01_PLATFORM_PLAN.md) · [데이터 모델](docs/02_DATA_MODEL.md) ·
[비전 측정 방법](docs/03_VISION_INSPECTION.md) · [지식 DB](docs/04_KNOWLEDGE_BASE.md) ·
[워크플로우](docs/05_WORKFLOWS.md)

## 실행 방법

### Backend (FastAPI, Python 3.11+)

```bash
cd backend
pip install -r requirements.txt
python -m app.seed                 # 데모 시드 데이터 (최초 1회)
uvicorn app.main:app --reload --port 8000
```

> **데모 데이터 초기화/갱신**: 코드 업데이트 후 샘플 데이터를 새로 받으려면 서버 중지 후
> 프로젝트 루트에서 `.\reset_demo.ps1` (Windows) 또는 `./reset_demo.sh` (macOS/Linux) 실행.
> 전 모듈(설비 11대, PM 17건, BM 8건, FDC 알람 7건, 이슈 8건, L&L 3건, 워크플로우 3건,
> 견적 2건, 지식 17건)이 채워진 상태로 시작합니다.

API 문서: http://localhost:8000/docs

### Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev                        # http://localhost:5180 (API는 8000 으로 프록시)
```

## 기술 스택

- **Backend**: FastAPI · SQLAlchemy 2 · SQLite(개발) / PostgreSQL(운영) · Pillow+numpy(비전)
- **Frontend**: React 18 · TypeScript · Vite · recharts

## FDC 데이터 수집 예시

```bash
curl -X POST http://localhost:8000/api/v1/fdc/ingest \
  -H 'Content-Type: application/json' \
  -d '{"readings":[{"sensor_id":1,"value":4.8}]}'
```

룰(상·하한 / 4σ 스파이크 / 드리프트) 위반 시 즉시 알람이 생성되고, UI에서 BM 보고로 전환할 수 있습니다.

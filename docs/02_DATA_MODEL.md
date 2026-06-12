# 데이터 모델

## 마스터
- **Site**: 법인/사이트 (code, name, country)
- **EquipmentModel**: 설비 모델 (STK/OHT/CNV/AGV/LIFTER 등 category, maker)
- **Equipment**: 설비 개체 (asset_code, model, site, line, status, install_date)
- **Part**: 스페어파츠 (part_no, maker, unit_price, lead_time_days, mtbf_hours, stock)
- **ModelPartBom**: 모델별 사용 파츠/수량/교체주기 — 파츠 선정 기초자료
- **User**: 사용자 (role: admin/engineer/operator, site)

## 생애주기
- **LifecycleEvent**: 단계 이력 (stage: DR / FABRICATION / SETUP / INSTALL_PARAM / PM / BM / MODIFY / SCRAP,
  title, detail, doc_ref, performed_by, event_date)
- **InstallParameter**: 설치 파라미터 이력 (name, value, unit, version, set_by, set_at) — 변경 시 새 버전 적재

## PM
- **PMStandardItem**: 모델별 표준 점검항목 (item_no, name, method: VISUAL/MEASURE/VISION/REPLACE/CLEAN,
  criteria, lower/upper limit, unit, period_days, vision_capable, vision_recipe)
- **PMOrder**: PM 오더 (equipment, plan_date, status: PLANNED/IN_PROGRESS/DONE/OVERDUE)
- **PMResult**: 항목별 실적 (measured_value, judgment: OK/NG/CHECK, vision_inspection 링크)

## BM
- **BMReport**: 고장 보고 (occurred_at, symptom, cause, action, downtime_min, failure_part,
  status: OPEN/ANALYZING/FIXED/CLOSED, fdc_alarm 링크, lesson 링크)

## Vision
- **VisionInspection**: 측정 이력 (kind: WEAR/DIMENSION/CORROSION/ALIGNMENT, image_path,
  measured_value, unit, judgment, detail JSON)

## FDC
- **FDCSensor**: 센서 정의 (equipment, name, unit, warn/alarm 상·하한)
- **FDCReading**: 시계열 측정값
- **FDCAlarm**: 이상 감지 (level: WARN/ALARM, classification: LEVEL_HIGH/LEVEL_LOW/SPIKE/DRIFT,
  status: OPEN/ACK/CLOSED)

## Lesson & Learn
- **Lesson**: 사례 (category, problem, root_cause, countermeasure, origin_site, std_reflected 여부)
- **LessonDeployment**: 법인별 전파 상태 (NOTIFIED → REVIEWING → APPLIED / NA)

## 스페어파츠 권장재고 산식
```
연간 예상 소요량 = Σ(해당 파츠 사용 설비 대수 × BOM 수량 × 연간가동시간 / MTBF)
권장재고 = 소요율 × 리드타임 + 안전재고(서비스레벨 z × √(리드타임 소요 분산))
```

## 엔지니어링 수명 모델 (services/engineering.py)
- **와이어로프**: 안전율 = 파단하중×가닥수 / 사용하중. D/d(시브비)·안전율 기반 굽힘피로 수명 사이클
  → 일일 사이클로 잔여 연수 환산. 안전율 < 법규 기준(권상용 5.0) 시 부적합 판정.
- **베어링**: L10h = 10⁶/(60·N) × (C/P)^p (볼 p=3, 롤러 p=10/3), 잔여 연수 = (L10h − 누적가동) / 연간가동
- **배터리**: 사이클 수명(DOD 보정) vs 캘린더 수명 중 짧은 쪽, SOH 추정
- **휠**: (현재경 − 마모한계경) / 마모율 → 잔여 주행거리/연수

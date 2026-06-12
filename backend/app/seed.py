"""데모 시드 데이터.  실행: python -m app.seed"""
from datetime import date, datetime, timedelta

from .database import Base, SessionLocal, engine
from . import models as m


def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    if db.query(m.Site).first():
        print("이미 시드됨 — 건너뜀")
        return

    # 법인
    kr = m.Site(code="KR1", name="한국 본사 공장", country="KR")
    cn = m.Site(code="CN1", name="중국 법인", country="CN")
    vn = m.Site(code="VN1", name="베트남 법인", country="VN")
    us = m.Site(code="US1", name="미국 법인", country="US")
    db.add_all([kr, cn, vn, us])
    db.flush()

    # 설비 모델
    stk = m.EquipmentModel(code="STK-2000", name="스태커크레인 2000", category="STK",
                           maker="FA중공업", description="자동창고용 스태커크레인, 권상 2t")
    oht = m.EquipmentModel(code="OHT-V5", name="천장반송차 V5", category="OHT",
                           maker="FA로보틱스", description="OHT, 리튬이온 배터리 구동")
    cnv = m.EquipmentModel(code="CNV-B12", name="벨트컨베이어 B12", category="CNV",
                           maker="FA시스템", description="공정간 반송 컨베이어")
    db.add_all([stk, oht, cnv])
    db.flush()

    # 설비
    eqs = []
    for i in range(1, 4):
        eqs.append(m.Equipment(asset_code=f"STK-2000-{i:03d}", model_id=stk.id, site_id=kr.id,
                               line=f"A{i}", status="RUN", install_date=date(2023, 3, 10),
                               annual_run_hours=7000))
    eqs.append(m.Equipment(asset_code="OHT-V5-001", model_id=oht.id, site_id=kr.id,
                           line="FAB1", status="RUN", install_date=date(2024, 1, 20),
                           annual_run_hours=8000))
    eqs.append(m.Equipment(asset_code="OHT-V5-101", model_id=oht.id, site_id=cn.id,
                           line="FAB2", status="RUN", install_date=date(2024, 6, 5),
                           annual_run_hours=8000))
    eqs.append(m.Equipment(asset_code="CNV-B12-001", model_id=cnv.id, site_id=vn.id,
                           line="PKG1", status="SETUP", install_date=None, annual_run_hours=6000))
    db.add_all(eqs)
    db.flush()
    e1 = eqs[0]

    # 생애주기 이력 (STK-2000-001)
    db.add_all([
        m.LifecycleEvent(equipment_id=e1.id, stage="DR", title="Design Review 1차 — 권상부 안전율 검토",
                         detail="와이어로프 6×Fi(29) Φ12, 안전율 6.2 확인", doc_ref="DR-2022-104",
                         performed_by="김설계", event_date=date(2022, 9, 15)),
        m.LifecycleEvent(equipment_id=e1.id, stage="FABRICATION", title="제작 완료 / 공장 출하 검사",
                         doc_ref="FAT-2022-211", performed_by="박제작", event_date=date(2023, 1, 20)),
        m.LifecycleEvent(equipment_id=e1.id, stage="SETUP", title="현장 설치 및 시운전 완료",
                         detail="주행 레일 정렬 0.3mm/10m", performed_by="이설치", event_date=date(2023, 3, 10)),
    ])

    # Install Parameter
    db.add_all([
        m.InstallParameter(equipment_id=e1.id, name="주행 최고속도", value="180", unit="m/min",
                           set_by="이설치", version=1),
        m.InstallParameter(equipment_id=e1.id, name="권상 속도", value="30", unit="m/min",
                           set_by="이설치", version=1),
        m.InstallParameter(equipment_id=e1.id, name="포크 가감속", value="0.5", unit="m/s²",
                           set_by="이설치", version=1),
    ])

    # PM 표준 점검항목 (STK)
    stds = [
        m.PMStandardItem(model_id=stk.id, item_no="PM-01", name="와이어로프 직경 측정",
                         part_area="권상부", method="VISION", criteria="공칭 12mm, 11.2mm 미만 교체",
                         lower_limit=11.2, upper_limit=12.5, unit="mm", period_days=30,
                         vision_capable=True,
                         vision_recipe={"kind": "DIMENSION", "ref_length_mm": 50, "ref_length_px": 400}),
        m.PMStandardItem(model_id=stk.id, item_no="PM-02", name="주행휠 답면 마모율",
                         part_area="주행부", method="VISION", criteria="마모영역 20% 이하",
                         lower_limit=0, upper_limit=20, unit="%", period_days=90,
                         vision_capable=True, vision_recipe={"kind": "WEAR", "mode": "dark"}),
        m.PMStandardItem(model_id=stk.id, item_no="PM-03", name="레일 부식 점검",
                         part_area="주행레일", method="VISION", criteria="부식률 5% 이하",
                         lower_limit=0, upper_limit=5, unit="%", period_days=180,
                         vision_capable=True, vision_recipe={"kind": "CORROSION"}),
        m.PMStandardItem(model_id=stk.id, item_no="PM-04", name="권상 모터 절연저항",
                         part_area="권상부", method="MEASURE", criteria="1MΩ 이상",
                         lower_limit=1.0, upper_limit=None, unit="MΩ", period_days=180),
        m.PMStandardItem(model_id=stk.id, item_no="PM-05", name="브레이크 라이닝 두께",
                         part_area="권상부", method="MEASURE", criteria="3mm 이상",
                         lower_limit=3.0, upper_limit=None, unit="mm", period_days=90),
        m.PMStandardItem(model_id=oht.id, item_no="PM-01", name="배터리 SOH 점검",
                         part_area="구동부", method="MEASURE", criteria="SOH 80% 이상",
                         lower_limit=80, upper_limit=None, unit="%", period_days=90),
        m.PMStandardItem(model_id=oht.id, item_no="PM-02", name="주행휠 직경 측정",
                         part_area="주행부", method="VISION", criteria="한계경 76mm",
                         lower_limit=76, upper_limit=82, unit="mm", period_days=90,
                         vision_capable=True,
                         vision_recipe={"kind": "DIMENSION", "ref_length_mm": 50, "ref_length_px": 380}),
        m.PMStandardItem(model_id=cnv.id, item_no="PM-01", name="벨트 마모/크랙 점검",
                         part_area="벨트", method="VISION", criteria="마모영역 15% 이하",
                         lower_limit=0, upper_limit=15, unit="%", period_days=60,
                         vision_capable=True, vision_recipe={"kind": "WEAR", "mode": "dark"}),
    ]
    db.add_all(stds)
    db.flush()

    # PM 오더
    done = m.PMOrder(equipment_id=e1.id, plan_date=date.today() - timedelta(days=30),
                     status="DONE", performed_date=date.today() - timedelta(days=29),
                     performer="최정비")
    db.add(done)
    db.flush()
    db.add_all([
        m.PMResult(order_id=done.id, standard_item_id=stds[0].id, measured_value=11.8,
                   judgment="OK", method_used="VISION"),
        m.PMResult(order_id=done.id, standard_item_id=stds[3].id, measured_value=12.0,
                   judgment="OK", method_used="MEASURE"),
        m.PMResult(order_id=done.id, standard_item_id=stds[4].id, measured_value=3.4,
                   judgment="CHECK", method_used="MEASURE", note="차기 PM 시 교체 검토"),
    ])
    db.add(m.LifecycleEvent(equipment_id=e1.id, stage="PM", title="PM 수행 완료 (오더 #1)",
                            performed_by="최정비", event_date=done.performed_date))
    db.add(m.PMOrder(equipment_id=e1.id, plan_date=date.today() + timedelta(days=2)))
    db.add(m.PMOrder(equipment_id=eqs[1].id, plan_date=date.today() - timedelta(days=3)))  # OVERDUE 대상
    db.add(m.PMOrder(equipment_id=eqs[3].id, plan_date=date.today() + timedelta(days=7)))

    # 파츠
    rope = m.Part(part_no="WR-12-6F29", name="와이어로프 Φ12 6×Fi(29)", category="권상",
                  maker="대한로프", unit_price=450000, lead_time_days=21, mtbf_hours=17000,
                  current_stock=2, min_stock=2)
    brg = m.Part(part_no="BRG-6310ZZ", name="베어링 6310ZZ", category="구동",
                 maker="NSK", unit_price=38000, lead_time_days=14, mtbf_hours=40000,
                 current_stock=8, min_stock=4)
    wheel = m.Part(part_no="WHL-OHT-80", name="OHT 주행휠 Φ80 우레탄", category="주행",
                   maker="FA로보틱스", unit_price=120000, lead_time_days=30, mtbf_hours=20000,
                   current_stock=1, min_stock=4)
    batt = m.Part(part_no="BAT-LI-48V", name="리튬이온 배터리팩 48V 40Ah", category="전장",
                  maker="셀파워", unit_price=1800000, lead_time_days=45, mtbf_hours=24000,
                  current_stock=1, min_stock=1)
    belt = m.Part(part_no="BLT-B12-10M", name="컨베이어 벨트 B12 10m", category="반송",
                  maker="FA시스템", unit_price=300000, lead_time_days=25, mtbf_hours=26000,
                  current_stock=0, min_stock=1)
    pad = m.Part(part_no="BRK-PAD-ST2", name="브레이크 라이닝 ST2", category="권상",
                 maker="FA중공업", unit_price=85000, lead_time_days=10, mtbf_hours=12000,
                 current_stock=6, min_stock=3)
    db.add_all([rope, brg, wheel, batt, belt, pad])
    db.flush()

    db.add_all([
        m.ModelPartBom(model_id=stk.id, part_id=rope.id, qty_per_unit=2, replace_cycle_months=24, critical=True),
        m.ModelPartBom(model_id=stk.id, part_id=brg.id, qty_per_unit=8, replace_cycle_months=48),
        m.ModelPartBom(model_id=stk.id, part_id=pad.id, qty_per_unit=2, replace_cycle_months=12, critical=True),
        m.ModelPartBom(model_id=oht.id, part_id=wheel.id, qty_per_unit=4, replace_cycle_months=18, critical=True),
        m.ModelPartBom(model_id=oht.id, part_id=batt.id, qty_per_unit=1, replace_cycle_months=36, critical=True),
        m.ModelPartBom(model_id=cnv.id, part_id=belt.id, qty_per_unit=1, replace_cycle_months=24),
        m.ModelPartBom(model_id=cnv.id, part_id=brg.id, qty_per_unit=12, replace_cycle_months=36),
    ])

    # FDC 센서
    s_vib = m.FDCSensor(equipment_id=e1.id, name="권상모터 진동", unit="mm/s",
                        warn_high=4.5, alarm_high=7.1)
    s_cur = m.FDCSensor(equipment_id=e1.id, name="주행모터 전류", unit="A",
                        warn_high=28, alarm_high=35)
    s_tmp = m.FDCSensor(equipment_id=eqs[3].id, name="배터리 온도", unit="°C",
                        warn_high=45, alarm_high=55)
    db.add_all([s_vib, s_cur, s_tmp])
    db.flush()

    now = datetime.utcnow()
    import math, random
    random.seed(42)
    for i in range(144):  # 24h, 10분 간격
        ts = now - timedelta(minutes=10 * (144 - i))
        v = 2.8 + random.gauss(0, 0.25) + (0.04 * (i - 120) if i > 120 else 0)
        db.add(m.FDCReading(sensor_id=s_vib.id, value=round(v, 2), ts=ts))
        db.add(m.FDCReading(sensor_id=s_cur.id,
                            value=round(22 + 3 * math.sin(i / 8) + random.gauss(0, 0.8), 2), ts=ts))
    db.add(m.FDCAlarm(sensor_id=s_vib.id, level="WARN", classification="DRIFT", value=4.1,
                      message="권상모터 진동 DRIFT (4.1mm/s)", ts=now - timedelta(hours=1)))

    # BM
    bm1 = m.BMReport(equipment_id=eqs[1].id, occurred_at=now - timedelta(days=5),
                     symptom="권상 동작 중 이상 소음 및 정지", cause="권상부 베어링 마모",
                     action="베어링 6310ZZ 교체", downtime_min=240, failure_part_id=brg.id,
                     status="CLOSED", reported_by="최정비")
    bm2 = m.BMReport(equipment_id=eqs[4].id, occurred_at=now - timedelta(days=1),
                     symptom="OHT 주행 중 배터리 저전압 경고 반복", status="ANALYZING",
                     reported_by="왕정비")
    db.add_all([bm1, bm2])
    db.flush()
    db.add(m.LifecycleEvent(equipment_id=eqs[1].id, stage="BM",
                            title="고장: 권상부 이상소음 — 베어링 교체", performed_by="최정비",
                            event_date=(now - timedelta(days=5)).date()))

    # Lesson & Learn
    lesson = m.Lesson(
        title="STK 권상부 베어링 조기 마모 — 그리스 주입주기 단축 필요",
        category="DOWNTIME", model_id=stk.id,
        problem="권상부 베어링이 L10 예상수명 대비 40% 시점에서 마모 고장 발생, 4시간 다운타임.",
        root_cause="고온 환경에서 그리스 열화 가속. 표준 주입주기(6개월)가 환경조건 미반영.",
        countermeasure="그리스 주입주기 6개월→3개월 단축, PM 항목에 진동 측정 추가, FDC 진동 임계 강화.",
        origin_site_id=kr.id, created_by="최정비",
    )
    db.add(lesson)
    db.flush()
    db.add_all([
        m.LessonDeployment(lesson_id=lesson.id, site_id=cn.id, status="APPLIED",
                           applied_date=date.today() - timedelta(days=10), note="PM 표준 v2 반영 완료"),
        m.LessonDeployment(lesson_id=lesson.id, site_id=vn.id, status="REVIEWING"),
        m.LessonDeployment(lesson_id=lesson.id, site_id=us.id, status="NOTIFIED"),
    ])
    bm1.lesson_id = lesson.id

    db.add_all([
        m.User(username="admin", name="관리자", role="admin", site_id=kr.id),
        m.User(username="engineer1", name="김엔지니어", role="engineer", site_id=kr.id),
    ])

    # 데모 워크플로우 (BM_FLOW — 진행중)
    from .workflow_templates import TEMPLATES
    wf = m.Workflow(wf_type="BM_FLOW", title="STK-2000-002 권상부 베어링 고장 처리",
                    equipment_id=eqs[1].id, model_id=stk.id, created_by="최정비")
    db.add(wf)
    db.flush()
    for i, s in enumerate(TEMPLATES["BM_FLOW"]["steps"], start=1):
        db.add(m.WorkflowStep(workflow_id=wf.id, seq=i, name=s["name"], guide=s["guide"],
                              link=s.get("link"),
                              status="DONE" if i <= 4 else "PENDING",
                              owner="최정비" if i <= 4 else ""))

    db.commit()
    print("시드 완료")

    # 지식 DB 시드
    from . import knowledge_seed
    knowledge_seed.run()


if __name__ == "__main__":
    run()

"""데모 시드 데이터 — 모든 화면·차트가 채워지도록 풍부하게 구성.

실행: python -m app.seed          (이미 시드된 DB 는 건너뜀)
초기화: 프로젝트 루트의 reset_demo.ps1 / reset_demo.sh 사용 (DB 삭제 후 재시드)
"""
import math
import random
from datetime import date, datetime, timedelta

from .database import Base, SessionLocal, engine
from . import models as m

random.seed(42)
NOW = datetime.utcnow()
TODAY = date.today()


def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    if db.query(m.Site).first():
        print("이미 시드됨 — 건너뜀 (초기화: reset_demo 스크립트 사용)")
        return

    # ── 법인 ──
    kr = m.Site(code="KR1", name="한국 본사 공장", country="KR")
    cn = m.Site(code="CN1", name="중국 법인", country="CN")
    vn = m.Site(code="VN1", name="베트남 법인", country="VN")
    us = m.Site(code="US1", name="미국 법인", country="US")
    db.add_all([kr, cn, vn, us])
    db.flush()

    # ── 설비 모델 ──
    stk = m.EquipmentModel(code="STK-2000", name="스태커크레인 2000", category="STK",
                           maker="FA중공업", description="자동창고용 스태커크레인, 권상 2t")
    oht = m.EquipmentModel(code="OHT-V5", name="천장반송차 V5", category="OHT",
                           maker="FA로보틱스", description="OHT, 리튬이온 배터리 구동")
    cnv = m.EquipmentModel(code="CNV-B12", name="벨트컨베이어 B12", category="CNV",
                           maker="FA시스템", description="공정간 반송 컨베이어")
    agv = m.EquipmentModel(code="AGV-X1", name="무인운반차 X1", category="AGV",
                           maker="FA로보틱스", description="LiFePO4 구동, 안전 LiDAR (ISO 3691-4)")
    lft = m.EquipmentModel(code="LFT-300", name="수직반송 리프터 300", category="LIFTER",
                           maker="FA중공업", description="리프 체인식 수직반송기, 300kg")
    db.add_all([stk, oht, cnv, agv, lft])
    db.flush()

    # ── 설비 11대 ──
    def eq(code, model, site, line, status="RUN", inst=None, hrs=7000.0):
        return m.Equipment(asset_code=code, model_id=model.id, site_id=site.id, line=line,
                           status=status, install_date=inst or date(2023, 3, 10),
                           annual_run_hours=hrs)
    eqs = [
        eq("STK-2000-001", stk, kr, "A1"),
        eq("STK-2000-002", stk, kr, "A2"),
        eq("STK-2000-003", stk, kr, "A3"),
        eq("OHT-V5-001", oht, kr, "FAB1", inst=date(2024, 1, 20), hrs=8000),
        eq("OHT-V5-101", oht, cn, "FAB2", inst=date(2024, 6, 5), hrs=8000),
        eq("CNV-B12-001", cnv, vn, "PKG1", status="SETUP", inst=None, hrs=6000),
        eq("CNV-B12-002", cnv, kr, "PKG2", inst=date(2022, 11, 1), hrs=6000),
        eq("AGV-X1-001", agv, kr, "AS1", inst=date(2024, 9, 1), hrs=7500),
        eq("AGV-X1-002", agv, kr, "AS1", status="BM", inst=date(2024, 9, 1), hrs=7500),
        eq("LFT-300-001", lft, kr, "B1", inst=date(2023, 8, 15), hrs=6500),
        eq("STK-2000-101", stk, cn, "C1", inst=date(2024, 3, 2)),
    ]
    db.add_all(eqs)
    db.flush()
    e1, e2 = eqs[0], eqs[1]

    # ── 생애주기 이력 (STK-2000-001 풀 스토리) ──
    db.add_all([
        m.LifecycleEvent(equipment_id=e1.id, stage="DR", title="Design Review 1차 — 권상부 안전율 검토",
                         detail="와이어로프 6×Fi(29) Φ12 2본, 안전율 6.2 확인 (기준 5.0)", doc_ref="DR-2022-104",
                         performed_by="김설계", event_date=date(2022, 9, 15)),
        m.LifecycleEvent(equipment_id=e1.id, stage="DR", title="DR 2차 — L&L 반영 확인 (그리스 주입주기)",
                         doc_ref="DR-2022-131", performed_by="김설계", event_date=date(2022, 10, 20)),
        m.LifecycleEvent(equipment_id=e1.id, stage="FABRICATION", title="FAT 완료 / 출하 승인",
                         detail="정격부하 사이클타임 58s (사양 60s 이내)", doc_ref="FAT-2022-211",
                         performed_by="박제작", event_date=date(2023, 1, 20)),
        m.LifecycleEvent(equipment_id=e1.id, stage="SETUP", title="현장 설치·시운전 완료",
                         detail="주행레일 직진도 0.3mm/10m, 2주 안정화 무고장 통과", performed_by="이설치",
                         event_date=date(2023, 3, 10)),
    ])

    # ── Install Parameter (버전 이력 포함) ──
    db.add_all([
        m.InstallParameter(equipment_id=e1.id, name="주행 최고속도", value="180", unit="m/min",
                           set_by="이설치", version=1, is_current=False,
                           set_at=NOW - timedelta(days=400)),
        m.InstallParameter(equipment_id=e1.id, name="주행 최고속도", value="170", unit="m/min",
                           set_by="박제어", version=2, note="커브 구간 진동 저감 (제어변경 WF#3)",
                           set_at=NOW - timedelta(days=120)),
        m.InstallParameter(equipment_id=e1.id, name="권상 속도", value="30", unit="m/min",
                           set_by="이설치", version=1),
        m.InstallParameter(equipment_id=e1.id, name="포크 가감속", value="0.5", unit="m/s²",
                           set_by="이설치", version=1),
        m.InstallParameter(equipment_id=eqs[7].id, name="주행 속도", value="90", unit="m/min",
                           set_by="이설치", version=1),
        m.InstallParameter(equipment_id=eqs[7].id, name="LiDAR 보호필드", value="Field-B(저속전환 1.2m)",
                           set_by="안전팀", version=1),
    ])
    db.add(m.LifecycleEvent(equipment_id=e1.id, stage="INSTALL_PARAM",
                            title="파라미터 변경: 주행 최고속도 180→170 m/min (v2)",
                            performed_by="박제어", event_date=(NOW - timedelta(days=120)).date()))

    # ── PM 표준 점검항목 ──
    stds = [
        m.PMStandardItem(model_id=stk.id, item_no="PM-01", name="와이어로프 직경 측정",
                         part_area="권상부", method="VISION", criteria="공칭 12mm, 11.2mm 미만 교체 (직경 7% 법규)",
                         lower_limit=11.2, upper_limit=12.5, unit="mm", period_days=30, vision_capable=True,
                         vision_recipe={"kind": "DIMENSION", "ref_length_mm": 50, "ref_length_px": 400}),
        m.PMStandardItem(model_id=stk.id, item_no="PM-02", name="주행휠 답면 마모율",
                         part_area="주행부", method="VISION", criteria="마모영역 20% 이하",
                         lower_limit=0, upper_limit=20, unit="%", period_days=90, vision_capable=True,
                         vision_recipe={"kind": "WEAR", "mode": "dark"}),
        m.PMStandardItem(model_id=stk.id, item_no="PM-03", name="레일 부식 점검",
                         part_area="주행레일", method="VISION", criteria="부식률 5% 이하",
                         lower_limit=0, upper_limit=5, unit="%", period_days=180, vision_capable=True,
                         vision_recipe={"kind": "CORROSION"}),
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
                         lower_limit=76, upper_limit=82, unit="mm", period_days=90, vision_capable=True,
                         vision_recipe={"kind": "DIMENSION", "ref_length_mm": 50, "ref_length_px": 380}),
        m.PMStandardItem(model_id=cnv.id, item_no="PM-01", name="벨트 마모/크랙 점검",
                         part_area="벨트", method="VISION", criteria="마모영역 15% 이하",
                         lower_limit=0, upper_limit=15, unit="%", period_days=60, vision_capable=True,
                         vision_recipe={"kind": "WEAR", "mode": "dark"}),
        m.PMStandardItem(model_id=agv.id, item_no="PM-01", name="배터리 SOH",
                         part_area="전장", method="MEASURE", criteria="SOH 80% 이상",
                         lower_limit=80, upper_limit=None, unit="%", period_days=60),
        m.PMStandardItem(model_id=agv.id, item_no="PM-02", name="안전 LiDAR 보호필드 작동시험",
                         part_area="안전", method="VISUAL", criteria="ISO 3691-4 — 필드 침입 시 정지", period_days=30),
        m.PMStandardItem(model_id=lft.id, item_no="PM-01", name="리프 체인 신율 측정",
                         part_area="승강부", method="MEASURE", criteria="2% 교체계획 / 3% 즉시교체 (FLTA)",
                         lower_limit=0, upper_limit=2.0, unit="%", period_days=90),
    ]
    db.add_all(stds)
    db.flush()

    # ── PM 오더: 과거 12주 완료 이력 + 현재 계획/지연 ──
    performers = ["최정비", "왕정비", "이정비"]
    for w in range(12, 0, -1):
        eq_i = eqs[w % 5]
        pd_ = TODAY - timedelta(days=7 * w)
        o = m.PMOrder(equipment_id=eq_i.id, plan_date=pd_, status="DONE",
                      performed_date=pd_ + timedelta(days=1), performer=performers[w % 3])
        db.add(o)
        db.flush()
        model_stds = [s for s in stds if s.model_id == eq_i.model_id][:3]
        for s in model_stds:
            base_v = (s.lower_limit or 0) + ((s.upper_limit or (s.lower_limit or 1) * 4) - (s.lower_limit or 0)) * 0.5
            db.add(m.PMResult(order_id=o.id, standard_item_id=s.id,
                              measured_value=round(base_v * random.uniform(0.9, 1.1), 2),
                              judgment=random.choices(["OK", "CHECK", "NG"], [0.8, 0.15, 0.05])[0],
                              method_used=s.method))
        db.add(m.LifecycleEvent(equipment_id=eq_i.id, stage="PM",
                                title=f"PM 수행 완료 (오더 #{o.id})", performed_by=o.performer,
                                event_date=o.performed_date))
    db.add_all([
        m.PMOrder(equipment_id=e1.id, plan_date=TODAY + timedelta(days=2)),
        m.PMOrder(equipment_id=eqs[3].id, plan_date=TODAY - timedelta(days=3)),   # 지연
        m.PMOrder(equipment_id=eqs[7].id, plan_date=TODAY - timedelta(days=6)),   # 지연
        m.PMOrder(equipment_id=eqs[9].id, plan_date=TODAY + timedelta(days=7)),
        m.PMOrder(equipment_id=eqs[6].id, plan_date=TODAY + timedelta(days=10)),
    ])

    # ── 파츠 ──
    rope = m.Part(part_no="WR-12-6F29", name="와이어로프 Φ12 6×Fi(29)", category="권상",
                  maker="대한로프", unit_price=450000, lead_time_days=21, mtbf_hours=17000,
                  current_stock=2, min_stock=2)
    brg = m.Part(part_no="BRG-6310ZZ", name="베어링 6310ZZ", category="구동",
                 maker="NSK", unit_price=38000, lead_time_days=14, mtbf_hours=40000,
                 current_stock=8, min_stock=4)
    whl = m.Part(part_no="WHL-OHT-80", name="OHT 주행휠 Φ80 우레탄", category="주행",
                 maker="FA로보틱스", unit_price=120000, lead_time_days=30, mtbf_hours=20000,
                 current_stock=1, min_stock=4)
    bat = m.Part(part_no="BAT-LI-48V", name="LiFePO4 배터리팩 48V 40Ah", category="전장",
                 maker="셀파워", unit_price=1800000, lead_time_days=45, mtbf_hours=24000,
                 current_stock=1, min_stock=1)
    blt = m.Part(part_no="BLT-B12-10M", name="컨베이어 벨트 B12 10m", category="반송",
                 maker="FA시스템", unit_price=300000, lead_time_days=25, mtbf_hours=26000,
                 current_stock=0, min_stock=1)
    pad = m.Part(part_no="BRK-PAD-ST2", name="브레이크 라이닝 ST2", category="권상",
                 maker="FA중공업", unit_price=85000, lead_time_days=10, mtbf_hours=12000,
                 current_stock=6, min_stock=3)
    chn = m.Part(part_no="CHN-BL534", name="리프 체인 BL534", category="승강",
                 maker="대동체인", unit_price=260000, lead_time_days=28, mtbf_hours=22000,
                 current_stock=2, min_stock=2)
    ldr = m.Part(part_no="LDR-S3000", name="안전 LiDAR S3000", category="안전",
                 maker="SICK", unit_price=2400000, lead_time_days=60, mtbf_hours=50000,
                 current_stock=1, min_stock=1)
    parts = [rope, brg, whl, bat, blt, pad, chn, ldr]
    db.add_all(parts)
    db.flush()

    db.add_all([
        m.ModelPartBom(model_id=stk.id, part_id=rope.id, qty_per_unit=2, replace_cycle_months=24, critical=True),
        m.ModelPartBom(model_id=stk.id, part_id=brg.id, qty_per_unit=8, replace_cycle_months=48),
        m.ModelPartBom(model_id=stk.id, part_id=pad.id, qty_per_unit=2, replace_cycle_months=12, critical=True),
        m.ModelPartBom(model_id=oht.id, part_id=whl.id, qty_per_unit=4, replace_cycle_months=18, critical=True),
        m.ModelPartBom(model_id=oht.id, part_id=bat.id, qty_per_unit=1, replace_cycle_months=36, critical=True),
        m.ModelPartBom(model_id=cnv.id, part_id=blt.id, qty_per_unit=1, replace_cycle_months=24),
        m.ModelPartBom(model_id=cnv.id, part_id=brg.id, qty_per_unit=12, replace_cycle_months=36),
        m.ModelPartBom(model_id=agv.id, part_id=bat.id, qty_per_unit=1, replace_cycle_months=30, critical=True),
        m.ModelPartBom(model_id=agv.id, part_id=ldr.id, qty_per_unit=2, replace_cycle_months=None, critical=True),
        m.ModelPartBom(model_id=lft.id, part_id=chn.id, qty_per_unit=2, replace_cycle_months=24, critical=True),
        m.ModelPartBom(model_id=lft.id, part_id=brg.id, qty_per_unit=4, replace_cycle_months=36),
    ])
    db.add_all([
        m.PartTransaction(part_id=brg.id, tx_type="IN", qty=10, ref_type="PURCHASE",
                          tx_date=NOW - timedelta(days=60)),
        m.PartTransaction(part_id=pad.id, tx_type="OUT", qty=2, ref_type="PM",
                          tx_date=NOW - timedelta(days=30)),
    ])

    # ── BM: 최근 8주 분산 발생 (주간 트렌드 차트용) ──
    bm_cases = [
        (e2, 35, "권상 동작 중 이상 소음·정지", "권상부 베어링 마모 (그리스 열화)", "베어링 6310ZZ 교체", 240, brg, "CLOSED"),
        (eqs[3], 30, "주행 중 위치인식 오차 반복", "가이드휠 편마모 → 차체 진동", "가이드휠 교체·레일 이음부 보정", 120, whl, "CLOSED"),
        (eqs[6], 24, "벨트 사행 발생", "텐션 롤러 베어링 고착", "롤러 교체·트래킹 조정", 90, brg, "CLOSED"),
        (e1, 19, "포크 진입 위치 어긋남", "위치 센서 오염", "센서 청소·게인 재조정", 45, None, "CLOSED"),
        (eqs[9], 15, "승강 시 체인 소음", "체인 윤활 부족 (신율 1.4%)", "급유·신율 측정 주기 단축", 60, None, "CLOSED"),
        (eqs[4], 11, "OHT 충전 불량", "충전 단자 마모", "단자 교체", 75, None, "CLOSED"),
        (e2, 8, "주행 모터 과전류 알람", "주행휠 답면 박리", "휠 교체 예정 — 부품 입고 대기", 180, whl, "ANALYZING"),
        (eqs[8], 2, "AGV 주행 중 비상정지 반복", "LiDAR 보호필드 오감지 (분진)", "", 30, None, "OPEN"),
    ]
    bm1 = None
    for eq_i, days_ago, sym, cause, act, dt_, part, st in bm_cases:
        r = m.BMReport(equipment_id=eq_i.id, occurred_at=NOW - timedelta(days=days_ago),
                       symptom=sym, cause=cause, action=act, downtime_min=dt_,
                       failure_part_id=part.id if part else None, status=st, reported_by="최정비")
        db.add(r)
        db.flush()
        if bm1 is None:
            bm1 = r
        db.add(m.LifecycleEvent(equipment_id=eq_i.id, stage="BM",
                                title=f"고장: {sym}", performed_by="최정비",
                                event_date=(NOW - timedelta(days=days_ago)).date()))

    # ── FDC 센서 + 24h 데이터 + 분류별 알람 ──
    s_vib = m.FDCSensor(equipment_id=e1.id, name="권상모터 진동", unit="mm/s", warn_high=4.5, alarm_high=7.1)
    s_cur = m.FDCSensor(equipment_id=e1.id, name="주행모터 전류", unit="A", warn_high=28, alarm_high=35)
    s_tmp = m.FDCSensor(equipment_id=eqs[7].id, name="배터리 온도", unit="°C", warn_high=45, alarm_high=55)
    s_spd = m.FDCSensor(equipment_id=eqs[3].id, name="OHT 차체 진동", unit="m/s²", warn_high=1.2, alarm_high=2.0)
    db.add_all([s_vib, s_cur, s_tmp, s_spd])
    db.flush()
    for i in range(144):  # 24h × 10분
        ts = NOW - timedelta(minutes=10 * (144 - i))
        v = 2.8 + random.gauss(0, 0.25) + (0.05 * (i - 115) if i > 115 else 0)  # 말미 드리프트
        db.add(m.FDCReading(sensor_id=s_vib.id, value=round(v, 2), ts=ts))
        db.add(m.FDCReading(sensor_id=s_cur.id,
                            value=round(22 + 3 * math.sin(i / 8) + random.gauss(0, 0.8), 2), ts=ts))
        db.add(m.FDCReading(sensor_id=s_tmp.id, value=round(38 + random.gauss(0, 1.5), 1), ts=ts))
    alarms = [
        (s_vib, "WARN", "DRIFT", 4.1, 1, "OPEN"),
        (s_vib, "WARN", "LEVEL_HIGH", 4.7, 26, "CLOSED"),
        (s_cur, "WARN", "SPIKE", 33.8, 3, "ACK"),
        (s_tmp, "WARN", "LEVEL_HIGH", 46.2, 5, "CLOSED"),
        (s_tmp, "ALARM", "LEVEL_HIGH", 55.4, 12, "CLOSED"),
        (s_spd, "WARN", "SPIKE", 1.9, 2, "OPEN"),
        (s_spd, "WARN", "DRIFT", 1.1, 9, "CLOSED"),
    ]
    for sen, lv, cls, val, hrs, st in alarms:
        db.add(m.FDCAlarm(sensor_id=sen.id, level=lv, classification=cls, value=val,
                          message=f"{sen.name} {cls} ({val}{sen.unit})",
                          ts=NOW - timedelta(hours=hrs), status=st))

    # ── 비전 측정 이력 ──
    db.add_all([
        m.VisionInspection(equipment_id=e1.id, kind="DIMENSION", measured_value=11.78, unit="mm",
                           judgment="OK", detail={"width_px": 377, "mm_per_px": 0.125, "rows_used": 380},
                           created_at=NOW - timedelta(days=29)),
        m.VisionInspection(equipment_id=e2.id, kind="WEAR", measured_value=17.4, unit="%",
                           judgment="CHECK", detail={"threshold": 96.2, "mode": "dark"},
                           created_at=NOW - timedelta(days=8)),
        m.VisionInspection(equipment_id=eqs[3].id, kind="DIMENSION", measured_value=77.1, unit="mm",
                           judgment="CHECK", detail={"width_px": 586, "mm_per_px": 0.1316},
                           created_at=NOW - timedelta(days=5)),
        m.VisionInspection(equipment_id=eqs[6].id, kind="CORROSION", measured_value=2.1, unit="%",
                           judgment="OK", detail={"rule": "R>1.15G & R>1.25B"},
                           created_at=NOW - timedelta(days=2)),
    ])

    # ── Lesson & Learn 3건 ──
    l1 = m.Lesson(title="STK 권상부 베어링 조기 마모 — 그리스 주입주기 단축",
                  category="DOWNTIME", model_id=stk.id,
                  problem="베어링이 L10 예상수명 40% 시점에 마모 고장, 4h 다운타임.",
                  root_cause="고온 환경 그리스 열화 가속 — 표준 주입주기(6개월)가 환경조건 미반영.",
                  countermeasure="주입주기 6→3개월, PM 진동 측정 추가, FDC 임계 강화.",
                  origin_site_id=kr.id, created_by="최정비", std_reflected=True,
                  created_at=NOW - timedelta(days=40))
    l2 = m.Lesson(title="OHT 가이드휠 편마모 — 레일 이음부 단차 관리 기준 신설",
                  category="QUALITY", model_id=oht.id,
                  problem="가이드휠 편마모로 차체 진동 → 위치인식 오차·수율 리스크.",
                  root_cause="레일 이음부 단차 0.5mm 초과 구간에서 충격 반복.",
                  countermeasure="이음부 단차 0.3mm 관리 기준 신설, 차체 진동 FDC 센서 추가.",
                  origin_site_id=kr.id, created_by="왕정비",
                  created_at=NOW - timedelta(days=18))
    l3 = m.Lesson(title="AGV LiDAR 분진 오감지 — 보호필드 클리닝 주기화",
                  category="SAFETY", model_id=agv.id,
                  problem="분진 누적으로 보호필드 오감지 → 비상정지 반복, 라인 정체.",
                  root_cause="LiDAR 윈도우 클리닝이 PM 항목에 없었음.",
                  countermeasure="PM 30일 주기 클리닝 항목 추가, 오감지율 FDC 모니터링.",
                  origin_site_id=kr.id, created_by="이정비",
                  created_at=NOW - timedelta(days=3))
    db.add_all([l1, l2, l3])
    db.flush()
    deps = [
        (l1, cn, "APPLIED", 30), (l1, vn, "APPLIED", 22), (l1, us, "REVIEWING", None),
        (l2, cn, "APPLIED", 7), (l2, vn, "REVIEWING", None), (l2, us, "NOTIFIED", None),
        (l3, cn, "NOTIFIED", None), (l3, vn, "NOTIFIED", None), (l3, us, "NOTIFIED", None),
    ]
    for les, site, st, d_ago in deps:
        db.add(m.LessonDeployment(lesson_id=les.id, site_id=site.id, status=st,
                                  applied_date=TODAY - timedelta(days=d_ago) if d_ago else None))
    bm1.lesson_id = l1.id

    # ── 워크플로우 3건 (진행중 BM / 완료 셋업 / 진행중 DR) ──
    from .workflow_templates import TEMPLATES

    def make_wf(wf_type, title, eq_id=None, model_id=None, done_until=0, status="OPEN",
                created_by="최정비", days_ago=5):
        wf = m.Workflow(wf_type=wf_type, title=title, equipment_id=eq_id, model_id=model_id,
                        status=status, created_by=created_by,
                        created_at=NOW - timedelta(days=days_ago),
                        closed_at=NOW - timedelta(days=1) if status == "DONE" else None)
        db.add(wf)
        db.flush()
        for i, s in enumerate(TEMPLATES[wf_type]["steps"], start=1):
            st = "DONE" if (status == "DONE" or i <= done_until) else "PENDING"
            db.add(m.WorkflowStep(workflow_id=wf.id, seq=i, name=s["name"], guide=s["guide"],
                                  link=s.get("link"), status=st,
                                  owner=created_by if st == "DONE" else "",
                                  done_at=NOW - timedelta(days=days_ago - i) if st == "DONE" else None))
        return wf

    make_wf("BM_FLOW", "STK-2000-002 주행휠 답면 박리 처리", eq_id=e2.id, model_id=stk.id, done_until=3)
    make_wf("SETUP_STAB", "CNV-B12-001 베트남 설치 안정화", eq_id=eqs[5].id, model_id=cnv.id,
            done_until=4, created_by="이설치", days_ago=12)
    make_wf("DR", "STK-3000 신모델 설계 검토", model_id=stk.id, done_until=2,
            created_by="김설계", days_ago=7)

    # ── 이슈 (전 도메인 분포) ──
    issues = [
        (eqs[5], "SETUP", "INTERLOCK", "HIGH", "합류부 인터락 누락 — 동시 진입 가능", "OPEN", "이설치", None),
        (eqs[5], "SETUP", "MCS", "MID", "MCS 반송지시 중복 수신 시 설비 Hold", "IN_PROGRESS", "박제어", None),
        (eqs[8], "PRODUCTION", "SAFETY", "HIGH", "LiDAR 보호필드 분진 오감지 — 비상정지 반복", "OPEN", "이정비", None),
        (eqs[3], "PRODUCTION", "CONTROL", "LOW", "OHT 커브 감속 파라미터 미세 튜닝", "IN_PROGRESS", "왕정비", None),
        (e1, "PRODUCTION", "CIM", "MID", "PM 실적 CIM 보고 누락 간헐 발생", "OPEN", "박제어", None),
        (eqs[6], "PRODUCTION", "MECH", "LOW", "텐션 장치 스트로크 잔량 20% — 차기 PM 조정", "CLOSED", "최정비", "텐션 재조정 완료"),
        (eqs[4], "PRODUCTION", "RTD", "MID", "RTD 디스패칭 우선순위 반영 지연", "CLOSED", "박제어", "벤더 패치 v2.3 적용"),
        (e2, "PRODUCTION", "ELEC", "MID", "주행 인버터 팬 소음 증가", "OPEN", "최정비", None),
    ]
    for eq_i, ph, dom, sev, title, st, owner, res in issues:
        db.add(m.Issue(equipment_id=eq_i.id, phase=ph, domain=dom, severity=sev, title=title,
                       status=st, owner=owner, resolution=res or "",
                       created_at=NOW - timedelta(days=random.randint(1, 20)),
                       closed_at=NOW - timedelta(days=1) if st == "CLOSED" else None))

    db.add_all([
        m.User(username="admin", name="관리자", role="admin", site_id=kr.id),
        m.User(username="engineer1", name="김엔지니어", role="engineer", site_id=kr.id),
    ])

    db.commit()
    print(f"시드 완료 — 설비 {len(eqs)}대, PM오더 17건, BM {len(bm_cases)}건, "
          f"알람 {len(alarms)}건, 이슈 {len(issues)}건, L&L 3건, 워크플로우 3건")

    # 지식 DB / 라이프사이클 / 견적 데모
    from . import knowledge_seed, lifecycle_seed
    knowledge_seed.run()
    lifecycle_seed.run()
    from .routers.quotations import seed_demo
    db2 = SessionLocal()
    try:
        r = seed_demo(db2)
        print(f"견적 데모: {r}")
    finally:
        db2.close()

    # 비전 상태감시 데모 (합성 이미지 4종 포인트 + 이상 회차)
    from .routers.vision_monitor import seed_demo as vm_seed
    db3 = SessionLocal()
    try:
        r = vm_seed(db3)
        print(f"비전 상태감시 데모: {r}")
    finally:
        db3.close()


if __name__ == "__main__":
    run()

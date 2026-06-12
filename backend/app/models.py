from datetime import datetime, date

from sqlalchemy import (
    String, Integer, Float, Boolean, Date, DateTime, Text, ForeignKey, JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


# ───────────────────────── 마스터 ─────────────────────────

class Site(Base):
    __tablename__ = "sites"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    country: Mapped[str] = mapped_column(String(50), default="")


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(50))
    role: Mapped[str] = mapped_column(String(20), default="engineer")  # admin/engineer/operator
    site_id: Mapped[int | None] = mapped_column(ForeignKey("sites.id"))


class EquipmentModel(Base):
    __tablename__ = "equipment_models"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    category: Mapped[str] = mapped_column(String(20))  # STK/OHT/CNV/AGV/LIFTER/RTV
    maker: Mapped[str] = mapped_column(String(100), default="")
    description: Mapped[str] = mapped_column(Text, default="")


class Equipment(Base):
    __tablename__ = "equipments"
    id: Mapped[int] = mapped_column(primary_key=True)
    asset_code: Mapped[str] = mapped_column(String(50), unique=True)
    model_id: Mapped[int] = mapped_column(ForeignKey("equipment_models.id"))
    site_id: Mapped[int] = mapped_column(ForeignKey("sites.id"))
    line: Mapped[str] = mapped_column(String(50), default="")
    status: Mapped[str] = mapped_column(String(20), default="DR")  # DR/FAB/SETUP/RUN/PM/BM/STOP/SCRAP
    install_date: Mapped[date | None] = mapped_column(Date)
    annual_run_hours: Mapped[float] = mapped_column(Float, default=6000.0)

    model: Mapped["EquipmentModel"] = relationship(lazy="joined")
    site: Mapped["Site"] = relationship(lazy="joined")


# ───────────────────────── 생애주기 ─────────────────────────

class LifecycleEvent(Base):
    __tablename__ = "lifecycle_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    equipment_id: Mapped[int] = mapped_column(ForeignKey("equipments.id"), index=True)
    stage: Mapped[str] = mapped_column(String(20))  # DR/FABRICATION/SETUP/INSTALL_PARAM/PM/BM/MODIFY/SCRAP
    title: Mapped[str] = mapped_column(String(200))
    detail: Mapped[str] = mapped_column(Text, default="")
    doc_ref: Mapped[str] = mapped_column(String(200), default="")
    performed_by: Mapped[str] = mapped_column(String(50), default="")
    event_date: Mapped[date] = mapped_column(Date, default=date.today)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class InstallParameter(Base):
    __tablename__ = "install_parameters"
    id: Mapped[int] = mapped_column(primary_key=True)
    equipment_id: Mapped[int] = mapped_column(ForeignKey("equipments.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    value: Mapped[str] = mapped_column(String(100))
    unit: Mapped[str] = mapped_column(String(20), default="")
    version: Mapped[int] = mapped_column(Integer, default=1)
    set_by: Mapped[str] = mapped_column(String(50), default="")
    set_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    note: Mapped[str] = mapped_column(Text, default="")
    is_current: Mapped[bool] = mapped_column(Boolean, default=True)


# ───────────────────────── PM ─────────────────────────

class PMStandardItem(Base):
    __tablename__ = "pm_standard_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    model_id: Mapped[int] = mapped_column(ForeignKey("equipment_models.id"))
    item_no: Mapped[str] = mapped_column(String(20))
    name: Mapped[str] = mapped_column(String(200))
    part_area: Mapped[str] = mapped_column(String(100), default="")  # 점검 부위
    method: Mapped[str] = mapped_column(String(20), default="VISUAL")  # VISUAL/MEASURE/VISION/REPLACE/CLEAN
    criteria: Mapped[str] = mapped_column(Text, default="")
    lower_limit: Mapped[float | None] = mapped_column(Float)
    upper_limit: Mapped[float | None] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(20), default="")
    period_days: Mapped[int] = mapped_column(Integer, default=90)
    vision_capable: Mapped[bool] = mapped_column(Boolean, default=False)
    vision_recipe: Mapped[dict | None] = mapped_column(JSON)  # kind/threshold/mm_per_px ...
    origin_lesson_id: Mapped[int | None] = mapped_column(ForeignKey("lessons.id"))


class PMOrder(Base):
    __tablename__ = "pm_orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    equipment_id: Mapped[int] = mapped_column(ForeignKey("equipments.id"), index=True)
    plan_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="PLANNED")  # PLANNED/IN_PROGRESS/DONE/OVERDUE
    performed_date: Mapped[date | None] = mapped_column(Date)
    performer: Mapped[str] = mapped_column(String(50), default="")
    note: Mapped[str] = mapped_column(Text, default="")

    equipment: Mapped["Equipment"] = relationship(lazy="joined")
    results: Mapped[list["PMResult"]] = relationship(back_populates="order")


class PMResult(Base):
    __tablename__ = "pm_results"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("pm_orders.id"), index=True)
    standard_item_id: Mapped[int] = mapped_column(ForeignKey("pm_standard_items.id"))
    measured_value: Mapped[float | None] = mapped_column(Float)
    judgment: Mapped[str] = mapped_column(String(10), default="OK")  # OK/NG/CHECK
    method_used: Mapped[str] = mapped_column(String(20), default="VISUAL")
    vision_inspection_id: Mapped[int | None] = mapped_column(ForeignKey("vision_inspections.id"))
    note: Mapped[str] = mapped_column(Text, default="")

    order: Mapped["PMOrder"] = relationship(back_populates="results")
    standard_item: Mapped["PMStandardItem"] = relationship(lazy="joined")


# ───────────────────────── BM ─────────────────────────

class BMReport(Base):
    __tablename__ = "bm_reports"
    id: Mapped[int] = mapped_column(primary_key=True)
    equipment_id: Mapped[int] = mapped_column(ForeignKey("equipments.id"), index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    symptom: Mapped[str] = mapped_column(Text)
    cause: Mapped[str] = mapped_column(Text, default="")
    action: Mapped[str] = mapped_column(Text, default="")
    downtime_min: Mapped[float] = mapped_column(Float, default=0)
    failure_part_id: Mapped[int | None] = mapped_column(ForeignKey("parts.id"))
    status: Mapped[str] = mapped_column(String(20), default="OPEN")  # OPEN/ANALYZING/FIXED/CLOSED
    fdc_alarm_id: Mapped[int | None] = mapped_column(ForeignKey("fdc_alarms.id"))
    lesson_id: Mapped[int | None] = mapped_column(ForeignKey("lessons.id"))
    reported_by: Mapped[str] = mapped_column(String(50), default="")

    equipment: Mapped["Equipment"] = relationship(lazy="joined")


# ───────────────────────── 스페어파츠 ─────────────────────────

class Part(Base):
    __tablename__ = "parts"
    id: Mapped[int] = mapped_column(primary_key=True)
    part_no: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(50), default="")
    maker: Mapped[str] = mapped_column(String(100), default="")
    unit_price: Mapped[float] = mapped_column(Float, default=0)
    lead_time_days: Mapped[int] = mapped_column(Integer, default=30)
    mtbf_hours: Mapped[float | None] = mapped_column(Float)
    current_stock: Mapped[int] = mapped_column(Integer, default=0)
    min_stock: Mapped[int] = mapped_column(Integer, default=0)


class ModelPartBom(Base):
    __tablename__ = "model_part_bom"
    id: Mapped[int] = mapped_column(primary_key=True)
    model_id: Mapped[int] = mapped_column(ForeignKey("equipment_models.id"))
    part_id: Mapped[int] = mapped_column(ForeignKey("parts.id"))
    qty_per_unit: Mapped[int] = mapped_column(Integer, default=1)
    replace_cycle_months: Mapped[int | None] = mapped_column(Integer)
    critical: Mapped[bool] = mapped_column(Boolean, default=False)

    part: Mapped["Part"] = relationship(lazy="joined")
    model: Mapped["EquipmentModel"] = relationship(lazy="joined")


class PartTransaction(Base):
    __tablename__ = "part_transactions"
    id: Mapped[int] = mapped_column(primary_key=True)
    part_id: Mapped[int] = mapped_column(ForeignKey("parts.id"))
    tx_type: Mapped[str] = mapped_column(String(10))  # IN/OUT
    qty: Mapped[int] = mapped_column(Integer)
    ref_type: Mapped[str] = mapped_column(String(20), default="")  # PM/BM/PURCHASE
    ref_id: Mapped[int | None] = mapped_column(Integer)
    tx_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    note: Mapped[str] = mapped_column(String(200), default="")


# ───────────────────────── FDC ─────────────────────────

class FDCSensor(Base):
    __tablename__ = "fdc_sensors"
    id: Mapped[int] = mapped_column(primary_key=True)
    equipment_id: Mapped[int] = mapped_column(ForeignKey("equipments.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    unit: Mapped[str] = mapped_column(String(20), default="")
    warn_low: Mapped[float | None] = mapped_column(Float)
    warn_high: Mapped[float | None] = mapped_column(Float)
    alarm_low: Mapped[float | None] = mapped_column(Float)
    alarm_high: Mapped[float | None] = mapped_column(Float)

    equipment: Mapped["Equipment"] = relationship(lazy="joined")


class FDCReading(Base):
    __tablename__ = "fdc_readings"
    id: Mapped[int] = mapped_column(primary_key=True)
    sensor_id: Mapped[int] = mapped_column(ForeignKey("fdc_sensors.id"), index=True)
    value: Mapped[float] = mapped_column(Float)
    ts: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class FDCAlarm(Base):
    __tablename__ = "fdc_alarms"
    id: Mapped[int] = mapped_column(primary_key=True)
    sensor_id: Mapped[int] = mapped_column(ForeignKey("fdc_sensors.id"), index=True)
    level: Mapped[str] = mapped_column(String(10))  # WARN/ALARM
    classification: Mapped[str] = mapped_column(String(20))  # LEVEL_HIGH/LEVEL_LOW/SPIKE/DRIFT
    value: Mapped[float] = mapped_column(Float)
    message: Mapped[str] = mapped_column(String(300), default="")
    ts: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String(10), default="OPEN")  # OPEN/ACK/CLOSED

    sensor: Mapped["FDCSensor"] = relationship(lazy="joined")


# ───────────────────────── Vision ─────────────────────────

class VisionInspection(Base):
    __tablename__ = "vision_inspections"
    id: Mapped[int] = mapped_column(primary_key=True)
    equipment_id: Mapped[int | None] = mapped_column(ForeignKey("equipments.id"))
    kind: Mapped[str] = mapped_column(String(20))  # WEAR/CORROSION/DIMENSION/ALIGNMENT
    image_path: Mapped[str] = mapped_column(String(300), default="")
    measured_value: Mapped[float | None] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(20), default="")
    judgment: Mapped[str] = mapped_column(String(10), default="CHECK")
    detail: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# ───────────────────────── Lesson & Learn ─────────────────────────

class Lesson(Base):
    __tablename__ = "lessons"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(50), default="")  # SAFETY/QUALITY/DOWNTIME/COST
    model_id: Mapped[int | None] = mapped_column(ForeignKey("equipment_models.id"))
    problem: Mapped[str] = mapped_column(Text)
    root_cause: Mapped[str] = mapped_column(Text, default="")
    countermeasure: Mapped[str] = mapped_column(Text, default="")
    origin_site_id: Mapped[int] = mapped_column(ForeignKey("sites.id"))
    std_reflected: Mapped[bool] = mapped_column(Boolean, default=False)  # PM 표준 반영 여부
    created_by: Mapped[str] = mapped_column(String(50), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    origin_site: Mapped["Site"] = relationship(lazy="joined")
    deployments: Mapped[list["LessonDeployment"]] = relationship(back_populates="lesson")


class LessonDeployment(Base):
    __tablename__ = "lesson_deployments"
    id: Mapped[int] = mapped_column(primary_key=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id"))
    site_id: Mapped[int] = mapped_column(ForeignKey("sites.id"))
    status: Mapped[str] = mapped_column(String(20), default="NOTIFIED")  # NOTIFIED/REVIEWING/APPLIED/NA
    applied_date: Mapped[date | None] = mapped_column(Date)
    note: Mapped[str] = mapped_column(Text, default="")

    lesson: Mapped["Lesson"] = relationship(back_populates="deployments")
    site: Mapped["Site"] = relationship(lazy="joined")


# ───────────────────────── 엔지니어링 지식 DB ─────────────────────────

class KnowledgeArticle(Base):
    """물류설비 엔지니어링 지식 — 표준·논문·기술자료 출처 포함.

    category: COMMON / STK / AGV_AMR / CNV / LIFT / PORT_OHT / ROBOT
    """
    __tablename__ = "knowledge_articles"
    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[str] = mapped_column(String(20), index=True)
    topic: Mapped[str] = mapped_column(String(50), default="")   # WIRE_ROPE/BEARING/BATTERY/WHEEL/CHAIN/SAFETY/...
    title: Mapped[str] = mapped_column(String(300))
    summary: Mapped[str] = mapped_column(Text, default="")
    content: Mapped[str] = mapped_column(Text, default="")        # 본문(plain text, 줄바꿈 유지)
    sources: Mapped[list | None] = mapped_column(JSON)            # [{"title":..,"url"/"ref":..}]
    tags: Mapped[str] = mapped_column(String(300), default="")    # 콤마 구분
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# ───────────────────────── 워크플로우 ─────────────────────────

class Workflow(Base):
    """표준 업무 워크플로우 인스턴스.

    wf_type: DR / SETUP_STAB / ALARM_ACTION / BM_FLOW / PM_FLOW / CONTROL_CHANGE / SYS_ISSUE
    """
    __tablename__ = "workflows"
    id: Mapped[int] = mapped_column(primary_key=True)
    wf_type: Mapped[str] = mapped_column(String(20), index=True)
    title: Mapped[str] = mapped_column(String(300))
    equipment_id: Mapped[int | None] = mapped_column(ForeignKey("equipments.id"))
    model_id: Mapped[int | None] = mapped_column(ForeignKey("equipment_models.id"))
    status: Mapped[str] = mapped_column(String(20), default="OPEN")  # OPEN/DONE/CANCELED
    created_by: Mapped[str] = mapped_column(String(50), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime)
    result_note: Mapped[str] = mapped_column(Text, default="")
    lesson_id: Mapped[int | None] = mapped_column(ForeignKey("lessons.id"))  # 완료 시 L&L 연계

    equipment: Mapped["Equipment | None"] = relationship(lazy="joined")
    model: Mapped["EquipmentModel | None"] = relationship(lazy="joined")
    steps: Mapped[list["WorkflowStep"]] = relationship(
        back_populates="workflow", order_by="WorkflowStep.seq")


class WorkflowStep(Base):
    __tablename__ = "workflow_steps"
    id: Mapped[int] = mapped_column(primary_key=True)
    workflow_id: Mapped[int] = mapped_column(ForeignKey("workflows.id"), index=True)
    seq: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(200))
    guide: Mapped[str] = mapped_column(Text, default="")          # 수행 지침(판정기준·참조 표준)
    link: Mapped[dict | None] = mapped_column(JSON)               # {"kind":"knowledge|tool|page","ref":...,"label":..}
    status: Mapped[str] = mapped_column(String(15), default="PENDING")  # PENDING/IN_PROGRESS/DONE/NG/SKIP
    owner: Mapped[str] = mapped_column(String(50), default="")
    note: Mapped[str] = mapped_column(Text, default="")
    done_at: Mapped[datetime | None] = mapped_column(DateTime)

    workflow: Mapped["Workflow"] = relationship(back_populates="steps")


# ───────────────────────── 라이프사이클 마스터 (편집 가능) ─────────────────────────

class LifecyclePhase(Base):
    """대단계: 투자 → 제작 → 셋업 → 양산 → 폐기/이설. 사용자 추가·이름변경·순서변경 가능."""
    __tablename__ = "lifecycle_phases"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(30), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    seq: Mapped[int] = mapped_column(Integer, default=0)
    description: Mapped[str] = mapped_column(Text, default="")

    processes: Mapped[list["LifecycleProcess"]] = relationship(
        back_populates="phase", order_by="LifecycleProcess.seq",
        cascade="all, delete-orphan")


class LifecycleProcess(Base):
    """세부 프로세스(블럭). module_key 로 플랫폼 기능 블럭에 연결된다.

    module_key 예: quotation / workflow:DR / params / issues / pm / bm / vision / fdc / parts / lessons
    """
    __tablename__ = "lifecycle_processes"
    id: Mapped[int] = mapped_column(primary_key=True)
    phase_id: Mapped[int] = mapped_column(ForeignKey("lifecycle_phases.id"))
    code: Mapped[str] = mapped_column(String(40))
    name: Mapped[str] = mapped_column(String(100))
    seq: Mapped[int] = mapped_column(Integer, default=0)
    description: Mapped[str] = mapped_column(Text, default="")
    module_key: Mapped[str] = mapped_column(String(50), default="")

    phase: Mapped["LifecyclePhase"] = relationship(back_populates="processes")


# ───────────────────────── 투자: 견적 분석 ─────────────────────────

class Quotation(Base):
    __tablename__ = "quotations"
    id: Mapped[int] = mapped_column(primary_key=True)
    project: Mapped[str] = mapped_column(String(200), index=True)   # 투자 프로젝트명
    vendor: Mapped[str] = mapped_column(String(100))
    model_id: Mapped[int | None] = mapped_column(ForeignKey("equipment_models.id"))
    currency: Mapped[str] = mapped_column(String(10), default="KRW")
    received_date: Mapped[date] = mapped_column(Date, default=date.today)
    total_amount: Mapped[float] = mapped_column(Float, default=0)
    file_name: Mapped[str] = mapped_column(String(200), default="")
    status: Mapped[str] = mapped_column(String(20), default="RECEIVED")  # RECEIVED/ANALYZED/SELECTED/REJECTED
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    items: Mapped[list["QuotationItem"]] = relationship(
        back_populates="quotation", cascade="all, delete-orphan")


class QuotationItem(Base):
    __tablename__ = "quotation_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    quotation_id: Mapped[int] = mapped_column(ForeignKey("quotations.id"), index=True)
    line_no: Mapped[int] = mapped_column(Integer, default=0)
    name: Mapped[str] = mapped_column(String(300))
    spec: Mapped[str] = mapped_column(String(300), default="")
    category: Mapped[str] = mapped_column(String(20), default="ETC")  # MECH/DRIVE/ELEC/CONTROL/SW/INSTALL/ETC
    qty: Mapped[float] = mapped_column(Float, default=1)
    unit_price: Mapped[float] = mapped_column(Float, default=0)
    amount: Mapped[float] = mapped_column(Float, default=0)
    errc: Mapped[str] = mapped_column(String(10), default="")  # ELIMINATE/RAISE/REDUCE/CREATE
    errc_note: Mapped[str] = mapped_column(String(300), default="")
    remark: Mapped[str] = mapped_column(String(300), default="")

    quotation: Mapped["Quotation"] = relationship(back_populates="items")


# ───────────────────────── 이슈 관리 (셋업 안정화 / 양산) ─────────────────────────

class Issue(Base):
    """설비(기구/전장/제어/인터락)·시스템(CIM/MCS/RTD)·안전·기타 이슈."""
    __tablename__ = "issues"
    id: Mapped[int] = mapped_column(primary_key=True)
    equipment_id: Mapped[int | None] = mapped_column(ForeignKey("equipments.id"))
    phase: Mapped[str] = mapped_column(String(30), default="SETUP")   # 라이프사이클 phase code
    domain: Mapped[str] = mapped_column(String(20))  # MECH/ELEC/CONTROL/INTERLOCK/CIM/MCS/RTD/SAFETY/ETC
    severity: Mapped[str] = mapped_column(String(10), default="MID")  # HIGH/MID/LOW
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="OPEN")   # OPEN/IN_PROGRESS/CLOSED
    owner: Mapped[str] = mapped_column(String(50), default="")
    due_date: Mapped[date | None] = mapped_column(Date)
    resolution: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime)

    equipment: Mapped["Equipment | None"] = relationship(lazy="joined")


# ───────────────────────── 비전 상태감시 (정기 촬영) ─────────────────────────

class InspectionPoint(Base):
    """정기 촬영 포인트 — 동일 지점·동일 구도로 주기 촬영하여 기준 대비 변화를 감시.

    target_type: BOLT(볼트 풀림) / WIRE(소선 불량) / SURFACE(파손·크랙) / RAIL(단차) / GENERIC
    params(JSON): sensitivity, rotation_limit_deg, step_limit_mm, mm_per_px,
                  warn_score, ng_score 등 타입별 판정 파라미터
    """
    __tablename__ = "inspection_points"
    id: Mapped[int] = mapped_column(primary_key=True)
    equipment_id: Mapped[int] = mapped_column(ForeignKey("equipments.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    target_type: Mapped[str] = mapped_column(String(20), default="GENERIC")
    location_note: Mapped[str] = mapped_column(String(300), default="")  # 촬영 위치·지그·구도 표준
    period_days: Mapped[int] = mapped_column(Integer, default=7)
    baseline_path: Mapped[str] = mapped_column(String(300), default="")
    params: Mapped[dict | None] = mapped_column(JSON)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    equipment: Mapped["Equipment"] = relationship(lazy="joined")
    shots: Mapped[list["InspectionShot"]] = relationship(
        back_populates="point", order_by="InspectionShot.captured_at")


class PatrolRun(Base):
    """순회 촬영 회차 — 한 동영상으로 여러 포인트를 커버하는 실사용 방식."""
    __tablename__ = "patrol_runs"
    id: Mapped[int] = mapped_column(primary_key=True)
    site_id: Mapped[int | None] = mapped_column(ForeignKey("sites.id"))
    file_name: Mapped[str] = mapped_column(String(200), default="")
    performed_by: Mapped[str] = mapped_column(String(50), default="")
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    frames_total: Mapped[int] = mapped_column(Integer, default=0)
    frames_unmatched: Mapped[int] = mapped_column(Integer, default=0)
    points_covered: Mapped[int] = mapped_column(Integer, default=0)
    ng_count: Mapped[int] = mapped_column(Integer, default=0)
    check_count: Mapped[int] = mapped_column(Integer, default=0)
    missed_points: Mapped[list | None] = mapped_column(JSON)
    note: Mapped[str] = mapped_column(String(300), default="")

    site: Mapped["Site | None"] = relationship(lazy="joined")


class InspectionShot(Base):
    """촬영 회차 — 분석 결과·오버레이·연계 이슈."""
    __tablename__ = "inspection_shots"
    id: Mapped[int] = mapped_column(primary_key=True)
    point_id: Mapped[int] = mapped_column(ForeignKey("inspection_points.id"), index=True)
    patrol_run_id: Mapped[int | None] = mapped_column(ForeignKey("patrol_runs.id"), index=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    image_path: Mapped[str] = mapped_column(String(300), default="")
    overlay_path: Mapped[str] = mapped_column(String(300), default="")
    source: Mapped[str] = mapped_column(String(10), default="IMAGE")  # IMAGE/VIDEO
    score: Mapped[float] = mapped_column(Float, default=0)
    judgment: Mapped[str] = mapped_column(String(10), default="OK")  # OK/CHECK/NG
    findings: Mapped[list | None] = mapped_column(JSON)
    detail: Mapped[dict | None] = mapped_column(JSON)
    issue_id: Mapped[int | None] = mapped_column(ForeignKey("issues.id"))

    point: Mapped["InspectionPoint"] = relationship(back_populates="shots")

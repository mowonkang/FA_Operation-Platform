from datetime import datetime, date

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ── 마스터 ──
class SiteOut(ORMModel):
    id: int
    code: str
    name: str
    country: str


class EquipmentModelIn(BaseModel):
    code: str
    name: str
    category: str
    maker: str = ""
    description: str = ""


class EquipmentModelOut(ORMModel, EquipmentModelIn):
    id: int


class EquipmentIn(BaseModel):
    asset_code: str
    model_id: int
    site_id: int
    line: str = ""
    status: str = "DR"
    install_date: date | None = None
    annual_run_hours: float = 6000.0


class EquipmentOut(ORMModel):
    id: int
    asset_code: str
    model_id: int
    site_id: int
    line: str
    status: str
    install_date: date | None
    annual_run_hours: float
    model: EquipmentModelOut
    site: SiteOut


# ── 생애주기 ──
class LifecycleEventIn(BaseModel):
    equipment_id: int
    stage: str
    title: str
    detail: str = ""
    doc_ref: str = ""
    performed_by: str = ""
    event_date: date | None = None


class LifecycleEventOut(ORMModel):
    id: int
    equipment_id: int
    stage: str
    title: str
    detail: str
    doc_ref: str
    performed_by: str
    event_date: date


class InstallParameterIn(BaseModel):
    equipment_id: int
    name: str
    value: str
    unit: str = ""
    set_by: str = ""
    note: str = ""


class InstallParameterOut(ORMModel):
    id: int
    equipment_id: int
    name: str
    value: str
    unit: str
    version: int
    set_by: str
    set_at: datetime
    note: str
    is_current: bool


# ── PM ──
class PMStandardItemIn(BaseModel):
    model_id: int
    item_no: str
    name: str
    part_area: str = ""
    method: str = "VISUAL"
    criteria: str = ""
    lower_limit: float | None = None
    upper_limit: float | None = None
    unit: str = ""
    period_days: int = 90
    vision_capable: bool = False
    vision_recipe: dict | None = None
    origin_lesson_id: int | None = None


class PMStandardItemOut(ORMModel, PMStandardItemIn):
    id: int


class PMOrderIn(BaseModel):
    equipment_id: int
    plan_date: date
    note: str = ""


class PMResultIn(BaseModel):
    standard_item_id: int
    measured_value: float | None = None
    judgment: str | None = None  # 미지정 시 한계값으로 자동판정
    method_used: str = "VISUAL"
    vision_inspection_id: int | None = None
    note: str = ""


class PMResultOut(ORMModel):
    id: int
    order_id: int
    standard_item_id: int
    measured_value: float | None
    judgment: str
    method_used: str
    vision_inspection_id: int | None
    note: str
    standard_item: PMStandardItemOut


class PMOrderOut(ORMModel):
    id: int
    equipment_id: int
    plan_date: date
    status: str
    performed_date: date | None
    performer: str
    note: str
    equipment: EquipmentOut


class PMOrderDetailOut(PMOrderOut):
    results: list[PMResultOut] = []


class PMCompleteIn(BaseModel):
    performer: str = ""
    performed_date: date | None = None
    results: list[PMResultIn] = []


# ── BM ──
class BMReportIn(BaseModel):
    equipment_id: int
    occurred_at: datetime | None = None
    symptom: str
    cause: str = ""
    action: str = ""
    downtime_min: float = 0
    failure_part_id: int | None = None
    fdc_alarm_id: int | None = None
    reported_by: str = ""


class BMReportUpdate(BaseModel):
    cause: str | None = None
    action: str | None = None
    downtime_min: float | None = None
    failure_part_id: int | None = None
    status: str | None = None
    lesson_id: int | None = None


class BMReportOut(ORMModel):
    id: int
    equipment_id: int
    occurred_at: datetime
    symptom: str
    cause: str
    action: str
    downtime_min: float
    failure_part_id: int | None
    status: str
    fdc_alarm_id: int | None
    lesson_id: int | None
    reported_by: str
    equipment: EquipmentOut


# ── 파츠 ──
class PartIn(BaseModel):
    part_no: str
    name: str
    category: str = ""
    maker: str = ""
    unit_price: float = 0
    lead_time_days: int = 30
    mtbf_hours: float | None = None
    current_stock: int = 0
    min_stock: int = 0


class PartOut(ORMModel, PartIn):
    id: int


class BomIn(BaseModel):
    model_id: int
    part_id: int
    qty_per_unit: int = 1
    replace_cycle_months: int | None = None
    critical: bool = False


class BomOut(ORMModel):
    id: int
    model_id: int
    part_id: int
    qty_per_unit: int
    replace_cycle_months: int | None
    critical: bool
    part: PartOut
    model: EquipmentModelOut


class PartTxIn(BaseModel):
    part_id: int
    tx_type: str
    qty: int
    ref_type: str = ""
    ref_id: int | None = None
    note: str = ""


# ── FDC ──
class FDCSensorIn(BaseModel):
    equipment_id: int
    name: str
    unit: str = ""
    warn_low: float | None = None
    warn_high: float | None = None
    alarm_low: float | None = None
    alarm_high: float | None = None


class FDCSensorOut(ORMModel, FDCSensorIn):
    id: int


class FDCIngestReading(BaseModel):
    sensor_id: int
    value: float
    ts: datetime | None = None


class FDCIngestIn(BaseModel):
    readings: list[FDCIngestReading]


class FDCAlarmOut(ORMModel):
    id: int
    sensor_id: int
    level: str
    classification: str
    value: float
    message: str
    ts: datetime
    status: str
    sensor: FDCSensorOut


# ── Lesson ──
class LessonIn(BaseModel):
    title: str
    category: str = ""
    model_id: int | None = None
    problem: str
    root_cause: str = ""
    countermeasure: str = ""
    origin_site_id: int
    created_by: str = ""


class LessonDeploymentOut(ORMModel):
    id: int
    lesson_id: int
    site_id: int
    status: str
    applied_date: date | None
    note: str
    site: SiteOut


class LessonOut(ORMModel):
    id: int
    title: str
    category: str
    model_id: int | None
    problem: str
    root_cause: str
    countermeasure: str
    origin_site_id: int
    std_reflected: bool
    created_by: str
    created_at: datetime
    origin_site: SiteOut
    deployments: list[LessonDeploymentOut] = []


class DeploymentUpdate(BaseModel):
    status: str
    applied_date: date | None = None
    note: str = ""


# ── Vision ──
class VisionInspectionOut(ORMModel):
    id: int
    equipment_id: int | None
    kind: str
    image_path: str
    measured_value: float | None
    unit: str
    judgment: str
    detail: dict | None
    created_at: datetime


# ── Engineering ──
class WireRopeIn(BaseModel):
    breaking_load_kn: float          # 로프 1본 파단하중
    rope_count: int = 1              # 로프 본수
    working_load_kn: float           # 최대 사용하중(권상하중+자중)
    d_over_d: float = 25             # 시브경/로프경 비
    cycles_per_day: float = 200      # 일일 권상 사이클
    required_sf: float = 5.0         # 법규 요구 안전율(권상용 5.0)


class BearingIn(BaseModel):
    dynamic_load_c_kn: float         # 기본 동정격하중 C
    equivalent_load_p_kn: float      # 등가 동하중 P
    rpm: float = 1500
    bearing_type: str = "ball"       # ball / roller
    operated_hours: float = 0        # 누적 가동시간
    annual_run_hours: float = 6000


class BatteryIn(BaseModel):
    rated_cycles: int = 3000         # 정격 사이클 수명(80% DOD 기준)
    dod_percent: float = 80          # 실제 운용 방전심도
    cycles_per_day: float = 4
    calendar_life_years: float = 8
    used_years: float = 0


class WheelIn(BaseModel):
    initial_diameter_mm: float
    current_diameter_mm: float
    wear_limit_diameter_mm: float
    wear_rate_mm_per_year: float     # 실측 기반 연간 마모량
    safety_margin: float = 0.8       # 안전계수(예측수명의 80%만 사용)

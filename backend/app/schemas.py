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


# ── 지식 DB ──
class KnowledgeOut(ORMModel):
    id: int
    category: str
    topic: str
    title: str
    summary: str
    content: str
    sources: list | None
    tags: str
    created_at: datetime


class KnowledgeIn(BaseModel):
    category: str
    topic: str = ""
    title: str
    summary: str = ""
    content: str = ""
    sources: list | None = None
    tags: str = ""


# ── 워크플로우 ──
class WorkflowCreateIn(BaseModel):
    wf_type: str
    title: str
    equipment_id: int | None = None
    model_id: int | None = None
    created_by: str = ""


class WorkflowStepOut(ORMModel):
    id: int
    seq: int
    name: str
    guide: str
    link: dict | None
    status: str
    owner: str
    note: str
    done_at: datetime | None


class WorkflowOut(ORMModel):
    id: int
    wf_type: str
    title: str
    equipment_id: int | None
    model_id: int | None
    status: str
    created_by: str
    created_at: datetime
    closed_at: datetime | None
    result_note: str
    lesson_id: int | None


class WorkflowDetailOut(WorkflowOut):
    steps: list[WorkflowStepOut] = []


class WorkflowStepUpdate(BaseModel):
    status: str | None = None
    owner: str | None = None
    note: str | None = None


class WorkflowCloseIn(BaseModel):
    result_note: str = ""
    create_lesson: bool = False
    lesson_title: str = ""
    lesson_category: str = "DOWNTIME"
    origin_site_id: int | None = None


# ── 비전 상태감시 ──
class InspectionPointIn(BaseModel):
    equipment_id: int
    name: str
    target_type: str = "GENERIC"   # BOLT/WIRE/SURFACE/RAIL/GENERIC
    location_note: str = ""
    period_days: int = 7
    params: dict | None = None


class InspectionPointOut(ORMModel):
    id: int
    equipment_id: int
    name: str
    target_type: str
    location_note: str
    period_days: int
    baseline_path: str
    params: dict | None
    active: bool
    created_at: datetime
    equipment: EquipmentOut


class PatrolRunOut(ORMModel):
    id: int
    site_id: int | None
    file_name: str
    performed_by: str
    started_at: datetime
    frames_total: int
    frames_unmatched: int
    points_covered: int
    ng_count: int
    check_count: int
    missed_points: list | None
    note: str


class InspectionShotOut(ORMModel):
    id: int
    point_id: int
    patrol_run_id: int | None
    captured_at: datetime
    image_path: str
    overlay_path: str
    source: str
    score: float
    judgment: str
    findings: list | None
    detail: dict | None
    issue_id: int | None


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


class WireRopeProIn(BaseModel):
    """와이어로프 전문가용 입력 — 가반하중·체결방식 기반."""
    payload_kg: float = 1000            # 가반하중
    carriage_weight_kg: float = 500     # 운반구(캐리지/포크) 자중
    dynamic_factor: float = 1.2         # 동적계수(기동/제동 충격)
    falls: int = 2                      # 로프 줄수(체결 방식: 1/2/4...)
    n_sheaves: int = 2                  # 로프가 통과하는 시브 수
    sheave_efficiency: float = 0.98     # 시브 1개당 효율
    rope_diameter_mm: float = 12
    rope_grade: int = 1770              # 소선 인장강도 N/mm² (1770/1960)
    rope_construction: str = "6x36"     # 6x19/6x36/8x19/rotation_resistant
    d_over_d: float = 25                # 시브경/로프경
    lift_height_m: float = 10           # 양정(로프 자중 가산)
    cycles_per_day: float = 200
    working_days_per_year: int = 300
    environment: str = "normal"         # clean/normal/dusty/corrosive
    required_sf: float = 5.0            # 법규 요구 안전율(화물 직접지지 5)


class WheelIn(BaseModel):
    initial_diameter_mm: float
    current_diameter_mm: float
    wear_limit_diameter_mm: float
    wear_rate_mm_per_year: float     # 실측 기반 연간 마모량
    safety_margin: float = 0.8       # 안전계수(예측수명의 80%만 사용)


class MotorIn(BaseModel):
    mode: str = "travel"             # travel(주행) / hoist(권상)
    mass_kg: float = 5000            # 총 질량(자중+하중)
    speed_m_min: float = 120
    accel_m_s2: float = 0.5
    rolling_resistance: float = 0.015  # 주행저항계수 (휠/레일 0.01~0.02)
    efficiency: float = 0.85
    service_factor: float = 1.2


class ConveyorIn(BaseModel):
    belt_speed_m_min: float = 30
    length_m: float = 20
    moving_mass_kg: float = 400      # 벨트+롤러 등 이동부 질량
    capacity_t_h: float = 30         # 반송 능력 (톤/시간)
    lift_height_m: float = 0         # 양정(경사 상승고)
    friction_coeff: float = 0.03
    efficiency: float = 0.85
    service_factor: float = 1.2


class ChainIn(BaseModel):
    load_kg: float = 1500            # 가반하중
    carriage_weight_kg: float = 500
    chain_count: int = 2             # 체인 줄수
    dynamic_factor: float = 1.3
    mbl_kn: float = 100              # 체인 1줄 최소파단하중
    required_sf: float = 5.0
    current_elongation_pct: float = 0.8   # 실측 신율
    elongation_rate_pct_year: float = 0.3  # 신율 진행률 (측정 이력 기반)


# ── 라이프사이클 설정 ──
class PhaseIn(BaseModel):
    code: str
    name: str
    seq: int = 0
    description: str = ""


class PhaseUpdate(BaseModel):
    name: str | None = None
    seq: int | None = None
    description: str | None = None


class ProcessIn(BaseModel):
    phase_id: int
    code: str
    name: str
    seq: int = 0
    description: str = ""
    module_key: str = ""


class ProcessUpdate(BaseModel):
    name: str | None = None
    seq: int | None = None
    description: str | None = None
    module_key: str | None = None
    phase_id: int | None = None


# ── 견적 ──
class QuotationItemOut(ORMModel):
    id: int
    line_no: int
    name: str
    spec: str
    category: str
    qty: float
    unit_price: float
    amount: float
    errc: str
    errc_note: str
    remark: str


class QuotationOut(ORMModel):
    id: int
    project: str
    vendor: str
    currency: str
    received_date: date
    total_amount: float
    file_name: str
    status: str
    note: str
    created_at: datetime


class QuotationDetailOut(QuotationOut):
    items: list[QuotationItemOut] = []


class QuotationItemUpdate(BaseModel):
    category: str | None = None
    errc: str | None = None
    errc_note: str | None = None


# ── 이슈 ──
class IssueIn(BaseModel):
    equipment_id: int | None = None
    phase: str = "SETUP"
    domain: str
    severity: str = "MID"
    title: str
    description: str = ""
    owner: str = ""
    due_date: date | None = None


class IssueUpdate(BaseModel):
    domain: str | None = None
    severity: str | None = None
    title: str | None = None
    description: str | None = None
    status: str | None = None
    owner: str | None = None
    due_date: date | None = None
    resolution: str | None = None


class IssueOut(ORMModel):
    id: int
    equipment_id: int | None
    phase: str
    domain: str
    severity: str
    title: str
    description: str
    status: str
    owner: str
    due_date: date | None
    resolution: str
    created_at: datetime
    closed_at: datetime | None

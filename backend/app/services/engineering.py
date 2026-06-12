"""설비 엔지니어링 수명 계산 모듈.

각 함수는 입력 스키마를 받아 계산 근거(basis)와 함께 dict 를 반환한다.
모델은 보수적인 간이식이며, Phase 4 에서 실측 데이터 기반 RUL 보정으로 고도화한다.
"""
from .. import schemas


# 로프 구조별 최소파단력 계수 K (EN 12385-4: F_min = K·d²·R0/1000 [kN], d[mm], R0[N/mm²])
ROPE_K = {
    "6x19": 0.330,
    "6x36": 0.356,
    "8x19": 0.293,
    "rotation_resistant": 0.318,  # 35(W)x7 등 회전저항 로프 대표값
}

# 환경 보정계수 (수명 배율)
ENV_FACTOR = {"clean": 1.0, "normal": 0.85, "dusty": 0.65, "corrosive": 0.45}


def wire_rope_pro(p: "schemas.WireRopeProIn") -> dict:
    """와이어로프 전문가용 수명 예측.

    입력: 가반하중·운반구 자중·체결(리빙) 방식·로프 직경/등급/구조·D/d·양정·듀티·환경
    출력: 줄당 장력, 최소파단력(EN 12385-4), 안전율(산업안전보건규칙 163조 대비),
          Feyrer 형태 간이식 굽힘피로 수명(폐기기준 도달), 민감도 곡선(차트용)

    수명 모델 (Feyrer 경향 반영 간이식, 문헌: Mechanics & Industry 2017 등):
      N_discard = N0 × (D/d ÷ 25)^2.5 × (SF ÷ 5)^2.0 × k_env × k_rope
      N0 = 300,000 굽힘 (D/d=25, SF=5, 일반 6스트랜드, 청정 환경 — Feyrer 시험 데이터 차수에 맞춘 보수값)
      회전저항 로프 k_rope = 0.6 (굽힘피로 수명 단축 경향)
    사이클당 굽힘 수 = (시브 통과 수 × 2) + 1(드럼)
    """
    total_load_kn = (p.payload_kg + p.carriage_weight_kg) * 9.81 / 1000.0
    dyn = max(p.dynamic_factor, 1.0)
    design_load_kn = total_load_kn * dyn

    falls = max(p.falls, 1)
    eta = p.sheave_efficiency ** max(p.n_sheaves, 0) if p.n_sheaves else 1.0
    line_tension_kn = design_load_kn / (falls * max(eta, 1e-6))
    # 대양정 로프 자중 가산 (강선 밀도 근사: 0.4 kg/m per 100mm² 단면 ≈ 0.0045·d² kg/m)
    rope_self_kg = 0.0045 * p.rope_diameter_mm**2 * p.lift_height_m
    line_tension_kn += rope_self_kg * 9.81 / 1000.0

    k = ROPE_K.get(p.rope_construction, 0.356)
    mbf_kn = k * p.rope_diameter_mm**2 * p.rope_grade / 1000.0
    sf = mbf_kn / line_tension_kn if line_tension_kn > 0 else float("inf")
    sf_pass = sf >= p.required_sf

    k_rope = 0.6 if p.rope_construction == "rotation_resistant" else 1.0
    k_env = ENV_FACTOR.get(p.environment, 0.85)

    def discard_cycles(sf_v: float, dd_v: float) -> float:
        if sf_v <= 0:
            return 0.0
        return 300000.0 * (dd_v / 25.0) ** 2.5 * (sf_v / 5.0) ** 2.0 * k_env * k_rope

    bendings_per_cycle = p.n_sheaves * 2 + 1
    n_bend = discard_cycles(sf, p.d_over_d)
    life_cycles = n_bend / bendings_per_cycle if bendings_per_cycle else n_bend
    life_years = life_cycles / (p.cycles_per_day * p.working_days_per_year) \
        if p.cycles_per_day > 0 else None
    replace_years = life_years * 0.8 if life_years else None  # 80% 시점 계획 교체

    # 민감도 곡선 (차트용)
    curve_dd = []
    for dd in range(12, 41, 2):
        n = discard_cycles(sf, dd) / bendings_per_cycle
        curve_dd.append({"x": dd, "years": round(n / (p.cycles_per_day * p.working_days_per_year), 2)
                         if p.cycles_per_day > 0 else None})
    curve_dia = []
    for delta in range(-4, 5):
        d2 = p.rope_diameter_mm + delta
        if d2 < 4:
            continue
        mbf2 = k * d2**2 * p.rope_grade / 1000.0
        sf2 = mbf2 / line_tension_kn if line_tension_kn > 0 else 0
        n2 = discard_cycles(sf2, p.d_over_d) / bendings_per_cycle
        curve_dia.append({"x": d2, "sf": round(sf2, 2),
                          "years": round(n2 / (p.cycles_per_day * p.working_days_per_year), 2)
                          if p.cycles_per_day > 0 else None})
    curve_falls = []
    for f in (1, 2, 4, 6, 8):
        eta_f = p.sheave_efficiency ** max(p.n_sheaves, 0) if p.n_sheaves else 1.0
        t = design_load_kn / (f * max(eta_f, 1e-6))
        sf_f = mbf_kn / t if t > 0 else 0
        curve_falls.append({"falls": f, "tension_kn": round(t, 2), "sf": round(sf_f, 2)})

    return {
        "design_load_kn": round(design_load_kn, 2),
        "line_tension_kn": round(line_tension_kn, 2),
        "rope_self_weight_kg": round(rope_self_kg, 1),
        "min_breaking_force_kn": round(mbf_kn, 1),
        "safety_factor": round(sf, 2),
        "required_sf": p.required_sf,
        "sf_pass": sf_pass,
        "bendings_per_cycle": bendings_per_cycle,
        "discard_life_bendings": round(n_bend),
        "discard_life_cycles": round(life_cycles),
        "discard_life_years": round(life_years, 1) if life_years else None,
        "planned_replace_years": round(replace_years, 1) if replace_years else None,
        "judgment": "OK" if sf_pass and (life_years or 0) > 1 else ("CHECK" if sf_pass else "NG"),
        "curves": {"life_vs_dd": curve_dd, "life_vs_diameter": curve_dia, "tension_vs_falls": curve_falls},
        "discard_criteria": (
            "폐기/사용금지 기준 — 산업안전보건규칙 제166조: 한 꼬임 소선 10% 이상 단선, 직경 7% 초과 감소, "
            "킹크·심한 변형·부식. ISO 4309: 6d/30d 구간 가시 단선 수(로프 구성·M등급별 표), "
            "단선 클러스터는 즉시 폐기 검토."
        ),
        "basis": (
            f"MBF = K({k})×d²({p.rope_diameter_mm}²)×R0({p.rope_grade})/1000 = {mbf_kn:.1f}kN (EN 12385-4). "
            f"줄당 장력 = (가반{p.payload_kg}+자중{p.carriage_weight_kg})kg×g×동적계수{dyn} ÷ "
            f"{falls}줄 ÷ 시브효율{eta:.3f} + 로프자중 = {line_tension_kn:.2f}kN. "
            f"SF = {sf:.2f} (법규 기준 {p.required_sf}). "
            f"수명 = 300,000굽힘 × (D/d {p.d_over_d}/25)^2.5 × (SF/5)^2 × 환경{k_env} × 로프계수{k_rope} "
            f"÷ 사이클당 {bendings_per_cycle}굽힘 (Feyrer 경향 간이식 — 실측 단선 추세로 보정 권장)."
        ),
    }


STD_MOTORS_KW = [0.4, 0.75, 1.5, 2.2, 3.7, 5.5, 7.5, 11, 15, 18.5, 22, 30, 37, 45, 55, 75, 90, 110]


def _std_motor(kw: float) -> float | None:
    for m in STD_MOTORS_KW:
        if m >= kw:
            return m
    return None


def motor_capacity(p: "schemas.MotorIn") -> dict:
    """주행/권상 모터 용량 산정.

    주행: F = m·g·μ(주행저항) + m·a(가속),  P = F·v/η
    권상: P = m·g·v/η (+ 가속분)
    서비스팩터를 곱해 표준 모터 용량을 선정한다.
    """
    g = 9.81
    v = p.speed_m_min / 60.0
    if p.mode == "hoist":
        f_steady = p.mass_kg * g
        f_accel = p.mass_kg * p.accel_m_s2
    else:
        f_steady = p.mass_kg * g * p.rolling_resistance
        f_accel = p.mass_kg * p.accel_m_s2
    p_steady = f_steady * v / max(p.efficiency, 1e-6) / 1000.0
    p_peak = (f_steady + f_accel) * v / max(p.efficiency, 1e-6) / 1000.0
    p_required = max(p_steady * p.service_factor, p_peak)
    std = _std_motor(p_required)

    curve = []
    for spd in range(20, 261, 20):
        vv = spd / 60.0
        ps = f_steady * vv / max(p.efficiency, 1e-6) / 1000.0
        pk = (f_steady + f_accel) * vv / max(p.efficiency, 1e-6) / 1000.0
        curve.append({"x": spd, "steady_kw": round(ps, 2),
                      "required_kw": round(max(ps * p.service_factor, pk), 2)})

    return {
        "mode": p.mode,
        "steady_kw": round(p_steady, 2),
        "peak_kw": round(p_peak, 2),
        "required_kw": round(p_required, 2),
        "recommended_motor_kw": std,
        "judgment": "OK" if std else "NG",
        "curves": {"power_vs_speed": curve},
        "basis": (
            f"{'권상: F=mg' if p.mode == 'hoist' else f'주행: F=mg×μ({p.rolling_resistance})'}"
            f"={f_steady / 1000:.2f}kN, 가속분 m×a({p.accel_m_s2}m/s²)={f_accel / 1000:.2f}kN. "
            f"정상 {p_steady:.2f}kW, 피크 {p_peak:.2f}kW, SF {p.service_factor} → 필요 {p_required:.2f}kW. "
            f"인버터 구동 시 피크는 모터 과부하율(150%/60s)로 흡수 가능 여부 별도 확인. "
            f"권상용은 제동저항·브레이크 토크(정격 1.5배) 함께 검토."
        ),
    }


def conveyor_power(p: "schemas.ConveyorIn") -> dict:
    """벨트 컨베이어 구동 출력 (간이식, CEMA 개념 기반).

    P = [μ·g·(이동질량) ·v + Q·g·H] / η
    Q(반송율 kg/s) = capacity_t_h × 1000/3600
    """
    g = 9.81
    v = p.belt_speed_m_min / 60.0
    q_kg_s = p.capacity_t_h * 1000.0 / 3600.0
    load_on_belt = q_kg_s * p.length_m / max(v, 1e-6)  # 벨트 위 체류 화물질량
    moving_mass = p.moving_mass_kg + load_on_belt
    p_friction = p.friction_coeff * moving_mass * g * v / 1000.0
    p_lift = q_kg_s * g * p.lift_height_m / 1000.0
    p_required = (p_friction + p_lift) / max(p.efficiency, 1e-6) * p.service_factor
    std = _std_motor(p_required)

    curve = []
    for cap in range(0, int(p.capacity_t_h * 2) + 1, max(int(p.capacity_t_h / 5), 1)):
        qq = cap * 1000.0 / 3600.0
        lm = p.moving_mass_kg + qq * p.length_m / max(v, 1e-6)
        pf = p.friction_coeff * lm * g * v / 1000.0
        pl = qq * g * p.lift_height_m / 1000.0
        curve.append({"x": cap, "required_kw": round((pf + pl) / max(p.efficiency, 1e-6) * p.service_factor, 2)})

    return {
        "friction_kw": round(p_friction, 2),
        "lift_kw": round(p_lift, 2),
        "required_kw": round(p_required, 2),
        "recommended_motor_kw": std,
        "load_on_belt_kg": round(load_on_belt, 1),
        "judgment": "OK" if std else "NG",
        "curves": {"power_vs_capacity": curve},
        "basis": (
            f"마찰분 = μ({p.friction_coeff})×({p.moving_mass_kg}+체류화물{load_on_belt:.0f})kg×g×v({v:.2f}m/s) "
            f"= {p_friction:.2f}kW, 양정분 = Q({q_kg_s:.2f}kg/s)×g×H({p.lift_height_m}m) = {p_lift:.2f}kW. "
            f"효율 {p.efficiency}, SF {p.service_factor}. 정밀 설계는 CEMA Belt Book/제조사 프로그램으로 검증."
        ),
    }


def chain_life(p: "schemas.ChainIn") -> dict:
    """리프 체인 안전율 + 신율 추세 기반 잔여수명.

    SF = MBL / 줄당 장력 (법규: 화물 직접지지 체인 5 이상)
    신율 한계: 2%(교체 계획) / 3%(즉시 교체) — FLTA/SAFed 기준
    """
    g = 9.81
    line_load_kn = (p.load_kg + p.carriage_weight_kg) * g * p.dynamic_factor \
        / max(p.chain_count, 1) / 1000.0
    sf = p.mbl_kn / line_load_kn if line_load_kn > 0 else float("inf")
    sf_pass = sf >= p.required_sf

    rate = max(p.elongation_rate_pct_year, 1e-6)
    to_plan = max((2.0 - p.current_elongation_pct) / rate, 0)
    to_limit = max((3.0 - p.current_elongation_pct) / rate, 0)
    strength_loss = round(p.current_elongation_pct / 3.0 * 15.0, 1)  # 3%≈15% 손실 비례 근사

    curve = []
    for yr in range(0, 11):
        e = p.current_elongation_pct + rate * yr
        curve.append({"x": yr, "elongation_pct": round(min(e, 4.0), 2)})

    if p.current_elongation_pct >= 3.0:
        judgment = "NG"
    elif p.current_elongation_pct >= 2.0 or not sf_pass:
        judgment = "CHECK" if sf_pass else "NG"
    else:
        judgment = "OK" if to_plan > 0.5 else "CHECK"

    return {
        "line_load_kn": round(line_load_kn, 2),
        "safety_factor": round(sf, 2),
        "sf_pass": sf_pass,
        "current_elongation_pct": p.current_elongation_pct,
        "estimated_strength_loss_pct": strength_loss,
        "years_to_plan_2pct": round(to_plan, 1),
        "years_to_limit_3pct": round(to_limit, 1),
        "judgment": judgment,
        "curves": {"elongation_projection": curve},
        "basis": (
            f"줄당 하중 = ({p.load_kg}+{p.carriage_weight_kg})kg×g×동적계수{p.dynamic_factor}÷{p.chain_count}줄 "
            f"= {line_load_kn:.2f}kN, SF = MBL {p.mbl_kn}kN ÷ 하중 = {sf:.2f} (기준 {p.required_sf}). "
            f"신율 {p.current_elongation_pct}% + {p.elongation_rate_pct_year}%/년 → 2%(교체계획) "
            f"{to_plan:.1f}년, 3%(즉시교체) {to_limit:.1f}년. 신율 3% = 강도 약 15% 손실(FLTA). "
            f"무윤활 시 신율 진행 3~5배 가속 — 급유 주기 준수."
        ),
    }


def wire_rope_life(p: schemas.WireRopeIn) -> dict:
    """와이어로프 안전율 및 굽힘피로 수명 예측.

    안전율 SF = (파단하중 × 본수) / 사용하중.
    굽힘피로 수명은 D/d 비와 SF 에 따른 보정계수를 적용한 간이 Feyrer 형태:
      기준 수명 50,000 굽힘 사이클 (D/d=25, SF=5 기준)
      D/d 보정: (D/d / 25)^2  — 시브가 클수록 굽힘응력 감소
      SF 보정: (SF / 5)^1.5   — 하중이 낮을수록 수명 증가
    """
    total_breaking = p.breaking_load_kn * p.rope_count
    sf = total_breaking / p.working_load_kn if p.working_load_kn > 0 else float("inf")
    pass_sf = sf >= p.required_sf

    base_cycles = 50000.0
    dd_factor = (p.d_over_d / 25.0) ** 2
    sf_factor = (sf / 5.0) ** 1.5
    life_cycles = base_cycles * dd_factor * sf_factor
    life_years = life_cycles / (p.cycles_per_day * 365) if p.cycles_per_day > 0 else None

    return {
        "safety_factor": round(sf, 2),
        "required_sf": p.required_sf,
        "sf_pass": pass_sf,
        "expected_life_cycles": round(life_cycles),
        "expected_life_years": round(life_years, 1) if life_years else None,
        "judgment": "OK" if pass_sf else "NG",
        "basis": (
            f"SF = {p.breaking_load_kn}kN × {p.rope_count}본 / {p.working_load_kn}kN = {sf:.2f} "
            f"(기준 {p.required_sf}). 수명 = 50,000cyc × (D/d {p.d_over_d}/25)² × (SF/5)^1.5, "
            f"일 {p.cycles_per_day}사이클 기준. 검사기준: 소선단선·직경 7% 감소 시 즉시 교체."
        ),
    }


def bearing_life(p: schemas.BearingIn) -> dict:
    """베어링 L10 수명 (ISO 281).  L10h = 10^6 / (60·N) × (C/P)^p"""
    exp = 3.0 if p.bearing_type == "ball" else 10.0 / 3.0
    if p.equivalent_load_p_kn <= 0 or p.rpm <= 0:
        return {"error": "P, rpm 은 0보다 커야 합니다."}
    l10h = 1e6 / (60 * p.rpm) * (p.dynamic_load_c_kn / p.equivalent_load_p_kn) ** exp
    remain_h = max(l10h - p.operated_hours, 0)
    remain_years = remain_h / p.annual_run_hours if p.annual_run_hours > 0 else None

    return {
        "l10_hours": round(l10h),
        "operated_hours": p.operated_hours,
        "remaining_hours": round(remain_h),
        "remaining_years": round(remain_years, 1) if remain_years is not None else None,
        "judgment": "OK" if remain_h > p.annual_run_hours else ("CHECK" if remain_h > 0 else "NG"),
        "basis": (
            f"L10h = 10⁶/(60×{p.rpm}rpm) × (C {p.dynamic_load_c_kn}/P {p.equivalent_load_p_kn})^"
            f"{'3' if p.bearing_type == 'ball' else '10/3'} = {l10h:,.0f}h. "
            f"잔여 = L10h − 누적 {p.operated_hours:,.0f}h. 90% 신뢰도 기준이므로 진동·온도 FDC 병행 감시 권장."
        ),
    }


def battery_life(p: schemas.BatteryIn) -> dict:
    """배터리(Li-ion) 수명: 사이클 수명(DOD 보정)과 캘린더 수명 중 짧은 쪽.

    DOD 보정: 정격(80% DOD) 대비 실제 DOD 가 낮으면 사이클 수명 증가 — cycles × (80/DOD)^1.1
    """
    if p.dod_percent <= 0 or p.cycles_per_day <= 0:
        return {"error": "DOD, cycles_per_day 는 0보다 커야 합니다."}
    adj_cycles = p.rated_cycles * (80.0 / p.dod_percent) ** 1.1
    cycle_years = adj_cycles / (p.cycles_per_day * 365)
    life_years = min(cycle_years, p.calendar_life_years)
    remain_years = max(life_years - p.used_years, 0)
    soh = max(1 - 0.2 * (p.used_years / life_years), 0.0) * 100 if life_years > 0 else 0
    limiting = "cycle" if cycle_years < p.calendar_life_years else "calendar"

    return {
        "adjusted_cycles": round(adj_cycles),
        "cycle_life_years": round(cycle_years, 1),
        "calendar_life_years": p.calendar_life_years,
        "expected_life_years": round(life_years, 1),
        "remaining_years": round(remain_years, 1),
        "estimated_soh_percent": round(soh, 1),
        "limiting_factor": limiting,
        "judgment": "OK" if remain_years > 1 else ("CHECK" if remain_years > 0 else "NG"),
        "basis": (
            f"보정 사이클 = {p.rated_cycles} × (80/{p.dod_percent})^1.1 = {adj_cycles:,.0f}. "
            f"사이클 수명 {cycle_years:.1f}년 vs 캘린더 {p.calendar_life_years}년 중 짧은 쪽 적용. "
            f"SOH 80% 도달 시점을 수명 종지로 간주(선형 열화 가정)."
        ),
    }


def wheel_life(p: schemas.WheelIn) -> dict:
    """주행 휠 마모 잔여 수명: (현재경 − 마모한계경) / 연간 마모율 × 안전계수"""
    margin_mm = p.current_diameter_mm - p.wear_limit_diameter_mm
    total_wear_band = p.initial_diameter_mm - p.wear_limit_diameter_mm
    wear_used_pct = (
        (p.initial_diameter_mm - p.current_diameter_mm) / total_wear_band * 100
        if total_wear_band > 0 else 0
    )
    if p.wear_rate_mm_per_year <= 0:
        return {"error": "wear_rate_mm_per_year 는 0보다 커야 합니다."}
    raw_years = margin_mm / p.wear_rate_mm_per_year
    safe_years = max(raw_years * p.safety_margin, 0)

    return {
        "wear_margin_mm": round(margin_mm, 2),
        "wear_used_percent": round(wear_used_pct, 1),
        "raw_remaining_years": round(raw_years, 1),
        "safe_remaining_years": round(safe_years, 1),
        "judgment": "OK" if safe_years > 1 else ("CHECK" if safe_years > 0 else "NG"),
        "basis": (
            f"잔여마모대 = 현재 {p.current_diameter_mm} − 한계 {p.wear_limit_diameter_mm} = {margin_mm:.2f}mm, "
            f"연간 마모율 {p.wear_rate_mm_per_year}mm/년, 안전계수 {p.safety_margin} 적용. "
            f"편마모·플랜지 마모는 비전 측정(WEAR/DIMENSION)으로 병행 감시."
        ),
    }

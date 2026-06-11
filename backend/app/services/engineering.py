"""설비 엔지니어링 수명 계산 모듈.

각 함수는 입력 스키마를 받아 계산 근거(basis)와 함께 dict 를 반환한다.
모델은 보수적인 간이식이며, Phase 4 에서 실측 데이터 기반 RUL 보정으로 고도화한다.
"""
from .. import schemas


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

import { useEffect, useState } from 'react'
import { LineChart, Line, XAxis, YAxis, Tooltip, ReferenceLine, ResponsiveContainer, Legend } from 'recharts'
import { api, judgeClass } from '../api'

function WireRopePro() {
  const [v, setV] = useState({
    payload_kg: 2000, carriage_weight_kg: 800, dynamic_factor: 1.2,
    falls: 2, n_sheaves: 2, sheave_efficiency: 0.98,
    rope_diameter_mm: 12, rope_grade: 1770, rope_construction: '6x36',
    d_over_d: 25, lift_height_m: 15, cycles_per_day: 250,
    working_days_per_year: 300, environment: 'normal', required_sf: 5,
  })
  const [r, setR] = useState<any>(null)
  const [err, setErr] = useState('')

  const num = (k: string, label: string, step = 1) => (
    <label key={k}>{label}
      <input type="number" step={step} value={(v as any)[k]}
        onChange={(e) => setV({ ...v, [k]: Number(e.target.value) })} />
    </label>
  )

  const run = async () => {
    setErr('')
    try { setR(await api.post('/engineering/wire-rope-pro', v)) } catch (e: any) { setErr(e.message) }
  }
  useEffect(() => { run() }, [])  // 초기 1회 자동 계산

  return (
    <div className="panel" style={{ borderLeft: '4px solid #2563eb' }}>
      <h3 style={{ marginTop: 0 }}>🔧 와이어로프 수명 예측 PRO — 가반하중·체결방식 기반 (인터랙티브)</h3>
      <p className="muted">
        EN 12385-4 최소파단력, 산업안전보건규칙 제163조 안전율(화물 직접지지 5), Feyrer 경향 굽힘피로 간이식.
        입력 변경 후 [계산]을 누르면 민감도 곡선이 갱신됩니다.
      </p>
      <div className="form-grid">
        {num('payload_kg', '가반하중 (kg)', 100)}
        {num('carriage_weight_kg', '운반구 자중 (kg)', 50)}
        {num('dynamic_factor', '동적계수', 0.05)}
        <label>체결 방식 (로프 줄수)
          <select value={v.falls} onChange={(e) => setV({ ...v, falls: Number(e.target.value) })}>
            <option value={1}>1줄 (직결)</option>
            <option value={2}>2줄 (1/2 하중)</option>
            <option value={4}>4줄 (1/4 하중)</option>
            <option value={6}>6줄</option>
            <option value={8}>8줄</option>
          </select>
        </label>
        {num('n_sheaves', '시브 통과 수', 1)}
        {num('rope_diameter_mm', '로프 직경 (mm)', 1)}
        <label>로프 등급 (N/mm²)
          <select value={v.rope_grade} onChange={(e) => setV({ ...v, rope_grade: Number(e.target.value) })}>
            <option value={1770}>1770</option>
            <option value={1960}>1960</option>
          </select>
        </label>
        <label>로프 구조
          <select value={v.rope_construction} onChange={(e) => setV({ ...v, rope_construction: e.target.value })}>
            <option value="6x36">6×36 WS</option>
            <option value="6x19">6×19</option>
            <option value="8x19">8×19</option>
            <option value="rotation_resistant">회전저항 로프</option>
          </select>
        </label>
        {num('d_over_d', 'D/d (시브경/로프경)', 0.5)}
        {num('lift_height_m', '양정 (m)', 1)}
        {num('cycles_per_day', '일일 사이클', 10)}
        {num('working_days_per_year', '연간 가동일', 5)}
        <label>환경
          <select value={v.environment} onChange={(e) => setV({ ...v, environment: e.target.value })}>
            <option value="clean">청정 (클린룸)</option>
            <option value="normal">일반</option>
            <option value="dusty">분진</option>
            <option value="corrosive">부식성 (염분 등)</option>
          </select>
        </label>
        {num('required_sf', '요구 안전율', 0.5)}
      </div>
      <button onClick={run}>계산</button>
      {err && <div className="error">{err}</div>}

      {r && !r.error && (
        <>
          <div className="result-box">
            <div className="big">
              SF {r.safety_factor} <span className={judgeClass(r.sf_pass ? 'OK' : 'NG')}>{r.sf_pass ? '안전율 충족' : '안전율 미달'}</span>{' '}
              · 폐기기준 도달 <b>{r.discard_life_years}년</b> · 계획교체 권고 <b>{r.planned_replace_years}년</b>{' '}
              <span className={judgeClass(r.judgment)}>{r.judgment}</span>
            </div>
            <p style={{ margin: '6px 0' }}>
              줄당 장력 <b>{r.line_tension_kn} kN</b> (로프 자중 {r.rope_self_weight_kg}kg 포함) ·
              최소파단력 <b>{r.min_breaking_force_kn} kN</b> ·
              사이클당 굽힘 {r.bendings_per_cycle}회 · 폐기 도달 {r.discard_life_cycles?.toLocaleString()} 사이클
            </p>
            <p className="muted">{r.basis}</p>
            <p className="muted">⚠ {r.discard_criteria}</p>
          </div>

          <div className="row" style={{ marginTop: 12 }}>
            <div>
              <b style={{ fontSize: 13 }}>수명 vs D/d (시브비 민감도)</b>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={r.curves.life_vs_dd}>
                  <XAxis dataKey="x" fontSize={11} label={{ value: 'D/d', position: 'insideBottomRight', fontSize: 11 }} />
                  <YAxis fontSize={11} label={{ value: '년', angle: -90, position: 'insideLeft', fontSize: 11 }} />
                  <Tooltip />
                  <ReferenceLine x={v.d_over_d} stroke="#dc2626" strokeDasharray="4 4" label={{ value: '현재', fontSize: 10 }} />
                  <Line type="monotone" dataKey="years" stroke="#2563eb" dot={false} strokeWidth={2} name="폐기수명(년)" />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <div>
              <b style={{ fontSize: 13 }}>수명 vs 로프 직경</b>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={r.curves.life_vs_diameter}>
                  <XAxis dataKey="x" fontSize={11} label={{ value: 'd (mm)', position: 'insideBottomRight', fontSize: 11 }} />
                  <YAxis fontSize={11} />
                  <Tooltip />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <ReferenceLine x={v.rope_diameter_mm} stroke="#dc2626" strokeDasharray="4 4" />
                  <Line type="monotone" dataKey="years" stroke="#2563eb" dot strokeWidth={2} name="폐기수명(년)" />
                  <Line type="monotone" dataKey="sf" stroke="#059669" dot strokeWidth={1.5} name="안전율" />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <div>
              <b style={{ fontSize: 13 }}>체결 줄수별 장력·안전율</b>
              <table style={{ marginTop: 8 }}>
                <thead><tr><th>줄수</th><th>줄당 장력(kN)</th><th>안전율</th><th>판정</th></tr></thead>
                <tbody>
                  {r.curves.tension_vs_falls.map((f: any) => (
                    <tr key={f.falls} style={{ background: f.falls === v.falls ? '#eff6ff' : undefined }}>
                      <td>{f.falls}{f.falls === v.falls && ' ◀ 현재'}</td>
                      <td>{f.tension_kn}</td><td>{f.sf}</td>
                      <td><span className={judgeClass(f.sf >= v.required_sf ? 'OK' : 'NG')}>{f.sf >= v.required_sf ? 'OK' : 'NG'}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

type Field = { key: string; label: string; def: number | string }

const CALCS: { id: string; title: string; endpoint: string; fields: Field[] }[] = [
  {
    id: 'wire', title: '와이어로프 안전율 / 수명', endpoint: '/engineering/wire-rope',
    fields: [
      { key: 'breaking_load_kn', label: '파단하중 (kN/본)', def: 85 },
      { key: 'rope_count', label: '로프 본수', def: 2 },
      { key: 'working_load_kn', label: '최대 사용하중 (kN)', def: 25 },
      { key: 'd_over_d', label: 'D/d (시브경/로프경)', def: 25 },
      { key: 'cycles_per_day', label: '일일 권상 사이클', def: 200 },
      { key: 'required_sf', label: '요구 안전율', def: 5 },
    ],
  },
  {
    id: 'bearing', title: '베어링 L10 수명', endpoint: '/engineering/bearing',
    fields: [
      { key: 'dynamic_load_c_kn', label: '동정격하중 C (kN)', def: 62 },
      { key: 'equivalent_load_p_kn', label: '등가 동하중 P (kN)', def: 6 },
      { key: 'rpm', label: '회전수 (rpm)', def: 1450 },
      { key: 'bearing_type', label: '형식 (ball/roller)', def: 'ball' },
      { key: 'operated_hours', label: '누적 가동시간 (h)', def: 0 },
      { key: 'annual_run_hours', label: '연간 가동시간 (h)', def: 6000 },
    ],
  },
  {
    id: 'battery', title: '배터리 수명 / SOH', endpoint: '/engineering/battery',
    fields: [
      { key: 'rated_cycles', label: '정격 사이클 (80% DOD)', def: 3000 },
      { key: 'dod_percent', label: '운용 DOD (%)', def: 80 },
      { key: 'cycles_per_day', label: '일일 충방전 사이클', def: 4 },
      { key: 'calendar_life_years', label: '캘린더 수명 (년)', def: 8 },
      { key: 'used_years', label: '사용 경과 (년)', def: 0 },
    ],
  },
  {
    id: 'wheel', title: '휠 마모 안전연수', endpoint: '/engineering/wheel',
    fields: [
      { key: 'initial_diameter_mm', label: '신품 직경 (mm)', def: 80 },
      { key: 'current_diameter_mm', label: '현재 직경 (mm)', def: 78 },
      { key: 'wear_limit_diameter_mm', label: '마모한계 직경 (mm)', def: 76 },
      { key: 'wear_rate_mm_per_year', label: '연간 마모율 (mm/년)', def: 1.0 },
      { key: 'safety_margin', label: '안전계수', def: 0.8 },
    ],
  },
]

function Calculator({ calc }: { calc: (typeof CALCS)[0] }) {
  const [values, setValues] = useState<Record<string, string>>(
    Object.fromEntries(calc.fields.map((f) => [f.key, String(f.def)])),
  )
  const [result, setResult] = useState<any>(null)
  const [err, setErr] = useState('')

  const run = async () => {
    setErr('')
    try {
      const body = Object.fromEntries(
        Object.entries(values).map(([k, v]) => [k, isNaN(Number(v)) ? v : Number(v)]),
      )
      setResult(await api.post(calc.endpoint, body))
    } catch (e: any) { setErr(e.message) }
  }

  return (
    <div className="panel">
      <h3 style={{ marginTop: 0 }}>{calc.title}</h3>
      <div className="form-grid">
        {calc.fields.map((f) => (
          <label key={f.key}>{f.label}
            <input value={values[f.key]} onChange={(e) => setValues({ ...values, [f.key]: e.target.value })} />
          </label>
        ))}
      </div>
      <button onClick={run}>계산</button>
      {err && <div className="error">{err}</div>}
      {result && (
        <div className="result-box">
          {result.judgment && <div className="big"><span className={judgeClass(result.judgment)}>{result.judgment}</span></div>}
          <table style={{ marginTop: 8, boxShadow: 'none' }}>
            <tbody>
              {Object.entries(result).filter(([k]) => k !== 'basis' && k !== 'judgment').map(([k, v]) => (
                <tr key={k}><td className="muted">{k}</td><td><b>{String(v)}</b></td></tr>
              ))}
            </tbody>
          </table>
          {result.basis && <p className="muted" style={{ marginBottom: 0 }}>근거: {result.basis}</p>}
        </div>
      )}
    </div>
  )
}

// ── 블럭형 PRO 계산기: 설정(fields/endpoint/curve)만 추가하면 새 툴 블럭이 생성됨 ──
type ProField = { key: string; label: string; def: number | string; step?: number; options?: { v: string | number; label: string }[] }
type ProConfig = {
  id: string; title: string; endpoint: string; note: string
  fields: ProField[]
  curveKey: string; curveName: string; curveX: string; curveSeries: { key: string; name: string; color: string }[]
  summary: (r: any) => string
}

const PRO_BLOCKS: ProConfig[] = [
  {
    id: 'motor', title: '⚡ 모터 용량 산정 (주행/권상)', endpoint: '/engineering/motor',
    note: '주행: F=mgμ+ma, 권상: F=mg(+ma). SF 적용 후 표준 모터 용량 추천. 인버터 과부하율·브레이크 토크는 별도 검토.',
    fields: [
      { key: 'mode', label: '구동 종류', def: 'travel', options: [{ v: 'travel', label: '주행' }, { v: 'hoist', label: '권상' }] },
      { key: 'mass_kg', label: '총 질량 (kg)', def: 5000, step: 100 },
      { key: 'speed_m_min', label: '속도 (m/min)', def: 120, step: 10 },
      { key: 'accel_m_s2', label: '가속도 (m/s²)', def: 0.5, step: 0.1 },
      { key: 'rolling_resistance', label: '주행저항계수', def: 0.015, step: 0.005 },
      { key: 'efficiency', label: '효율', def: 0.85, step: 0.05 },
      { key: 'service_factor', label: '서비스팩터', def: 1.2, step: 0.1 },
    ],
    curveKey: 'power_vs_speed', curveName: '속도 vs 필요출력', curveX: 'x',
    curveSeries: [{ key: 'required_kw', name: '필요(kW)', color: '#2563eb' }, { key: 'steady_kw', name: '정상(kW)', color: '#059669' }],
    summary: (r) => `정상 ${r.steady_kw}kW · 피크 ${r.peak_kw}kW → 필요 ${r.required_kw}kW → 추천 모터 ${r.recommended_motor_kw}kW`,
  },
  {
    id: 'conveyor', title: '📦 컨베이어 구동 출력', endpoint: '/engineering/conveyor',
    note: 'P = [μ·g·이동질량·v + Q·g·H]/η × SF (CEMA 개념 간이식). 정밀 설계는 제조사 프로그램 검증.',
    fields: [
      { key: 'belt_speed_m_min', label: '벨트 속도 (m/min)', def: 30, step: 5 },
      { key: 'length_m', label: '길이 (m)', def: 20, step: 5 },
      { key: 'moving_mass_kg', label: '이동부 질량 (kg)', def: 400, step: 50 },
      { key: 'capacity_t_h', label: '반송능력 (t/h)', def: 30, step: 5 },
      { key: 'lift_height_m', label: '양정 (m)', def: 0, step: 0.5 },
      { key: 'friction_coeff', label: '마찰계수', def: 0.03, step: 0.005 },
      { key: 'efficiency', label: '효율', def: 0.85, step: 0.05 },
    ],
    curveKey: 'power_vs_capacity', curveName: '반송능력 vs 필요출력', curveX: 'x',
    curveSeries: [{ key: 'required_kw', name: '필요(kW)', color: '#2563eb' }],
    summary: (r) => `마찰 ${r.friction_kw}kW + 양정 ${r.lift_kw}kW → 필요 ${r.required_kw}kW → 추천 모터 ${r.recommended_motor_kw}kW`,
  },
  {
    id: 'chain', title: '⛓ 리프 체인 수명 (신율 추세)', endpoint: '/engineering/chain',
    note: 'SF = MBL/줄당장력 (법규 5 이상). 신율 2% 교체계획 / 3% 즉시교체 (FLTA). 신율 측정 이력으로 진행률 입력.',
    fields: [
      { key: 'load_kg', label: '가반하중 (kg)', def: 1500, step: 100 },
      { key: 'carriage_weight_kg', label: '캐리지 자중 (kg)', def: 500, step: 50 },
      { key: 'chain_count', label: '체인 줄수', def: 2, step: 1 },
      { key: 'dynamic_factor', label: '동적계수', def: 1.3, step: 0.05 },
      { key: 'mbl_kn', label: 'MBL (kN/줄)', def: 100, step: 10 },
      { key: 'current_elongation_pct', label: '현재 신율 (%)', def: 0.8, step: 0.1 },
      { key: 'elongation_rate_pct_year', label: '신율 진행률 (%/년)', def: 0.3, step: 0.05 },
    ],
    curveKey: 'elongation_projection', curveName: '신율 진행 예측 (년)', curveX: 'x',
    curveSeries: [{ key: 'elongation_pct', name: '신율(%)', color: '#2563eb' }],
    summary: (r) => `SF ${r.safety_factor} · 강도손실 ~${r.estimated_strength_loss_pct}% · 2%(교체계획) ${r.years_to_plan_2pct}년 · 3%(한계) ${r.years_to_limit_3pct}년`,
  },
]

function ProBlock({ cfg }: { cfg: ProConfig }) {
  const [v, setV] = useState<Record<string, any>>(
    Object.fromEntries(cfg.fields.map((f) => [f.key, f.def])))
  const [r, setR] = useState<any>(null)
  const [err, setErr] = useState('')

  const run = async () => {
    setErr('')
    try {
      const body = Object.fromEntries(Object.entries(v).map(([k, x]) =>
        [k, typeof x === 'string' && !isNaN(Number(x)) && x !== '' ? Number(x) : x]))
      setR(await api.post(cfg.endpoint, body))
    } catch (e: any) { setErr(e.message) }
  }
  useEffect(() => { run() }, [])

  return (
    <div className="panel" style={{ borderLeft: '4px solid #059669' }}>
      <h3 style={{ marginTop: 0 }}>{cfg.title}</h3>
      <p className="muted">{cfg.note}</p>
      <div className="form-grid">
        {cfg.fields.map((f) => (
          <label key={f.key}>{f.label}
            {f.options ? (
              <select value={v[f.key]} onChange={(e) => setV({ ...v, [f.key]: e.target.value })}>
                {f.options.map((o) => <option key={o.v} value={o.v}>{o.label}</option>)}
              </select>
            ) : (
              <input type="number" step={f.step ?? 1} value={v[f.key]}
                onChange={(e) => setV({ ...v, [f.key]: e.target.value })} />
            )}
          </label>
        ))}
      </div>
      <button onClick={run}>계산</button>
      {err && <div className="error">{err}</div>}
      {r && !r.error && (
        <div className="result-box">
          <div className="big"><span className={judgeClass(r.judgment)}>{r.judgment}</span> {cfg.summary(r)}</div>
          {r.curves?.[cfg.curveKey] && (
            <ResponsiveContainer width="100%" height={180}>
              <LineChart data={r.curves[cfg.curveKey]}>
                <XAxis dataKey={cfg.curveX} fontSize={11} />
                <YAxis fontSize={11} />
                <Tooltip />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                {cfg.curveSeries.map((s) => (
                  <Line key={s.key} type="monotone" dataKey={s.key} stroke={s.color} dot={false} strokeWidth={2} name={s.name} />
                ))}
              </LineChart>
            </ResponsiveContainer>
          )}
          <p className="muted" style={{ marginBottom: 0 }}>근거: {r.basis}</p>
        </div>
      )}
    </div>
  )
}

export default function Engineering() {
  return (
    <div>
      <h2>설비 엔지니어링 검토</h2>
      <p className="muted">간이 수명모델 기반 검토용입니다. 결과는 FDC 실측 데이터와 병행하여 판단하세요. 산식 근거는 [지식 DB] 참조.</p>
      <WireRopePro />
      {PRO_BLOCKS.map((b) => <ProBlock key={b.id} cfg={b} />)}
      <div className="row">
        {CALCS.map((c) => <Calculator key={c.id} calc={c} />)}
      </div>
    </div>
  )
}

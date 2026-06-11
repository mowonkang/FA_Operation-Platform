import { useState } from 'react'
import { api, judgeClass } from '../api'

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

export default function Engineering() {
  return (
    <div>
      <h2>설비 엔지니어링 검토</h2>
      <p className="muted">간이 수명모델 기반 검토용입니다. 결과는 FDC 실측 데이터와 병행하여 판단하세요.</p>
      <div className="row">
        {CALCS.map((c) => <Calculator key={c.id} calc={c} />)}
      </div>
    </div>
  )
}

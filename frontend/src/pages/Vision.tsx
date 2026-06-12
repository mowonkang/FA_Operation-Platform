import { useEffect, useState } from 'react'
import { api, judgeClass } from '../api'

const KINDS = [
  { v: 'WEAR', label: '마모율 (%)' },
  { v: 'CORROSION', label: '부식률 (%)' },
  { v: 'DIMENSION', label: '치수 (mm)' },
  { v: 'ALIGNMENT', label: '정렬 편차 (deg)' },
]

export default function Vision() {
  const [eqs, setEqs] = useState<any[]>([])
  const [standards, setStandards] = useState<any[]>([])
  const [history, setHistory] = useState<any[]>([])
  const [kind, setKind] = useState('WEAR')
  const [eqId, setEqId] = useState('')
  const [stdId, setStdId] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [result, setResult] = useState<any>(null)
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)

  const load = () => {
    api.get('/equipments').then(setEqs)
    api.get('/pm/standards').then((s) => setStandards(s.filter((x: any) => x.vision_capable)))
    api.get('/vision/inspections').then(setHistory)
  }
  useEffect(load, [])

  const inspect = async () => {
    if (!file) return
    setBusy(true); setErr(''); setResult(null)
    try {
      const form = new FormData()
      form.append('file', file)
      form.append('kind', kind)
      if (eqId) form.append('equipment_id', eqId)
      if (stdId) form.append('standard_item_id', stdId)
      const r = await api.upload('/vision/inspect', form)
      setResult(r)
      load()
    } catch (e: any) { setErr(e.message) } finally { setBusy(false) }
  }

  return (
    <div>
      <h2>비전 측정 (PM/BM 설비 상태)</h2>
      <div className="row">
        <div className="panel">
          <h3 style={{ marginTop: 0 }}>이미지 업로드 → 자동 측정/판정</h3>
          <div className="form-grid">
            <label>측정 종류
              <select value={kind} onChange={(e) => { setKind(e.target.value); setStdId('') }}>
                {KINDS.map((k) => <option key={k.v} value={k.v}>{k.label}</option>)}
              </select>
            </label>
            <label>설비 (선택)
              <select value={eqId} onChange={(e) => setEqId(e.target.value)}>
                <option value="">미지정</option>
                {eqs.map((e) => <option key={e.id} value={e.id}>{e.asset_code}</option>)}
              </select>
            </label>
            <label>PM 표준항목 연계 (레시피·한계값 자동 적용)
              <select value={stdId} onChange={(e) => {
                setStdId(e.target.value)
                const s = standards.find((x) => x.id === Number(e.target.value))
                if (s?.vision_recipe?.kind) setKind(s.vision_recipe.kind)
              }}>
                <option value="">미연계</option>
                {standards.map((s) => <option key={s.id} value={s.id}>{s.item_no} {s.name}</option>)}
              </select>
            </label>
            <label>이미지 파일
              <input type="file" accept="image/*" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
            </label>
          </div>
          <button disabled={!file || busy} onClick={inspect}>{busy ? '분석중…' : '측정 실행'}</button>
          {err && <div className="error">{err}</div>}
          {result && (
            <div className="result-box">
              <div className="big">{result.measured_value ?? '측정 실패'} {result.unit}{' '}
                <span className={judgeClass(result.judgment)}>{result.judgment}</span></div>
              <pre style={{ fontSize: 11, overflow: 'auto' }}>{JSON.stringify(result.detail, null, 2)}</pre>
            </div>
          )}
          <p className="muted">
            DIMENSION 측정 시 기준 스케일(예: 50mm 마커)을 함께 촬영하고 레시피의
            ref_length_mm / ref_length_px 로 캘리브레이션합니다. 자세한 방법: docs/03_VISION_INSPECTION.md
          </p>
        </div>

        <div className="panel">
          <h3 style={{ marginTop: 0 }}>측정 이력</h3>
          <table>
            <thead><tr><th>#</th><th>일시</th><th>설비</th><th>종류</th><th>측정값</th><th>판정</th></tr></thead>
            <tbody>
              {history.map((h) => (
                <tr key={h.id}>
                  <td>{h.id}</td>
                  <td>{h.created_at?.slice(0, 16).replace('T', ' ')}</td>
                  <td>{eqs.find((e) => e.id === h.equipment_id)?.asset_code ?? '-'}</td>
                  <td>{h.kind}</td>
                  <td>{h.measured_value ?? '-'} {h.unit}</td>
                  <td><span className={judgeClass(h.judgment)}>{h.judgment}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

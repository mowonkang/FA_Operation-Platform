import { useEffect, useState } from 'react'
import { api } from '../api'

export default function BM() {
  const [reports, setReports] = useState<any[]>([])
  const [eqs, setEqs] = useState<any[]>([])
  const [parts, setParts] = useState<any[]>([])
  const [form, setForm] = useState({ equipment_id: '', symptom: '', reported_by: '' })
  const [edit, setEdit] = useState<any>(null)

  const load = () => {
    api.get('/bm/reports').then(setReports)
    api.get('/equipments').then(setEqs)
    api.get('/parts').then(setParts)
  }
  useEffect(load, [])

  const create = async () => {
    await api.post('/bm/reports', { ...form, equipment_id: Number(form.equipment_id) })
    setForm({ equipment_id: '', symptom: '', reported_by: '' })
    load()
  }

  const save = async () => {
    await api.patch(`/bm/reports/${edit.id}`, {
      cause: edit.cause, action: edit.action, downtime_min: Number(edit.downtime_min || 0),
      failure_part_id: edit.failure_part_id ? Number(edit.failure_part_id) : null,
      status: edit.status,
    })
    setEdit(null)
    load()
  }

  return (
    <div>
      <h2>BM (사후정비)</h2>
      <div className="panel">
        <h3 style={{ marginTop: 0 }}>고장 보고 등록</h3>
        <div className="form-grid">
          <label>설비
            <select value={form.equipment_id} onChange={(e) => setForm({ ...form, equipment_id: e.target.value })}>
              <option value="">선택</option>
              {eqs.map((e) => <option key={e.id} value={e.id}>{e.asset_code}</option>)}
            </select>
          </label>
          <label>증상<input value={form.symptom} onChange={(e) => setForm({ ...form, symptom: e.target.value })} /></label>
          <label>보고자<input value={form.reported_by} onChange={(e) => setForm({ ...form, reported_by: e.target.value })} /></label>
        </div>
        <button disabled={!form.equipment_id || !form.symptom} onClick={create}>등록 (설비상태 BM 전환)</button>
      </div>

      <table>
        <thead><tr><th>#</th><th>설비</th><th>발생</th><th>증상</th><th>원인</th><th>조치</th><th>다운타임</th><th>상태</th><th>연계</th><th></th></tr></thead>
        <tbody>
          {reports.map((r) => (
            <tr key={r.id}>
              <td>{r.id}</td><td>{r.equipment.asset_code}</td>
              <td>{r.occurred_at?.slice(0, 16).replace('T', ' ')}</td>
              <td>{r.symptom}</td><td>{r.cause || '-'}</td><td>{r.action || '-'}</td>
              <td>{r.downtime_min}분</td>
              <td><span className={`badge ${r.status === 'CLOSED' || r.status === 'FIXED' ? 'ok' : 'ng'}`}>{r.status}</span></td>
              <td>
                {r.fdc_alarm_id && <span className="badge info">FDC#{r.fdc_alarm_id}</span>}{' '}
                {r.lesson_id && <span className="badge check">L&L#{r.lesson_id}</span>}
              </td>
              <td>{r.status !== 'CLOSED' && <button className="secondary" onClick={() => setEdit({ ...r })}>처리</button>}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {edit && (
        <div className="panel" style={{ marginTop: 16 }}>
          <h3 style={{ marginTop: 0 }}>BM #{edit.id} 처리 — {edit.equipment.asset_code}</h3>
          <div className="form-grid">
            <label>원인<input value={edit.cause ?? ''} onChange={(e) => setEdit({ ...edit, cause: e.target.value })} /></label>
            <label>조치<input value={edit.action ?? ''} onChange={(e) => setEdit({ ...edit, action: e.target.value })} /></label>
            <label>다운타임(분)<input type="number" value={edit.downtime_min ?? 0} onChange={(e) => setEdit({ ...edit, downtime_min: e.target.value })} /></label>
            <label>고장 파츠 (완료 시 재고 1개 차감)
              <select value={edit.failure_part_id ?? ''} onChange={(e) => setEdit({ ...edit, failure_part_id: e.target.value })}>
                <option value="">없음</option>
                {parts.map((p) => <option key={p.id} value={p.id}>{p.part_no} (재고 {p.current_stock})</option>)}
              </select>
            </label>
            <label>상태
              <select value={edit.status} onChange={(e) => setEdit({ ...edit, status: e.target.value })}>
                {['OPEN', 'ANALYZING', 'FIXED', 'CLOSED'].map((s) => <option key={s}>{s}</option>)}
              </select>
            </label>
          </div>
          <button onClick={save}>저장</button>{' '}
          <button className="secondary" onClick={() => setEdit(null)}>취소</button>
        </div>
      )}
    </div>
  )
}

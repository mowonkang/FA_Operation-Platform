import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api, STAGE_LABEL, STATUS_LABEL } from '../api'

export default function EquipmentDetail() {
  const { id } = useParams()
  const [eq, setEq] = useState<any>(null)
  const [events, setEvents] = useState<any[]>([])
  const [params, setParams] = useState<any[]>([])
  const [showAllVersions, setShowAllVersions] = useState(false)
  const [evForm, setEvForm] = useState({ stage: 'DR', title: '', detail: '', doc_ref: '', performed_by: '' })
  const [pForm, setPForm] = useState({ name: '', value: '', unit: '', set_by: '', note: '' })

  const load = () => {
    api.get(`/equipments/${id}`).then(setEq)
    api.get(`/equipments/${id}/lifecycle`).then(setEvents)
    api.get(`/equipments/${id}/parameters?all_versions=${showAllVersions}`).then(setParams)
  }
  useEffect(load, [id, showAllVersions])

  if (!eq) return <p>로딩중…</p>

  const addEvent = async () => {
    await api.post('/lifecycle', { ...evForm, equipment_id: Number(id) })
    setEvForm({ stage: 'DR', title: '', detail: '', doc_ref: '', performed_by: '' })
    load()
  }
  const addParam = async () => {
    await api.post('/parameters', { ...pForm, equipment_id: Number(id) })
    setPForm({ name: '', value: '', unit: '', set_by: '', note: '' })
    load()
  }

  return (
    <div>
      <h2>{eq.asset_code} <span className="badge info">{STATUS_LABEL[eq.status] ?? eq.status}</span></h2>
      <p className="muted">{eq.model.name} ({eq.model.category}) · {eq.site.name} · 라인 {eq.line} · 연간 가동 {eq.annual_run_hours}h</p>

      <div className="row">
        <div className="panel">
          <h3 style={{ marginTop: 0 }}>생애주기 이력 (DR → 제작 → 셋업 → PM/BM)</h3>
          <ul className="timeline">
            {events.map((ev) => (
              <li key={ev.id}>
                <div className="date">{ev.event_date} · {STAGE_LABEL[ev.stage] ?? ev.stage}{ev.performed_by && ` · ${ev.performed_by}`}</div>
                <div className="title">{ev.title}</div>
                {ev.detail && <div className="detail">{ev.detail}</div>}
                {ev.doc_ref && <div className="detail">문서: {ev.doc_ref}</div>}
              </li>
            ))}
          </ul>
          <h3>이력 추가</h3>
          <div className="form-grid">
            <label>단계
              <select value={evForm.stage} onChange={(e) => setEvForm({ ...evForm, stage: e.target.value })}>
                {Object.entries(STAGE_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select>
            </label>
            <label>제목<input value={evForm.title} onChange={(e) => setEvForm({ ...evForm, title: e.target.value })} /></label>
            <label>상세<input value={evForm.detail} onChange={(e) => setEvForm({ ...evForm, detail: e.target.value })} /></label>
            <label>문서번호<input value={evForm.doc_ref} onChange={(e) => setEvForm({ ...evForm, doc_ref: e.target.value })} /></label>
            <label>수행자<input value={evForm.performed_by} onChange={(e) => setEvForm({ ...evForm, performed_by: e.target.value })} /></label>
          </div>
          <button disabled={!evForm.title} onClick={addEvent}>추가</button>
        </div>

        <div className="panel">
          <h3 style={{ marginTop: 0 }}>
            Install Parameter{' '}
            <label style={{ fontWeight: 400, fontSize: 12 }}>
              <input type="checkbox" checked={showAllVersions}
                onChange={(e) => setShowAllVersions(e.target.checked)} /> 전체 버전 이력
            </label>
          </h3>
          <table>
            <thead><tr><th>파라미터</th><th>값</th><th>버전</th><th>설정자</th><th>일시</th></tr></thead>
            <tbody>
              {params.map((p) => (
                <tr key={p.id} style={{ opacity: p.is_current ? 1 : 0.55 }}>
                  <td>{p.name}</td><td>{p.value} {p.unit}</td>
                  <td>v{p.version}{p.is_current && ' (현재)'}</td>
                  <td>{p.set_by}</td><td>{p.set_at?.slice(0, 16).replace('T', ' ')}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <h3>파라미터 설정 (변경 시 새 버전 적재)</h3>
          <div className="form-grid">
            <label>이름<input value={pForm.name} onChange={(e) => setPForm({ ...pForm, name: e.target.value })} /></label>
            <label>값<input value={pForm.value} onChange={(e) => setPForm({ ...pForm, value: e.target.value })} /></label>
            <label>단위<input value={pForm.unit} onChange={(e) => setPForm({ ...pForm, unit: e.target.value })} /></label>
            <label>설정자<input value={pForm.set_by} onChange={(e) => setPForm({ ...pForm, set_by: e.target.value })} /></label>
          </div>
          <button disabled={!pForm.name || !pForm.value} onClick={addParam}>설정</button>
        </div>
      </div>
    </div>
  )
}

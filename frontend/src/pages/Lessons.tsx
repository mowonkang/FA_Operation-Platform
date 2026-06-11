import { useEffect, useState } from 'react'
import { api } from '../api'

const DEP_STATUS = ['NOTIFIED', 'REVIEWING', 'APPLIED', 'NA']
const DEP_LABEL: Record<string, string> = {
  NOTIFIED: '통보', REVIEWING: '검토중', APPLIED: '적용완료', NA: '해당없음',
}

export default function Lessons() {
  const [lessons, setLessons] = useState<any[]>([])
  const [sites, setSites] = useState<any[]>([])
  const [models, setModels] = useState<any[]>([])
  const [form, setForm] = useState({
    title: '', category: 'DOWNTIME', model_id: '', problem: '', root_cause: '',
    countermeasure: '', origin_site_id: '', created_by: '',
  })

  const load = () => {
    api.get('/lessons').then(setLessons)
    api.get('/sites').then(setSites)
    api.get('/models').then(setModels)
  }
  useEffect(load, [])

  const create = async () => {
    await api.post('/lessons', {
      ...form,
      model_id: form.model_id ? Number(form.model_id) : null,
      origin_site_id: Number(form.origin_site_id),
    })
    setForm({ title: '', category: 'DOWNTIME', model_id: '', problem: '', root_cause: '', countermeasure: '', origin_site_id: '', created_by: '' })
    load()
  }

  const updateDep = async (depId: number, status: string) => {
    await api.patch(`/lessons/deployments/${depId}`, { status })
    load()
  }

  return (
    <div>
      <h2>Lesson & Learn — 다법인 확산</h2>
      <div className="panel">
        <h3 style={{ marginTop: 0 }}>등록 (등록 시 전 법인에 자동 전파)</h3>
        <div className="form-grid">
          <label>제목<input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} /></label>
          <label>카테고리
            <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
              {['SAFETY', 'QUALITY', 'DOWNTIME', 'COST'].map((c) => <option key={c}>{c}</option>)}
            </select>
          </label>
          <label>설비 모델
            <select value={form.model_id} onChange={(e) => setForm({ ...form, model_id: e.target.value })}>
              <option value="">공통</option>
              {models.map((m) => <option key={m.id} value={m.id}>{m.code}</option>)}
            </select>
          </label>
          <label>발생 법인
            <select value={form.origin_site_id} onChange={(e) => setForm({ ...form, origin_site_id: e.target.value })}>
              <option value="">선택</option>
              {sites.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
          </label>
          <label>작성자<input value={form.created_by} onChange={(e) => setForm({ ...form, created_by: e.target.value })} /></label>
          <label>문제<input value={form.problem} onChange={(e) => setForm({ ...form, problem: e.target.value })} /></label>
          <label>근본원인<input value={form.root_cause} onChange={(e) => setForm({ ...form, root_cause: e.target.value })} /></label>
          <label>대책<input value={form.countermeasure} onChange={(e) => setForm({ ...form, countermeasure: e.target.value })} /></label>
        </div>
        <button disabled={!form.title || !form.problem || !form.origin_site_id} onClick={create}>등록 + 전파</button>
      </div>

      {lessons.map((l) => (
        <div className="panel" key={l.id}>
          <h3 style={{ marginTop: 0 }}>
            #{l.id} {l.title}{' '}
            <span className="badge gray">{l.category}</span>{' '}
            {l.std_reflected && <span className="badge ok">PM 표준 반영</span>}
          </h3>
          <p className="muted">발생: {l.origin_site.name} · {l.created_by} · {l.created_at?.slice(0, 10)}</p>
          <table style={{ marginBottom: 12 }}>
            <tbody>
              <tr><th style={{ width: 100 }}>문제</th><td>{l.problem}</td></tr>
              <tr><th>근본원인</th><td>{l.root_cause}</td></tr>
              <tr><th>대책</th><td>{l.countermeasure}</td></tr>
            </tbody>
          </table>
          <b style={{ fontSize: 13 }}>법인별 전파 현황</b>
          <table>
            <thead><tr><th>법인</th><th>상태</th><th>적용일</th><th>비고</th><th>변경</th></tr></thead>
            <tbody>
              {l.deployments.map((d: any) => (
                <tr key={d.id}>
                  <td>{d.site.name}</td>
                  <td><span className={`badge ${d.status === 'APPLIED' ? 'ok' : d.status === 'NOTIFIED' ? 'ng' : 'check'}`}>
                    {DEP_LABEL[d.status]}</span></td>
                  <td>{d.applied_date ?? '-'}</td><td>{d.note}</td>
                  <td>
                    <select value={d.status} onChange={(e) => updateDep(d.id, e.target.value)}>
                      {DEP_STATUS.map((s) => <option key={s} value={s}>{DEP_LABEL[s]}</option>)}
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </div>
  )
}

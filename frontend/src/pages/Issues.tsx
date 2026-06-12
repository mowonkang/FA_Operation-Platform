import { useEffect, useState } from 'react'
import { api } from '../api'
import { useSite, sq } from '../site'

const STATUS_LABEL: Record<string, string> = { OPEN: '미결', IN_PROGRESS: '진행중', CLOSED: '완료' }

export default function Issues() {
  const { site } = useSite()
  const [domains, setDomains] = useState<any[]>([])
  const [stats, setStats] = useState<any>(null)
  const [list, setList] = useState<any[]>([])
  const [eqs, setEqs] = useState<any[]>([])
  const [filter, setFilter] = useState('')
  const [form, setForm] = useState({ domain: 'MECH', severity: 'MID', title: '', description: '',
    equipment_id: '', owner: '', phase: 'SETUP' })
  const [edit, setEdit] = useState<any>(null)

  const load = () => {
    api.get('/issues/domains').then(setDomains)
    api.get('/issues/stats').then(setStats)
    api.get(sq(site, `/issues${filter ? `?domain=${filter}` : ''}`)).then(setList)
    api.get(`/equipments${sq(site)}`).then(setEqs)
  }
  useEffect(load, [filter, site])

  const create = async () => {
    await api.post('/issues', {
      ...form, equipment_id: form.equipment_id ? Number(form.equipment_id) : null,
    })
    setForm({ ...form, title: '', description: '' })
    load()
  }

  const save = async () => {
    await api.patch(`/issues/${edit.id}`, {
      status: edit.status, resolution: edit.resolution, owner: edit.owner,
    })
    setEdit(null)
    load()
  }

  const sevBadge = (s: string) => s === 'HIGH' ? 'ng' : s === 'MID' ? 'check' : 'gray'

  return (
    <div>
      <h2>이슈 관리 (설비 / 시스템 / 안전)</h2>
      <p className="muted">
        설비(기구·전장·제어·인터락), 시스템(CIM·MCS·RTD), 안전, 기타 이슈를 분류 관리.
        안전 이슈는 자동 HIGH. 미결 HIGH 이슈가 있으면 안정화 판정을 보류하세요.
      </p>

      {stats && (
        <div className="cards" style={{ marginBottom: 14 }}>
          <div className="card"><div className="label">미결 HIGH</div>
            <div className={`value ${stats.high_open > 0 ? 'bad' : 'good'}`}>{stats.high_open}</div></div>
          {stats.by_domain.map((d: any) => (
            <div className="card" key={d.domain}>
              <div className="label">{d.label}</div>
              <div className="value" style={{ fontSize: 18 }}>
                <span style={{ color: '#ef4444' }}>{d.open}</span> / <span style={{ color: '#f59e0b' }}>{d.in_progress}</span> / <span style={{ color: '#22c55e' }}>{d.closed}</span>
              </div>
              <div className="muted">미결/진행/완료</div>
            </div>
          ))}
        </div>
      )}

      <div className="panel">
        <h3 style={{ marginTop: 0 }}>이슈 등록</h3>
        <div className="form-grid">
          <label>도메인
            <select value={form.domain} onChange={(e) => setForm({ ...form, domain: e.target.value })}>
              {domains.map((d) => <option key={d.code} value={d.code}>[{d.group}] {d.label}</option>)}
            </select>
          </label>
          <label>심각도
            <select value={form.severity} onChange={(e) => setForm({ ...form, severity: e.target.value })}>
              {['HIGH', 'MID', 'LOW'].map((s) => <option key={s}>{s}</option>)}
            </select>
          </label>
          <label>단계
            <select value={form.phase} onChange={(e) => setForm({ ...form, phase: e.target.value })}>
              {['INVEST', 'FABRICATION', 'SETUP', 'PRODUCTION'].map((s) => <option key={s}>{s}</option>)}
            </select>
          </label>
          <label>설비 (선택)
            <select value={form.equipment_id} onChange={(e) => setForm({ ...form, equipment_id: e.target.value })}>
              <option value="">없음</option>
              {eqs.map((e) => <option key={e.id} value={e.id}>{e.asset_code}</option>)}
            </select>
          </label>
          <label>제목<input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} /></label>
          <label>상세<input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></label>
          <label>담당<input value={form.owner} onChange={(e) => setForm({ ...form, owner: e.target.value })} /></label>
        </div>
        <button disabled={!form.title} onClick={create}>등록</button>
      </div>

      <p>
        <button className={filter === '' ? '' : 'secondary'} onClick={() => setFilter('')}>전체</button>{' '}
        {domains.map((d) => (
          <span key={d.code}>
            <button className={filter === d.code ? '' : 'secondary'} onClick={() => setFilter(d.code)}>{d.label}</button>{' '}
          </span>
        ))}
      </p>

      <table>
        <thead><tr><th>#</th><th>도메인</th><th>심각도</th><th>제목</th><th>설비</th><th>단계</th><th>담당</th><th>상태</th><th></th></tr></thead>
        <tbody>
          {list.map((i) => (
            <tr key={i.id}>
              <td>{i.id}</td>
              <td><span className="badge gray">{domains.find((d) => d.code === i.domain)?.label ?? i.domain}</span></td>
              <td><span className={`badge ${sevBadge(i.severity)}`}>{i.severity}</span></td>
              <td>{i.title}<div className="muted">{i.description}</div></td>
              <td>{eqs.find((e) => e.id === i.equipment_id)?.asset_code ?? '-'}</td>
              <td>{i.phase}</td><td>{i.owner || '-'}</td>
              <td><span className={`badge ${i.status === 'CLOSED' ? 'ok' : i.status === 'OPEN' ? 'ng' : 'check'}`}>{STATUS_LABEL[i.status]}</span></td>
              <td>{i.status !== 'CLOSED' && <button className="secondary" onClick={() => setEdit({ ...i })}>처리</button>}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {edit && (
        <div className="panel" style={{ marginTop: 14 }}>
          <h3 style={{ marginTop: 0 }}>이슈 #{edit.id} 처리 — {edit.title}</h3>
          <div className="form-grid">
            <label>상태
              <select value={edit.status} onChange={(e) => setEdit({ ...edit, status: e.target.value })}>
                {['OPEN', 'IN_PROGRESS', 'CLOSED'].map((s) => <option key={s} value={s}>{STATUS_LABEL[s]}</option>)}
              </select>
            </label>
            <label>담당<input value={edit.owner} onChange={(e) => setEdit({ ...edit, owner: e.target.value })} /></label>
            <label>해결 내용<input value={edit.resolution ?? ''} onChange={(e) => setEdit({ ...edit, resolution: e.target.value })} /></label>
          </div>
          <button onClick={save}>저장 {edit.status === 'CLOSED' && '(설비 이력에 자동 기록)'}</button>{' '}
          <button className="secondary" onClick={() => setEdit(null)}>취소</button>
        </div>
      )}
    </div>
  )
}

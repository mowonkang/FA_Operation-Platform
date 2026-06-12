import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, STATUS_LABEL } from '../api'
import { useSite, sq } from '../site'

export default function Equipment() {
  const [list, setList] = useState<any[]>([])
  const [models, setModels] = useState<any[]>([])
  const [sites, setSites] = useState<any[]>([])
  const [form, setForm] = useState({ asset_code: '', model_id: '', site_id: '', line: '' })
  const [err, setErr] = useState('')

  const { site } = useSite()
  const load = () => {
    api.get(`/equipments${sq(site)}`).then(setList)
    api.get('/models').then(setModels)
    api.get('/sites').then(setSites)
  }
  useEffect(load, [site])

  const create = async () => {
    setErr('')
    try {
      await api.post('/equipments', {
        ...form, model_id: Number(form.model_id), site_id: Number(form.site_id), status: 'DR',
      })
      setForm({ asset_code: '', model_id: '', site_id: '', line: '' })
      load()
    } catch (e: any) { setErr(e.message) }
  }

  return (
    <div>
      <h2>설비 마스터</h2>
      <div className="panel">
        <h3 style={{ marginTop: 0 }}>설비 등록 (DR 단계부터 시작)</h3>
        <div className="form-grid">
          <label>Asset Code
            <input value={form.asset_code} onChange={(e) => setForm({ ...form, asset_code: e.target.value })} />
          </label>
          <label>모델
            <select value={form.model_id} onChange={(e) => setForm({ ...form, model_id: e.target.value })}>
              <option value="">선택</option>
              {models.map((m) => <option key={m.id} value={m.id}>{m.code} ({m.category})</option>)}
            </select>
          </label>
          <label>법인
            <select value={form.site_id} onChange={(e) => setForm({ ...form, site_id: e.target.value })}>
              <option value="">선택</option>
              {sites.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
          </label>
          <label>라인
            <input value={form.line} onChange={(e) => setForm({ ...form, line: e.target.value })} />
          </label>
        </div>
        <button disabled={!form.asset_code || !form.model_id || !form.site_id} onClick={create}>등록</button>
        {err && <div className="error">{err}</div>}
      </div>

      <table>
        <thead>
          <tr><th>Asset Code</th><th>모델</th><th>분류</th><th>법인</th><th>라인</th><th>상태</th><th>설치일</th></tr>
        </thead>
        <tbody>
          {list.map((e) => (
            <tr key={e.id}>
              <td><Link to={`/equipment/${e.id}`}>{e.asset_code}</Link></td>
              <td>{e.model.name}</td>
              <td>{e.model.category}</td>
              <td>{e.site.name}</td>
              <td>{e.line}</td>
              <td><span className={`badge ${e.status === 'RUN' ? 'ok' : e.status === 'BM' ? 'ng' : 'info'}`}>
                {STATUS_LABEL[e.status] ?? e.status}</span></td>
              <td>{e.install_date ?? '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

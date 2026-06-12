import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { useSite, sq } from '../site'

const STATUS = [
  { v: 'PLANNING', label: '기획', cls: 'info' },
  { v: 'ONGOING', label: '진행중', cls: 'check' },
  { v: 'DONE', label: '완료', cls: 'ok' },
  { v: 'HOLD', label: '보류', cls: 'gray' },
]
const fmt = (n: number) => n?.toLocaleString(undefined, { maximumFractionDigits: 0 })

export default function Projects() {
  const { site } = useSite()
  const [list, setList] = useState<any[]>([])
  const [sites, setSites] = useState<any[]>([])
  const [sel, setSel] = useState<any>(null)
  const [summary, setSummary] = useState<any>(null)
  const [form, setForm] = useState<any>(null)   // 생성/수정 폼
  const [err, setErr] = useState('')
  const isAdmin = (localStorage.getItem('fa_role') ?? 'user') === 'admin'

  const load = () => {
    api.get(`/projects${sq(site)}`).then(setList)
    api.get('/sites').then(setSites)
  }
  useEffect(load, [site])

  const open = async (p: any) => {
    setSel(p)
    setForm(null)
    setSummary(await api.get(`/projects/${p.id}/summary`))
  }

  const save = async () => {
    setErr('')
    try {
      const body = { ...form, site_id: form.site_id ? Number(form.site_id) : null,
        budget: Number(form.budget || 0) }
      if (form.id) await api.patch(`/projects/${form.id}`, body)
      else await api.post('/projects', body)
      setForm(null)
      load()
    } catch (e: any) { setErr(e.message) }
  }

  const remove = async (p: any) => {
    if (!confirm(`프로젝트 '${p.name}' 을(를) 삭제할까요? (관리자 전용)`)) return
    setErr('')
    try {
      await api.del(`/projects/${p.id}`)
      setSel(null)
      load()
    } catch (e: any) { setErr(e.message) }
  }

  const statusOf = (v: string) => STATUS.find((s) => s.v === v) ?? STATUS[0]

  return (
    <div>
      <p className="page-desc">
        투자/구축 프로젝트의 관리 단위 — 견적 분석·설비 도입과 연결됩니다.
        생성·수정은 전체, <b>삭제는 관리자만</b> 가능합니다 (설정 ⚙ 에서 역할 변경).
      </p>
      <p>
        <button onClick={() => { setForm({ code: '', name: '', site_id: '', status: 'PLANNING',
          budget: 0, owner: '', start_date: null, end_date: null, description: '' }); setSel(null) }}>
          + 프로젝트 생성
        </button>
        {!isAdmin && <span className="muted" style={{ marginLeft: 10 }}>현재 역할: 일반 사용자 (삭제 불가)</span>}
      </p>
      {err && <div className="error">{err}</div>}

      {form && (
        <div className="panel">
          <div className="panel-title">{form.id ? `프로젝트 수정 — ${form.code}` : '새 프로젝트'}</div>
          <div className="form-grid">
            {!form.id && <label>코드 (고유)<input value={form.code} placeholder="P-2026-003"
              onChange={(e) => setForm({ ...form, code: e.target.value })} /></label>}
            <label>이름<input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></label>
            <label>사이트
              <select value={form.site_id ?? ''} onChange={(e) => setForm({ ...form, site_id: e.target.value })}>
                <option value="">미지정</option>
                {sites.map((s) => <option key={s.id} value={s.id}>{s.code} {s.name}</option>)}
              </select>
            </label>
            <label>상태
              <select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
                {STATUS.map((s) => <option key={s.v} value={s.v}>{s.label}</option>)}
              </select>
            </label>
            <label>예산 (원)<input type="number" value={form.budget}
              onChange={(e) => setForm({ ...form, budget: e.target.value })} /></label>
            <label>담당 PM<input value={form.owner} onChange={(e) => setForm({ ...form, owner: e.target.value })} /></label>
            <label>착수일<input type="date" value={form.start_date ?? ''}
              onChange={(e) => setForm({ ...form, start_date: e.target.value || null })} /></label>
            <label>완료 목표일<input type="date" value={form.end_date ?? ''}
              onChange={(e) => setForm({ ...form, end_date: e.target.value || null })} /></label>
            <label>설명<input value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })} /></label>
          </div>
          <button disabled={!form.name || (!form.id && !form.code)} onClick={save}>저장</button>{' '}
          <button className="secondary" onClick={() => setForm(null)}>취소</button>
        </div>
      )}

      <table>
        <thead><tr><th>코드</th><th>프로젝트</th><th>사이트</th><th>상태</th><th className="num">예산</th><th>PM</th><th>기간</th><th></th></tr></thead>
        <tbody>
          {list.map((p) => {
            const st = statusOf(p.status)
            return (
              <tr key={p.id} className={`clickable ${sel?.id === p.id ? 'selected' : ''}`} onClick={() => open(p)}>
                <td>{p.code}</td>
                <td><b>{p.name}</b><div className="muted">{p.description}</div></td>
                <td>{p.site?.code ?? '-'}</td>
                <td><span className={`badge ${st.cls}`}>{st.label}</span></td>
                <td className="num">{fmt(p.budget)}</td>
                <td>{p.owner || '-'}</td>
                <td>{p.start_date ?? '?'} ~ {p.end_date ?? '?'}</td>
                <td onClick={(e) => e.stopPropagation()}>
                  <button className="secondary" onClick={() => { setForm({ ...p, site_id: p.site_id ?? '' }); setSel(null) }}>수정</button>{' '}
                  {isAdmin && <button className="danger" onClick={() => remove(p)}>삭제</button>}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>

      {sel && summary && (
        <div className="panel" style={{ marginTop: 14 }}>
          <div className="panel-title">{sel.code} {sel.name} — 현황 요약</div>
          <div className="cards">
            <div className="card status-neutral"><div className="label">접수 견적</div>
              <div className="value">{summary.quotation_count}<span className="unit">건</span></div>
              <div className="sub">{summary.vendors.join(', ') || '-'}</div></div>
            <div className="card status-neutral"><div className="label">선정 업체</div>
              <div className="value" style={{ fontSize: 17 }}>{summary.selected_vendor ?? '미선정'}</div>
              <div className="sub">{summary.selected_amount ? `${fmt(summary.selected_amount)}원` : ''}</div></div>
            <div className={`card ${summary.budget_usage_pct == null ? 'status-neutral'
              : summary.budget_usage_pct <= 100 ? 'status-ok' : 'status-ng'}`}>
              <div className="label">예산 대비 선정가</div>
              <div className="value">{summary.budget_usage_pct ?? '-'}<span className="unit">%</span></div>
              <div className="sub">예산 {fmt(sel.budget)}원</div></div>
          </div>
          <p style={{ marginBottom: 0 }}>
            <Link to="/investment">→ 견적 분석으로 이동</Link>
            <span className="muted" style={{ marginLeft: 10 }}>
              ※ 견적 업로드 시 프로젝트명을 '{sel.name}' 으로 입력하면 자동 연결됩니다
            </span>
          </p>
        </div>
      )}
    </div>
  )
}

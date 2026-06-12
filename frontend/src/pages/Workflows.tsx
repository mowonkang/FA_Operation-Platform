import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'

const STEP_STATUS = ['PENDING', 'IN_PROGRESS', 'DONE', 'NG', 'SKIP']
const STEP_LABEL: Record<string, string> = {
  PENDING: '대기', IN_PROGRESS: '진행중', DONE: '완료', NG: 'NG', SKIP: '생략',
}

export default function Workflows() {
  const [templates, setTemplates] = useState<any[]>([])
  const [list, setList] = useState<any[]>([])
  const [eqs, setEqs] = useState<any[]>([])
  const [models, setModels] = useState<any[]>([])
  const [sites, setSites] = useState<any[]>([])
  const [sel, setSel] = useState<any>(null)         // 선택된 워크플로우 상세
  const [createType, setCreateType] = useState('')
  const [form, setForm] = useState({ title: '', equipment_id: '', model_id: '', created_by: '' })
  const [drPack, setDrPack] = useState<any>(null)
  const [closeForm, setCloseForm] = useState<any>(null)
  const [err, setErr] = useState('')

  const load = () => {
    api.get('/workflows/templates').then(setTemplates)
    api.get('/workflows').then(setList)
    api.get('/equipments').then(setEqs)
    api.get('/models').then(setModels)
    api.get('/sites').then(setSites)
  }
  useEffect(load, [])

  const open = async (id: number) => {
    setSel(await api.get(`/workflows/${id}`))
    setDrPack(null)
    setCloseForm(null)
    setErr('')
  }

  const create = async () => {
    setErr('')
    try {
      const wf = await api.post('/workflows', {
        wf_type: createType, title: form.title,
        equipment_id: form.equipment_id ? Number(form.equipment_id) : null,
        model_id: form.model_id ? Number(form.model_id) : null,
        created_by: form.created_by,
      })
      setCreateType('')
      setForm({ title: '', equipment_id: '', model_id: '', created_by: '' })
      load()
      setSel(wf)
    } catch (e: any) { setErr(e.message) }
  }

  const setStep = async (stepId: number, patch: any) => {
    await api.patch(`/workflows/steps/${stepId}`, patch)
    open(sel.id)
  }

  const loadDrPack = async () => {
    const modelId = sel.model_id ?? eqs.find((e) => e.id === sel.equipment_id)?.model_id
    if (!modelId) { setErr('모델이 지정되지 않은 워크플로우입니다'); return }
    setDrPack(await api.get(`/workflows/dr-pack?model_id=${modelId}`))
  }

  const close = async () => {
    setErr('')
    try {
      await api.post(`/workflows/${sel.id}/close`, {
        result_note: closeForm.result_note,
        create_lesson: closeForm.create_lesson,
        lesson_title: closeForm.lesson_title,
        origin_site_id: closeForm.origin_site_id ? Number(closeForm.origin_site_id) : null,
      })
      setCloseForm(null)
      load()
      open(sel.id)
    } catch (e: any) { setErr(e.message) }
  }

  const progress = (wf: any) => {
    if (!wf.steps) return ''
    const done = wf.steps.filter((s: any) => ['DONE', 'SKIP', 'NG'].includes(s.status)).length
    return `${done}/${wf.steps.length}`
  }

  return (
    <div>
      <h2>워크플로우</h2>
      <p className="muted">DR · 셋업 안정화 · 알람 조치 · BM · PM · 제어 변경 · 시스템 이슈 — 표준 절차 기반 업무 관리. 완료 시 L&L 자동 등록 가능.</p>

      <div className="cards" style={{ marginBottom: 16 }}>
        {templates.map((t) => (
          <div className="card" key={t.wf_type} style={{ cursor: 'pointer' }}
            onClick={() => { setCreateType(t.wf_type); setSel(null) }}>
            <div className="label">{t.wf_type} · {t.step_count}단계</div>
            <div style={{ fontWeight: 700, fontSize: 14, marginTop: 4 }}>{t.label}</div>
            <div className="muted" style={{ marginTop: 4 }}>{t.description}</div>
          </div>
        ))}
      </div>

      {createType && (
        <div className="panel">
          <h3 style={{ marginTop: 0 }}>새 워크플로우: {templates.find((t) => t.wf_type === createType)?.label}</h3>
          <div className="form-grid">
            <label>제목<input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} /></label>
            <label>대상 설비 (선택)
              <select value={form.equipment_id} onChange={(e) => setForm({ ...form, equipment_id: e.target.value })}>
                <option value="">없음</option>
                {eqs.map((e) => <option key={e.id} value={e.id}>{e.asset_code}</option>)}
              </select>
            </label>
            <label>대상 모델 (DR 권장)
              <select value={form.model_id} onChange={(e) => setForm({ ...form, model_id: e.target.value })}>
                <option value="">없음</option>
                {models.map((m) => <option key={m.id} value={m.id}>{m.code}</option>)}
              </select>
            </label>
            <label>생성자<input value={form.created_by} onChange={(e) => setForm({ ...form, created_by: e.target.value })} /></label>
          </div>
          <button disabled={!form.title} onClick={create}>생성</button>{' '}
          <button className="secondary" onClick={() => setCreateType('')}>취소</button>
        </div>
      )}

      <div className="row">
        <div className="panel">
          <h3 style={{ marginTop: 0 }}>진행 목록</h3>
          <table>
            <thead><tr><th>#</th><th>유형</th><th>제목</th><th>대상</th><th>상태</th><th>생성</th></tr></thead>
            <tbody>
              {list.map((w) => (
                <tr key={w.id} onClick={() => open(w.id)} style={{ cursor: 'pointer',
                  background: sel?.id === w.id ? '#eff6ff' : undefined }}>
                  <td>{w.id}</td>
                  <td><span className="badge info">{w.wf_type}</span></td>
                  <td>{w.title}</td>
                  <td>{eqs.find((e) => e.id === w.equipment_id)?.asset_code
                    ?? models.find((m) => m.id === w.model_id)?.code ?? '-'}</td>
                  <td><span className={`badge ${w.status === 'DONE' ? 'ok' : 'check'}`}>{w.status}</span></td>
                  <td>{w.created_at?.slice(0, 10)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {sel && (
          <div className="panel">
            <h3 style={{ marginTop: 0 }}>
              #{sel.id} {sel.title} <span className="badge gray">{sel.wf_type}</span>{' '}
              <span className={`badge ${sel.status === 'DONE' ? 'ok' : 'check'}`}>{sel.status} {progress(sel)}</span>
            </h3>
            {sel.wf_type === 'DR' && (
              <p><button className="secondary" onClick={loadDrPack}>📊 DR 데이터팩 생성 (BM·L&L·FDC 이력 집계)</button></p>
            )}
            {err && <div className="error">{err}</div>}

            <ul className="timeline">
              {sel.steps?.map((s: any) => (
                <li key={s.id}>
                  <div className="title">{s.seq}. {s.name}{' '}
                    <select value={s.status} disabled={sel.status === 'DONE'}
                      onChange={(e) => setStep(s.id, { status: e.target.value })}
                      style={{ fontSize: 11, padding: '2px 4px' }}>
                      {STEP_STATUS.map((st) => <option key={st} value={st}>{STEP_LABEL[st]}</option>)}
                    </select>
                  </div>
                  <div className="detail">{s.guide}</div>
                  {s.link && (
                    <div className="detail">
                      {s.link.kind === 'page' && s.link.ref !== 'drpack' &&
                        <Link to={s.link.ref}>→ {s.link.label}</Link>}
                      {s.link.kind === 'page' && s.link.ref === 'drpack' &&
                        <a onClick={loadDrPack} style={{ cursor: 'pointer' }}>→ {s.link.label}</a>}
                      {s.link.kind === 'tool' && <Link to="/engineering">→ {s.link.label}</Link>}
                      {s.link.kind === 'knowledge' && <Link to="/knowledge">→ {s.link.label}</Link>}
                    </div>
                  )}
                  <div className="detail">
                    <input placeholder="담당" value={s.owner} style={{ width: 80, fontSize: 11, padding: '2px 6px' }}
                      disabled={sel.status === 'DONE'}
                      onChange={(e) => setStep(s.id, { owner: e.target.value })} />{' '}
                    <input placeholder="메모" defaultValue={s.note} style={{ width: 220, fontSize: 11, padding: '2px 6px' }}
                      disabled={sel.status === 'DONE'}
                      onBlur={(e) => e.target.value !== s.note && setStep(s.id, { note: e.target.value })} />
                  </div>
                </li>
              ))}
            </ul>

            {sel.status !== 'DONE' && !closeForm && (
              <button onClick={() => setCloseForm({ result_note: '', create_lesson: false, lesson_title: '', origin_site_id: '' })}>
                워크플로우 종료
              </button>
            )}
            {closeForm && (
              <div className="result-box">
                <div className="form-grid">
                  <label>결과 요약<input value={closeForm.result_note}
                    onChange={(e) => setCloseForm({ ...closeForm, result_note: e.target.value })} /></label>
                  <label style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                    <input type="checkbox" checked={closeForm.create_lesson}
                      onChange={(e) => setCloseForm({ ...closeForm, create_lesson: e.target.checked })} />
                    L&L 자동 등록 (전 법인 전파)
                  </label>
                  {closeForm.create_lesson && (
                    <>
                      <label>L&L 제목<input value={closeForm.lesson_title}
                        onChange={(e) => setCloseForm({ ...closeForm, lesson_title: e.target.value })} /></label>
                      <label>발생 법인
                        <select value={closeForm.origin_site_id}
                          onChange={(e) => setCloseForm({ ...closeForm, origin_site_id: e.target.value })}>
                          <option value="">선택</option>
                          {sites.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
                        </select>
                      </label>
                    </>
                  )}
                </div>
                <button onClick={close}>종료 확정</button>{' '}
                <button className="secondary" onClick={() => setCloseForm(null)}>취소</button>
              </div>
            )}
          </div>
        )}
      </div>

      {drPack && (
        <div className="panel">
          <h3 style={{ marginTop: 0 }}>📊 DR 데이터팩 — {drPack.model.code} ({drPack.equipment_count}대 운영 이력)</h3>
          <p className="muted">{drPack.guide}</p>
          <div className="row">
            <div>
              <h3>BM 이력 (총 {drPack.bm_summary.total}건 / 다운타임 {drPack.bm_summary.total_downtime_min}분)</h3>
              <table>
                <thead><tr><th>원인</th><th>건수</th><th>다운타임(분)</th></tr></thead>
                <tbody>
                  {drPack.bm_summary.top_causes.map((c: any, i: number) => (
                    <tr key={i}><td>{c.cause}</td><td>{c.count}</td><td>{c.downtime_min}</td></tr>
                  ))}
                </tbody>
              </table>
              <h3>PM NG/CHECK 빈발 항목</h3>
              <table>
                <thead><tr><th>항목</th><th>판정</th><th>건수</th></tr></thead>
                <tbody>
                  {drPack.pm_ng_items.map((p: any, i: number) => (
                    <tr key={i}><td>{p.item}</td><td><span className={`badge ${p.judgment === 'NG' ? 'ng' : 'check'}`}>{p.judgment}</span></td><td>{p.count}</td></tr>
                  ))}
                </tbody>
              </table>
              <h3>FDC 알람 통계</h3>
              <table>
                <thead><tr><th>센서</th><th>분류</th><th>건수</th></tr></thead>
                <tbody>
                  {drPack.fdc_alarm_stats.map((f: any, i: number) => (
                    <tr key={i}><td>{f.sensor}</td><td>{f.classification}</td><td>{f.count}</td></tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div>
              <h3>L&L (미반영 {drPack.unreflected_lessons.length}건 ← 설계 반영 필수 검토)</h3>
              <table>
                <thead><tr><th>제목</th><th>대책</th><th>표준반영</th></tr></thead>
                <tbody>
                  {drPack.lessons.map((l: any) => (
                    <tr key={l.id}><td>{l.title}</td><td>{l.countermeasure}</td>
                      <td>{l.std_reflected ? <span className="badge ok">반영</span> : <span className="badge ng">미반영</span>}</td></tr>
                  ))}
                </tbody>
              </table>
              <h3>관련 지식 DB ({drPack.knowledge.length}건)</h3>
              <ul style={{ fontSize: 13 }}>
                {drPack.knowledge.map((k: any) => (
                  <li key={k.id}><Link to="/knowledge">[{k.category}] {k.title}</Link></li>
                ))}
              </ul>
              <p className="muted">Install Parameter 변경 버전 수: {drPack.param_change_versions}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

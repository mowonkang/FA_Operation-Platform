import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { LineChart, Line, XAxis, YAxis, Tooltip, ReferenceLine, ResponsiveContainer } from 'recharts'
import { api, judgeClass } from '../api'
import { useSite, sq } from '../site'

/* ───────────────── 정기 상태감시 (촬영 기반 이상감지) ───────────────── */

function MonitorTab() {
  const [types, setTypes] = useState<any[]>([])
  const [points, setPoints] = useState<any[]>([])
  const [eqs, setEqs] = useState<any[]>([])
  const [sel, setSel] = useState<any>(null)
  const [shots, setShots] = useState<any[]>([])
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({ equipment_id: '', name: '', target_type: 'BOLT',
    location_note: '', period_days: 7 })
  const [baseFile, setBaseFile] = useState<File | null>(null)
  const [shotFile, setShotFile] = useState<File | null>(null)
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState('')
  const [err, setErr] = useState('')

  const { site } = useSite()
  const load = () => {
    api.get('/vision-monitor/types').then(setTypes).catch(() => {})
    api.get(`/vision-monitor/points${sq(site)}`).then(setPoints).catch(() => {})
    api.get(`/equipments${sq(site)}`).then(setEqs).catch(() => {})
  }
  useEffect(load, [site])

  const open = async (p: any) => {
    setSel(p)
    setErr(''); setMsg('')
    setShots(await api.get(`/vision-monitor/points/${p.id}/shots`))
  }

  const create = async () => {
    setErr('')
    try {
      const p = await api.post('/vision-monitor/points', {
        ...form, equipment_id: Number(form.equipment_id), period_days: Number(form.period_days),
      })
      if (baseFile) {
        const fd = new FormData()
        fd.append('file', baseFile)
        await api.upload(`/vision-monitor/points/${p.id}/baseline`, fd)
      }
      setShowCreate(false)
      setForm({ equipment_id: '', name: '', target_type: 'BOLT', location_note: '', period_days: 7 })
      setBaseFile(null)
      load()
    } catch (e: any) { setErr(e.message) }
  }

  const uploadShot = async () => {
    if (!shotFile || !sel) return
    setBusy(true); setErr(''); setMsg('')
    try {
      const fd = new FormData()
      fd.append('file', shotFile)
      const s = await api.upload(`/vision-monitor/points/${sel.id}/shots`, fd)
      setMsg(`분석 완료 — ${s.judgment} (이상점수 ${s.score})${s.issue_id ? ` · 이슈 #${s.issue_id} 자동 생성` : ''}`)
      setShotFile(null)
      load()
      open({ ...sel })
    } catch (e: any) { setErr(e.message) } finally { setBusy(false) }
  }

  const trend = shots.map((s) => ({
    t: s.captured_at?.slice(5, 10), score: s.score, judgment: s.judgment,
  }))
  const latest = shots[shots.length - 1]

  // ── 순회(패트롤) 동영상 ──
  const [patrolFile, setPatrolFile] = useState<File | null>(null)
  const [patrolBusy, setPatrolBusy] = useState(false)
  const [patrolReport, setPatrolReport] = useState<any>(null)
  const [patrols, setPatrols] = useState<any[]>([])
  useEffect(() => {
    api.get(`/vision-monitor/patrols${sq(site)}`).then(setPatrols).catch(() => {})
  }, [site])

  const runPatrol = async () => {
    if (!patrolFile) return
    setPatrolBusy(true); setErr(''); setPatrolReport(null)
    try {
      const fd = new FormData()
      fd.append('file', patrolFile)
      if (site) fd.append('site_id', site)
      setPatrolReport(await api.upload('/vision-monitor/patrol', fd))
      setPatrolFile(null)
      load()
      api.get(`/vision-monitor/patrols${sq(site)}`).then(setPatrols).catch(() => {})
    } catch (e: any) { setErr(e.message) } finally { setPatrolBusy(false) }
  }

  const demoPatrol = async () => {
    setPatrolBusy(true); setErr('')
    try {
      setPatrolReport(await api.post('/vision-monitor/patrol-demo'))
      load()
      api.get('/vision-monitor/patrols').then(setPatrols).catch(() => {})
    } catch (e: any) { setErr(e.message) } finally { setPatrolBusy(false) }
  }

  return (
    <div>
      <p className="page-desc">
        동일 지점·동일 구도로 정기 촬영(사진/동영상) → 기준 이미지 대비 자동 변화 감지.
        볼트 풀림(합마크 회전)·와이어 소선 돌출·표면 파손·레일 단차를 검출하고,
        이상 시 <Link to="/issues">이슈</Link>가 자동 생성되어 대시보드 조치 대상에 표출됩니다.
      </p>
      <p>
        <button onClick={() => setShowCreate(!showCreate)}>+ 촬영 포인트 등록</button>{' '}
        {points.length === 0 && (
          <button className="secondary"
            onClick={() => api.post('/vision-monitor/seed-demo').then(() => load())}>
            데모 포인트 생성 (볼트/와이어/레일/표면 4종)
          </button>
        )}
      </p>

      {showCreate && (
        <div className="panel">
          <div className="panel-title">촬영 포인트 등록</div>
          <div className="form-grid">
            <label>설비
              <select value={form.equipment_id} onChange={(e) => setForm({ ...form, equipment_id: e.target.value })}>
                <option value="">선택</option>
                {eqs.map((e) => <option key={e.id} value={e.id}>{e.asset_code}</option>)}
              </select>
            </label>
            <label>포인트 이름<input value={form.name} placeholder="예: 새들 고정볼트 M20 #3"
              onChange={(e) => setForm({ ...form, name: e.target.value })} /></label>
            <label>감시 유형
              <select value={form.target_type} onChange={(e) => setForm({ ...form, target_type: e.target.value })}>
                {types.map((t) => <option key={t.code} value={t.code}>{t.label}</option>)}
              </select>
            </label>
            <label>촬영 주기 (일)<input type="number" value={form.period_days}
              onChange={(e) => setForm({ ...form, period_days: Number(e.target.value) })} /></label>
            <label>촬영 표준 (위치·지그·구도)<input value={form.location_note}
              placeholder="예: 지그 J-01, 정면 30cm, 조명 일정"
              onChange={(e) => setForm({ ...form, location_note: e.target.value })} /></label>
            <label>기준 이미지 (정상 상태 골든샘플)
              <input type="file" accept="image/*" onChange={(e) => setBaseFile(e.target.files?.[0] ?? null)} /></label>
          </div>
          <button disabled={!form.equipment_id || !form.name} onClick={create}>등록</button>
          {err && <div className="error">{err}</div>}
        </div>
      )}

      {/* 순회 동영상 분석 */}
      <div className="panel" style={{ borderLeft: '4px solid var(--accent)' }}>
        <div className="panel-title">
          🎥 순회 동영상 분석
          <span className="hint">이동하며 촬영한 영상 1개로 여러 포인트 자동 매칭·판정 — 미촬영 포인트도 리포트</span>
        </div>
        <input type="file" accept="video/*" onChange={(e) => setPatrolFile(e.target.files?.[0] ?? null)} />{' '}
        <button disabled={!patrolFile || patrolBusy} onClick={runPatrol}>
          {patrolBusy ? '분석중…' : '순회 영상 분석'}
        </button>{' '}
        <button className="secondary" disabled={patrolBusy} onClick={demoPatrol}>데모 순회 실행</button>
        {err && <div className="error">{err}</div>}

        {patrolReport && (
          <div className="result-box">
            <div className="big">
              순회 #{patrolReport.run.id} — 커버 {patrolReport.run.points_covered}곳 /
              {' '}NG <span style={{ color: 'var(--ng)' }}>{patrolReport.run.ng_count}</span> ·
              CHECK <span style={{ color: 'var(--warn)' }}>{patrolReport.run.check_count}</span> ·
              미촬영 {(patrolReport.run.missed_points ?? []).length}곳
              <span className="muted" style={{ marginLeft: 8 }}>
                (프레임 {patrolReport.run.frames_total}, 이동장면 {patrolReport.run.frames_unmatched})
              </span>
            </div>
            <table style={{ marginTop: 8 }}>
              <thead><tr><th>포인트</th><th>유형</th><th>매칭</th><th>점수</th><th>판정</th><th>검출 내용</th><th>이슈</th></tr></thead>
              <tbody>
                {patrolReport.shots.map((s: any) => (
                  <tr key={s.id}>
                    <td>{s.point_name}</td>
                    <td><span className="badge info">{s.target_type}</span></td>
                    <td className="num">{s.detail?.match_confidence}</td>
                    <td className="num">{s.score}</td>
                    <td><span className={judgeClass(s.judgment)}>{s.judgment}</span></td>
                    <td>{(s.findings ?? []).join('; ') || '-'}</td>
                    <td>{s.issue_id ? `#${s.issue_id}` : '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {(patrolReport.run.missed_points ?? []).length > 0 && (
              <p style={{ color: 'var(--warn)', marginBottom: 0 }}>
                ⚠ 미촬영: {(patrolReport.run.missed_points ?? []).map((m: any) => m.name).join(', ')} — 재순회 필요
              </p>
            )}
            <div className="row" style={{ marginTop: 8 }}>
              {patrolReport.shots.filter((s: any) => s.judgment !== 'OK').map((s: any) => (
                <div key={s.id} style={{ maxWidth: 300 }}>
                  <img src={s.overlay_url} style={{ width: '100%', borderRadius: 6, border: '1px solid var(--border)' }} />
                  <div className="muted">{s.point_name} — {s.judgment}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {patrols.length > 0 && (
          <>
            <h3>순회 이력</h3>
            <table>
              <thead><tr><th>#</th><th>일시</th><th>수행</th><th>커버</th><th>NG</th><th>CHECK</th><th>미촬영</th><th>프레임</th></tr></thead>
              <tbody>
                {patrols.map((r) => (
                  <tr key={r.id} className="clickable"
                    onClick={() => api.get(`/vision-monitor/patrols/${r.id}`).then(setPatrolReport)}>
                    <td>{r.id}</td>
                    <td>{r.started_at?.slice(0, 16).replace('T', ' ')}</td>
                    <td>{r.performed_by || '-'}</td>
                    <td className="num">{r.points_covered}</td>
                    <td className="num">{r.ng_count > 0 ? <span className="badge ng">{r.ng_count}</span> : 0}</td>
                    <td className="num">{r.check_count}</td>
                    <td className="num">{(r.missed_points ?? []).length}</td>
                    <td className="num">{r.frames_total}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}
      </div>

      <table>
        <thead><tr><th>유형</th><th>포인트</th><th>설비</th><th>주기</th><th>회차</th><th>최근 판정</th><th>점수</th><th>차기 촬영</th></tr></thead>
        <tbody>
          {points.map((p) => (
            <tr key={p.id} className={`clickable ${sel?.id === p.id ? 'selected' : ''}`} onClick={() => open(p)}>
              <td><span className="badge info">{p.target_type}</span></td>
              <td>{p.name}</td>
              <td>{p.equipment.asset_code}</td>
              <td className="num">{p.period_days}일</td>
              <td className="num">{p.shot_count}</td>
              <td>{p.last_judgment ? <span className={judgeClass(p.last_judgment)}>{p.last_judgment}</span> : '-'}</td>
              <td className="num">{p.last_score ?? '-'}</td>
              <td>{p.overdue ? <span className="badge ng">촬영 지연</span> : p.next_due?.slice(5, 10)}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {sel && (
        <div className="panel" style={{ marginTop: 14 }}>
          <div className="panel-title">
            {sel.name} <span className="badge info">{sel.target_type}</span>
            <span className="hint">{sel.location_note}</span>
          </div>

          <div className="row">
            <div style={{ flex: 1.4 }}>
              <div className="row">
                <div>
                  <h3 style={{ marginTop: 0 }}>기준 이미지 (골든 샘플)</h3>
                  {sel.baseline_url
                    ? <img src={sel.baseline_url} style={{ width: '100%', borderRadius: 6, border: '1px solid var(--border)' }} />
                    : <p className="muted">기준 이미지 미등록</p>}
                </div>
                <div>
                  <h3 style={{ marginTop: 0 }}>최근 촬영 — 변화영역 표시{latest && <> <span className={judgeClass(latest.judgment)}>{latest.judgment}</span></>}</h3>
                  {latest
                    ? <img src={`/uploads/${latest.overlay_path.split('/').pop()}`}
                        style={{ width: '100%', borderRadius: 6, border: '1px solid var(--border)' }} />
                    : <p className="muted">촬영 이력 없음</p>}
                </div>
              </div>
              {latest?.findings?.length > 0 && (
                <div className="result-box">
                  {latest.findings.map((f: string, i: number) => <div key={i}>⚠ {f}</div>)}
                  {latest.issue_id && <div style={{ marginTop: 4 }}><Link to="/issues">→ 자동 생성 이슈 #{latest.issue_id} 처리</Link></div>}
                </div>
              )}
            </div>

            <div style={{ flex: 1 }}>
              <h3 style={{ marginTop: 0 }}>이상점수 추세 <span className="hint" style={{ fontWeight: 400 }}>30=CHECK / 60=NG 기준선</span></h3>
              <ResponsiveContainer width="100%" height={160}>
                <LineChart data={trend}>
                  <XAxis dataKey="t" fontSize={11} />
                  <YAxis domain={[0, 100]} fontSize={11} />
                  <Tooltip />
                  <ReferenceLine y={30} stroke="#f59e0b" strokeDasharray="4 4" />
                  <ReferenceLine y={60} stroke="#ef4444" strokeDasharray="4 4" />
                  <Line type="monotone" dataKey="score" stroke="#3b82f6" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>

              <h3>정기 촬영 업로드 (사진 또는 동영상)</h3>
              <input type="file" accept="image/*,video/*"
                onChange={(e) => setShotFile(e.target.files?.[0] ?? null)} />{' '}
              <button disabled={!shotFile || busy} onClick={uploadShot}>
                {busy ? '분석중…' : '업로드 + 자동분석'}
              </button>
              {msg && <p className="muted" style={{ color: 'var(--ok)' }}>{msg}</p>}
              {err && <div className="error">{err}</div>}

              <h3>촬영 이력</h3>
              <table>
                <thead><tr><th>일시</th><th>소스</th><th>점수</th><th>판정</th><th>이슈</th></tr></thead>
                <tbody>
                  {[...shots].reverse().map((s) => (
                    <tr key={s.id}>
                      <td>{s.captured_at?.slice(0, 16).replace('T', ' ')}</td>
                      <td>{s.source}</td>
                      <td className="num">{s.score}</td>
                      <td><span className={judgeClass(s.judgment)}>{s.judgment}</span></td>
                      <td>{s.issue_id ? `#${s.issue_id}` : '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

/* ───────────────── 수동 측정 (기존 1회성 측정) ───────────────── */

const KINDS = [
  { v: 'WEAR', label: '마모율 (%)' },
  { v: 'CORROSION', label: '부식률 (%)' },
  { v: 'DIMENSION', label: '치수 (mm)' },
  { v: 'ALIGNMENT', label: '정렬 편차 (deg)' },
]

function ManualTab() {
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
    <div className="row">
      <div className="panel">
        <div className="panel-title">이미지 업로드 → 자동 측정/판정 <span className="hint">PM 항목 연계 시 한계값 자동판정</span></div>
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
          <label>PM 표준항목 연계
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
          ref_length_mm / ref_length_px 로 캘리브레이션합니다.
        </p>
      </div>

      <div className="panel">
        <div className="panel-title">측정 이력</div>
        <table>
          <thead><tr><th>#</th><th>일시</th><th>설비</th><th>종류</th><th>측정값</th><th>판정</th></tr></thead>
          <tbody>
            {history.map((h) => (
              <tr key={h.id}>
                <td>{h.id}</td>
                <td>{h.created_at?.slice(0, 16).replace('T', ' ')}</td>
                <td>{eqs.find((e) => e.id === h.equipment_id)?.asset_code ?? '-'}</td>
                <td>{h.kind}</td>
                <td className="num">{h.measured_value ?? '-'} {h.unit}</td>
                <td><span className={judgeClass(h.judgment)}>{h.judgment}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default function Vision() {
  const [tab, setTab] = useState<'monitor' | 'manual'>('monitor')
  return (
    <div>
      <div className="tabs">
        <button className={tab === 'monitor' ? 'on' : ''} onClick={() => setTab('monitor')}>
          📷 정기 상태감시 (이상 자동감지)
        </button>
        <button className={tab === 'manual' ? 'on' : ''} onClick={() => setTab('manual')}>
          수동 측정 (마모/부식/치수/정렬)
        </button>
      </div>
      {tab === 'monitor' ? <MonitorTab /> : <ManualTab />}
    </div>
  )
}

import { useEffect, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { api } from '../api'

const ERRC = [
  { v: '', label: '-' },
  { v: 'ELIMINATE', label: 'E 제거' },
  { v: 'RAISE', label: 'R 강화' },
  { v: 'REDUCE', label: 'R 절감' },
  { v: 'CREATE', label: 'C 신설' },
]
const fmt = (n: number) => n?.toLocaleString(undefined, { maximumFractionDigits: 0 })

export default function Investment() {
  const [quotes, setQuotes] = useState<any[]>([])
  const [sel, setSel] = useState<any>(null)
  const [analysisData, setAnalysisData] = useState<any>(null)
  const [cmp, setCmp] = useState<any>(null)
  const [up, setUp] = useState({ project: '', vendor: '' })
  const [file, setFile] = useState<File | null>(null)
  const [msg, setMsg] = useState('')
  const [err, setErr] = useState('')

  const load = () => api.get('/quotations').then(setQuotes)
  useEffect(() => { load() }, [])

  const open = async (id: number) => {
    setSel(await api.get(`/quotations/${id}`))
    setAnalysisData(await api.get(`/quotations/${id}/analysis`))
    setCmp(null)
  }

  const upload = async () => {
    if (!file) return
    setErr(''); setMsg('')
    try {
      const form = new FormData()
      form.append('file', file)
      form.append('project', up.project)
      form.append('vendor', up.vendor)
      const q = await api.upload('/quotations/upload', form)
      setMsg(`업로드 완료 — ${q.items.length}개 항목 자동 인식·분류`)
      load()
      open(q.id)
    } catch (e: any) { setErr(e.message) }
  }

  const compare = async () => {
    if (!sel) return
    try {
      setCmp(await api.get(`/quotations/compare?project=${encodeURIComponent(sel.project)}`))
    } catch (e: any) { setErr(e.message) }
  }

  const tag = async (itemId: number, errc: string) => {
    await api.patch(`/quotations/items/${itemId}`, { errc })
    open(sel.id)
  }

  const setStatus = async (status: string) => {
    await api.patch(`/quotations/${sel.id}/status?status=${status}`)
    load()
    open(sel.id)
  }

  return (
    <div>
      <h2>투자 분석 — 견적서 자동 데이터 분석</h2>
      <p className="muted">
        견적서(CSV/XLSX) 업로드 → 컬럼·항목 자동 인식/분류 → 원가구조·계산오류·이상단가·중복·파레토 분석
        → ERRC 태깅 → 업체 비교 (구매 Nego 기초자료).
      </p>

      <div className="panel">
        <h3 style={{ marginTop: 0 }}>견적서 업로드</h3>
        <div className="form-grid">
          <label>프로젝트<input value={up.project} onChange={(e) => setUp({ ...up, project: e.target.value })}
            placeholder="예: STK-3000 신규라인" /></label>
          <label>업체<input value={up.vendor} onChange={(e) => setUp({ ...up, vendor: e.target.value })} /></label>
          <label>파일 (CSV/XLSX — 품명/수량/단가/금액 컬럼 자동 인식)
            <input type="file" accept=".csv,.xlsx" onChange={(e) => setFile(e.target.files?.[0] ?? null)} /></label>
        </div>
        <button disabled={!file || !up.project || !up.vendor} onClick={upload}>업로드 + 자동분석</button>{' '}
        <button className="secondary" onClick={() => api.post('/quotations/seed-demo').then((r) => { setMsg(`데모 견적 ${r.seeded}건 생성`); load() })}>
          데모 견적 생성 (업체 2개사)
        </button>
        {msg && <p className="muted">{msg}</p>}
        {err && <div className="error">{err}</div>}
      </div>

      <table>
        <thead><tr><th>#</th><th>프로젝트</th><th>업체</th><th>총액</th><th>상태</th><th>접수일</th></tr></thead>
        <tbody>
          {quotes.map((q) => (
            <tr key={q.id} onClick={() => open(q.id)} style={{ cursor: 'pointer',
              background: sel?.id === q.id ? 'var(--row-selected)' : undefined }}>
              <td>{q.id}</td><td>{q.project}</td><td>{q.vendor}</td>
              <td>{fmt(q.total_amount)} {q.currency}</td>
              <td><span className={`badge ${q.status === 'SELECTED' ? 'ok' : q.status === 'REJECTED' ? 'ng' : 'info'}`}>{q.status}</span></td>
              <td>{q.received_date}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {sel && analysisData && (
        <div className="panel" style={{ marginTop: 16 }}>
          <h3 style={{ marginTop: 0 }}>
            분석: {sel.vendor} — {sel.project} (총 {fmt(analysisData.total_amount)}원, {analysisData.item_count}항목){' '}
            <button className="secondary" onClick={compare}>동일 프로젝트 업체 비교</button>{' '}
            {sel.status !== 'SELECTED' && <button onClick={() => setStatus('SELECTED')}>이 업체 선정</button>}
          </h3>

          <div className="result-box">
            {analysisData.findings.map((f: string, i: number) => <div key={i}>• {f}</div>)}
            <div style={{ marginTop: 6 }}>
              <b>ERRC 절감 추정: {fmt(analysisData.errc_summary.estimated_saving)}원</b>{' '}
              (E {fmt(analysisData.errc_summary.eliminate_amount)} + Reduce 30%, 태깅 {analysisData.errc_summary.tagged_count}건)
            </div>
          </div>

          <div className="row" style={{ marginTop: 12 }}>
            <div>
              <b style={{ fontSize: 13 }}>원가 구조 (카테고리별)</b>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={analysisData.structure}>
                  <XAxis dataKey="label" fontSize={11} />
                  <YAxis fontSize={11} tickFormatter={(v) => `${(v / 1e6).toFixed(0)}M`} />
                  <Tooltip formatter={(v: any) => fmt(v)} />
                  <Bar dataKey="amount" fill="#3b82f6" name="금액" />
                </BarChart>
              </ResponsiveContainer>
              {analysisData.calc_errors.length > 0 && (
                <>
                  <b style={{ fontSize: 13, color: '#ef4444' }}>계산 오류</b>
                  <table>
                    <thead><tr><th>항목</th><th>수량×단가</th><th>표기 금액</th><th>차이</th></tr></thead>
                    <tbody>
                      {analysisData.calc_errors.map((c: any, i: number) => (
                        <tr key={i}><td>{c.name}</td><td>{fmt(c.expected)}</td><td>{fmt(c.amount)}</td>
                          <td style={{ color: '#ef4444' }}>{fmt(c.diff)}</td></tr>
                      ))}
                    </tbody>
                  </table>
                </>
              )}
              {analysisData.price_outliers.length > 0 && (
                <>
                  <b style={{ fontSize: 13, color: '#f59e0b' }}>이상 단가 (카테고리 평균 +2σ)</b>
                  <table>
                    <thead><tr><th>항목</th><th>단가</th><th>카테고리 평균</th><th>z</th></tr></thead>
                    <tbody>
                      {analysisData.price_outliers.map((o: any, i: number) => (
                        <tr key={i}><td>{o.name}</td><td>{fmt(o.unit_price)}</td><td>{fmt(o.category_mean)}</td><td>{o.z_score}</td></tr>
                      ))}
                    </tbody>
                  </table>
                </>
              )}
              {analysisData.duplicates.length > 0 && (
                <>
                  <b style={{ fontSize: 13, color: '#f59e0b' }}>중복 의심</b>
                  <table>
                    <thead><tr><th>항목</th><th>출현</th><th>합계</th></tr></thead>
                    <tbody>
                      {analysisData.duplicates.map((d: any, i: number) => (
                        <tr key={i}><td>{d.name}</td><td>{d.count}회</td><td>{fmt(d.total_amount)}</td></tr>
                      ))}
                    </tbody>
                  </table>
                </>
              )}
            </div>
            <div>
              <b style={{ fontSize: 13 }}>항목별 ERRC 태깅 (금액순)</b>
              <table>
                <thead><tr><th>항목</th><th>분류</th><th>수량</th><th>금액</th><th>ERRC</th></tr></thead>
                <tbody>
                  {[...sel.items].sort((a: any, b: any) => b.amount - a.amount).map((i: any) => (
                    <tr key={i.id}>
                      <td>{i.name}</td>
                      <td><span className="badge gray">{i.category}</span></td>
                      <td>{i.qty}</td><td>{fmt(i.amount)}</td>
                      <td>
                        <select value={i.errc} onChange={(e) => tag(i.id, e.target.value)}
                          style={{ fontSize: 11, padding: '2px 4px',
                            background: i.errc === 'ELIMINATE' ? '#fee2e2' : i.errc === 'REDUCE' ? '#fef3c7' : undefined }}>
                          {ERRC.map((o) => <option key={o.v} value={o.v}>{o.label}</option>)}
                        </select>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {cmp && !cmp.error && (
        <div className="panel">
          <h3 style={{ marginTop: 0 }}>업체 비교 — 공통 {cmp.common_item_count}항목, Nego 여지 {fmt(cmp.nego_potential_amount)}원</h3>
          <p className="muted">{cmp.guide}</p>
          <div className="row">
            <div>
              <table>
                <thead><tr><th>업체</th><th>총액</th><th>최저가 대비</th><th>항목수</th></tr></thead>
                <tbody>
                  {cmp.totals.map((t: any) => (
                    <tr key={t.vendor}><td>{t.vendor}</td><td>{fmt(t.total)}</td>
                      <td>{t.vs_lowest_pct > 0 ? <span className="badge ng">+{t.vs_lowest_pct}%</span> : <span className="badge ok">최저</span>}</td>
                      <td>{t.item_count}</td></tr>
                  ))}
                </tbody>
              </table>
              <b style={{ fontSize: 13 }}>카테고리별 비교</b>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={cmp.category_matrix}>
                  <XAxis dataKey="label" fontSize={11} />
                  <YAxis fontSize={11} tickFormatter={(v) => `${(v / 1e6).toFixed(0)}M`} />
                  <Tooltip formatter={(v: any) => fmt(v)} />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  {cmp.vendors.map((v: string, i: number) => (
                    <Bar key={v} dataKey={v} fill={['#3b82f6', '#22c55e', '#f59e0b'][i % 3]} />
                  ))}
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div>
              <b style={{ fontSize: 13 }}>공통 항목 단가차 (협상 우선순위)</b>
              <table>
                <thead><tr><th>항목</th>{cmp.vendors.map((v: string) => <th key={v}>{v}</th>)}<th>차이</th><th>유리</th></tr></thead>
                <tbody>
                  {cmp.common_items.map((c: any, i: number) => (
                    <tr key={i}>
                      <td>{c.name}</td>
                      {cmp.vendors.map((v: string) => <td key={v}>{fmt(c.prices[v])}</td>)}
                      <td>{c.spread_pct > 15 ? <span className="badge ng">{c.spread_pct}%</span> : `${c.spread_pct}%`}</td>
                      <td>{c.best_vendor}</td>
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

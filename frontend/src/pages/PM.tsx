import { useEffect, useState } from 'react'
import { api, judgeClass } from '../api'

export default function PM() {
  const [standards, setStandards] = useState<any[]>([])
  const [orders, setOrders] = useState<any[]>([])
  const [models, setModels] = useState<any[]>([])
  const [modelFilter, setModelFilter] = useState('')
  const [active, setActive] = useState<any>(null) // 수행중 오더
  const [results, setResults] = useState<Record<number, { measured_value: string; note: string }>>({})
  const [performer, setPerformer] = useState('')
  const [msg, setMsg] = useState('')

  const load = () => {
    api.get(`/pm/standards${modelFilter ? `?model_id=${modelFilter}` : ''}`).then(setStandards)
    api.get('/pm/orders').then(setOrders)
    api.get('/models').then(setModels)
  }
  useEffect(load, [modelFilter])

  const startPerform = async (order: any) => {
    const stds = await api.get(`/pm/standards?model_id=${order.equipment.model_id}`)
    setActive({ ...order, stds })
    setResults({})
    setMsg('')
  }

  const complete = async () => {
    const body = {
      performer,
      results: active.stds
        .filter((s: any) => results[s.id]?.measured_value !== undefined && results[s.id]?.measured_value !== '')
        .map((s: any) => ({
          standard_item_id: s.id,
          measured_value: Number(results[s.id].measured_value),
          method_used: s.method,
          note: results[s.id].note ?? '',
        })),
    }
    const done = await api.post(`/pm/orders/${active.id}/complete`, body)
    setMsg(`오더 #${done.id} 완료 — 판정: ${done.results.map((r: any) => r.judgment).join(', ')}`)
    setActive(null)
    load()
  }

  return (
    <div>
      <h2>PM (예방정비)</h2>

      <div className="panel">
        <h3 style={{ marginTop: 0 }}>PM 오더
          {' '}<button className="secondary" onClick={() => api.post('/pm/orders/generate').then((r) => { setMsg(`오더 ${r.created}건 자동 생성`); load() })}>주기 기반 자동 생성</button>
        </h3>
        {msg && <p className="muted">{msg}</p>}
        <table>
          <thead><tr><th>#</th><th>설비</th><th>계획일</th><th>상태</th><th>수행일</th><th>수행자</th><th></th></tr></thead>
          <tbody>
            {orders.map((o) => (
              <tr key={o.id}>
                <td>{o.id}</td><td>{o.equipment.asset_code}</td><td>{o.plan_date}</td>
                <td><span className={`badge ${o.status === 'DONE' ? 'ok' : o.status === 'OVERDUE' ? 'ng' : 'info'}`}>{o.status}</span></td>
                <td>{o.performed_date ?? '-'}</td><td>{o.performer || '-'}</td>
                <td>{o.status !== 'DONE' && <button onClick={() => startPerform(o)}>수행</button>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {active && (
        <div className="panel">
          <h3 style={{ marginTop: 0 }}>PM 수행 — 오더 #{active.id} ({active.equipment.asset_code})</h3>
          <label style={{ fontSize: 13 }}>수행자 <input value={performer} onChange={(e) => setPerformer(e.target.value)} /></label>
          <table style={{ marginTop: 10 }}>
            <thead><tr><th>항목</th><th>방법</th><th>기준</th><th>측정값</th><th>비고</th></tr></thead>
            <tbody>
              {active.stds.map((s: any) => (
                <tr key={s.id}>
                  <td>{s.item_no} {s.name}{s.vision_capable && <span className="badge info" style={{ marginLeft: 6 }}>VISION</span>}</td>
                  <td>{s.method}</td>
                  <td className="muted">{s.criteria} {s.lower_limit != null && `(${s.lower_limit}~${s.upper_limit ?? ''}${s.unit})`}</td>
                  <td><input style={{ width: 90 }} value={results[s.id]?.measured_value ?? ''}
                    onChange={(e) => setResults({ ...results, [s.id]: { ...results[s.id], measured_value: e.target.value } })} /> {s.unit}</td>
                  <td><input value={results[s.id]?.note ?? ''}
                    onChange={(e) => setResults({ ...results, [s.id]: { measured_value: results[s.id]?.measured_value ?? '', note: e.target.value } })} /></td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="muted">측정값 입력 시 표준 한계값으로 OK/CHECK/NG 자동 판정됩니다. 비전 항목은 [비전 측정] 메뉴에서 이미지 업로드로 측정할 수 있습니다.</p>
          <button onClick={complete}>완료 처리</button>{' '}
          <button className="secondary" onClick={() => setActive(null)}>취소</button>
        </div>
      )}

      <div className="panel">
        <h3 style={{ marginTop: 0 }}>표준 점검항목
          {' '}<select value={modelFilter} onChange={(e) => setModelFilter(e.target.value)}>
            <option value="">전체 모델</option>
            {models.map((m) => <option key={m.id} value={m.id}>{m.code}</option>)}
          </select>
        </h3>
        <table>
          <thead><tr><th>모델</th><th>No</th><th>항목</th><th>부위</th><th>방법</th><th>판정기준</th><th>주기(일)</th><th>비전</th><th>L&L</th></tr></thead>
          <tbody>
            {standards.map((s) => {
              const model = models.find((m) => m.id === s.model_id)
              return (
                <tr key={s.id}>
                  <td>{model?.code}</td><td>{s.item_no}</td><td>{s.name}</td><td>{s.part_area}</td>
                  <td><span className="badge gray">{s.method}</span></td>
                  <td>{s.criteria}</td><td>{s.period_days}</td>
                  <td>{s.vision_capable ? <span className="badge ok">가능</span> : '-'}</td>
                  <td>{s.origin_lesson_id ? <span className="badge check">L&L#{s.origin_lesson_id}</span> : '-'}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

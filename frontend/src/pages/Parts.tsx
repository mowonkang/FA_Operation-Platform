import { useEffect, useState } from 'react'
import { api } from '../api'

export default function Parts() {
  const [parts, setParts] = useState<any[]>([])
  const [bom, setBom] = useState<any[]>([])
  const [rec, setRec] = useState<any[]>([])
  const [tab, setTab] = useState<'stock' | 'rec' | 'bom'>('stock')

  const load = () => {
    api.get('/parts').then(setParts)
    api.get('/parts/bom').then(setBom)
    api.get('/parts/recommendation').then(setRec)
  }
  useEffect(load, [])

  const tx = async (partId: number, type: 'IN' | 'OUT') => {
    const qty = Number(prompt(`${type === 'IN' ? '입고' : '출고'} 수량?`, '1'))
    if (!qty) return
    try {
      await api.post('/parts/transactions', { part_id: partId, tx_type: type, qty, ref_type: 'PURCHASE' })
      load()
    } catch (e: any) { alert(e.message) }
  }

  return (
    <div>
      <h2>스페어 파츠</h2>
      <p>
        <button className={tab === 'stock' ? '' : 'secondary'} onClick={() => setTab('stock')}>재고 현황</button>{' '}
        <button className={tab === 'rec' ? '' : 'secondary'} onClick={() => setTab('rec')}>권장재고 / 선정 기초자료</button>{' '}
        <button className={tab === 'bom' ? '' : 'secondary'} onClick={() => setTab('bom')}>모델별 BOM</button>
      </p>

      {tab === 'stock' && (
        <table>
          <thead><tr><th>Part No</th><th>품명</th><th>분류</th><th>메이커</th><th>단가</th><th>L/T(일)</th><th>MTBF(h)</th><th>재고</th><th>최소</th><th></th></tr></thead>
          <tbody>
            {parts.map((p) => (
              <tr key={p.id}>
                <td>{p.part_no}</td><td>{p.name}</td><td>{p.category}</td><td>{p.maker}</td>
                <td>{p.unit_price.toLocaleString()}</td><td>{p.lead_time_days}</td><td>{p.mtbf_hours ?? '-'}</td>
                <td><span className={`badge ${p.current_stock < p.min_stock ? 'ng' : 'ok'}`}>{p.current_stock}</span></td>
                <td>{p.min_stock}</td>
                <td>
                  <button className="secondary" onClick={() => tx(p.id, 'IN')}>입고</button>{' '}
                  <button className="secondary" onClick={() => tx(p.id, 'OUT')}>출고</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {tab === 'rec' && (
        <>
          <p className="muted">
            연간 소요 = Σ(설비대수 × BOM수량 × 연간가동시간 / MTBF), 권장재고 = 리드타임 소요 + 안전재고(z=1.65).
            부족(shortage) 큰 순으로 정렬 — 발주 우선순위 기초자료.
          </p>
          <table>
            <thead><tr><th>Part No</th><th>품명</th><th>연간 예상소요</th><th>L/T</th><th>권장재고</th><th>현재고</th><th>부족</th><th>사용 모델</th></tr></thead>
            <tbody>
              {rec.map((r) => (
                <tr key={r.part_id}>
                  <td>{r.part_no}</td><td>{r.name}</td><td>{r.annual_demand}</td><td>{r.lead_time_days}일</td>
                  <td>{r.recommended_stock}</td><td>{r.current_stock}</td>
                  <td>{r.shortage > 0 ? <span className="badge ng">{r.shortage}</span> : <span className="badge ok">0</span>}</td>
                  <td className="muted">{r.used_on.map((u: any) => `${u.model}×${u.equipment_count}${u.critical ? '★' : ''}`).join(', ')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}

      {tab === 'bom' && (
        <table>
          <thead><tr><th>모델</th><th>Part No</th><th>품명</th><th>대당 수량</th><th>교체주기(月)</th><th>Critical</th></tr></thead>
          <tbody>
            {bom.map((b) => (
              <tr key={b.id}>
                <td>{b.model.code}</td><td>{b.part.part_no}</td><td>{b.part.name}</td>
                <td>{b.qty_per_unit}</td><td>{b.replace_cycle_months ?? '-'}</td>
                <td>{b.critical ? <span className="badge ng">★</span> : '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}

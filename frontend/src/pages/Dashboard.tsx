import { useEffect, useState } from 'react'
import { api } from '../api'

export default function Dashboard() {
  const [d, setD] = useState<any>(null)
  useEffect(() => { api.get('/dashboard').then(setD) }, [])
  if (!d) return <p>로딩중…</p>

  const kpis = [
    { label: '전체 설비', value: d.equipment_total },
    { label: '가동중 설비', value: d.equipment_running, cls: 'good' },
    { label: 'PM 준수율', value: `${d.pm_compliance_pct}%`, cls: d.pm_compliance_pct < 90 ? 'warn' : 'good' },
    { label: 'PM 계획', value: d.pm_planned },
    { label: 'PM 지연', value: d.pm_overdue, cls: d.pm_overdue > 0 ? 'bad' : 'good' },
    { label: 'BM 미결', value: d.bm_open, cls: d.bm_open > 0 ? 'warn' : 'good' },
    { label: '총 다운타임(분)', value: d.total_downtime_min },
    { label: 'FDC 미처리 알람', value: d.fdc_alarms_open, cls: d.fdc_alarms_open > 0 ? 'bad' : 'good' },
    { label: '재고 부족 파츠', value: d.parts_below_min_stock, cls: d.parts_below_min_stock > 0 ? 'warn' : 'good' },
    { label: 'L&L 등록', value: d.lessons_total },
    { label: 'L&L 법인 적용률', value: `${d.lesson_apply_rate_pct}%`, cls: d.lesson_apply_rate_pct < 80 ? 'warn' : 'good' },
  ]

  return (
    <div>
      <h2>운영 대시보드</h2>
      <div className="cards">
        {kpis.map((k) => (
          <div className="card" key={k.label}>
            <div className="label">{k.label}</div>
            <div className={`value ${k.cls ?? ''}`}>{k.value}</div>
          </div>
        ))}
      </div>
      <p className="muted" style={{ marginTop: 16 }}>
        PM 준수율 = 완료 / (완료 + 지연). FDC 알람·재고 부족은 즉시 조치 대상입니다.
      </p>
    </div>
  )
}

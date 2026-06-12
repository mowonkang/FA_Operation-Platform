import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend, ComposedChart, Line,
} from 'recharts'
import { api } from '../api'
import { useSite, sq } from '../site'

const PM_COLORS: Record<string, string> = {
  DONE: '#22c55e', PLANNED: '#3b82f6', IN_PROGRESS: '#f59e0b', OVERDUE: '#ef4444',
}

export default function Dashboard() {
  const [d, setD] = useState<any>(null)
  const [err, setErr] = useState('')
  const [overdue, setOverdue] = useState<any[]>([])
  const [alarms, setAlarms] = useState<any[]>([])
  const [issues, setIssues] = useState<any[]>([])
  const [shortage, setShortage] = useState<any[]>([])

  const { site } = useSite()
  useEffect(() => {
    api.get(`/dashboard${sq(site)}`).then(setD).catch((e) => setErr(String(e.message ?? e)))
    api.get(sq(site, '/pm/orders?status=OVERDUE')).then(setOverdue).catch(() => {})
    api.get(sq(site, '/fdc/alarms?status=OPEN')).then(setAlarms).catch(() => {})
    api.get(sq(site, '/issues?status=OPEN'))
      .then((l) => setIssues(l.filter((i: any) => i.severity === 'HIGH'))).catch(() => {})
    api.get('/parts/recommendation')
      .then((r) => setShortage(r.filter((p: any) => p.shortage > 0))).catch(() => {})
  }, [site])

  if (err) return (
    <div className="panel">
      <div className="panel-title">백엔드 연결 실패</div>
      <p className="error">{err}</p>
      <p className="muted">
        백엔드(8000)가 실행 중인지, 최신 코드로 재시작했는지 확인하세요:
        <code> cd backend → uvicorn app.main:app --reload --port 8000</code>.
        데모 데이터가 없으면 프로젝트 루트의 <code>reset_demo.ps1</code> 을 실행하세요.
      </p>
    </div>
  )
  if (!d) return <p className="muted">로딩중…</p>

  const weekly = d.weekly_bm ?? []
  const pmDist = d.pm_status_dist ?? {}
  const alarmDist = d.alarm_classification_dist ?? []
  const availability = d.availability_pct ??
    (d.equipment_total ? Math.round((d.equipment_running / d.equipment_total) * 1000) / 10 : 0)

  const primary = [
    { label: '설비 가동률', value: availability, unit: '%', sub: `${d.equipment_running}/${d.equipment_total} 대 가동중`,
      cls: availability >= 90 ? 'ok' : availability >= 70 ? 'warn' : 'ng' },
    { label: 'PM 준수율', value: d.pm_compliance_pct, unit: '%', sub: `완료 ${d.pm_done} · 지연 ${d.pm_overdue}`,
      cls: d.pm_compliance_pct >= 90 ? 'ok' : d.pm_compliance_pct >= 70 ? 'warn' : 'ng' },
    { label: '미결 BM', value: d.bm_open, unit: '건', sub: `누적 다운타임 ${(d.total_downtime_min ?? 0).toLocaleString()}분`,
      cls: d.bm_open === 0 ? 'ok' : d.bm_open <= 2 ? 'warn' : 'ng' },
    { label: 'OPEN 알람 (FDC)', value: d.fdc_alarms_open, unit: '건', sub: '미조치 이상감지',
      cls: d.fdc_alarms_open === 0 ? 'ok' : 'ng' },
  ]
  const secondary = [
    { label: 'PM 계획', value: d.pm_planned, to: '/pm' },
    { label: '재고부족 파츠', value: d.parts_below_min_stock, to: '/parts', bad: d.parts_below_min_stock > 0 },
    { label: 'HIGH 이슈 미결', value: issues.length, to: '/issues', bad: issues.length > 0 },
    { label: 'L&L 등록', value: d.lessons_total, to: '/lessons' },
    { label: 'L&L 법인 적용률', value: `${d.lesson_apply_rate_pct}%`, to: '/lessons',
      bad: d.lesson_apply_rate_pct < 80 },
  ]

  const actionCount = overdue.length + alarms.length + issues.length + shortage.length
  const pmPie = Object.entries(pmDist).map(([name, value]) => ({ name, value }))

  return (
    <div>
      <div className="cards kpi-primary">
        {primary.map((k) => (
          <div className={`card status-${k.cls}`} key={k.label}>
            <div className="label">{k.label}</div>
            <div className={`value ${k.cls === 'ng' ? 'bad' : k.cls === 'warn' ? 'warn' : ''}`}>
              {k.value}<span className="unit">{k.unit}</span>
            </div>
            <div className="sub">{k.sub}</div>
          </div>
        ))}
      </div>

      <div className="cards" style={{ marginTop: 10 }}>
        {secondary.map((k) => (
          <Link to={k.to} key={k.label} style={{ textDecoration: 'none', color: 'inherit' }}>
            <div className="card status-neutral">
              <div className="label">{k.label}</div>
              <div className={`value ${k.bad ? 'bad' : ''}`} style={{ fontSize: 19 }}>{k.value}</div>
            </div>
          </Link>
        ))}
      </div>

      <div className="row" style={{ marginTop: 16 }}>
        {/* 액션 큐 — 오늘 조치 대상 */}
        <div className="panel" style={{ flex: 1.2 }}>
          <div className="panel-title">
            오늘의 조치 대상
            <span className={`badge ${actionCount ? 'ng' : 'ok'}`}>{actionCount}건</span>
            <span className="hint">우선순위순 — 클릭하여 해당 화면으로 이동</span>
          </div>
          {actionCount === 0 && <p className="muted">조치 대상이 없습니다.</p>}
          {alarms.map((a) => (
            <div className="action-item" key={`a${a.id}`}>
              <span className={`badge ${a.level === 'ALARM' ? 'ng' : 'check'}`}>{a.level}</span>
              <span className="ai-text"><Link to="/fdc">{a.message}</Link></span>
              <span className="ai-meta">{a.classification} · {a.ts?.slice(5, 16).replace('T', ' ')}</span>
            </div>
          ))}
          {issues.map((i) => (
            <div className="action-item" key={`i${i.id}`}>
              <span className="badge ng">HIGH</span>
              <span className="ai-text"><Link to="/issues">[{i.domain}] {i.title}</Link></span>
              <span className="ai-meta">담당 {i.owner || '미정'}</span>
            </div>
          ))}
          {overdue.map((o) => (
            <div className="action-item" key={`o${o.id}`}>
              <span className="badge check">PM지연</span>
              <span className="ai-text"><Link to="/pm">{o.equipment.asset_code} PM 오더 #{o.id}</Link></span>
              <span className="ai-meta">계획일 {o.plan_date}</span>
            </div>
          ))}
          {shortage.map((p) => (
            <div className="action-item" key={`p${p.part_id}`}>
              <span className="badge check">발주</span>
              <span className="ai-text"><Link to="/parts">{p.part_no} {p.name}</Link></span>
              <span className="ai-meta">부족 {p.shortage} (권장 {p.recommended_stock} / 현 {p.current_stock}) · L/T {p.lead_time_days}일</span>
            </div>
          ))}
        </div>

        {/* PM 상태 분포 */}
        <div className="panel" style={{ flex: 0.8, minWidth: 260 }}>
          <div className="panel-title">PM 오더 상태</div>
          <ResponsiveContainer width="100%" height={190}>
            <PieChart>
              <Pie data={pmPie} dataKey="value" nameKey="name" innerRadius={45} outerRadius={70}
                paddingAngle={2}>
                {pmPie.map((e: any) => <Cell key={e.name} fill={PM_COLORS[e.name] ?? '#8492a6'} />)}
              </Pie>
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="row">
        <div className="panel">
          <div className="panel-title">주간 BM 발생 · 다운타임 추이 <span className="hint">최근 8주</span></div>
          <ResponsiveContainer width="100%" height={200}>
            <ComposedChart data={weekly}>
              <XAxis dataKey="week" fontSize={11} />
              <YAxis yAxisId="l" fontSize={11} allowDecimals={false} />
              <YAxis yAxisId="r" orientation="right" fontSize={11} />
              <Tooltip />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Bar yAxisId="l" dataKey="bm_count" fill="#3b82f6" name="BM 건수" barSize={18} />
              <Line yAxisId="r" dataKey="downtime_min" stroke="#ef4444" name="다운타임(분)" strokeWidth={2} dot={false} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
        <div className="panel">
          <div className="panel-title">FDC 알람 분류 분포 <span className="hint">LEVEL=한계 / SPIKE=충격성 / DRIFT=열화 진행</span></div>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={alarmDist} layout="vertical">
              <XAxis type="number" fontSize={11} allowDecimals={false} />
              <YAxis type="category" dataKey="name" fontSize={11} width={90} />
              <Tooltip />
              <Bar dataKey="count" fill="#f59e0b" barSize={16} name="건수" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}

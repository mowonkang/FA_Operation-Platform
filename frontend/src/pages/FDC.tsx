import { useEffect, useState } from 'react'
import { LineChart, Line, XAxis, YAxis, Tooltip, ReferenceLine, ResponsiveContainer } from 'recharts'
import { api } from '../api'
import { useSite, sq } from '../site'

export default function FDC() {
  const [sensors, setSensors] = useState<any[]>([])
  const [alarms, setAlarms] = useState<any[]>([])
  const [sensorId, setSensorId] = useState<number | null>(null)
  const [readings, setReadings] = useState<any[]>([])
  const [msg, setMsg] = useState('')

  const { site } = useSite()
  const load = () => {
    api.get(`/fdc/sensors${sq(site)}`).then((s) => {
      setSensors(s)
      if (s.length && sensorId === null) setSensorId(s[0].id)
    })
    api.get(sq(site, '/fdc/alarms')).then(setAlarms)
  }
  useEffect(load, [site])
  useEffect(() => {
    if (sensorId != null) {
      api.get(`/fdc/readings?sensor_id=${sensorId}&limit=200`).then((rs) =>
        setReadings(rs.map((r: any) => ({ ...r, t: r.ts.slice(11, 16) }))))
    }
  }, [sensorId])

  const sensor = sensors.find((s) => s.id === sensorId)

  const simulate = async () => {
    if (!sensorId) return
    const r = await api.post(`/fdc/simulate?sensor_id=${sensorId}&hours=24`)
    setMsg(`수집 ${r.ingested}건, 알람 ${r.alarms_raised}건 발생`)
    load()
    api.get(`/fdc/readings?sensor_id=${sensorId}&limit=200`).then((rs) =>
      setReadings(rs.map((x: any) => ({ ...x, t: x.ts.slice(11, 16) }))))
  }

  const toBM = async (alarmId: number) => {
    const r = await api.post(`/fdc/alarms/${alarmId}/to-bm`)
    setMsg(`알람 #${alarmId} → BM 보고 #${r.id} 생성`)
    load()
  }

  return (
    <div>
      <h2>FDC (Fault Detection & Classification)</h2>
      <div className="panel">
        <h3 style={{ marginTop: 0 }}>
          센서 트렌드{' '}
          <select value={sensorId ?? ''} onChange={(e) => setSensorId(Number(e.target.value))}>
            {sensors.map((s) => <option key={s.id} value={s.id}>{s.name} ({s.unit})</option>)}
          </select>{' '}
          <button className="secondary" onClick={simulate}>데모 데이터 수집 (24h)</button>
        </h3>
        {msg && <p className="muted">{msg}</p>}
        <ResponsiveContainer width="100%" height={260}>
          <LineChart data={readings}>
            <XAxis dataKey="t" minTickGap={40} fontSize={11} />
            <YAxis domain={['auto', 'auto']} fontSize={11} />
            <Tooltip />
            {sensor?.warn_high != null && <ReferenceLine y={sensor.warn_high} stroke="#d97706" strokeDasharray="4 4" label={{ value: 'WARN', fontSize: 10 }} />}
            {sensor?.alarm_high != null && <ReferenceLine y={sensor.alarm_high} stroke="#dc2626" strokeDasharray="4 4" label={{ value: 'ALARM', fontSize: 10 }} />}
            <Line type="monotone" dataKey="value" stroke="#2563eb" dot={false} strokeWidth={1.5} />
          </LineChart>
        </ResponsiveContainer>
        <p className="muted">룰: 레벨 상·하한 / 스파이크(4σ) / 드리프트(워닝한계 70% 접근). 운영 시 게이트웨이가 POST /api/v1/fdc/ingest 로 전송.</p>
      </div>

      <div className="panel">
        <h3 style={{ marginTop: 0 }}>알람</h3>
        <table>
          <thead><tr><th>#</th><th>시각</th><th>설비</th><th>센서</th><th>레벨</th><th>분류</th><th>값</th><th>상태</th><th></th></tr></thead>
          <tbody>
            {alarms.map((a) => (
              <tr key={a.id}>
                <td>{a.id}</td><td>{a.ts?.slice(0, 16).replace('T', ' ')}</td>
                <td>{a.sensor?.equipment_id}</td><td>{a.sensor?.name}</td>
                <td><span className={`badge ${a.level === 'ALARM' ? 'ng' : 'check'}`}>{a.level}</span></td>
                <td>{a.classification}</td><td>{a.value}</td>
                <td><span className={`badge ${a.status === 'OPEN' ? 'ng' : 'gray'}`}>{a.status}</span></td>
                <td>
                  {a.status === 'OPEN' && (
                    <>
                      <button className="secondary" onClick={() => api.patch(`/fdc/alarms/${a.id}?status=ACK`).then(load)}>ACK</button>{' '}
                      <button onClick={() => toBM(a.id)}>BM 전환</button>
                    </>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

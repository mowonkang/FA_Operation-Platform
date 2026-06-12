import { NavLink, Route, Routes, useLocation } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Equipment from './pages/Equipment'
import EquipmentDetail from './pages/EquipmentDetail'
import PM from './pages/PM'
import BM from './pages/BM'
import Vision from './pages/Vision'
import Parts from './pages/Parts'
import Engineering from './pages/Engineering'
import FDC from './pages/FDC'
import Lessons from './pages/Lessons'
import Workflows from './pages/Workflows'
import Knowledge from './pages/Knowledge'
import Lifecycle from './pages/Lifecycle'
import Investment from './pages/Investment'
import Issues from './pages/Issues'

const groups: { name: string; items: { to: string; label: string; ico: string }[] }[] = [
  {
    name: '모니터링',
    items: [
      { to: '/', label: '대시보드', ico: '▦' },
      { to: '/fdc', label: 'FDC 트렌드/알람', ico: '∿' },
      { to: '/issues', label: '이슈 관리', ico: '⚑' },
    ],
  },
  {
    name: '라이프사이클',
    items: [
      { to: '/lifecycle', label: '라이프사이클 맵', ico: '⇶' },
      { to: '/investment', label: '투자·견적 분석', ico: '₩' },
      { to: '/equipment', label: '설비 마스터/이력', ico: '▣' },
      { to: '/workflows', label: '워크플로우', ico: '☑' },
    ],
  },
  {
    name: '정비 운영',
    items: [
      { to: '/pm', label: 'PM 표준/오더', ico: '◔' },
      { to: '/bm', label: 'BM 고장정비', ico: '✕' },
      { to: '/vision', label: '비전 측정', ico: '◎' },
      { to: '/parts', label: '스페어 파츠', ico: '⬡' },
    ],
  },
  {
    name: '엔지니어링',
    items: [
      { to: '/engineering', label: '계산 툴 (PRO)', ico: 'ƒ' },
      { to: '/knowledge', label: '지식 DB·표준', ico: '§' },
      { to: '/lessons', label: 'Lesson & Learn', ico: '↻' },
    ],
  },
]

const titleMap: Record<string, string> = Object.fromEntries(
  groups.flatMap((g) => g.items.map((i) => [i.to, i.label])),
)

export default function App() {
  const loc = useLocation()
  const base = '/' + (loc.pathname.split('/')[1] ?? '')
  const group = groups.find((g) => g.items.some((i) => i.to === base))
  return (
    <div className="layout">
      <nav className="sidebar">
        <div className="brand">
          <b>FA Operation Platform</b>
          <span>물류설비 생애주기 운영</span>
        </div>
        {groups.map((g) => (
          <div key={g.name}>
            <div className="group">{g.name}</div>
            {g.items.map((m) => (
              <NavLink key={m.to} to={m.to} end={m.to === '/'}
                className={({ isActive }) => (isActive ? 'active' : '')}>
                <span className="ico">{m.ico}</span>{m.label}
              </NavLink>
            ))}
          </div>
        ))}
      </nav>
      <main className="main">
        <div className="topbar">
          <h1>{titleMap[base] ?? 'FA Operation Platform'}</h1>
          {group && <span className="crumb">{group.name}</span>}
          <div className="right">
            <span className="badge gray">KR1 한국 본사</span>
            <span>{new Date().toLocaleDateString('ko-KR')}</span>
          </div>
        </div>
        <div className="content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/lifecycle" element={<Lifecycle />} />
            <Route path="/investment" element={<Investment />} />
            <Route path="/issues" element={<Issues />} />
            <Route path="/equipment" element={<Equipment />} />
            <Route path="/equipment/:id" element={<EquipmentDetail />} />
            <Route path="/pm" element={<PM />} />
            <Route path="/bm" element={<BM />} />
            <Route path="/vision" element={<Vision />} />
            <Route path="/parts" element={<Parts />} />
            <Route path="/engineering" element={<Engineering />} />
            <Route path="/fdc" element={<FDC />} />
            <Route path="/lessons" element={<Lessons />} />
            <Route path="/workflows" element={<Workflows />} />
            <Route path="/knowledge" element={<Knowledge />} />
          </Routes>
        </div>
      </main>
    </div>
  )
}

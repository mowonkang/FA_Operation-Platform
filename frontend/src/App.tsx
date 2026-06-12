import { NavLink, Route, Routes } from 'react-router-dom'
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

const menu = [
  { to: '/', label: '대시보드' },
  { to: '/lifecycle', label: '라이프사이클 맵' },
  { to: '/investment', label: '투자 (견적분석)' },
  { to: '/equipment', label: '설비 / 이력' },
  { to: '/issues', label: '이슈 관리' },
  { to: '/pm', label: 'PM 표준 / 오더' },
  { to: '/bm', label: 'BM (고장정비)' },
  { to: '/vision', label: '비전 측정' },
  { to: '/parts', label: '스페어 파츠' },
  { to: '/engineering', label: '엔지니어링 검토' },
  { to: '/fdc', label: 'FDC 모니터링' },
  { to: '/lessons', label: 'Lesson & Learn' },
  { to: '/workflows', label: '워크플로우' },
  { to: '/knowledge', label: '지식 DB' },
]

export default function App() {
  return (
    <div className="layout">
      <nav className="sidebar">
        <h1>FA Operation Platform</h1>
        {menu.map((m) => (
          <NavLink key={m.to} to={m.to} end={m.to === '/'}
            className={({ isActive }) => (isActive ? 'active' : '')}>
            {m.label}
          </NavLink>
        ))}
      </nav>
      <main className="main">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/equipment" element={<Equipment />} />
          <Route path="/equipment/:id" element={<EquipmentDetail />} />
          <Route path="/pm" element={<PM />} />
          <Route path="/bm" element={<BM />} />
          <Route path="/vision" element={<Vision />} />
          <Route path="/parts" element={<Parts />} />
          <Route path="/engineering" element={<Engineering />} />
          <Route path="/fdc" element={<FDC />} />
          <Route path="/lessons" element={<Lessons />} />
          <Route path="/lifecycle" element={<Lifecycle />} />
          <Route path="/investment" element={<Investment />} />
          <Route path="/issues" element={<Issues />} />
          <Route path="/workflows" element={<Workflows />} />
          <Route path="/knowledge" element={<Knowledge />} />
        </Routes>
      </main>
    </div>
  )
}

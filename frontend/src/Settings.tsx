import { useEffect, useState } from 'react'

/* 설정창 (⚙) — 테마/밀도/역할/기본 사이트. localStorage 에 저장된다. */

export type AppSettings = {
  theme: string      // light / dark / petrol / contrast
  density: string    // normal / compact
  role: string       // user / admin
}

export const THEMES = [
  { v: 'light', label: '라이트', swatch: '#eef0f3', desc: '사무 환경 기본' },
  { v: 'dark', label: '다크', swatch: '#0d1117', desc: '관제실·야간 (Siemens iX Classic 계열)' },
  { v: 'petrol', label: '페트롤', swatch: '#00c1b6', desc: '청록 액센트 다크 (iX Brand 계열)' },
  { v: 'contrast', label: '고대비', swatch: '#000000', desc: '밝은 현장·프로젝터' },
]

export function loadSettings(): AppSettings {
  return {
    theme: localStorage.getItem('fa_theme') ?? 'light',
    density: localStorage.getItem('fa_density') ?? 'normal',
    role: localStorage.getItem('fa_role') ?? 'user',
  }
}

export function applySettings(s: AppSettings) {
  document.documentElement.dataset.theme = s.theme
  document.documentElement.dataset.density = s.density
  localStorage.setItem('fa_theme', s.theme)
  localStorage.setItem('fa_density', s.density)
  localStorage.setItem('fa_role', s.role)
}

export default function SettingsModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [s, setS] = useState<AppSettings>(loadSettings())

  useEffect(() => { applySettings(s) }, [s])
  useEffect(() => { if (open) setS(loadSettings()) }, [open])

  if (!open) return null
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h3>⚙ 설정</h3>
        <p className="muted" style={{ margin: '0 0 6px' }}>이 브라우저에 저장되며 즉시 적용됩니다.</p>

        <div className="set-row">
          <div className="sr-label">테마
            <div className="sr-desc">화면 환경에 맞게 선택</div>
          </div>
          <div className="theme-chips">
            {THEMES.map((t) => (
              <div key={t.v} className={`theme-chip ${s.theme === t.v ? 'on' : ''}`}
                title={t.desc} onClick={() => setS({ ...s, theme: t.v })}>
                <span className="swatch" style={{ background: t.swatch }} />{t.label}
              </div>
            ))}
          </div>
        </div>

        <div className="set-row">
          <div className="sr-label">표시 밀도
            <div className="sr-desc">컴팩트 = 더 많은 행 표시</div>
          </div>
          <div className="theme-chips">
            {[{ v: 'normal', label: '보통' }, { v: 'compact', label: '컴팩트' }].map((d) => (
              <div key={d.v} className={`theme-chip ${s.density === d.v ? 'on' : ''}`}
                onClick={() => setS({ ...s, density: d.v })}>{d.label}</div>
            ))}
          </div>
        </div>

        <div className="set-row">
          <div className="sr-label">역할
            <div className="sr-desc">프로젝트 삭제 등 관리자 기능 — 운영 전환 시 SSO/RBAC 대체 예정</div>
          </div>
          <div className="theme-chips">
            {[{ v: 'user', label: '일반 사용자' }, { v: 'admin', label: '관리자' }].map((r) => (
              <div key={r.v} className={`theme-chip ${s.role === r.v ? 'on' : ''}`}
                onClick={() => setS({ ...s, role: r.v })}>{r.label}</div>
            ))}
          </div>
        </div>

        <div style={{ marginTop: 14, textAlign: 'right' }}>
          <button onClick={onClose}>닫기</button>
        </div>
      </div>
    </div>
  )
}

import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'

// module_key → 플랫폼 화면 라우트 (블럭 연결)
const MODULE_ROUTE: Record<string, string> = {
  quotation: '/investment', knowledge: '/knowledge', params: '/equipment',
  issues: '/issues', pm: '/pm', bm: '/bm', vision: '/vision', fdc: '/fdc',
  parts: '/parts', lessons: '/lessons', engineering: '/engineering',
}

function moduleLink(key: string): { to: string; label: string } | null {
  if (!key) return null
  if (key.startsWith('workflow:')) return { to: '/workflows', label: `워크플로우 ${key.split(':')[1]}` }
  const to = MODULE_ROUTE[key]
  return to ? { to, label: '모듈 열기' } : null
}

export default function Lifecycle() {
  const [phases, setPhases] = useState<any[]>([])
  const [edit, setEdit] = useState(false)
  const [newProc, setNewProc] = useState<any>(null) // {phase_id, name, description}
  const [newPhase, setNewPhase] = useState<any>(null)

  const load = () => api.get('/lifecycle-config/map').then(setPhases)
  useEffect(() => { load() }, [])

  const renameProc = async (pr: any) => {
    const name = prompt('프로세스 이름 변경', pr.name)
    if (name && name !== pr.name) {
      await api.patch(`/lifecycle-config/processes/${pr.id}`, { name })
      load()
    }
  }
  const editDesc = async (pr: any) => {
    const description = prompt('설명 수정', pr.description)
    if (description !== null) {
      await api.patch(`/lifecycle-config/processes/${pr.id}`, { description })
      load()
    }
  }
  const delProc = async (pr: any) => {
    if (confirm(`'${pr.name}' 프로세스를 삭제할까요?`)) {
      await fetch(`/api/v1/lifecycle-config/processes/${pr.id}`, { method: 'DELETE' })
      load()
    }
  }
  const moveProc = async (p: any, pr: any, dir: number) => {
    // 전체 재번호 방식: 이웃과 자리 교환 후 1..n 정수로 정규화 (seq 중복에도 안전)
    const sorted = [...p.processes].sort((a: any, b: any) => a.seq - b.seq || a.id - b.id)
    const idx = sorted.findIndex((x: any) => x.id === pr.id)
    const j = idx + dir
    if (j < 0 || j >= sorted.length) return
    ;[sorted[idx], sorted[j]] = [sorted[j], sorted[idx]]
    await Promise.all(sorted.map((x: any, i: number) =>
      api.patch(`/lifecycle-config/processes/${x.id}`, { seq: i + 1 })))
    load()
  }
  const renamePhase = async (p: any) => {
    const name = prompt('단계 이름 변경', p.name)
    if (name && name !== p.name) {
      await api.patch(`/lifecycle-config/phases/${p.id}`, { name })
      load()
    }
  }
  const addProc = async () => {
    await api.post('/lifecycle-config/processes', {
      phase_id: newProc.phase_id, code: `CUSTOM_${Date.now() % 100000}`,
      name: newProc.name, description: newProc.description ?? '', seq: 99,
    })
    setNewProc(null)
    load()
  }
  const addPhase = async () => {
    await api.post('/lifecycle-config/phases', {
      code: `PHASE_${Date.now() % 100000}`, name: newPhase.name,
      seq: phases.length + 1, description: newPhase.description ?? '',
    })
    setNewPhase(null)
    load()
  }

  return (
    <div>
      <h2>설비 라이프사이클 맵{' '}
        <button className={edit ? '' : 'secondary'} onClick={() => setEdit(!edit)}>
          {edit ? '편집 종료' : '✏ 편집 모드'}
        </button>{' '}
        {edit && <button className="secondary" onClick={() => setNewPhase({ name: '' })}>+ 단계 추가</button>}
      </h2>
      <p className="muted">
        투자 → 제작 → 셋업 → 양산 → 폐기/이설. 모든 단계·프로세스는 추가/이름변경/수정/삭제/순서변경이 가능하며,
        각 프로세스(블럭)는 플랫폼 모듈에 연결됩니다.
      </p>

      {newPhase && (
        <div className="panel">
          <input placeholder="새 단계 이름" value={newPhase.name}
            onChange={(e) => setNewPhase({ ...newPhase, name: e.target.value })} />{' '}
          <button disabled={!newPhase.name} onClick={addPhase}>추가</button>{' '}
          <button className="secondary" onClick={() => setNewPhase(null)}>취소</button>
        </div>
      )}

      {phases.map((p) => (
        <div className="panel" key={p.id}>
          <h3 style={{ marginTop: 0 }}>
            <span className="badge info">{p.seq}</span> {p.name}
            {edit && (
              <>
                {' '}<button className="secondary" onClick={() => renamePhase(p)}>이름변경</button>{' '}
                <button className="secondary" onClick={() => setNewProc({ phase_id: p.id, name: '' })}>+ 프로세스</button>
              </>
            )}
          </h3>
          <p className="muted" style={{ marginTop: 0 }}>{p.description}</p>
          <div className="cards">
            {p.processes.map((pr: any) => {
              const link = moduleLink(pr.module_key)
              return (
                <div className="card" key={pr.id}>
                  <div style={{ fontWeight: 700, fontSize: 13 }}>{pr.name}</div>
                  <div className="muted" style={{ marginTop: 4, minHeight: 40 }}>{pr.description}</div>
                  <div style={{ marginTop: 6 }}>
                    {link && <Link to={link.to} style={{ fontSize: 12 }}>→ {link.label}</Link>}
                    {edit && (
                      <div style={{ marginTop: 6, display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                        <button className="secondary" style={{ padding: '2px 6px', fontSize: 11 }} onClick={() => moveProc(p, pr, -1)}>◀</button>
                        <button className="secondary" style={{ padding: '2px 6px', fontSize: 11 }} onClick={() => moveProc(p, pr, 1)}>▶</button>
                        <button className="secondary" style={{ padding: '2px 6px', fontSize: 11 }} onClick={() => renameProc(pr)}>이름</button>
                        <button className="secondary" style={{ padding: '2px 6px', fontSize: 11 }} onClick={() => editDesc(pr)}>설명</button>
                        <button className="secondary" style={{ padding: '2px 6px', fontSize: 11, color: '#dc2626' }} onClick={() => delProc(pr)}>삭제</button>
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
          {newProc?.phase_id === p.id && (
            <div style={{ marginTop: 10 }}>
              <input placeholder="프로세스 이름" value={newProc.name}
                onChange={(e) => setNewProc({ ...newProc, name: e.target.value })} />{' '}
              <input placeholder="설명 (선택)" style={{ width: 300 }} value={newProc.description ?? ''}
                onChange={(e) => setNewProc({ ...newProc, description: e.target.value })} />{' '}
              <button disabled={!newProc.name} onClick={addProc}>추가</button>{' '}
              <button className="secondary" onClick={() => setNewProc(null)}>취소</button>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

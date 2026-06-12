import { useEffect, useState } from 'react'
import { api } from '../api'

export default function Knowledge() {
  const [cats, setCats] = useState<any[]>([])
  const [articles, setArticles] = useState<any[]>([])
  const [cat, setCat] = useState('')
  const [q, setQ] = useState('')
  const [sel, setSel] = useState<any>(null)

  const load = () => {
    api.get('/knowledge/categories').then(setCats)
    const params = new URLSearchParams()
    if (cat) params.set('category', cat)
    if (q) params.set('q', q)
    api.get(`/knowledge?${params.toString()}`).then(setArticles)
  }
  useEffect(load, [cat])

  return (
    <div>
      <h2>엔지니어링 지식 DB</h2>
      <p className="muted">표준·논문·기술문헌 조사 기반 물류설비 엔지니어링 지식. 출처 링크 포함 — DR/PM 표준 수립의 근거자료.</p>
      <p>
        <button className={cat === '' ? '' : 'secondary'} onClick={() => setCat('')}>전체</button>{' '}
        {cats.map((c) => (
          <span key={c.code}>
            <button className={cat === c.code ? '' : 'secondary'} onClick={() => setCat(c.code)}>
              {c.label} ({c.count})
            </button>{' '}
          </span>
        ))}
      </p>
      <p>
        <input placeholder="검색 (제목·본문·태그)" value={q} onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && load()} style={{ width: 300 }} />{' '}
        <button onClick={load}>검색</button>
      </p>

      <div className="row">
        <div>
          <table>
            <thead><tr><th>분류</th><th>주제</th><th>제목</th></tr></thead>
            <tbody>
              {articles.map((a) => (
                <tr key={a.id} onClick={() => setSel(a)} style={{ cursor: 'pointer',
                  background: sel?.id === a.id ? 'var(--row-selected)' : undefined }}>
                  <td><span className="badge gray">{a.category}</span></td>
                  <td>{a.topic}</td>
                  <td>{a.title}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="panel">
          {!sel && <p className="muted">왼쪽 목록에서 항목을 선택하세요.</p>}
          {sel && (
            <>
              <h3 style={{ marginTop: 0 }}>{sel.title}</h3>
              <p><b>{sel.summary}</b></p>
              <div style={{ whiteSpace: 'pre-wrap', fontSize: 13, lineHeight: 1.7 }}>{sel.content}</div>
              {sel.sources?.length > 0 && (
                <>
                  <h3>출처</h3>
                  <ul style={{ fontSize: 13 }}>
                    {sel.sources.map((s: any, i: number) => (
                      <li key={i}>
                        {s.url ? <a href={s.url} target="_blank" rel="noreferrer">{s.title}</a> : `${s.title} (${s.ref ?? ''})`}
                      </li>
                    ))}
                  </ul>
                </>
              )}
              <p className="muted">태그: {sel.tags}</p>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

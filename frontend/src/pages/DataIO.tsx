import { useEffect, useState } from 'react'
import { api } from '../api'

/* 항목별 엑셀 입출력 — 양식 다운로드 → 데이터 입력 → 가져오기(DB 반영) / 현재 데이터 내보내기 */

export default function DataIO() {
  const [entities, setEntities] = useState<any[]>([])
  const [result, setResult] = useState<any>(null)
  const [busy, setBusy] = useState('')
  const [err, setErr] = useState('')
  const [expanded, setExpanded] = useState<string | null>(null)

  useEffect(() => { api.get('/excel/entities').then(setEntities).catch(() => {}) }, [])

  const importFile = async (key: string, file: File | null) => {
    if (!file) return
    setBusy(key); setErr(''); setResult(null)
    try {
      const fd = new FormData()
      fd.append('file', file)
      setResult(await api.upload(`/excel/import/${key}`, fd))
    } catch (e: any) { setErr(e.message) } finally { setBusy('') }
  }

  return (
    <div>
      <p className="page-desc">
        각 항목의 <b>엑셀 양식을 내려받아 데이터를 채운 뒤 업로드</b>하면 DB에 반영됩니다 (코드 기준 생성/갱신).
        현재 데이터는 언제든 엑셀로 내보낼 수 있습니다. 양식의 '작성안내' 시트에 컬럼 설명이 있습니다.
      </p>

      {result && (
        <div className="panel" style={{ borderLeft: `4px solid var(${result.error_count ? '--warn' : '--ok'})` }}>
          <div className="panel-title">
            가져오기 결과 — {entities.find((e) => e.key === result.entity)?.label}
            <span className="badge ok">생성 {result.created}</span>
            <span className="badge info">갱신 {result.updated}</span>
            {result.error_count > 0 && <span className="badge ng">오류 {result.error_count}</span>}
          </div>
          {result.errors?.length > 0 && (
            <table>
              <thead><tr><th style={{ width: 80 }}>행</th><th>오류 내용</th></tr></thead>
              <tbody>
                {result.errors.map((e: any, i: number) => (
                  <tr key={i}><td className="num">{e.row}</td><td>{e.error}</td></tr>
                ))}
              </tbody>
            </table>
          )}
          {result.error_count > 0 && result.created + result.updated === 0 &&
            <p className="muted">전체 실패 시 DB 에 반영되지 않습니다 — 오류 수정 후 재업로드하세요.</p>}
        </div>
      )}
      {err && <div className="error">{err}</div>}

      <table>
        <thead><tr><th>항목</th><th>방식</th><th>설명</th><th style={{ width: 380 }}>작업</th></tr></thead>
        <tbody>
          {entities.map((e) => (
            <>
              <tr key={e.key}>
                <td><b>{e.label}</b></td>
                <td>{e.insert_only ? <span className="badge gray">추가 전용</span>
                  : <span className="badge info">생성/갱신</span>}</td>
                <td className="muted">{e.desc}{' '}
                  <a style={{ cursor: 'pointer' }}
                    onClick={() => setExpanded(expanded === e.key ? null : e.key)}>
                    {expanded === e.key ? '컬럼 접기 ▲' : '컬럼 보기 ▼'}
                  </a>
                </td>
                <td>
                  <a className="btn" style={{ marginRight: 6, textDecoration: 'none' }}
                    href={`/api/v1/excel/template/${e.key}`}>📄 양식</a>
                  <a className="btn" style={{ marginRight: 6, textDecoration: 'none',
                    background: 'var(--surface)', color: 'var(--text-2)', border: '1px solid var(--border-strong)' }}
                    href={`/api/v1/excel/export/${e.key}`}>⬇ 내보내기</a>
                  <label className="btn" style={{ cursor: 'pointer',
                    background: 'var(--ok)', borderColor: 'var(--ok)' }}>
                    {busy === e.key ? '반영중…' : '⬆ 가져오기'}
                    <input type="file" accept=".xlsx" style={{ display: 'none' }}
                      onChange={(ev) => { importFile(e.key, ev.target.files?.[0] ?? null); ev.target.value = '' }} />
                  </label>
                </td>
              </tr>
              {expanded === e.key && (
                <tr key={e.key + '_cols'}>
                  <td colSpan={4} style={{ background: 'var(--surface-2)' }}>
                    <table style={{ border: 'none' }}>
                      <thead><tr><th>컬럼</th><th>필수</th><th>설명</th></tr></thead>
                      <tbody>
                        {e.columns.map((c: any) => (
                          <tr key={c.name}>
                            <td><code>{c.name}</code></td>
                            <td>{c.required ? <span className="badge ng">필수</span> : ''}</td>
                            <td className="muted">{c.desc}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </td>
                </tr>
              )}
            </>
          ))}
        </tbody>
      </table>

      <p className="muted" style={{ marginTop: 12 }}>
        ※ 참조 코드(model_code / site_code / asset_code / part_no)는 자동으로 ID 로 해석되며,
        존재하지 않는 코드는 행 단위 오류로 리포트됩니다. 견적서는 [투자·견적 분석] 화면의
        전용 업로드(자동 분석 포함)를 사용하세요.
      </p>
    </div>
  )
}

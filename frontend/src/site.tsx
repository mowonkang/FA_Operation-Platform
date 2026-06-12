import { createContext, useContext } from 'react'

/* 사이트(프로젝트) 컨텍스트 — 상단바 셀렉터로 선택.
   사이트 범위 화면(설비/PM/BM/FDC/이슈/상태감시/워크플로우/대시보드)은 이 값으로 필터되고,
   전사 공통(지식 DB·엔지니어링 기준·L&L 풀·라이프사이클 표준)은 영향받지 않는다. */
export const SiteCtx = createContext<{ site: string; setSite: (s: string) => void }>(
  { site: '', setSite: () => {} })

export const useSite = () => useContext(SiteCtx)

/** 쿼리스트링 헬퍼: sq('?status=OPEN') → '?status=OPEN&site_id=N' */
export function sq(site: string, base = '') {
  if (!site) return base
  return base ? `${base}&site_id=${site}` : `?site_id=${site}`
}

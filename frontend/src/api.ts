const BASE = '/api/v1'

function roleHeader(): Record<string, string> {
  return { 'X-Role': localStorage.getItem('fa_role') ?? 'user' }
}

async function handle(res: Response) {
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`${res.status}: ${text}`)
  }
  return res.json()
}

export const api = {
  get: (path: string) => fetch(`${BASE}${path}`, { headers: roleHeader() }).then(handle),
  post: (path: string, body?: unknown) =>
    fetch(`${BASE}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...roleHeader() },
      body: body === undefined ? undefined : JSON.stringify(body),
    }).then(handle),
  patch: (path: string, body?: unknown) =>
    fetch(`${BASE}${path}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json', ...roleHeader() },
      body: body === undefined ? undefined : JSON.stringify(body),
    }).then(handle),
  put: (path: string, body?: unknown) =>
    fetch(`${BASE}${path}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', ...roleHeader() },
      body: JSON.stringify(body),
    }).then(handle),
  del: (path: string) =>
    fetch(`${BASE}${path}`, { method: 'DELETE', headers: roleHeader() }).then(handle),
  upload: (path: string, form: FormData) =>
    fetch(`${BASE}${path}`, { method: 'POST', body: form, headers: roleHeader() }).then(handle),
}

export const STAGE_LABEL: Record<string, string> = {
  DR: 'Design Review',
  FABRICATION: '제작',
  SETUP: '셋업',
  INSTALL_PARAM: 'Install Parameter',
  PM: 'PM',
  BM: 'BM',
  MODIFY: '개조',
  SCRAP: '폐기',
}

export const STATUS_LABEL: Record<string, string> = {
  DR: '설계검토',
  FAB: '제작중',
  SETUP: '셋업중',
  RUN: '가동중',
  PM: 'PM중',
  BM: '고장정비',
  STOP: '정지',
  SCRAP: '폐기',
}

export function judgeClass(j: string) {
  return j === 'OK' ? 'badge ok' : j === 'NG' ? 'badge ng' : 'badge check'
}

const BASE = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000'

async function req(path: string, opts: any = {}) {
  const res = await fetch(`${BASE}${path}`, { headers: { 'Content-Type': 'application/json', ...(opts.headers || {}) }, ...opts })
  const text = await res.text()
  let data: any = {}
  try { data = text ? JSON.parse(text) : {} } catch { data = { detail: text } }
  if (!res.ok) throw new Error(data.detail || `Request failed (${res.status})`)
  return data
}
export const api = {
  health: () => req('/api/health'),
  list: (q = '', status = '') => req(`/api/investigations?q=${encodeURIComponent(q)}&status=${encodeURIComponent(status)}&page_size=100`),
  get: (id: string) => req(`/api/investigations/${id}`),
  create: (body: any) => req('/api/investigations', { method: 'POST', body: JSON.stringify(body) }),
  patch: (id: string, body: any) => req(`/api/investigations/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
  save: (id: string, body: any) => req(`/api/investigations/${id}/save`, { method: 'POST', body: JSON.stringify(body) }),
  approve: (id: string, body: any) => req(`/api/investigations/${id}/approve`, { method: 'POST', body: JSON.stringify(body) }),
  extract: (source_text: string, source_type = 'pasted_text') => req('/api/ai/extract', { method: 'POST', body: JSON.stringify({ source_text, source_type }) }),
  analyze: (source_text: string, source_type = 'pasted_text', investigation_id?: string) => req('/api/ai/analyze-rca', { method: 'POST', body: JSON.stringify({ source_text, source_type, investigation_id }) }),
  recommendCapa: (body: any) => req('/api/ai/recommend-capa', { method: 'POST', body: JSON.stringify(body) }),
  extractFile: async (file: File) => {
    const fd = new FormData(); fd.append('file', file)
    const res = await fetch(`${BASE}/api/ai/extract-file`, { method: 'POST', body: fd })
    const data = await res.json().catch(() => ({}))
    if (!res.ok) throw new Error(data.detail || `Upload failed (${res.status})`)
    return data
  },
  listCapa: (params = '') => req(`/api/capa${params}`),
  patchCapa: (id: string, body: any) => req(`/api/capa/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
}

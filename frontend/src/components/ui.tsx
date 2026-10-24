import React from 'react'

export function Badge({ children, tone = 'blue' }: { children: React.ReactNode; tone?: string }) {
  return <span className={`badge badge-${tone}`}>{children}</span>
}
export function Field({ label, value, onChange, multiline = false, provenance }: any) {
  return (
    <label className="field">
      <span>{label} {provenance && <Badge tone={provenance === 'Explicit' ? 'green' : provenance === 'Missing' ? 'grey' : 'amber'}>{provenance}</Badge>}</span>
      {multiline
        ? <textarea value={value || ''} onChange={(e) => onChange(e.target.value)} rows={3} />
        : <input value={value || ''} onChange={(e) => onChange(e.target.value)} />}
    </label>
  )
}
export function ErrorBox({ error, onRetry }: { error: string; onRetry?: () => void }) {
  if (!error) return null
  return <div className="error" role="alert">⚠ {error} {onRetry && <button className="btn small" onClick={onRetry}>Retry</button>}</div>
}
export function Empty({ text }: { text: string }) { return <div className="empty">{text}</div> }

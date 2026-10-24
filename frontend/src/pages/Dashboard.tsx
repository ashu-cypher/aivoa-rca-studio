import { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { Link } from 'react-router-dom'
import { AppDispatch, RootState } from '../store/store'
import { fetchInvestigations } from '../store/slices'
import { Badge, Empty, ErrorBox } from '../components/ui'

export default function Dashboard() {
  const dispatch = useDispatch<AppDispatch>()
  const { items, loading, error } = useSelector((s: RootState) => s.investigations)
  const [q, setQ] = useState('')
  const [status, setStatus] = useState('')
  useEffect(() => { dispatch(fetchInvestigations({ q: '', status: '' })) }, [dispatch])
  const search = () => dispatch(fetchInvestigations({ q, status }))
  const openCapas = 0 // CAPA count comes from the tracker; dashboard counts investigations here
  return (
    <div>
      <div className="page-head"><div><h1>Investigations</h1><p>AI-powered root cause analysis for API manufacturing. Synthetic demo data is labelled as fictional.</p></div><Link className="btn primary" to="/new">+ New Investigation</Link></div>
      <div className="stats">
        <div className="stat"><b>{items.length}</b><span>Total investigations</span></div>
        <div className="stat"><b>{items.filter((i: any) => i.status === 'Draft').length}</b><span>Draft</span></div>
        <div className="stat"><b>{items.filter((i: any) => i.status === 'Awaiting Review').length}</b><span>Awaiting review</span></div>
        <div className="stat"><b>{items.reduce((n: number, i: any) => n + (i.capas || []).filter((c: any) => c.status !== 'Closed').length, 0)}</b><span>Open CAPAs in listed investigations</span></div>
      </div>
      <div className="toolbar">
        <input placeholder="Search title, description or deviation reference…" value={q} onChange={(e) => setQ(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && search()} />
        <select value={status} onChange={(e) => setStatus(e.target.value)}><option value="">All statuses</option><option>Draft</option><option>Investigation In Progress</option><option>Awaiting Review</option><option>Approved</option><option>Closed</option></select>
        <button className="btn" onClick={search}>Search</button>
      </div>
      <ErrorBox error={error} onRetry={search} />
      {loading && <p>Loading…</p>}
      {!loading && items.length === 0 && <Empty text="No investigations yet. Start a new RCA investigation — or load the fictional drying-stage demo." />}
      <div className="list">
        {items.map((i: any) => (
          <Link key={i.id} className="card row" to={`/investigations/${i.id}`}>
            <div><b>{i.title}</b><p>{i.description?.slice(0, 140)}</p><small>Updated {i.updated_at?.slice(0, 16).replace('T', ' ')} · {i.manufacturing_stage || 'Stage not provided'}</small></div>
            <Badge tone={i.status === 'Approved' ? 'green' : i.status === 'Awaiting Review' ? 'amber' : 'blue'}>{i.status}</Badge>
          </Link>
        ))}
      </div>
    </div>
  )
}

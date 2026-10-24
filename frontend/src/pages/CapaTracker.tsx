import { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { Link } from 'react-router-dom'
import { AppDispatch, RootState } from '../store/store'
import { fetchCapa } from '../store/slices'
import { api } from '../services/api'
import { Badge, Empty } from '../components/ui'

export default function CapaTracker() {
  const dispatch = useDispatch<AppDispatch>()
  const { items, loading } = useSelector((s: RootState) => s.capa)
  const [status, setStatus] = useState('')
  const [type, setType] = useState('')
  useEffect(() => { dispatch(fetchCapa('')) }, [dispatch])
  const load = () => dispatch(fetchCapa(`?status=${encodeURIComponent(status)}&action_type=${encodeURIComponent(type)}`))
  return (
    <div>
      <h1>CAPA Tracker</h1>
      <div className="toolbar">
        <select value={status} onChange={(e) => setStatus(e.target.value)}><option value="">All statuses</option><option>Proposed</option><option>Accepted</option><option>In Progress</option><option>Closed</option><option>Rejected</option></select>
        <select value={type} onChange={(e) => setType(e.target.value)}><option value="">All types</option><option>Correction</option><option>Corrective Action</option><option>Preventive Action</option></select>
        <button className="btn" onClick={load}>Filter</button>
      </div>
      {loading && <p>Loading…</p>}
      {!loading && items.length === 0 && <Empty text="No CAPA actions yet. Generate them from an investigation's RCA analysis." />}
      <div className="list">{items.map((c: any) => (
        <div key={c.id} className="card row">
          <div><b>{c.description}</b><p>{c.rationale}</p><small>Owner role: {c.owner_role || 'Not assigned'} · Target: {c.target_date || 'Not set'} · Effectiveness: {c.effectiveness_method || 'Not defined'}</small><br /><Link to={`/investigations/${c.investigation_id}`}>Open investigation →</Link></div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, alignItems: 'flex-end' }}>
            <Badge>{c.action_type}</Badge><Badge tone={c.priority === 'High' ? 'red' : 'blue'}>{c.priority}</Badge>
            <select value={c.status} onChange={async (e) => { await api.patchCapa(c.id, { status: e.target.value }); load() }}><option>Proposed</option><option>Accepted</option><option>In Progress</option><option>Closed</option><option>Rejected</option></select>
          </div>
        </div>
      ))}</div>
    </div>
  )
}

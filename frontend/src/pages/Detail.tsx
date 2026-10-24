import { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { useParams } from 'react-router-dom'
import { AppDispatch, RootState } from '../store/store'
import { fetchInvestigation, runAnalyze } from '../store/slices'
import { api } from '../services/api'
import { CHECKLIST, DISCLAIMER, FISHBONE_CATEGORIES } from '../types'
import { Badge, ErrorBox, Field } from '../components/ui'

const STATUSES = ['Draft', 'Investigation In Progress', 'Awaiting Review', 'Approved', 'Closed']
const RC_STATUSES = ['Hypothesis', 'Under Investigation', 'Supported', 'Rejected']

export default function Detail() {
  const { id = '' } = useParams()
  const dispatch = useDispatch<AppDispatch>()
  const { current, loading, error } = useSelector((s: RootState) => s.investigations)
  const ai = useSelector((s: RootState) => s.ai)
  const [form, setForm] = useState<any>({})
  const [whys, setWhys] = useState<any[]>([])
  const [fish, setFish] = useState<any[]>([])
  const [causes, setCauses] = useState<any[]>([])
  const [capas, setCapas] = useState<any[]>([])
  const [checklist, setChecklist] = useState<Record<string, string>>({})
  const [msg, setMsg] = useState('')
  const [reviewer, setReviewer] = useState('')
  const [comment, setComment] = useState('')

  useEffect(() => { dispatch(fetchInvestigation(id)) }, [dispatch, id])
  useEffect(() => {
    if (!current) return
    setForm({ ...current }); setWhys(current.five_whys || []); setFish(current.fishbone || []); setCauses(current.root_causes || []); setCapas(current.capas || [])
    const c: Record<string, string> = {}; CHECKLIST.forEach((x) => (c[x] = 'Not reviewed')); setChecklist(c)
  }, [current?.id])

  if (loading && !current) return <p>Loading…</p>
  if (!current) return <div><ErrorBox error={error || 'Investigation not found'} /></div>
  const gaps = current.extracted_json?.evidence_gaps || []
  const observations = current.extracted_json?.confirmed_observations || current.evidence?.filter((e: any) => e.kind === 'confirmed').map((e: any) => e.text) || []

  const payload = () => ({ ...form, five_whys: whys, fishbone: fish, root_causes: causes, capas, evidence: current.evidence })
  const save = async (status?: string) => {
    try { const body: any = payload(); if (status) body.status = status; const r = await api.save(id, body); dispatch(fetchInvestigation(id)); setMsg(status ? `Saved with status ${status}.` : 'Saved. Reload the page to confirm persistence.') } catch (e: any) { setMsg('Save failed: ' + e.message) }
  }
  const approve = async () => {
    if (!reviewer.trim()) { setMsg('Enter a reviewer name to approve — AI cannot approve its own findings.'); return }
    try { await api.approve(id, { reviewer_name: reviewer, reviewer_comment: comment }); dispatch(fetchInvestigation(id)); setMsg('Approved by human reviewer (demo, unauthenticated).') } catch (e: any) { setMsg('Approve failed: ' + e.message) }
  }
  const rerun = async () => {
    const src = current.source_text || form.description || ''
    if (src.length < 10) { setMsg('No source text to re-analyze. Paste a narrative on the New page or edit the description.'); return }
    const r: any = await dispatch(runAnalyze({ text: src, type: current.source_type || 'pasted_text', id }))
    if (r.payload) { setWhys(r.payload.five_whys); setFish(r.payload.fishbone); setCauses(r.payload.root_causes); setCapas(r.payload.capas); setMsg('AI analysis refreshed — review and save to persist.') }
  }
  const refreshCapa = async () => {
    try { const r = await api.recommendCapa({ source_text: current.source_text || form.description, root_causes: causes }); setCapas(r.capas); setMsg('CAPA suggestions refreshed — review and save to persist.') } catch (e: any) { setMsg('CAPA refresh failed: ' + e.message) }
  }

  return (
    <div>
      <div className="page-head"><div><h1>{form.title}</h1><p className="muted">ID {current.id} · Updated {current.updated_at?.slice(0, 16).replace('T', ' ')}</p></div><Badge tone={current.status === 'Approved' ? 'green' : current.status === 'Awaiting Review' ? 'amber' : 'blue'}>{current.status}</Badge></div>
      <div className="banner">{DISCLAIMER} · Local demo without production access controls — reviewer identity is not authenticated.</div>
      <ErrorBox error={error} />
      <section className="card"><h2>Event information (editable)</h2><div className="grid2">
        <Field label="Title" value={form.title} onChange={(v: string) => setForm({ ...form, title: v })} />
        <Field label="Deviation reference" value={form.deviation_reference} onChange={(v: string) => setForm({ ...form, deviation_reference: v })} />
        <Field label="Event date" value={form.event_date} onChange={(v: string) => setForm({ ...form, event_date: v })} />
        <Field label="Manufacturing stage" value={form.manufacturing_stage} onChange={(v: string) => setForm({ ...form, manufacturing_stage: v })} />
        <Field label="Product / batch" value={form.product_batch} onChange={(v: string) => setForm({ ...form, product_batch: v })} />
        <Field label="Site / equipment" value={form.site_equipment} onChange={(v: string) => setForm({ ...form, site_equipment: v })} />
        <Field label="Description" value={form.description} onChange={(v: string) => setForm({ ...form, description: v })} multiline />
        <Field label="Observed result" value={form.observed_result} onChange={(v: string) => setForm({ ...form, observed_result: v })} multiline />
        <Field label="Expected result" value={form.expected_result} onChange={(v: string) => setForm({ ...form, expected_result: v })} multiline />
        <Field label="Containment" value={form.containment_actions} onChange={(v: string) => setForm({ ...form, containment_actions: v })} multiline />
        <Field label="Impact" value={form.impact} onChange={(v: string) => setForm({ ...form, impact: v })} multiline />
        <Field label="Summary" value={form.summary} onChange={(v: string) => setForm({ ...form, summary: v })} multiline />
      </div></section>

      <section className="card"><h2>Evidence workspace</h2>
        <h3>Confirmed observations</h3>{observations.length ? <ul>{observations.map((o: string, i: number) => <li key={i}>{o}</li>)}</ul> : <p className="muted">None recorded yet.</p>}
        <h3>Evidence gaps — where evidence is insufficient, no definitive conclusion is forced</h3>{gaps.length ? <ul>{gaps.map((g: string, i: number) => <li key={i}>{g}</li>)}</ul> : <p className="muted">No gaps recorded. Add gaps from the AI analysis or your review.</p>}
        <h3>Evidence checklist (investigation prompts, not mandatory for every incident)</h3>
        <div className="grid2">{CHECKLIST.map((item) => <label key={item} className="check"><span>{item}</span><select value={checklist[item]} onChange={(e) => setChecklist({ ...checklist, [item]: e.target.value })}><option>Not reviewed</option><option>Requested</option><option>Reviewed</option><option>Not applicable</option></select></label>)}</div>
        {current.source_text && <details><summary>Source document / excerpt</summary><pre>{current.source_text.slice(0, 4000)}</pre></details>}
      </section>

      <section className="card"><h2>Five Whys <small>(edit, add, remove, reorder)</small></h2>
        {whys.length === 0 && <p className="muted">No Five Whys yet — run AI analysis below.</p>}
        {whys.map((w: any, i: number) => (
          <div key={i} className="subcard">
            <b>Why {i + 1}</b> {w.is_hypothesis && <Badge tone="amber">Hypothesis — unsupported</Badge>}
            <input value={w.question || ''} placeholder="Why question" onChange={(e) => { const n = [...whys]; n[i] = { ...n[i], question: e.target.value }; setWhys(n) }} />
            <textarea value={w.answer || ''} placeholder="Answer" onChange={(e) => { const n = [...whys]; n[i] = { ...n[i], answer: e.target.value }; setWhys(n) }} rows={2} />
            <input value={w.connection || ''} placeholder="How this connects to the next step" onChange={(e) => { const n = [...whys]; n[i] = { ...n[i], connection: e.target.value }; setWhys(n) }} />
            <label><input type="checkbox" checked={!!w.is_hypothesis} onChange={(e) => { const n = [...whys]; n[i] = { ...n[i], is_hypothesis: e.target.checked }; setWhys(n) }} /> Mark as hypothesis</label>
            <button className="btn small" onClick={() => setWhys(whys.filter((_, j) => j !== i))}>Remove</button>
            {i > 0 && <button className="btn small" onClick={() => { const n = [...whys]; [n[i - 1], n[i]] = [n[i], n[i - 1]]; n.forEach((x, k) => (x.position = k + 1)); setWhys(n) }}>Move up</button>}
          </div>
        ))}
        <button className="btn" onClick={() => setWhys([...whys, { position: whys.length + 1, question: 'Why?', answer: '', connection: '', is_hypothesis: true }])}>+ Add why</button>
      </section>

      <section className="card"><h2>Fishbone / Ishikawa</h2>
        <div className="fishbone">
          {FISHBONE_CATEGORIES.map((cat) => (
            <div key={cat} className="bone"><h3>{cat}</h3>
              {fish.filter((f: any) => f.category === cat).map((f: any, i: number) => { const idx = fish.indexOf(f); return (
                <div key={i} className="subcard small"><textarea value={f.cause} onChange={(e) => { const n = [...fish]; n[idx] = { ...n[idx], cause: e.target.value }; setFish(n) }} rows={2} /><input value={f.supporting_evidence || ''} placeholder="Supporting evidence" onChange={(e) => { const n = [...fish]; n[idx] = { ...n[idx], supporting_evidence: e.target.value }; setFish(n) }} /><input value={f.evidence_gap || ''} placeholder="Evidence gap" onChange={(e) => { const n = [...fish]; n[idx] = { ...n[idx], evidence_gap: e.target.value }; setFish(n) }} /><button className="btn small" onClick={() => setFish(fish.filter((_, j) => j !== idx))}>Remove</button></div>) })}
              <button className="btn small" onClick={() => setFish([...fish, { category: cat, cause: '', supporting_evidence: '', evidence_gap: '', status: 'Hypothesis' }])}>+ Add cause</button>
            </div>
          ))}
        </div>
      </section>

      <section className="card"><h2>Ranked potential root causes</h2><p className="muted">AI suggestions only. Only a human reviewer can record an approved conclusion — a cause is never “Confirmed” because the model generated it.</p>
        {causes.map((c: any, i: number) => (
          <div key={i} className="subcard">
            <b>#{c.rank || i + 1} {c.cause}</b>
            <textarea value={c.cause} onChange={(e) => { const n = [...causes]; n[i] = { ...n[i], cause: e.target.value }; setCauses(n) }} rows={2} />
            <textarea value={c.rationale || ''} placeholder="Rationale" onChange={(e) => { const n = [...causes]; n[i] = { ...n[i], rationale: e.target.value }; setCauses(n) }} rows={2} />
            <input value={c.supporting_evidence || ''} placeholder="Supporting evidence" onChange={(e) => { const n = [...causes]; n[i] = { ...n[i], supporting_evidence: e.target.value }; setCauses(n) }} />
            <input value={c.contradictory_evidence || ''} placeholder="Contradictory / missing evidence" onChange={(e) => { const n = [...causes]; n[i] = { ...n[i], contradictory_evidence: e.target.value }; setCauses(n) }} />
            <input value={c.verification_steps || ''} placeholder="Verification steps" onChange={(e) => { const n = [...causes]; n[i] = { ...n[i], verification_steps: e.target.value }; setCauses(n) }} />
            <select value={c.status} onChange={(e) => { const n = [...causes]; n[i] = { ...n[i], status: e.target.value }; setCauses(n) }}>{RC_STATUSES.map((s) => <option key={s}>{s}</option>)}</select>
            <button className="btn small" onClick={() => setCauses(causes.filter((_, j) => j !== i))}>Remove</button>
          </div>
        ))}
        <button className="btn" onClick={() => setCauses([...causes, { rank: causes.length + 1, cause: '', rationale: '', supporting_evidence: '', contradictory_evidence: '', contributing_factors: '', verification_steps: '', status: 'Hypothesis' }])}>+ Add root-cause hypothesis</button>
      </section>

      <section className="card"><h2>CAPA actions</h2><p className="muted">Correction = immediate issue · Corrective = established cause · Preventive = substantiated risk elsewhere. No named employees, no invented target dates.</p>
        {capas.map((c: any, i: number) => (
          <div key={i} className="subcard">
            <div><Badge>{c.action_type}</Badge> <Badge tone={c.priority === 'High' ? 'red' : 'blue'}>{c.priority}</Badge> <Badge tone="grey">{c.status}</Badge></div>
            <textarea value={c.description} onChange={(e) => { const n = [...capas]; n[i] = { ...n[i], description: e.target.value }; setCapas(n) }} rows={2} />
            <input value={c.rationale || ''} placeholder="Rationale — why it may help" onChange={(e) => { const n = [...capas]; n[i] = { ...n[i], rationale: e.target.value }; setCapas(n) }} />
            <input value={c.linked_cause || ''} placeholder="Linked root cause" onChange={(e) => { const n = [...capas]; n[i] = { ...n[i], linked_cause: e.target.value }; setCapas(n) }} />
            <input value={c.owner_role || ''} placeholder="Owner role (not a named person)" onChange={(e) => { const n = [...capas]; n[i] = { ...n[i], owner_role: e.target.value }; setCapas(n) }} />
            <input type="date" value={c.target_date || ''} onChange={(e) => { const n = [...capas]; n[i] = { ...n[i], target_date: e.target.value || null }; setCapas(n) }} />
            <input value={c.effectiveness_method || ''} placeholder="Effectiveness-check method" onChange={(e) => { const n = [...capas]; n[i] = { ...n[i], effectiveness_method: e.target.value }; setCapas(n) }} />
            <input value={c.evidence_to_close || ''} placeholder="Evidence required to close" onChange={(e) => { const n = [...capas]; n[i] = { ...n[i], evidence_to_close: e.target.value }; setCapas(n) }} />
            <select value={c.status} onChange={(e) => { const n = [...capas]; n[i] = { ...n[i], status: e.target.value }; setCapas(n) }}><option>Proposed</option><option>Accepted</option><option>Rejected</option><option>In Progress</option><option>Closed</option></select>
            <button className="btn small" onClick={() => setCapas(capas.filter((_, j) => j !== i))}>Remove</button>
          </div>
        ))}
        <button className="btn" onClick={() => setCapas([...capas, { action_type: 'Corrective Action', description: '', rationale: '', linked_cause: '', priority: 'Medium', owner_role: '', target_date: null, effectiveness_method: '', evidence_to_close: '', status: 'Proposed' }])}>+ Add CAPA</button>
      </section>

      <section className="card"><h2>Review and save</h2>
        <p className="muted">Saving does not approve. Approval requires an explicit human reviewer action below.</p>
        <div className="actions">
          <button className="btn primary" onClick={() => save()}>Save Investigation</button>
          <button className="btn" onClick={() => save('Draft')}>Save Draft</button>
          <select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>{STATUSES.map((s) => <option key={s}>{s}</option>)}</select>
          <button className="btn" onClick={() => save(form.status)}>Apply status</button>
          <button className="btn" onClick={rerun} disabled={ai.loading}>{ai.loading ? 'Analyzing…' : 'Re-run AI analysis'}</button>
          <button className="btn" onClick={refreshCapa}>Refresh CAPA suggestions</button>
        </div>
        <ErrorBox error={ai.error} />
        <div className="grid2" style={{ marginTop: 12 }}>
          <Field label="Reviewer name (human, demo)" value={reviewer} onChange={setReviewer} />
          <Field label="Reviewer comment" value={comment} onChange={setComment} multiline />
        </div>
        <button className="btn primary" onClick={approve}>Approve investigation (human review)</button>
        {msg && <p>{msg}</p>}
        <h3>Audit trail</h3>{current.reviews?.length ? <ul>{current.reviews.map((r: any) => <li key={r.id}>{r.created_at?.slice(0, 16).replace('T', ' ')} — {r.event_type} {r.from_status ? `${r.from_status} → ${r.to_status}` : ''} by {r.actor} {r.comment ? `— ${r.comment}` : ''}</li>)}</ul> : <p className="muted">No review events yet.</p>}
      </section>
    </div>
  )
}

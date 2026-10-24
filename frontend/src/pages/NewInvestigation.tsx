import { useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { useNavigate } from 'react-router-dom'
import { AppDispatch, RootState } from '../store/store'
import { runAnalyze, runExtract } from '../store/slices'
import { api } from '../services/api'
import { DEMO_TEXT, DISCLAIMER } from '../types'
import { ErrorBox, Field } from '../components/ui'

const FIELDS: [string, string][] = [
  ['title', 'Investigation title'], ['deviation_reference', 'Deviation / event reference'], ['event_date', 'Event date'],
  ['manufacturing_stage', 'Manufacturing stage / process step'], ['product_batch', 'API / product or batch identifier'],
  ['site_equipment', 'Site / equipment identifier'], ['description', 'Deviation description'], ['observed_result', 'Observed result'],
  ['expected_result', 'Expected result / acceptance criterion'], ['containment_actions', 'Immediate containment actions taken'],
  ['impact', 'Potential product / process impact'], ['summary', 'Preliminary investigation summary'],
]

export default function NewInvestigation() {
  const dispatch = useDispatch<AppDispatch>()
  const nav = useNavigate()
  const ai = useSelector((s: RootState) => s.ai)
  const [tab, setTab] = useState<'paste' | 'email' | 'pdf'>('paste')
  const [text, setText] = useState('')
  const [sourceType, setSourceType] = useState('pasted_text')
  const [fileName, setFileName] = useState('')
  const [form, setForm] = useState<Record<string, string>>({})
  const [analysis, setAnalysis] = useState<any>(null)
  const [saving, setSaving] = useState(false)
  const [saveMsg, setSaveMsg] = useState('')

  const loadDemo = () => { setText(DEMO_TEXT); setSourceType('pasted_text'); setTab('paste') }
  const applyExtraction = (ex: any) => {
    const next: Record<string, string> = {}
    for (const [k] of FIELDS) next[k] = ex?.[k]?.value || ''
    setForm(next)
  }
  const doExtract = async () => {
    const r: any = await dispatch(runExtract({ text, type: sourceType }))
    if (r.payload?.extraction) applyExtraction(r.payload.extraction)
  }
  const doAnalyze = async () => {
    const r: any = await dispatch(runAnalyze({ text, type: sourceType }))
    if (r.payload) { setAnalysis(r.payload); applyExtraction(r.payload.extraction) }
  }
  const doFile = async (f: File) => {
    setFileName(f.name)
    try {
      const r = await api.extractFile(f)
      setText(r.source_text || ''); setSourceType('pdf'); applyExtraction(r.extraction)
    } catch (e: any) { alert(e.message) }
  }
  const save = async () => {
    setSaving(true); setSaveMsg('')
    try {
      const created = await api.create({ title: form.title || 'Untitled investigation', description: form.description || '', deviation_reference: form.deviation_reference || null, event_date: form.event_date || null, manufacturing_stage: form.manufacturing_stage || null, product_batch: form.product_batch || null, site_equipment: form.site_equipment || null, observed_result: form.observed_result || null, expected_result: form.expected_result || null, containment_actions: form.containment_actions || null, impact: form.impact || null, summary: form.summary || null, source_type: sourceType, source_filename: fileName || null, source_text: text })
      const nested: any = { title: form.title }
      if (analysis) {
        nested.five_whys = analysis.five_whys; nested.fishbone = analysis.fishbone; nested.root_causes = analysis.root_causes; nested.capas = analysis.capas
        nested.evidence = [
          ...(analysis.extraction?.confirmed_observations || []).map((t: string) => ({ kind: 'confirmed', text: t })),
          ...(analysis.extraction?.evidence_gaps || []).map((t: string) => ({ kind: 'missing', text: t })),
          ...(analysis.extraction?.followup_questions || []).map((t: string) => ({ kind: 'followup', text: t })),
        ]
      }
      await api.save(created.id, nested)
      setSaveMsg('Saved. Opening the investigation…')
      nav(`/investigations/${created.id}`)
    } catch (e: any) { setSaveMsg('Save failed: ' + e.message) }
    setSaving(false)
  }

  return (
    <div>
      <h1>New RCA Investigation</h1>
      <p className="muted">Start from a source — you do not need to complete every field before AI processing. AI output is editable and never auto-approved.</p>
      <div className="banner">FICTIONAL DEMO DATA — NOT A REAL BATCH OR GMP RECORD · {DISCLAIMER}</div>
      <section className="card">
        <h2>1 · AI-assisted source intake</h2>
        <div className="tabs">
          <button className={tab === 'paste' ? 'active' : ''} onClick={() => { setTab('paste'); setSourceType('pasted_text') }}>Paste narrative</button>
          <button className={tab === 'email' ? 'active' : ''} onClick={() => { setTab('email'); setSourceType('email') }}>Paste email / incident report</button>
          <button className={tab === 'pdf' ? 'active' : ''} onClick={() => setTab('pdf')}>Upload PDF</button>
          <button className="link" onClick={loadDemo}>Load fictional demo incident</button>
        </div>
        {tab === 'pdf' ? (
          <div><input type="file" accept=".pdf" onChange={(e) => e.target.files?.[0] && doFile(e.target.files[0])} /><p className="muted">PDF only, max 10 MB. Scanned PDFs with no extractable text will explain that OCR is needed — no content is fabricated.</p>{fileName && <p>Selected: {fileName}</p>}</div>
        ) : (
          <textarea rows={10} value={text} onChange={(e) => setText(e.target.value)} placeholder="Paste the investigation narrative or email here…" />
        )}
        {text && <details><summary>Source preview</summary><pre>{text.slice(0, 2000)}</pre>{fileName && <p>File: {fileName}</p>}</details>}
        <div className="actions">
          <button className="btn primary" disabled={!text || ai.loading} onClick={doAnalyze}>{ai.loading ? 'Analyzing…' : 'Analyze with AI (full RCA workflow)'}</button>
          <button className="btn" disabled={!text || ai.loading} onClick={doExtract}>Extract fields only</button>
          {text && <button className="btn ghost" onClick={() => { setText(''); setFileName('') }}>Remove source</button>}
        </div>
        <ErrorBox error={ai.error} onRetry={doAnalyze} />
        {ai.error && <p className="muted">If the key is missing, set GROQ_API_KEY in backend/.env and restart the backend — the app will not show fake AI results instead.</p>}
      </section>

      <section className="card">
        <h2>2 · Review and edit extracted fields</h2>
        <p className="muted">“Not provided” means the source did not state it. Edit any field — your edits are what gets saved.</p>
        <div className="grid2">
          {FIELDS.map(([k, label]) => (
            <Field key={k} label={label} value={form[k] || ''} onChange={(v: string) => setForm({ ...form, [k]: v })} multiline={['description', 'containment_actions', 'impact', 'summary'].includes(k)} provenance={ai.extraction?.[k]?.provenance} />
          ))}
        </div>
        {ai.extraction?.evidence_gaps?.length > 0 && <div><h3>Evidence gaps</h3><ul>{ai.extraction.evidence_gaps.map((g: string, i: number) => <li key={i}>{g}</li>)}</ul></div>}
        {analysis && <div><h3>AI analysis ready</h3><p>Five Whys: {analysis.five_whys?.length} · Fishbone causes: {analysis.fishbone?.length} · Root-cause hypotheses: {analysis.root_causes?.length} · CAPA suggestions: {analysis.capas?.length}. These will be saved with the investigation and are fully editable on the details page.</p></div>}
        <div className="actions">
          <button className="btn primary" disabled={saving} onClick={save}>{saving ? 'Saving…' : 'Save Investigation'}</button>
          {saveMsg && <span>{saveMsg}</span>}
        </div>
      </section>
    </div>
  )
}

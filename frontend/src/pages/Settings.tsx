import { useEffect, useState } from 'react'
import { api } from '../services/api'

export default function Settings() {
  const [health, setHealth] = useState<any>(null)
  const [err, setErr] = useState('')
  useEffect(() => { api.health().then(setHealth).catch((e: any) => setErr(e.message)) }, [])
  return (
    <div>
      <h1>Settings / AI Configuration</h1>
      <section className="card">
        <h2>Backend status</h2>
        {err && <p className="error">{err} — is the backend running on http://localhost:8000?</p>}
        {health && <ul>
          <li>Database in use: <b>{health.database}</b> {health.database === 'sqlite' ? '(local fallback — PostgreSQL remains the intended primary database; see README and docker-compose.yml)' : '(PostgreSQL)'}</li>
          <li>Database connected: {String(health.database_connected)}</li>
          <li>Groq model configured: <b>{health.groq_model}</b></li>
          <li>Groq key configured on backend: {String(health.groq_configured)}</li>
        </ul>}
        <h2>Groq setup</h2>
        <p>1. Create a key at console.groq.com. 2. Put it in <code>backend/.env</code> as GROQ_API_KEY — never in frontend code, .env for the frontend, localStorage, or Redux. 3. Restart the backend. 4. Set GROQ_MODEL to change models (default llama-3.3-70b-versatile).</p>
        <h2>Access controls</h2>
        <p>This is a local demo without production access controls. Reviewer names entered in the UI are not authenticated. Do not use this build for real GMP records, and do not claim validated or production-ready status.</p>
      </section>
    </div>
  )
}

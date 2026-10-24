import { Link, NavLink, Route, Routes } from 'react-router-dom'
import Dashboard from '../pages/Dashboard'
import NewInvestigation from '../pages/NewInvestigation'
import Detail from '../pages/Detail'
import CapaTracker from '../pages/CapaTracker'
import Settings from '../pages/Settings'

export default function App() {
  return (
    <div>
      <header className="topbar">
        <Link to="/" style={{ color: '#fff' }}><b>AIVOA RCA Studio</b></Link>
        <NavLink to="/">Investigations</NavLink>
        <NavLink to="/new">New RCA Investigation</NavLink>
        <NavLink to="/capa">CAPA Tracker</NavLink>
        <NavLink to="/settings">Settings / AI Configuration</NavLink>
      </header>
      <main>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/new" element={<NewInvestigation />} />
          <Route path="/investigations/:id" element={<Detail />} />
          <Route path="/capa" element={<CapaTracker />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
        <footer className="muted" style={{ marginTop: 24, fontSize: 13 }}>
          Demo product identity only — not affiliated with any real company. No regulatory compliance, validated status, or production readiness is claimed.
        </footer>
      </main>
    </div>
  )
}

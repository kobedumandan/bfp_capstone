import { useState, useEffect } from 'react'

const NAV_ITEMS = ['Dashboard', 'Incidents', 'Personnel', 'Stations', 'Reports', 'GNN Model']

export default function TopBar() {
  const [activeNav, setActiveNav] = useState('Dashboard')
  const [clock, setClock] = useState('')

  useEffect(() => {
    const tick = () => setClock(new Date().toLocaleTimeString('en-US', { hour12: false }))
    tick()
    const id = setInterval(tick, 1000)
    return () => clearInterval(id)
  }, [])

  return (
    <div className="topbar">
      <div className="topbar-logo">
        <div className="logo-icon" />
        <div className="logo-text">FIRE<span>TRACKR</span></div>
      </div>

      <div className="topbar-divider" />

      <nav className="topbar-nav">
        {NAV_ITEMS.map(item => (
          <button
            key={item}
            className={`nav-btn${activeNav === item ? ' active' : ''}`}
            onClick={() => setActiveNav(item)}
          >
            {item}
          </button>
        ))}
      </nav>

      <div className="topbar-right">
        <div className="alert-badge">2 ACTIVE</div>
        <div className="status-dot" />
        <div className="system-time">{clock}</div>
        <div className="topbar-divider" />
        <div className="user-chip">
          <div className="user-avatar">RC</div>
          Disp. R. Cruz
        </div>
      </div>
    </div>
  )
}

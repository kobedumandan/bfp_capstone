import { useState, useEffect } from 'react'
import '../styles/TopBar.css'

const NAV_ITEMS = ['Dashboard', 'Incidents', 'Personnel', 'Stations', 'Reports']

export default function TopBar({ activeNav, onNavChange, theme, onThemeToggle }) {
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
            onClick={() => onNavChange(item)}
          >
            {item}
          </button>
        ))}
      </nav>

      <div className="topbar-right">
        <div className="alert-badge">2 ACTIVE</div>
        <div className="status-dot" />
        <button className="theme-toggle" onClick={onThemeToggle} title="Toggle theme">
          {theme === 'dark' ? '☀' : '☾'}
        </button>
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

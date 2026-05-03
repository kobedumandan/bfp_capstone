import { useState, useEffect } from 'react'

export default function StatusBar() {
  const [lastSync, setLastSync] = useState('')

  useEffect(() => {
    const tick = () => setLastSync(new Date().toLocaleTimeString('en-US', { hour12: false }))
    tick()
    const id = setInterval(tick, 1000)
    return () => clearInterval(id)
  }, [])

  return (
    <div className="statusbar">
      <div className="status-item"><div className="dot dot-green" />GNN MODEL ONLINE</div>
      <div className="status-item"><div className="dot dot-blue" />SMS GATEWAY ACTIVE</div>
      <div className="status-item"><div className="dot dot-fire" />2 CRITICAL INCIDENTS</div>
      <div className="status-item"><div className="dot dot-amber" />6 PERSONNEL TRACKED</div>
      <div className="status-item" style={{ marginLeft: 'auto' }}>
        <span style={{ color: 'var(--text-muted)' }}>COORD SYS:</span> WGS84 · PH
      </div>
      <div className="status-item">
        <span style={{ color: 'var(--text-muted)' }}>LAST SYNC:</span> {lastSync}
      </div>
    </div>
  )
}

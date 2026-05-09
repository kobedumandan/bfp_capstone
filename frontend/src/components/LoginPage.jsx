import { useState } from 'react'
import '../styles/LoginPage.css'

export default function LoginPage({ onLogin }) {
  const [email, setEmail]         = useState('')
  const [password, setPassword]   = useState('')
  const [showPw, setShowPw]       = useState(false)
  const [remembered, setRemembered] = useState(false)
  const [loading, setLoading]     = useState(false)
  const [alert, setAlert]         = useState('')
  const [errors, setErrors]       = useState({ email: false, password: false })

  function validate() {
    const e = {
      email:    !email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email),
      password: !password,
    }
    setErrors(e)
    return !e.email && !e.password
  }

  function handleLogin() {
    setAlert('')
    if (!validate()) return

    setLoading(true)
    setTimeout(() => {
      setLoading(false)
      // TODO: replace with real auth check
      if (email === 'admin@bfp.gov.ph' && password === 'admin') {
        onLogin()
      } else {
        setErrors({ email: true, password: true })
        setAlert('Invalid credentials. Please check your email and password.')
      }
    }, 1600)
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter') handleLogin()
  }

  return (
    <div className="lp-body" onKeyDown={handleKeyDown}>
      <div className="lp-wrapper">

        {/* LEFT: HERO */}
        <div className="lp-hero">
          <div className="lp-eyebrow">Bureau of Fire Protection</div>

          <div className="lp-title">
            <div className="lp-title-wrap">
              <div className="lp-title-logo-icon" />
              <div className="lp-title-logo-text">FIRE<span>OPS</span></div>
            </div>
          </div>

          <div className="lp-subtitle">GNN-Powered Geospatial Routing &amp; Dispatch</div>
          <div className="lp-rule" />

          <div className="lp-features">
            {[
              { cls: 'fi-fire', icon: '🔥', title: 'Real-Time Incident Management',
                desc: 'Monitor active fire incidents across all barangays with live severity tracking and alarm escalation.' },
              { cls: 'fi-blue', icon: '🧠', title: 'GNN-RL Routing Engine',
                desc: 'Optimal routing computed by a Graph Neural Network trained with reinforcement learning for dynamic road conditions.' },
              { cls: 'fi-green', icon: '📡', title: 'IoT Personnel Tracking',
                desc: 'Field unit locations tracked via ESP32 GPS with SMS fallback for low-coverage areas.' },
              { cls: 'fi-amber', icon: '🗺', title: 'Multi-Station Dispatch',
                desc: 'Coordinate response teams across main and sub-stations from a single command dashboard.' },
            ].map(f => (
              <div className="lp-feature" key={f.title}>
                <div className={`lp-feature-icon ${f.cls}`}>{f.icon}</div>
                <div>
                  <div className="lp-feature-title">{f.title}</div>
                  <div className="lp-feature-desc">{f.desc}</div>
                </div>
              </div>
            ))}
          </div>

          <div className="lp-stats">
            {[
              { val: '3',   label: 'Main Stations' },
              { val: '14',  label: 'Personnel' },
              { val: '8',   label: 'Fire Units' },
              { val: '94%', label: 'Model Accuracy' },
            ].map(s => (
              <div key={s.label}>
                <span className="lp-stat-val">{s.val}</span>
                <span className="lp-stat-label">{s.label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* RIGHT: LOGIN CARD */}
        <div className="lp-card">
          <div className="lp-card-header">
            <div className="lp-logo-row">
              <div className="lp-logo-icon" />
              <div className="lp-logo-text">FIRE<span>OPS</span></div>
            </div>
            <div className="lp-card-title">Administrator Sign In</div>
          </div>

          <hr className="lp-divider" />

          {alert && (
            <div className="lp-alert">
              <span>⚠</span>
              <span>{alert}</span>
            </div>
          )}

          {/* Email */}
          <div className="lp-field-group">
            <label className="lp-field-label">Email</label>
            <div className="lp-field-wrap">
              <span className="lp-field-icon">✉</span>
              <input
                className={`lp-field-input${errors.email ? ' error' : ''}`}
                type="email"
                placeholder="you@bfp.gov.ph"
                value={email}
                onChange={e => setEmail(e.target.value)}
                autoComplete="email"
              />
            </div>
            {errors.email && (
              <div className="lp-field-error">Please enter a valid email address.</div>
            )}
          </div>

          {/* Password */}
          <div className="lp-field-group">
            <label className="lp-field-label">Password</label>
            <div className="lp-field-wrap">
              <span className="lp-field-icon">🔒</span>
              <input
                className={`lp-field-input${errors.password ? ' error' : ''}`}
                type={showPw ? 'text' : 'password'}
                placeholder="••••••••••"
                value={password}
                onChange={e => setPassword(e.target.value)}
                autoComplete="current-password"
              />
              <span
                className="lp-pw-toggle"
                onClick={() => setShowPw(v => !v)}
                style={showPw ? { color: 'var(--lp-accent-blue)' } : {}}
              >
                {showPw ? 'HIDE' : 'SHOW'}
              </span>
            </div>
            {errors.password && (
              <div className="lp-field-error">Password is required.</div>
            )}
          </div>

          {/* Meta row */}
          <div className="lp-meta-row">
            <div className="lp-remember-wrap" onClick={() => setRemembered(v => !v)}>
              <div className={`lp-remember-box${remembered ? ' on' : ''}`}>✓</div>
              <span className="lp-remember-label">Remember me</span>
            </div>
            <a className="lp-forgot" href="#">Forgot password?</a>
          </div>

          <button
            className={`lp-btn-login${loading ? ' loading' : ''}`}
            onClick={handleLogin}
            disabled={loading}
          >
            {loading ? 'Authenticating...' : 'Sign In'}
          </button>

          <div className="lp-card-footer">
            <div className="lp-online-row">
              <div className="lp-online-dot" />
              System online · Authorized access only
            </div>
            <div className="lp-copyright">
              © 2026 FireGIS · Bureau of Fire Protection All rights reserved.
            </div>
          </div>
        </div>

      </div>
    </div>
  )
}

import { useState, useEffect } from 'react'
import '../styles/LocationRequestModal.css'

function generateToken() {
  return `RPT-${Date.now().toString(36).toUpperCase().slice(-6)}`
}

export default function LocationRequestModal({ onClose, onLocationReceived }) {
  const [token]       = useState(generateToken)
  const [urlCopied,  setUrlCopied]  = useState(false)
  const [smsCopied,  setSmsCopied]  = useState(false)
  const [reqStatus,  setReqStatus]  = useState('awaiting') // awaiting | received

  const reportUrl = `${window.location.origin}${window.location.pathname}#/report/${token}`
  const smsText   = `BFP FireGIS: Please share your location to help emergency responders reach you. Open: ${reportUrl}`

  // ── Backend integration point ──────────────────────────────────────────────
  // Poll for location once the backend is ready:
  //
  // useEffect(() => {
  //   if (reqStatus === 'received') return
  //   const id = setInterval(async () => {
  //     const res  = await fetch(`/api/report-sessions/${token}`)
  //     const data = await res.json()
  //     if (data.coords) {
  //       setReqStatus('received')
  //       onLocationReceived({ token, coords: data.coords, receivedAt: data.receivedAt })
  //     }
  //   }, 3000)
  //   return () => clearInterval(id)
  // }, [token, reqStatus])
  // ──────────────────────────────────────────────────────────────────────────

  useEffect(() => {
    const onKey = e => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  async function copy(text, setCopied) {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // Fallback for browsers without clipboard API
      const el = document.createElement('textarea')
      el.value = text
      document.body.appendChild(el)
      el.select()
      document.execCommand('copy')
      document.body.removeChild(el)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  return (
    <div className="lrm-overlay" onMouseDown={e => e.target === e.currentTarget && onClose()}>
      <div className="lrm-panel">

        {/* Header */}
        <div className="lrm-header">
          <div>
            <div className="lrm-eyebrow">REPORTER LINK</div>
            <div className="lrm-title">Request Location from Reporter</div>
          </div>
          <button className="nim-close" onClick={onClose}>✕</button>
        </div>

        <div className="lrm-body">

          {/* Description */}
          <p className="lrm-desc">
            Send this link to the reporter. When they open it and allow
            location access, their GPS coordinates will appear on your map.
          </p>

          {/* Session token */}
          <div className="lrm-token-row">
            <span className="lrm-token-label">SESSION</span>
            <span className="lrm-token">{token}</span>
          </div>

          {/* Shareable URL */}
          <div className="lrm-block">
            <div className="lrm-block-label">LINK</div>
            <div className="lrm-url-row">
              <span className="lrm-url">{reportUrl}</span>
              <button
                className={`lrm-copy-btn${urlCopied ? ' lrm-copied' : ''}`}
                onClick={() => copy(reportUrl, setUrlCopied)}
              >
                {urlCopied ? '✓ Copied' : 'Copy'}
              </button>
            </div>
          </div>

          {/* SMS template */}
          <div className="lrm-block">
            <div className="lrm-block-label">SMS TEMPLATE</div>
            <div className="lrm-sms-text">{smsText}</div>
            <button
              className={`lrm-copy-btn lrm-sms-copy-btn${smsCopied ? ' lrm-copied' : ''}`}
              onClick={() => copy(smsText, setSmsCopied)}
            >
              {smsCopied ? '✓ Copied' : 'Copy Message'}
            </button>
          </div>

          {/* Status */}
          <div className={`lrm-status lrm-status-${reqStatus}`}>
            <div className={`lrm-status-dot lrm-sd-${reqStatus}`} />
            {reqStatus === 'awaiting'
              ? 'Awaiting reporter response…'
              : '✓ Location received — marker added to map'}
          </div>

        </div>

        <div className="lrm-footer">
          <button className="nim-btn-cancel" onClick={onClose}>Close</button>
        </div>

      </div>
    </div>
  )
}

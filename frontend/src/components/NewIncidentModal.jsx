import { useState, useEffect } from 'react'
import '../styles/NewIncidentModal.css'

export default function NewIncidentModal({ location, onSubmit, onCancel }) {
  const [form, setForm] = useState({
    locationName: '',
    address:      '',
    severity:     'Moderate',
    alarm:        '1st Alarm',
    structure:    '',
    reporter:     '911 Call',
  })

  useEffect(() => {
    const onKey = e => { if (e.key === 'Escape') onCancel() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onCancel])

  function set(field, val) { setForm(f => ({ ...f, [field]: val })) }

  function handleSubmit(e) {
    e.preventDefault()
    if (!form.locationName.trim()) return
    onSubmit({
      locationName: form.locationName.trim(),
      address:      form.address.trim(),
      severity:     form.severity,
      alarm:        form.alarm,
      structure:    form.structure.trim() || 'Unknown',
      reporter:     form.reporter,
      coords:       location,
    })
  }

  const sevColor = { Critical: 'var(--accent-fire)', Moderate: 'var(--accent-amber)', Minor: 'var(--accent-green)' }

  return (
    <div className="nim-overlay" onMouseDown={e => e.target === e.currentTarget && onCancel()}>
      <div className="nim-panel">

        <div className="nim-header">
          <div>
            <div className="nim-eyebrow">NEW INCIDENT</div>
            <div className="nim-title">Log Incident</div>
          </div>
          <button className="nim-close" onClick={onCancel}>✕</button>
        </div>

        <div className="nim-coords-bar">
          <span className="nim-coords-label">PINNED LOCATION</span>
          <span className="nim-coords-value">
            {location[0].toFixed(5)},&nbsp;{location[1].toFixed(5)}
          </span>
          <span className="nim-coords-hint">Click map to reposition pin</span>
        </div>

        <form className="nim-form" onSubmit={handleSubmit}>
          <div className="nim-field nim-field-full">
            <label>Location Name <span className="nim-required">*</span></label>
            <input
              placeholder="e.g. Brgy. San Francisco, Panabo City"
              value={form.locationName}
              onChange={e => set('locationName', e.target.value)}
              required
              autoFocus
            />
          </div>

          <div className="nim-field nim-field-full">
            <label>Street / Landmark</label>
            <input
              placeholder="e.g. 123 Rizal St., near the church"
              value={form.address}
              onChange={e => set('address', e.target.value)}
            />
          </div>

          <div className="nim-row">
            <div className="nim-field">
              <label>Severity</label>
              <select
                value={form.severity}
                onChange={e => set('severity', e.target.value)}
                style={{ color: sevColor[form.severity] }}
              >
                <option value="Critical">Critical</option>
                <option value="Moderate">Moderate</option>
                <option value="Minor">Minor</option>
              </select>
            </div>
            <div className="nim-field">
              <label>Alarm Level</label>
              <select value={form.alarm} onChange={e => set('alarm', e.target.value)}>
                <option>1st Alarm</option>
                <option>2nd Alarm</option>
                <option>3rd Alarm</option>
              </select>
            </div>
          </div>

          <div className="nim-row">
            <div className="nim-field">
              <label>Structure Type</label>
              <input
                placeholder="e.g. Residential, Commercial"
                value={form.structure}
                onChange={e => set('structure', e.target.value)}
              />
            </div>
            <div className="nim-field">
              <label>Reported Via</label>
              <select value={form.reporter} onChange={e => set('reporter', e.target.value)}>
                <option>911 Call</option>
                <option>BFP Hotline</option>
                <option>SMS Report</option>
                <option>Walk-in</option>
                <option>Dispatcher</option>
              </select>
            </div>
          </div>

          <div className="nim-actions">
            <button type="button" className="nim-btn-cancel" onClick={onCancel}>Cancel</button>
            <button type="submit" className="nim-btn-submit">
              🔥 Log Incident
            </button>
          </div>
        </form>

      </div>
    </div>
  )
}

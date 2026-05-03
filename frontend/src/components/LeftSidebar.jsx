const INCIDENTS = [
  {
    id: 'INC-2026-084',
    severity: 'critical',
    badge: 'Critical',
    location: 'Brgy. San Isidro, Quezon City',
    time: '08:42',
    distance: '2.1 km',
    units: 2,
  },
  {
    id: 'INC-2026-083',
    severity: 'moderate',
    badge: 'Moderate',
    location: 'Tandang Sora Ave., QC',
    time: '07:15',
    distance: '4.7 km',
    units: 1,
  },
  {
    id: 'INC-2026-081',
    severity: 'contained',
    badge: 'Contained',
    location: 'Batasan Hills, QC',
    time: '05:30',
    distance: '8.3 km',
    units: 3,
  },
]

const PERSONNEL = [
  { initials: 'JD', name: 'J. Dela Cruz', statusClass: 'pa-dispatched', dotClass: 'ps-dispatched', statusText: 'En Route → INC-084', iot: 'IoT ✓' },
  { initials: 'MR', name: 'M. Reyes',     statusClass: 'pa-dispatched', dotClass: 'ps-dispatched', statusText: 'En Route → INC-084', iot: 'IoT ✓' },
  { initials: 'AB', name: 'A. Bautista',  statusClass: 'pa-onscene',    dotClass: 'ps-onscene',    statusText: 'On Scene → INC-083', iot: 'IoT ✓' },
  { initials: 'KS', name: 'K. Santos',    statusClass: 'pa-standby',    dotClass: 'ps-standby',    statusText: 'Standby → Station 1', iot: 'SMS' },
  { initials: 'RL', name: 'R. Lim',       statusClass: 'pa-standby',    dotClass: 'ps-standby',    statusText: 'Standby → Station 2', iot: 'IoT ✓' },
  { initials: 'FT', name: 'F. Torres',    statusClass: 'pa-standby',    dotClass: 'ps-standby',    statusText: 'Standby → Station 1', iot: 'IoT ✓' },
]

export default function LeftSidebar({ selectedId, onSelectIncident }) {
  return (
    <div className="sidebar-left">
      {/* Incidents */}
      <div className="sidebar-section">
        <div className="section-header">
          <span className="section-title">Active Incidents</span>
          <span className="section-count">3 TOTAL</span>
        </div>
        <div className="incident-list">
          {INCIDENTS.map(inc => (
            <div
              key={inc.id}
              className={`incident-card ${inc.severity}${selectedId === inc.id ? ' selected' : ''}`}
              onClick={() => onSelectIncident(inc.id)}
            >
              <div className="incident-top">
                <span className="incident-id">{inc.id}</span>
                <span className={`incident-badge badge-${inc.severity}`}>{inc.badge}</span>
              </div>
              <div className="incident-location">{inc.location}</div>
              <div className="incident-meta">
                <span>⏱ {inc.time}</span>
                <span>📍 {inc.distance}</span>
                <span>{inc.units} units</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Personnel */}
      <div className="sidebar-section-last">
        <div className="section-header">
          <span className="section-title">Field Personnel</span>
          <span className="section-count">6 ACTIVE</span>
        </div>
        <div className="incident-list">
          {PERSONNEL.map(p => (
            <div key={p.initials} className="personnel-item">
              <div className={`personnel-avatar ${p.statusClass}`}>
                <div className="status-ring" />
                {p.initials}
              </div>
              <div className="personnel-info">
                <div className="personnel-name">{p.name}</div>
                <div className="personnel-status">
                  <div className={`pstatus-dot ${p.dotClass}`} />
                  {p.statusText}
                </div>
              </div>
              <div
                className="personnel-iot"
                style={p.iot === 'SMS' ? { color: 'var(--text-muted)' } : {}}
              >
                {p.iot}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

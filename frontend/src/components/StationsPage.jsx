import { useState, useMemo } from 'react'
import '../styles/StationsPage.css'

const STATIONS = [
  {
    id: 'STA-001', code: 'BFP-QC-M1', name: 'Station 1 – Diliman', type: 'main',
    district: 'District 1', address: 'E. Rodriguez Ave., Diliman, QC',
    status: 'operational', personnel: 6, units: 3, activeUnits: 2,
    contact: '+63-2-8123-0001', commander: 'SFO Elvira Garcia',
    established: '1998', coverage: 'Diliman, Proj. 4, Proj. 6',
    capacity: 8, capUsed: 6,
    incident: 'INC-2026-084',
    subs: ['STA-004', 'STA-005'],
    personnelList: [
      { initials: 'JD', name: 'J. Dela Cruz', rank: 'FO II',  status: 'dispatched' },
      { initials: 'MR', name: 'M. Reyes',     rank: 'FO I',   status: 'dispatched' },
      { initials: 'KS', name: 'K. Santos',    rank: 'FO III', status: 'dispatched' },
      { initials: 'FT', name: 'F. Torres',    rank: 'FO II',  status: 'standby' },
      { initials: 'EG', name: 'E. Garcia',    rank: 'SFO',    status: 'standby' },
      { initials: 'HA', name: 'H. Aquino',    rank: 'FO III', status: 'offduty' },
    ],
  },
  {
    id: 'STA-002', code: 'BFP-QC-M2', name: 'Station 2 – Fairview', type: 'main',
    district: 'District 2', address: 'Regalado Ave., Fairview, QC',
    status: 'operational', personnel: 5, units: 3, activeUnits: 1,
    contact: '+63-2-8123-0002', commander: 'SFO Antonio Bautista',
    established: '2003', coverage: 'Fairview, Novaliches, Batasan',
    capacity: 8, capUsed: 5,
    incident: 'INC-2026-083',
    subs: ['STA-006', 'STA-007'],
    personnelList: [
      { initials: 'AB', name: 'A. Bautista', rank: 'SFO',   status: 'onscene' },
      { initials: 'RL', name: 'R. Lim',      rank: 'FO I',  status: 'standby' },
      { initials: 'CM', name: 'C. Mendoza',  rank: 'FO I',  status: 'standby' },
      { initials: 'FP', name: 'F. Pascual',  rank: 'FO II', status: 'standby' },
      { initials: 'IS', name: 'I. Soriano',  rank: 'FI',    status: 'offduty' },
    ],
  },
  {
    id: 'STA-003', code: 'BFP-QC-M3', name: 'Station 3 – Commonwealth', type: 'main',
    district: 'District 3', address: 'Commonwealth Ave., QC',
    status: 'operational', personnel: 3, units: 2, activeUnits: 0,
    contact: '+63-2-8123-0003', commander: 'FO III Danilo Cruz',
    established: '2010', coverage: 'Commonwealth, Batasan Hills, Payatas',
    capacity: 6, capUsed: 3,
    incident: '—',
    subs: ['STA-008'],
    personnelList: [
      { initials: 'BV', name: 'B. Villanueva', rank: 'FI',    status: 'onscene' },
      { initials: 'DC', name: 'D. Cruz',       rank: 'FO III', status: 'standby' },
      { initials: 'GN', name: 'G. Navarro',    rank: 'FO I',   status: 'offduty' },
    ],
  },
  {
    id: 'STA-004', code: 'BFP-QC-S1A', name: 'Sub-Station 1A – Proj. 6', type: 'sub',
    parent: 'STA-001', district: 'District 1', address: 'Proj. 6, Quezon Ave., QC',
    status: 'operational', personnel: 0, units: 1, activeUnits: 0,
    contact: '+63-2-8123-0004', commander: '(Under STA-001)',
    established: '2015', coverage: 'Project 6, Proj. 7, Proj. 8',
    capacity: 3, capUsed: 0, incident: '—', subs: [], personnelList: [],
  },
  {
    id: 'STA-005', code: 'BFP-QC-S1B', name: 'Sub-Station 1B – Tandang Sora', type: 'sub',
    parent: 'STA-001', district: 'District 1', address: 'Tandang Sora Ave., QC',
    status: 'operational', personnel: 0, units: 1, activeUnits: 1,
    contact: '+63-2-8123-0005', commander: '(Under STA-001)',
    established: '2018', coverage: 'Tandang Sora, Vasra, Old Balara',
    capacity: 3, capUsed: 1, incident: 'INC-2026-083', subs: [], personnelList: [],
  },
  {
    id: 'STA-006', code: 'BFP-QC-S2A', name: 'Sub-Station 2A – Novaliches', type: 'sub',
    parent: 'STA-002', district: 'District 2', address: 'Quirino Hwy., Novaliches, QC',
    status: 'operational', personnel: 0, units: 1, activeUnits: 0,
    contact: '+63-2-8123-0006', commander: '(Under STA-002)',
    established: '2016', coverage: 'Novaliches, Sta. Lucia, Gulod',
    capacity: 3, capUsed: 0, incident: '—', subs: [], personnelList: [],
  },
  {
    id: 'STA-007', code: 'BFP-QC-S2B', name: 'Sub-Station 2B – Batasan', type: 'sub',
    parent: 'STA-002', district: 'District 2', address: 'Batasan Hills, QC',
    status: 'standby', personnel: 0, units: 1, activeUnits: 0,
    contact: '+63-2-8123-0007', commander: '(Under STA-002)',
    established: '2019', coverage: 'Batasan Hills, Constitution Hills',
    capacity: 3, capUsed: 0, incident: '—', subs: [], personnelList: [],
  },
  {
    id: 'STA-008', code: 'BFP-QC-S3A', name: 'Sub-Station 3A – Payatas', type: 'sub',
    parent: 'STA-003', district: 'District 3', address: 'Payatas Rd., QC',
    status: 'operational', personnel: 0, units: 1, activeUnits: 0,
    contact: '+63-2-8123-0008', commander: '(Under STA-003)',
    established: '2020', coverage: 'Payatas, Matandang Balara',
    capacity: 2, capUsed: 0, incident: '—', subs: [], personnelList: [],
  },
]

const TABS = ['all', 'main', 'sub']
const TAB_LABELS = { all: 'All Stations', main: 'Main Stations', sub: 'Sub-Stations' }

const P_STATUS_MAP = {
  dispatched: { cls: 'sta-hb-fire',  label: 'Dispatched' },
  onscene:    { cls: 'sta-hb-amber', label: 'On Scene' },
  standby:    { cls: 'sta-hb-blue',  label: 'Standby' },
  offduty:    { cls: 'sta-hb-muted', label: 'Off Duty' },
}

function StatusBadge({ status }) {
  if (status === 'operational') return <span className="sta-hbadge sta-hb-green">Operational</span>
  if (status === 'standby')     return <span className="sta-hbadge sta-hb-amber">Standby</span>
  return <span className="sta-hbadge sta-hb-muted">{status}</span>
}

function PStatusPill({ status }) {
  const { cls, label } = P_STATUS_MAP[status] || { cls: 'sta-hb-muted', label: status }
  return <span className={`sta-hbadge ${cls}`}>{label}</span>
}

function CapBar({ used, capacity }) {
  const pct = capacity > 0 ? Math.round((used / capacity) * 100) : 0
  const cls = pct >= 80 ? 'cap-fire' : pct >= 50 ? 'cap-amber' : 'cap-green'
  return (
    <div className="sta-cap-wrap">
      <div className="sta-cap-bar">
        <div className={`sta-cap-fill ${cls}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="sta-cap-pct">{pct}%</span>
    </div>
  )
}

function StationListItem({ s, selected, onSelect }) {
  const isMain = s.type === 'main'
  const parent = !isMain && STATIONS.find(x => x.id === s.parent)

  return (
    <div
      className={`sta-item ${isMain ? 'sta-item-main' : 'sta-item-sub'}${selected ? ' selected' : ''}`}
      onClick={() => onSelect(s.id)}
    >
      <div className="sta-item-top">
        <div className="sta-item-name-wrap">
          <div className={isMain ? 'sta-icon-main' : 'sta-icon-sub'}>
            {isMain ? '🏠' : '🏡'}
          </div>
          <div>
            <div className="sta-item-name">{s.name}</div>
            <div className="sta-item-code">{s.code}</div>
          </div>
        </div>
        <span className={`sta-type-tag ${isMain ? 'sta-tt-main' : 'sta-tt-sub'}`}>
          {isMain ? 'Main' : 'Sub'}
        </span>
      </div>
      <div className="sta-item-meta">
        <div className="sta-meta-chip">
          <div className={`sta-meta-dot ${s.activeUnits > 0 ? 'md-fire' : isMain ? 'md-green' : 'md-muted'}`} />
          {isMain ? `${s.personnel} personnel` : `${s.units} unit${s.units > 1 ? 's' : ''}`}
        </div>
        <div className="sta-meta-chip">
          <div className="sta-meta-dot md-amber" />
          {s.units} units
        </div>
        <div className="sta-meta-chip">
          <div className="sta-meta-dot md-muted" />
          {s.district}
        </div>
      </div>
      {parent && (
        <div className="sta-item-parent">▲ Under {parent.name}</div>
      )}
    </div>
  )
}

function StationDetail({ s, onSelectStation }) {
  if (!s) {
    return (
      <div className="sta-no-selection">
        <div className="sta-no-sel-icon">🏠</div>
        <div className="sta-no-sel-text">Select a station to view details</div>
      </div>
    )
  }

  const isMain = s.type === 'main'
  const capPct = s.capacity > 0 ? Math.round((s.capUsed / s.capacity) * 100) : 0

  const subData = isMain
    ? s.subs.map(sid => STATIONS.find(x => x.id === sid)).filter(Boolean)
    : []
  const parentStation = !isMain && s.parent
    ? STATIONS.find(x => x.id === s.parent)
    : null

  return (
    <div className="sta-detail-scroll">
      {/* Hero */}
      <div className={`sta-detail-hero ${isMain ? 'hero-main' : 'hero-sub'}`}>
        <div className="sta-hero-top">
          <div className="sta-hero-left">
            <div className={isMain ? 'sta-hero-icon-main' : 'sta-hero-icon-sub'}>
              {isMain ? '🏠' : '🏡'}
            </div>
            <div>
              <div className={`sta-hero-tag ${isMain ? 'hero-tag-main' : 'hero-tag-sub'}`}>
                <div className={isMain ? 'sta-hero-crown' : 'sta-hero-subicon'} />
                {isMain ? 'Main Station · Command Hub' : 'Sub-Station · Satellite Unit'}
              </div>
              <div className="sta-hero-name">{s.name}</div>
              <div className="sta-hero-code">{s.code} · {s.district}</div>
            </div>
          </div>
          <div className="sta-hero-badges">
            <StatusBadge status={s.status} />
            {s.incident !== '—' && (
              <span className="sta-hbadge sta-hb-fire">{s.incident}</span>
            )}
            <span className={`sta-hbadge ${isMain ? 'sta-hb-gold' : 'sta-hb-blue'}`}>
              {isMain ? 'Command' : 'Satellite'}
            </span>
          </div>
        </div>

        <div className="sta-detail-grid">
          <div className="sta-detail-stat">
            <div className="sta-ds-label">Personnel</div>
            <div className="sta-ds-value">{s.personnel}</div>
            <div className="sta-ds-sub">ASSIGNED</div>
          </div>
          <div className="sta-detail-stat">
            <div className="sta-ds-label">Fire Units</div>
            <div className="sta-ds-value">{s.units}</div>
            <div className="sta-ds-sub">{s.activeUnits} DEPLOYED</div>
          </div>
          <div className="sta-detail-stat">
            <div className="sta-ds-label">Capacity</div>
            <div className="sta-ds-value">{s.capUsed}/{s.capacity}</div>
            <CapBar used={s.capUsed} capacity={s.capacity} />
          </div>
          <div className="sta-detail-stat">
            <div className="sta-ds-label">{isMain ? 'Sub-Stations' : 'Parent'}</div>
            <div className="sta-ds-value">{isMain ? s.subs.length : 1}</div>
            <div className="sta-ds-sub">{isMain ? 'UNDER COMMAND' : 'REPORTING TO'}</div>
          </div>
        </div>
      </div>

      {/* Station Info */}
      <div className="sta-info-section">
        <div className="sta-info-title">Station Information</div>
        <div className="sta-info-grid">
          {[
            { label: 'Address',       value: s.address },
            { label: 'Contact',       value: s.contact, mono: true },
            { label: 'Commander',     value: s.commander },
            { label: 'Established',   value: s.established },
            { label: 'Coverage Area', value: s.coverage },
            { label: 'District',      value: s.district },
          ].map(({ label, value, mono }) => (
            <div key={label} className="sta-info-row">
              <span className="sta-info-label">{label}</span>
              <span className="sta-info-value" style={mono ? { fontFamily: 'var(--font-mono)', fontSize: 11 } : undefined}>
                {value}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Sub-stations panel (main only) */}
      {isMain && subData.length > 0 && (
        <div className="sta-info-section">
          <div className="sta-info-title">Sub-Stations under this command</div>
          <div className="sta-subs-grid">
            {subData.map(sub => (
              <div key={sub.id} className="sta-sub-card" onClick={() => onSelectStation(sub.id)}>
                <div className="sta-smc-name">{sub.name}</div>
                <div className="sta-smc-code">{sub.code}</div>
                <div className="sta-smc-row"><span className="sta-smc-label">Status</span><span className="sta-smc-val">{sub.status}</span></div>
                <div className="sta-smc-row"><span className="sta-smc-label">District</span><span className="sta-smc-val">{sub.district}</span></div>
                <div className="sta-smc-row"><span className="sta-smc-label">Units</span><span className="sta-smc-val">{sub.units}</span></div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Parent station panel (sub only) */}
      {!isMain && parentStation && (
        <div className="sta-info-section">
          <div className="sta-info-title">Parent Station</div>
          <div
            className="sta-sub-card"
            style={{ borderLeftColor: 'var(--accent-gold)' }}
            onClick={() => onSelectStation(parentStation.id)}
          >
            <div className="sta-smc-name">{parentStation.name}</div>
            <div className="sta-smc-code">{parentStation.code} · Main Station</div>
            <div className="sta-smc-row"><span className="sta-smc-label">Commander</span><span className="sta-smc-val">{parentStation.commander}</span></div>
            <div className="sta-smc-row"><span className="sta-smc-label">Contact</span><span className="sta-smc-val">{parentStation.contact}</span></div>
          </div>
        </div>
      )}

      {/* Personnel */}
      {s.personnelList.length > 0 && (
        <div className="sta-info-section">
          <div className="sta-info-title">Assigned Personnel</div>
          <div className="sta-personnel-list">
            {s.personnelList.map((p, i) => (
              <div key={i} className="sta-p-row">
                <div className={`sta-p-av ${p.status === 'dispatched' ? 'pav-fire' : p.status === 'onscene' ? 'pav-amber' : 'pav-blue'}`}>
                  {p.initials}
                </div>
                <div className="sta-p-info">
                  <div className="sta-p-name">{p.name}</div>
                  <div className="sta-p-rank">{p.rank}</div>
                </div>
                <PStatusPill status={p.status} />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="sta-detail-actions">
        <button className="sta-btn-dispatch">▶ Dispatch From This Station</button>
        <button className="sta-btn-sec">⊙ View on Map</button>
        <button className="sta-btn-sec">✎ Edit Station</button>
        <button className="sta-btn-sec">↻ Incident History</button>
      </div>
    </div>
  )
}

export default function StationsPage() {
  const [activeTab, setActiveTab]   = useState('all')
  const [search, setSearch]         = useState('')
  const [districtFilter, setDistrictFilter] = useState('')
  const [selectedId, setSelectedId] = useState('STA-001')

  const stats = useMemo(() => ({
    main:      STATIONS.filter(s => s.type === 'main').length,
    sub:       STATIONS.filter(s => s.type === 'sub').length,
    personnel: STATIONS.reduce((acc, s) => acc + s.personnel, 0),
  }), [])

  const filtered = useMemo(() => {
    const q = search.toLowerCase()
    return STATIONS.filter(s => {
      const mq = !q             || s.name.toLowerCase().includes(q) || s.code.toLowerCase().includes(q)
      const md = !districtFilter || s.district === districtFilter
      const mt = activeTab === 'all'
               || (activeTab === 'main' && s.type === 'main')
               || (activeTab === 'sub'  && s.type === 'sub')
      return mq && md && mt
    })
  }, [search, districtFilter, activeTab])

  const selected = STATIONS.find(s => s.id === selectedId) || null

  function handleSelectStation(id) {
    setSelectedId(id)
  }

  return (
    <div className="sta-page">

      {/* PAGE HEADER */}
      <div className="sta-header">
        <div className="sta-title-row">
          <div className="sta-title">
            Stations
            <span>↳ {STATIONS.length} TOTAL</span>
          </div>
          <div className="sta-header-actions">
            <button className="sta-btn-secondary">⬇ Export</button>
            <button className="sta-btn-primary">+ Add Station</button>
          </div>
        </div>

        {/* STAT CARDS — 3 cards: Main, Sub, Personnel */}
        <div className="sta-stat-row">
          <div className="sta-stat-card gold">
            <div className="sta-stat-label">Main Stations</div>
            <div className="sta-stat-value">{stats.main}</div>
            <div className="sta-stat-sub">COMMAND HUBS</div>
          </div>
          <div className="sta-stat-card blue">
            <div className="sta-stat-label">Sub-Stations</div>
            <div className="sta-stat-value">{stats.sub}</div>
            <div className="sta-stat-sub">SATELLITE UNITS</div>
          </div>
          <div className="sta-stat-card amber">
            <div className="sta-stat-label">Total Personnel</div>
            <div className="sta-stat-value">{stats.personnel}</div>
            <div className="sta-stat-sub">ACROSS ALL STATIONS</div>
          </div>
        </div>

        {/* STATUS TABS */}
        <div className="sta-status-tabs">
          {TABS.map(t => (
            <button
              key={t}
              className={`sta-status-tab${activeTab === t ? ' active' : ''}`}
              onClick={() => setActiveTab(t)}
            >
              {TAB_LABELS[t]}
            </button>
          ))}
        </div>
      </div>

      {/* TOOLBAR */}
      <div className="sta-toolbar">
        <div className="sta-search-wrap">
          <span className="sta-search-icon">⌕</span>
          <input
            type="text"
            placeholder="Search station name, code..."
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>
        <select
          className="sta-filter-select"
          value={districtFilter}
          onChange={e => setDistrictFilter(e.target.value)}
        >
          <option value="">All Districts</option>
          <option value="District 1">District 1</option>
          <option value="District 2">District 2</option>
          <option value="District 3">District 3</option>
        </select>
        <div className="sta-legend">
          <div className="sta-legend-item"><div className="sta-legend-line ll-gold" />Main station</div>
          <div className="sta-legend-item"><div className="sta-legend-line ll-blue" />Sub-station</div>
        </div>
        <span className="sta-result-count">
          SHOWING {filtered.length} STATION{filtered.length !== 1 ? 'S' : ''}
        </span>
      </div>

      {/* CONTENT AREA */}
      <div className="sta-content">

        {/* LEFT: Station List */}
        <div className="sta-list">
          {filtered.length === 0 ? (
            <div className="sta-list-empty">No stations match your filters</div>
          ) : (
            filtered.map(s => (
              <StationListItem
                key={s.id}
                s={s}
                selected={selectedId === s.id}
                onSelect={handleSelectStation}
              />
            ))
          )}
        </div>

        {/* RIGHT: Station Detail */}
        <div className="sta-detail">
          <StationDetail s={selected} onSelectStation={handleSelectStation} />
        </div>

      </div>
    </div>
  )
}

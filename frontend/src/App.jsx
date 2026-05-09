import { useState, useEffect } from 'react'
import TopBar from './components/TopBar'
import LeftSidebar from './components/LeftSidebar'
import MapArea from './components/MapArea'
import RightSidebar from './components/RightSidebar'
import StatusBar from './components/StatusBar'
import IncidentsPage from './components/IncidentsPage'
import PersonnelPage from './components/PersonnelPage'
import NewIncidentModal from './components/NewIncidentModal'
import LocationRequestModal from './components/LocationRequestModal'
import ReporterPage from './components/ReporterPage'
import StationsPage from './components/StationsPage'
import LoginPage from './components/LoginPage'
import './App.css'

// Detect reporter route from URL hash once on load — no reactivity needed
function getInitialRoute() {
  const hash = window.location.hash
  if (hash.startsWith('#/report/')) {
    return { view: 'reporter', token: hash.slice('#/report/'.length) }
  }
  return { view: 'login' }
}

export default function App() {
  const [route, setRoute] = useState(getInitialRoute)

  // ── Dashboard-only state ───────────────────────────────────────────────────
  const [activeNav, setActiveNav]                 = useState('Dashboard')
  const [selectedIncident, setSelectedIncident]   = useState('INC-2026-084')
  const [theme, setTheme]                         = useState('dark')
  const [pickingMode, setPickingMode]             = useState(false)
  const [pickedLocation, setPickedLocation]       = useState(null)
  const [loggedIncidents, setLoggedIncidents]     = useState([])
  const [showLocationRequest, setShowLocationRequest] = useState(false)
  const [reporterLocations, setReporterLocations] = useState([])

  useEffect(() => {
    document.documentElement.dataset.theme = theme
  }, [theme])

  useEffect(() => {
    const onKey = e => { if (e.key === 'Escape') cancelPicking() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  function toggleTheme() { setTheme(t => t === 'dark' ? 'light' : 'dark') }

  function startPicking() { setPickingMode(true); setPickedLocation(null) }
  function cancelPicking() { setPickingMode(false); setPickedLocation(null) }

  function handleLocationPicked(coords) { setPickedLocation(coords) }

  function handleIncidentSubmit(formData) {
    const time = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false })
    setLoggedIncidents(prev => [
      ...prev,
      { ...formData, id: `INC-2026-${String(85 + prev.length).padStart(3, '0')}`, time },
    ])
    cancelPicking()
  }

  function handleReporterLocationReceived(data) {
    // data: { token, coords: [lat, lng], receivedAt }
    setReporterLocations(prev => {
      const exists = prev.find(r => r.token === data.token)
      if (exists) return prev.map(r => r.token === data.token ? { ...r, ...data } : r)
      return [...prev, data]
    })
  }

  // ── Login page ────────────────────────────────────────────────────────────
  if (route.view === 'login') {
    return <LoginPage onLogin={() => setRoute({ view: 'dashboard' })} />
  }

  // ── Reporter page — render in isolation, no chrome ───────────────────────
  if (route.view === 'reporter') {
    return <ReporterPage token={route.token} />
  }

  // ── Dashboard ─────────────────────────────────────────────────────────────
  return (
    <>
      <TopBar activeNav={activeNav} onNavChange={setActiveNav} theme={theme} onThemeToggle={toggleTheme} />
      {activeNav === 'Incidents' ? (
        <IncidentsPage />
      ) : activeNav === 'Personnel' ? (
        <PersonnelPage />
      ) : activeNav === 'Stations' ? (
        <StationsPage />
      ) : (
        <div className="main">
          <LeftSidebar
            selectedId={selectedIncident}
            onSelectIncident={setSelectedIncident}
            newIncidents={loggedIncidents}
            onStartPicking={startPicking}
            pickingMode={pickingMode}
            onOpenLocationRequest={() => setShowLocationRequest(true)}
            reporterCount={reporterLocations.length}
          />
          <MapArea
            pickingMode={pickingMode}
            onLocationPicked={handleLocationPicked}
            pickedLocation={pickedLocation}
            newIncidents={loggedIncidents}
            reporterLocations={reporterLocations}
          />
          <RightSidebar />
        </div>
      )}
      <StatusBar />

      {pickedLocation && (
        <NewIncidentModal
          location={pickedLocation}
          onSubmit={handleIncidentSubmit}
          onCancel={cancelPicking}
        />
      )}

      {showLocationRequest && (
        <LocationRequestModal
          onClose={() => setShowLocationRequest(false)}
          onLocationReceived={handleReporterLocationReceived}
        />
      )}
    </>
  )
}

import { useState } from 'react'
import TopBar from './components/TopBar'
import LeftSidebar from './components/LeftSidebar'
import MapArea from './components/MapArea'
import RightSidebar from './components/RightSidebar'
import StatusBar from './components/StatusBar'
import './App.css'

export default function App() {
  const [selectedIncident, setSelectedIncident] = useState('INC-2026-084')

  return (
    <>
      <TopBar />
      <div className="main">
        <LeftSidebar selectedId={selectedIncident} onSelectIncident={setSelectedIncident} />
        <MapArea />
        <RightSidebar />
      </div>
      <StatusBar />
    </>
  )
}

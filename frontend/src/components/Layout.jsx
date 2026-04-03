import { useState } from 'react'
import Navbar from './Navbar'
import SideNav from './SideNav'
import FeederSelector from './FeederSelector'

export default function Layout({
  children,
  darkMode,
  setDarkMode,
  selectedHouseId,
  setSelectedHouseId,
  selectedFeeder,
  setSelectedFeeder,
}) {
  const [sidenavOpen, setSidenavOpen] = useState(false)

  return (
    <div style={{ minHeight: '100vh' }}>
      <Navbar
        darkMode={darkMode}
        setDarkMode={setDarkMode}
        onMenuClick={() => setSidenavOpen(!sidenavOpen)}
      />
      
      <SideNav
        isOpen={sidenavOpen}
        onClose={() => setSidenavOpen(false)}
      />

      <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
        <div style={{ flex: 1 }}>
          <FeederSelector
            selectedFeeder={selectedFeeder}
            setSelectedFeeder={setSelectedFeeder}
            selectedHouseId={selectedHouseId}
            setSelectedHouseId={setSelectedHouseId}
          />
        </div>
      </div>

      <main className="container" style={{ paddingBottom: '2rem' }}>
        {children}
      </main>

      <footer style={{
        textAlign: 'center',
        padding: '2rem',
        borderTop: '1px solid rgba(255, 255, 255, 0.1)',
        marginTop: '3rem',
        color: '#888',
      }}>
        <p>🌞 ROSHNI v1.0 - AI-powered Solar Energy Pool | DISCOM-compliant | Blockchain-backed</p>
        <p style={{ fontSize: '0.85rem', marginTop: '0.5rem' }}>
          Feeder: {selectedFeeder} | Net Metering Compatible
        </p>
      </footer>
    </div>
  )
}
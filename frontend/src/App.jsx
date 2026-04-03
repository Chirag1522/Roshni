import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import Layout from './components/Layout'
import SellerDashboard from './pages/SellerDashboard'
import BuyerDashboard from './pages/BuyerDashboard'
import BillingPage from './pages/BillingPage'
import AdminPanel from './pages/AdminPanel'
import BlockchainExplorer from './pages/BlockchainExplorer'

function App() {
  const [darkMode, setDarkMode] = useState(true)
  const [selectedHouseId, setSelectedHouseId] = useState(localStorage.getItem('selectedHouseId') || 'HOUSE_FDR12_001')
  const [selectedFeeder, setSelectedFeeder] = useState(localStorage.getItem('selectedFeeder') || 'FDR_12')

  useEffect(() => {
    localStorage.setItem('selectedHouseId', selectedHouseId)
  }, [selectedHouseId])

  useEffect(() => {
    localStorage.setItem('selectedFeeder', selectedFeeder)
  }, [selectedFeeder])

  return (
    <Router>
      <div className={darkMode ? 'dark-mode' : 'light-mode'}>
        <Layout 
          darkMode={darkMode} 
          setDarkMode={setDarkMode}
          selectedHouseId={selectedHouseId}
          setSelectedHouseId={setSelectedHouseId}
          selectedFeeder={selectedFeeder}
          setSelectedFeeder={setSelectedFeeder}
        >
          <Routes>
            <Route path="/" element={<Navigate to="/seller" />} />
            <Route path="/seller" element={<SellerDashboard houseId={selectedHouseId} />} />
            <Route path="/buyer" element={<BuyerDashboard houseId={selectedHouseId} />} />
            <Route path="/billing" element={<BillingPage houseId={selectedHouseId} />} />
            <Route path="/blockchain" element={<BlockchainExplorer houseId={selectedHouseId} />} />
            <Route path="/admin" element={<AdminPanel feederCode={selectedFeeder} />} />
          </Routes>
        </Layout>
      </div>
    </Router>
  )
}

export default App
import { useState, useEffect } from 'react'
import api from '../services/api'
import voiceService from '../services/voice'
import AIReasoningConsole from '../components/AIReasoningConsole'
import WalletDisplay from '../components/WalletDisplay'
import IoTDeviceMonitor from '../components/IoTDeviceMonitor'

export default function SellerDashboard({ houseId }) {
  const [dashboard, setDashboard] = useState(null)
  const [iotData, setIotData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [voiceEnabled] = useState(localStorage.getItem('voiceEnabled') !== 'false')
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [showAIReasoning, setShowAIReasoning] = useState(false)

  useEffect(() => {
    fetchDashboard()
    const interval = setInterval(() => {
      fetchDashboard()
    }, 2000)
    return () => clearInterval(interval)
  }, [houseId])

  useEffect(() => {
    // Only fetch IoT data if this is actually a prosumer/seller house
    if (dashboard && ['prosumer', 'seller', 'generator'].includes(dashboard.prosumer_type)) {
      fetchIoTData()
      const interval = setInterval(() => {
        fetchIoTData()
      }, 2000)
      return () => clearInterval(interval)
    }
  }, [houseId, dashboard?.prosumer_type])

  const fetchDashboard = async () => {
    try {
      const response = await api.get(`/dashboard/${houseId}?t=${Date.now()}`)
      console.log('Dashboard data:', response.data)
      setDashboard(response.data)
      setError(null)
    } catch (err) {
      console.error('Dashboard fetch error:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const fetchIoTData = async () => {
    try {
      const response = await api.get(`/iot/status/${houseId}?t=${Date.now()}`)
      console.log('IoT data:', response.data)
      setIotData(response.data)
    } catch (err) {
      console.error('IoT fetch error:', err)
      setIotData(null)
    }
  }

  const speakDashboard = async () => {
    if (dashboard && voiceEnabled) {
      setIsSpeaking(true)
      await voiceService.narrateDashboard(dashboard, 'seller')
      setIsSpeaking(false)
    }
  }

  if (loading) return <div className="spinner" />
  if (error) return <div className="alert danger">Error: {error}</div>
  if (!dashboard) return <div className="alert info">No data available</div>

  // Check if this is actually a consumer house
  if (dashboard.prosumer_type === 'consumer' || dashboard.prosumer_type === 'buyer') {
    return (
      <div>
        <h1>⚠️ Wrong Dashboard</h1>
        <div className="alert info" style={{ marginTop: '1rem' }}>
          <p><strong>{dashboard.house_id}</strong> is a <strong>Consumer/Buyer</strong> house.</p>
          <p>Please switch to the <strong>Buyer Dashboard</strong> to manage energy demand.</p>
          <p>ℹ️ The Seller Dashboard is for prosumers and generators only.</p>
        </div>
      </div>
    )
  }

  // Use real IoT data for live metrics
  const currentGeneration = iotData?.generation_kwh || 0
  const cumulativeGeneration = iotData?.cumulative_kwh || 0
  const supply = dashboard.live_pool_state?.current_supply_kwh || 0
  const pendingDemand = dashboard.live_pool_state?.current_demand_kwh || 0
  const todayFulfilled = dashboard.live_pool_state?.today_fulfilled_kwh || 0
  const todayTrades = dashboard.live_pool_state?.today_trade_count || 0
  const demand = pendingDemand
  const poolUtilPct = supply > 0 ? Math.min(100, (todayFulfilled / supply) * 100) : 0

  // Use backend-calculated estimate based on configured pool rate.
  const earningsEstimate = dashboard.allocation_earnings_estimate_inr || 0

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h1>🔆 Seller Dashboard</h1>
          <p style={{ color: '#888', marginBottom: 0 }}>
            House: {dashboard.house_id} | Feeder: {dashboard.feeder_code}
          </p>
        </div>
        <button onClick={speakDashboard} disabled={isSpeaking} className="voice-btn active">
          {isSpeaking ? '🔊 Speaking...' : '🔊 Speak Summary'}
        </button>
      </div>

      {/* Top metrics */}
      <div className="grid grid-3">
        <div className="metric-box success">
          <div className="metric-label">Current Generation</div>
          <div className="metric-value">
            {currentGeneration.toFixed(2)}
          </div>
          <div style={{ fontSize: '0.85rem' }}>kW (Live)</div>
        </div>
        <div className="metric-box info">
          <div className="metric-label">{pendingDemand > 0 ? 'Pending Demand' : 'Traded Today'}</div>
          <div className="metric-value">{demand.toFixed(2)}</div>
          <div style={{ fontSize: '0.85rem' }}>{pendingDemand > 0 ? 'kWh (awaiting)' : `kWh (${todayTrades} trades)`}</div>
        </div>
        <div className="metric-box">
          <div className="metric-label">Total Earnings</div>
          <div className="metric-value">₹{earningsEstimate.toFixed(2)}</div>
          <div style={{ fontSize: '0.85rem' }}>From {cumulativeGeneration.toFixed(2)} kWh</div>
        </div>
      </div>

      {/* IoT Device Monitor — shows real data from ESP32 devices */}
      <IoTDeviceMonitor houseId={houseId} />

      {/* Live Pool Status */}
      <div className="card" style={{ marginTop: '1.5rem' }}>
        <h3>Live Pool Status</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem', marginBottom: '1.25rem' }}>
          <div>
            <div style={{ opacity: 0.7, fontSize: '0.9rem' }}>Live Supply</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 'bold', color: '#27ae60' }}>
              {supply.toFixed(2)} kWh
            </div>
          </div>
          <div>
            <div style={{ opacity: 0.7, fontSize: '0.9rem' }}>Traded Today</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 'bold', color: '#3498db' }}>
              {todayFulfilled.toFixed(2)} kWh
            </div>
            <div style={{ fontSize: '0.78rem', opacity: 0.6 }}>{todayTrades} trades completed</div>
          </div>
          <div>
            <div style={{ opacity: 0.7, fontSize: '0.9rem' }}>Pending</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 'bold', color: pendingDemand > 0 ? '#f39c12' : '#888' }}>
              {pendingDemand.toFixed(2)} kWh
            </div>
          </div>
          <div>
            <div style={{ opacity: 0.7, fontSize: '0.9rem' }}>Grid Fallback</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 'bold', color: '#ff6b6b' }}>
              {dashboard.live_pool_state.grid_drawdown_kwh.toFixed(2)} kWh
            </div>
          </div>
        </div>
        {/* Pool fill bar */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '0.3rem', opacity: 0.7 }}>
            <span>Pool Utilization (Traded / Cumulative)</span>
            <span>{poolUtilPct.toFixed(0)}%</span>
          </div>
          <div style={{ height: '10px', background: 'rgba(255,255,255,0.1)', borderRadius: '5px', overflow: 'hidden' }}>
            <div style={{
              height: '100%',
              width: `${poolUtilPct}%`,
              background: poolUtilPct > 80 ? '#e74c3c' : poolUtilPct > 50 ? '#f39c12' : '#27ae60',
              borderRadius: '5px',
              transition: 'width 0.5s ease',
            }} />
          </div>
        </div>
      </div>

      {/* Generation details */}
      <div className="card">
        <h3>📊 Generation Details</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem' }}>
          <div>
            <div style={{ opacity: 0.7, fontSize: '0.9rem' }}>Current Output</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 'bold', color: 'var(--primary)' }}>
              {currentGeneration.toFixed(2)} kW
            </div>
          </div>
          <div>
            <div style={{ opacity: 0.7, fontSize: '0.9rem' }}>Status</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 'bold', color: currentGeneration > 0 ? '#27ae60' : '#e74c3c' }}>
              {currentGeneration > 0 ? 'GENERATING' : 'IDLE'}
            </div>
          </div>
          <div>
            <div style={{ opacity: 0.7, fontSize: '0.9rem' }}>Device</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 'bold', color: 'var(--primary)' }}>
              {iotData?.device_id || 'No IoT Device'}
            </div>
          </div>
        </div>
      </div>

      <WalletDisplay houseId={houseId} />

      {/* AI Reasoning */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h3>🤖 AI Pool Analysis</h3>
          <button onClick={() => setShowAIReasoning(!showAIReasoning)} style={{ padding: '0.5rem 1rem', fontSize: '0.9rem' }}>
            {showAIReasoning ? 'Hide' : 'Show Details'}
          </button>
        </div>
        {showAIReasoning && (
          <AIReasoningConsole
            reasoning={`Pool State Analysis:
- Current Supply: ${supply.toFixed(2)} kWh
- Current Demand: ${demand.toFixed(2)} kWh
- Grid Fallback: ${dashboard.live_pool_state.grid_drawdown_kwh.toFixed(2)} kWh
- Your Generation Today: ${dashboard.generation_summary?.today_generated_kwh.toFixed(2) || '0'} kWh
- Earnings Estimate: ₹${dashboard.allocation_earnings_estimate_inr.toFixed(2)}
- Pool Utilization: ${poolUtilPct.toFixed(0)}%

AI matching engine continuously allocates renewable energy to pending
demands prioritizing high-priority consumers and minimizing grid usage.`}
            isVisible={true}
          />
        )}
      </div>

      <div className="alert info" style={{ marginTop: '1.5rem' }}>
        <strong>ℹ️ How it works:</strong> Your solar generation fills the feeder pool.
        Buyers request allocation — AI decides how much comes from pool vs grid.
        You earn ₹6/kWh for pool sales + DISCOM export credits.
      </div>
    </div>
  )
}
import { useState, useEffect } from 'react'
import api from '../services/api'
import voiceService from '../services/voice'
import AIReasoningConsole from '../components/AIReasoningConsole'
import WalletDisplay from '../components/WalletDisplay'

export default function BuyerDashboard({ houseId }) {
  const [dashboard, setDashboard] = useState(null)
  const [iotDemand, setIotDemand] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [voiceEnabled] = useState(localStorage.getItem('voiceEnabled') !== 'false')
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [showAIReasoning, setShowAIReasoning] = useState(false)

  // Fetch dashboard every 5 seconds
  useEffect(() => {
    fetchDashboard()
    const interval = setInterval(() => {
      fetchDashboard()
    }, 2000)
    return () => clearInterval(interval)
  }, [houseId])

  // Fetch IoT demand status every 5 seconds
  useEffect(() => {
    if (dashboard && (dashboard.prosumer_type === 'buyer' || dashboard.prosumer_type === 'consumer')) {
      fetchIotDemand()
      const interval = setInterval(() => {
        fetchIotDemand()
      }, 2000)
      return () => clearInterval(interval)
    }
  }, [houseId, dashboard?.prosumer_type])

  const fetchDashboard = async () => {
    try {
      const response = await api.get(`/dashboard/${houseId}?t=${Date.now()}`)
      console.log('[BUYER] Dashboard data:', response.data)
      setDashboard(response.data)
      setError(null)
    } catch (err) {
      console.error('[BUYER] Dashboard fetch error:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const fetchIotDemand = async () => {
    try {
      const response = await api.get(`/iot/demand-status/${houseId}?t=${Date.now()}`)
      console.log('[BUYER] IoT demand data:', response.data)
      setIotDemand(response.data)
    } catch (err) {
      console.error('[BUYER] IoT demand fetch error:', err)
      setIotDemand(null)
    }
  }

  const speakDashboard = async () => {
    if (dashboard && voiceEnabled) {
      setIsSpeaking(true)
      await voiceService.narrateDashboard(dashboard, 'buyer')
      setIsSpeaking(false)
    }
  }

  if (loading) return <div className="spinner" />
  if (error) return <div className="alert danger">Error: {error}</div>
  if (!dashboard) return <div className="alert info">No data available</div>

  // Check if this is actually a seller/generator house
  if (dashboard.prosumer_type === 'seller' || dashboard.prosumer_type === 'generator' || dashboard.prosumer_type === 'prosumer') {
    return (
      <div>
        <h1>⚠️ Wrong Dashboard</h1>
        <div className="alert info" style={{ marginTop: '1rem' }}>
          <p><strong>{dashboard.house_id}</strong> is a <strong>Seller/Generator</strong> house.</p>
          <p>Please switch to the <strong>Seller Dashboard</strong> to manage energy generation.</p>
          <p>ℹ️ The Buyer Dashboard is for consumers and buyers only.</p>
        </div>
      </div>
    )
  }

  // Extract data
  const currentDemand = iotDemand?.current_demand_kwh || 0
  const poolDemand = iotDemand?.pool_demand_kwh ?? dashboard.live_pool_state?.current_demand_kwh ?? currentDemand
  const poolSupply = iotDemand?.pool_supply_kwh ?? dashboard.live_pool_state?.current_supply_kwh ?? 0
  const allocation = iotDemand?.allocation || null
  const allocatedKwh = allocation?.allocated_kwh || 0
  const gridKwh = allocation?.grid_required_kwh || 0
  const totalDemand = allocation?.demand_kwh || currentDemand
  const safeTotalDemand = totalDemand > 0 ? totalDemand : 1

  const todayDemandKwh = dashboard.demand_summary?.today_demand_kwh || 0
  const allocationRate = allocation ? ((allocatedKwh / safeTotalDemand) * 100) : 0
  const gridDependency = allocation ? ((gridKwh / safeTotalDemand) * 100) : 0

  const savingsEstimate = allocatedKwh * 3 // ₹3 saved per kWh (₹9 grid - ₹6 pool)
  const costEstimate = allocation?.estimated_cost_inr || 0

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h1>🔌 Buyer Dashboard</h1>
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
        <div className="metric-box info">
          <div className="metric-label">Pool Demand</div>
          <div className="metric-value">
            {poolDemand.toFixed(2)}
          </div>
          <div style={{ fontSize: '0.85rem' }}>kWh (Shared with seller view)</div>
        </div>
        <div className="metric-box success">
          <div className="metric-label">From Pool</div>
          <div className="metric-value">{allocatedKwh.toFixed(2)}</div>
          <div style={{ fontSize: '0.85rem' }}>kWh (Renewable)</div>
        </div>
        <div className="metric-box">
          <div className="metric-label">Cost Estimate</div>
          <div className="metric-value">₹{costEstimate.toFixed(2)}</div>
          <div style={{ fontSize: '0.85rem' }}>Today's allocation</div>
        </div>
      </div>

      {/* Live IoT Status */}
      <div className="card">
        <h3>📱 Live Demand Status</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem', marginBottom: '1.25rem' }}>
          <div>
            <div style={{ opacity: 0.7, fontSize: '0.9rem' }}>Current Demand</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 'bold', color: '#3498db' }}>
              {currentDemand.toFixed(2)} kW
            </div>
          </div>
          <div>
            <div style={{ opacity: 0.7, fontSize: '0.9rem' }}>Pool Supply</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 'bold', color: '#2ecc71' }}>
              {poolSupply.toFixed(2)} kWh
            </div>
          </div>
          <div>
            <div style={{ opacity: 0.7, fontSize: '0.9rem' }}>From Pool</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 'bold', color: '#27ae60' }}>
              {allocatedKwh.toFixed(2)} kWh
            </div>
          </div>
          <div>
            <div style={{ opacity: 0.7, fontSize: '0.9rem' }}>From Grid</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 'bold', color: '#ff6b6b' }}>
              {gridKwh.toFixed(2)} kWh
            </div>
          </div>
          <div>
            <div style={{ opacity: 0.7, fontSize: '0.9rem' }}>Device Status</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 'bold', color: currentDemand > 0 ? '#27ae60' : '#888' }}>
              {iotDemand?.device_online ? 'ONLINE' : 'OFFLINE'}
            </div>
          </div>
        </div>

        {/* Allocation breakdown bar */}
        {allocation && (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '0.3rem', opacity: 0.7 }}>
              <span>Energy Source Breakdown</span>
              <span>{allocationRate.toFixed(0)}% Pool | {gridDependency.toFixed(0)}% Grid</span>
            </div>
            <div style={{ height: '20px', background: 'rgba(255,255,255,0.1)', borderRadius: '5px', overflow: 'hidden', display: 'flex' }}>
              <div style={{
                width: `${allocationRate}%`,
                background: 'linear-gradient(90deg, #2ecc71, #27ae60)',
                borderRadius: allocationRate === 100 ? '5px' : '5px 0 0 5px',
                transition: 'width 0.5s ease',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                fontSize: '0.75rem',
                fontWeight: 'bold',
              }}>
                {allocationRate > 15 && `${allocationRate.toFixed(0)}% ☀️`}
              </div>
              <div style={{
                width: `${gridDependency}%`,
                background: 'linear-gradient(90deg, #e74c3c, #c0392b)',
                borderRadius: gridDependency === 100 ? '5px' : '0 5px 5px 0',
                transition: 'width 0.5s ease',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                fontSize: '0.75rem',
                fontWeight: 'bold',
              }}>
                {gridDependency > 15 && `${gridDependency.toFixed(0)}% 🔌`}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Allocation Details */}
      {allocation && (
        <div className="card">
          <h3>✅ Allocation Details</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
            <div style={{ paddingRight: '1rem', borderRight: '1px solid rgba(255,255,255,0.1)' }}>
              <div style={{ marginBottom: '1.5rem' }}>
                <div style={{ opacity: 0.7, fontSize: '0.9rem', marginBottom: '0.5rem' }}>From Solar Pool (₹6/kWh)</div>
                <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#27ae60', marginBottom: '0.25rem' }}>
                  {allocatedKwh.toFixed(2)} kWh
                </div>
                <div style={{ fontSize: '0.9rem', color: '#27ae60' }}>
                  ₹{(allocatedKwh * 6).toFixed(2)} cost
                </div>
              </div>
              <div>
                <div style={{ opacity: 0.7, fontSize: '0.85rem', marginBottom: '0.5rem' }}>Status</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 'bold', color: '#27ae60' }}>
                  ✓ {allocation.allocation_status === 'matched' ? '100% Renewable' : 'Hybrid'}
                </div>
              </div>
            </div>
            <div style={{ paddingLeft: '1rem' }}>
              <div style={{ marginBottom: '1.5rem' }}>
                <div style={{ opacity: 0.7, fontSize: '0.9rem', marginBottom: '0.5rem' }}>Grid Fallback (₹9/kWh)</div>
                <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#ff6b6b', marginBottom: '0.25rem' }}>
                  {gridKwh.toFixed(2)} kWh
                </div>
                <div style={{ fontSize: '0.9rem', color: '#ff6b6b' }}>
                  ₹{(gridKwh * 9).toFixed(2)} cost
                </div>
              </div>
              {savingsEstimate > 0 && (
                <div>
                  <div style={{ opacity: 0.7, fontSize: '0.85rem', marginBottom: '0.5rem' }}>Savings</div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 'bold', color: '#f39c12' }}>
                    ₹{savingsEstimate.toFixed(2)}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* AI Reasoning */}
          {allocation.ai_reasoning && (
            <div style={{ marginTop: '1.5rem', paddingTop: '1.5rem', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
              <div style={{ opacity: 0.7, fontSize: '0.9rem', marginBottom: '0.75rem', fontWeight: 'bold' }}>
                🤖 AI Matching Reasoning
              </div>
              <div style={{ fontSize: '0.9rem', lineHeight: '1.6', opacity: 0.9 }}>
                {allocation.ai_reasoning}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Today's Summary */}
      {dashboard.demand_summary && (
        <div className="card">
          <h3>📊 Today's Summary</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem' }}>
            <div>
              <div style={{ opacity: 0.7, fontSize: '0.9rem' }}>Total Demand</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 'bold', color: '#3498db' }}>
                {todayDemandKwh.toFixed(2)} kWh
              </div>
            </div>
            <div>
              <div style={{ opacity: 0.7, fontSize: '0.9rem' }}>Avg Hourly</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 'bold', color: '#9b59b6' }}>
                {(dashboard.demand_summary.average_hourly_kw || 0).toFixed(2)} kW
              </div>
            </div>
            <div>
              <div style={{ opacity: 0.7, fontSize: '0.9rem' }}>Total Cost</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 'bold', color: '#e67e22' }}>
                ₹{(todayDemandKwh * 6).toFixed(2)}
              </div>
            </div>
          </div>
        </div>
      )}

      <WalletDisplay houseId={houseId} />

      {/* AI Analysis Toggle */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h3>🤖 Buyer Analysis</h3>
          <button onClick={() => setShowAIReasoning(!showAIReasoning)} style={{ padding: '0.5rem 1rem', fontSize: '0.9rem' }}>
            {showAIReasoning ? 'Hide' : 'Show Details'}
          </button>
        </div>
        {showAIReasoning && (
          <AIReasoningConsole
            reasoning={`Buyer Energy Analysis:
- Current Demand: ${currentDemand.toFixed(2)} kW
- From Pool: ${allocatedKwh.toFixed(2)} kWh @ ₹6/kWh
- From Grid: ${gridKwh.toFixed(2)} kWh @ ₹9/kWh
- Pool Allocation Rate: ${allocationRate.toFixed(0)}%
- Grid Dependency: ${gridDependency.toFixed(0)}%
- Estimated Savings: ₹${savingsEstimate.toFixed(2)}
- Total Daily Demand: ${todayDemandKwh.toFixed(2)} kWh

The AI matching engine prioritizes renewable energy allocation from
the pool while maintaining 99.9% supply reliability through grid fallback.
Higher pool allocation = more savings + less carbon footprint.`}
            isVisible={true}
          />
        )}
      </div>

      <div className="alert info" style={{ marginTop: '1.5rem' }}>
        <strong>ℹ️ How it works:</strong> Your IoT device sends demand automatically.
        AI allocates from the solar pool first (₹6/kWh), then grid (₹9/kWh) if needed.
        The more renewable energy available = more savings for you!
      </div>
    </div>
  )
}
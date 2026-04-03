import { useState, useEffect } from 'react'
import api from '../services/api'
import voiceService from '../services/voice'
import AIReasoningConsole from '../components/AIReasoningConsole'
import WalletDisplay from '../components/WalletDisplay'

export default function BuyerDashboard({ houseId }) {
  const [currentDemand, setCurrentDemand] = useState(0)
  const [response, setResponse] = useState(null)
  const [voiceEnabled] = useState(localStorage.getItem('voiceEnabled') !== 'false')
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [walletRefreshKey, setWalletRefreshKey] = useState(0)
  const [iotStatus, setIotStatus] = useState('Waiting for IoT data...')

  // Fetch latest demand and allocation status every 5 seconds
  useEffect(() => {
    const pollDemand = async () => {
      try {
        const res = await api.get(`/iot/demand-status/${houseId}`)
        console.log('[BUYER] Poll response:', res.data)
        
        if (res.data) {
          setCurrentDemand(res.data.current_demand_kwh || 0)
          
          if (res.data.device_online) {
            setIotStatus('IoT device connected ✓')
          } else {
            setIotStatus('Waiting for IoT data...')
          }
          
          // If allocation is available, update response
          if (res.data.allocation) {
            console.log('[BUYER] Allocation received:', res.data.allocation)
            setResponse(res.data.allocation)
            
            // Refresh wallet if tokens were minted
            if (res.data.allocation.sun_tokens_minted > 0) {
              setWalletRefreshKey(k => k + 1)
            }
            
            // Narrate if voice enabled and newly matched
            if (voiceEnabled && res.data.allocation.allocation_status === 'matched' && !isSpeaking) {
              setIsSpeaking(true)
              await voiceService.narrateAllocation(res.data.allocation)
              setIsSpeaking(false)
            }
          }
        }
      } catch (error) {
        console.error('[BUYER] Poll error:', error)
        setIotStatus('Waiting for IoT data...')
        setCurrentDemand(0)
      }
    }

    const interval = setInterval(pollDemand, 5000)
    pollDemand() // Initial call
    return () => clearInterval(interval)
  }, [houseId, voiceEnabled, isSpeaking])

  const speakResult = async () => {
    if (response && voiceEnabled) {
      setIsSpeaking(true)
      await voiceService.narrateAllocation(response)
      setIsSpeaking(false)
    }
  }

  return (
    <div>
      <h1>🔌 Buyer Dashboard</h1>
      <p style={{ color: '#888', marginBottom: '2rem' }}>
        House: {houseId} | Automatic demand from IoT device
      </p>

      {/* IoT Status */}
      <div className="card" style={{ background: 'rgba(52,152,219,0.05)', borderLeft: '4px solid #3498db' }}>
        <h3>🔌 Live IoT Status</h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
          <div>
            <div style={{ opacity: 0.7, fontSize: '0.9rem' }}>Current Demand (from Potentiometer)</div>
            <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#3498db' }}>
              {currentDemand.toFixed(2)} kWh
            </div>
          </div>
          <div>
            <div style={{ opacity: 0.7, fontSize: '0.9rem' }}>Device Status</div>
            <div style={{ fontSize: '1.1rem', fontWeight: 'bold', color: currentDemand > 0 ? '#27ae60' : '#95a5a6' }}>
              {iotStatus}
            </div>
          </div>
        </div>
        <small style={{ opacity: 0.6, marginTop: '0.5rem', display: 'block' }}>
          📱 Demand is automatically generated from your IoT device based on potentiometer readings.
        </small>
      </div>

      {/* Matching in progress indicator */}
      {currentDemand > 0 && !response && (
        <div className="card" style={{ background: 'rgba(255, 140, 0, 0.05)', borderLeft: '4px solid #ff8c00' }}>
          <h3>⚡ Matching Energy</h3>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{ fontSize: '2rem' }}>⏳</div>
            <div>
              <div style={{ fontWeight: 'bold', marginBottom: '0.25rem' }}>
                Allocating {currentDemand.toFixed(2)} kWh from pool...
              </div>
              <div style={{ fontSize: '0.85rem', opacity: 0.7 }}>
                Checking available solar energy • Calculating grid fallback • Processing allocation...
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Allocation result */}
      {response && (
        <div className="card" style={{ borderLeft: '4px solid #27ae60' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
            <h3>✅ Allocation Result</h3>
            <button onClick={speakResult} disabled={isSpeaking} className="voice-btn active">
              {isSpeaking ? '🔊 Speaking...' : '🔊 Speak Result'}
            </button>
          </div>

          {/* AI Reasoning */}
          {response.ai_reasoning && (
            <div style={{ background: 'rgba(100, 200, 255, 0.08)', padding: '1rem', borderRadius: '8px', marginBottom: '1.5rem', borderLeft: '3px solid #3498db' }}>
              <div style={{ fontSize: '0.85rem', fontWeight: 'bold', marginBottom: '0.5rem', color: '#3498db' }}>📊 AI Reasoning</div>
              <div style={{ fontSize: '0.9rem', lineHeight: '1.5' }}>{response.ai_reasoning}</div>
            </div>
          )}

          {/* Pool vs Grid breakdown with visual bar */}
          <div style={{ marginBottom: '1.5rem' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
              <div>
                <div style={{ opacity: 0.7, fontSize: '0.9rem' }}>From Solar Pool ☀️</div>
                <div style={{ fontSize: '1.8rem', fontWeight: 'bold', color: '#27ae60' }}>
                  {response.allocated_kwh.toFixed(2)} kWh
                </div>
                <div style={{ fontSize: '0.85rem', color: '#27ae60', marginTop: '0.25rem' }}>
                  {((response.allocated_kwh / response.demand_kwh) * 100).toFixed(0)}% of demand
                </div>
                <div style={{ fontSize: '0.85rem', color: '#27ae60' }}>
                  ₹{(response.allocated_kwh * 9).toFixed(2)} @ ₹9/kWh
                </div>
              </div>
              <div>
                <div style={{ opacity: 0.7, fontSize: '0.9rem' }}>From Grid (Fallback) 🔌</div>
                <div style={{ fontSize: '1.8rem', fontWeight: 'bold', color: '#ff6b6b' }}>
                  {response.grid_required_kwh.toFixed(2)} kWh
                </div>
                <div style={{ fontSize: '0.85rem', color: '#ff6b6b', marginTop: '0.25rem' }}>
                  {((response.grid_required_kwh / response.demand_kwh) * 100).toFixed(0)}% of demand
                </div>
                <div style={{ fontSize: '0.85rem', color: '#ff6b6b' }}>
                  ₹{(response.grid_required_kwh * 12).toFixed(2)} @ ₹12/kWh
                </div>
              </div>
            </div>

            {/* Visual allocation bar */}
            <div style={{ 
              background: '#ecf0f1', 
              borderRadius: '8px', 
              height: '30px', 
              overflow: 'hidden',
              display: 'flex'
            }}>
              <div style={{
                width: `${((response.allocated_kwh / response.demand_kwh) * 100).toFixed(0)}%`,
                background: 'linear-gradient(90deg, #2ecc71, #27ae60)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                fontWeight: 'bold',
                fontSize: '0.85rem',
                transition: 'width 0.3s ease'
              }}>
                {response.allocated_kwh > 0.1 && `${((response.allocated_kwh / response.demand_kwh) * 100).toFixed(0)}% Pool`}
              </div>
              <div style={{
                width: `${((response.grid_required_kwh / response.demand_kwh) * 100).toFixed(0)}%`,
                background: 'linear-gradient(90deg, #e74c3c, #c0392b)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                fontWeight: 'bold',
                fontSize: '0.85rem',
                transition: 'width 0.3s ease'
              }}>
                {response.grid_required_kwh > 0.1 && `${((response.grid_required_kwh / response.demand_kwh) * 100).toFixed(0)}% Grid`}
              </div>
            </div>
          </div>

          {/* Status and Cost */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
            <div style={{ background: 'rgba(52,152,219,0.05)', padding: '1rem', borderRadius: '8px', borderLeft: '3px solid #3498db' }}>
              <div style={{ fontSize: '0.85rem', opacity: 0.7, marginBottom: '0.5rem' }}>Allocation Status</div>
              <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: response.allocation_status === 'matched' ? '#27ae60' : '#f39c12' }}>
                {response.allocation_status === 'matched' ? '✓ 100% Pool' : '⚡ ' + response.allocation_status.toUpperCase()}
              </div>
            </div>
            <div style={{ background: 'rgba(255,140,66,0.05)', padding: '1rem', borderRadius: '8px', borderLeft: '3px solid #ff8c00' }}>
              <div style={{ fontSize: '0.85rem', opacity: 0.7, marginBottom: '0.5rem' }}>Total Cost</div>
              <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#ff8c00' }}>
                ₹{response.estimated_cost_inr.toFixed(2)}
              </div>
              <div style={{ fontSize: '0.75rem', opacity: 0.7, marginTop: '0.25rem' }}>
                Pool: ₹{(response.allocated_kwh * 9).toFixed(2)} + Grid: ₹{(response.grid_required_kwh * 12).toFixed(2)}
              </div>
            </div>
          </div>

          {/* Savings callout */}
          {response.grid_required_kwh === 0 && (
            <div style={{
              marginTop: '1rem',
              padding: '0.75rem 1rem',
              background: 'rgba(39,174,96,0.1)',
              borderRadius: '8px',
              border: '1px solid rgba(39,174,96,0.3)',
              fontSize: '0.9rem',
              color: '#27ae60',
              fontWeight: 'bold',
            }}>
              100% renewable! Saved {((response.allocated_kwh) * (12 - 9)).toFixed(2)} vs grid rate.
            </div>
          )}

          {/* SUN Tokens minted banner */}
          {response.sun_tokens_minted > 0 && (
            <div style={{
              marginTop: '1rem',
              padding: '1rem 1.25rem',
              background: 'rgba(255, 193, 7, 0.12)',
              borderRadius: '8px',
              border: '1px solid rgba(255, 193, 7, 0.4)',
              display: 'flex',
              alignItems: 'center',
              gap: '0.75rem',
            }}>
              <span style={{ fontSize: '1.5rem' }}>☀️</span>
              <div>
                <div style={{ fontWeight: 'bold', color: '#f39c12' }}>
                  {response.sun_tokens_minted.toFixed(2)} SUN Tokens Minted!
                </div>
                <div style={{ fontSize: '0.82rem', opacity: 0.8, marginTop: '0.2rem' }}>
                  {response.blockchain_tx
                    ? `TX: ${response.blockchain_tx.slice(0, 16)}... — Balance updating below`
                    : 'Syncing with blockchain...'}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      <WalletDisplay houseId={houseId} refreshTrigger={walletRefreshKey} />

      {/* ── Demo Simulator for buyer houses ── */}

      <div className="alert info" style={{ marginTop: '1.5rem' }}>
        <strong>💡 Pool Benefits:</strong> Save up to 25% vs grid rates by using renewable energy from your feeder.
        Higher priority = faster allocation. Grid fallback ensures 99.9% reliability.
      </div>
    </div>
  )
}
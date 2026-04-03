import { useState } from 'react'
import api from '../services/api'
import voiceService from '../services/voice'
import AIReasoningConsole from '../components/AIReasoningConsole'
import WalletDisplay from '../components/WalletDisplay'

export default function BuyerDashboard({ houseId }) {
  const [demand, setDemand] = useState('')
  const [duration, setDuration] = useState('1')
  const [loading, setLoading] = useState(false)
  const [response, setResponse] = useState(null)
  const [estimatedCost, setEstimatedCost] = useState(0)
  const [voiceEnabled] = useState(localStorage.getItem('voiceEnabled') !== 'false')
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [walletRefreshKey, setWalletRefreshKey] = useState(0)

  const handleDemandChange = (e) => {
    const val = parseFloat(e.target.value) || 0
    setDemand(val)
    setEstimatedCost(val * 9)
  }

  const submitDemand = async () => {
    if (!demand || demand <= 0) {
      alert('Please enter valid demand')
      return
    }
    setLoading(true)
    try {
      const res = await api.post('/demand/submit', {
        house_id: houseId,
        demand_kwh: parseFloat(demand),
        duration_hours: parseFloat(duration),
      })
      setResponse(res.data)

      // If SUN tokens were minted, refresh wallet balance after a short delay
      // (give blockchain time to confirm the transaction)
      if (res.data.sun_tokens_minted > 0) {
        setTimeout(() => setWalletRefreshKey(k => k + 1), 3000)
        setTimeout(() => setWalletRefreshKey(k => k + 1), 8000)
      }

      if (voiceEnabled && res.data.allocation_status === 'matched') {
        setIsSpeaking(true)
        await voiceService.narrateAllocation(res.data)
        setIsSpeaking(false)
      }

      setDemand('')
    } catch (error) {
      alert(`Error: ${error.message}`)
    } finally {
      setLoading(false)
    }
  }

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
        House: {houseId} | Request solar supply from feeder pool
      </p>

      {/* Demand form */}
      <div className="card">
        <h3>📋 Request Energy Allocation</h3>

        <div className="form-group">
          <label>Demand (kWh)</label>
          <input
            type="number"
            value={demand}
            onChange={handleDemandChange}
            placeholder="e.g., 5.0"
            min="0"
            step="0.1"
          />
          <small style={{ opacity: 0.7 }}>Amount of energy you need</small>
        </div>

        <div className="form-group">
          <label>Duration (hours)</label>
          <input
            type="number"
            value={duration}
            onChange={(e) => setDuration(e.target.value)}
            min="0.5"
            step="0.5"
          />
        </div>

        <div className="metric-box info" style={{ marginBottom: '1rem' }}>
          <div className="metric-label">Estimated Cost</div>
          <div className="metric-value">₹{estimatedCost.toFixed(2)}</div>
          <div style={{ fontSize: '0.85rem' }}>@ ₹9/kWh pool rate</div>
        </div>

        <button
          onClick={submitDemand}
          disabled={loading}
          style={{ width: '100%', padding: '1rem', fontSize: '1.1rem', fontWeight: 'bold' }}
        >
          {loading ? 'Processing...' : '🎯 Submit Demand'}
        </button>
      </div>

      {/* Allocation result */}
      {response && (
        <div className="card" style={{ borderLeft: '4px solid #27ae60' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
            <h3>✅ Allocation Result</h3>
            <button onClick={speakResult} disabled={isSpeaking} className="voice-btn active">
              {isSpeaking ? '🔊 Speaking...' : '🔊 Speak Result'}
            </button>
          </div>

          <AIReasoningConsole reasoning={response.ai_reasoning} isVisible={true} />

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
            <div>
              <div style={{ opacity: 0.7, fontSize: '0.9rem' }}>From Pool ☀️</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 'bold', color: '#27ae60' }}>
                {response.allocated_kwh.toFixed(2)} kWh
              </div>
              <div style={{ fontSize: '0.85rem', color: '#27ae60' }}>
                ₹{(response.allocated_kwh * 9).toFixed(2)} @ ₹9/kWh
              </div>
            </div>
            <div>
              <div style={{ opacity: 0.7, fontSize: '0.9rem' }}>From Grid (Fallback) 🔌</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 'bold', color: '#ff6b6b' }}>
                {response.grid_required_kwh.toFixed(2)} kWh
              </div>
              <div style={{ fontSize: '0.85rem', color: '#ff6b6b' }}>
                ₹{(response.grid_required_kwh * 12).toFixed(2)} @ ₹12/kWh
              </div>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div style={{ background: 'rgba(52,152,219,0.05)', padding: '1rem', borderRadius: '8px' }}>
              <div style={{ fontSize: '0.85rem', opacity: 0.7 }}>Status</div>
              <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#3498db' }}>
                <span className={`status ${response.allocation_status}`}>
                  {response.allocation_status.toUpperCase()}
                </span>
              </div>
            </div>
            <div style={{ background: 'rgba(255,140,66,0.05)', padding: '1rem', borderRadius: '8px' }}>
              <div style={{ fontSize: '0.85rem', opacity: 0.7 }}>Total Cost</div>
              <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: 'var(--primary)' }}>
                ₹{response.estimated_cost_inr.toFixed(2)}
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
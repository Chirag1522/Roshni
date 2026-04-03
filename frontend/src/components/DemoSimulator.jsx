/**
 * DemoSimulator — sends simulated solar generation to backend
 * Shown only on non-NodeMCU houses during hackathon demo
 * Clearly labeled as demo/simulation
 */
import { useState, useEffect, useRef } from 'react'
import api from '../services/api'

export default function DemoSimulator({ houseId, solarCapacityKw = 3.0 }) {
  const [generationKw, setGenerationKw] = useState(0)
  const [isSimulating, setIsSimulating] = useState(false)
  const [lastResponse, setLastResponse] = useState(null)
  const [sendCount, setSendCount] = useState(0)
  const intervalRef = useRef(null)

  // Auto-send every 5 seconds when simulating (same as NodeMCU)
  useEffect(() => {
    if (isSimulating && generationKw > 0) {
      sendGeneration() // send immediately on start
      intervalRef.current = setInterval(sendGeneration, 5000)
    } else {
      clearInterval(intervalRef.current)
    }
    return () => clearInterval(intervalRef.current)
  }, [isSimulating, generationKw])

  const sendGeneration = async () => {
    try {
      const res = await api.post('/iot/update', {
        house_id: houseId,
        generation_kwh: parseFloat(generationKw.toFixed(3)),
        device_id: `DEMO_${houseId}`,
        signal_strength: -55,
        auth_token: import.meta.env.VITE_IOT_AUTH_TOKEN || 'iot_secret_token_12345',
      })
      setLastResponse(res.data)
      setSendCount(c => c + 1)
    } catch (err) {
      console.warn('[DemoSimulator] Send failed:', err.message)
    }
  }

  const getSliderColor = () => {
    const pct = generationKw / solarCapacityKw
    if (pct > 0.7) return '#27ae60'
    if (pct > 0.3) return '#f39c12'
    return '#e74c3c'
  }

  const poolStatusColor = {
    sufficient: '#27ae60',
    allocating: '#f39c12',
    shortage: '#e74c3c',
  }

  return (
    <div style={{
      border: '2px dashed #f39c12',
      borderRadius: '12px',
      padding: '1.5rem',
      background: 'rgba(243, 156, 18, 0.05)',
      marginTop: '1.5rem',
    }}>
      {/* Demo label */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
        <span style={{
          background: '#f39c12',
          color: '#000',
          fontSize: '0.7rem',
          fontWeight: 'bold',
          padding: '2px 8px',
          borderRadius: '4px',
          letterSpacing: '1px',
        }}>DEMO MODE</span>
        <h3 style={{ margin: 0, fontSize: '1rem' }}>
          ☀️ Solar Generation Simulator
        </h3>
        <span style={{ marginLeft: 'auto', fontSize: '0.8rem', opacity: 0.6 }}>
          Real hardware: NodeMCU on House 1
        </span>
      </div>

      {/* Slider */}
      <div style={{ marginBottom: '1.25rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
          <label style={{ fontSize: '0.9rem', opacity: 0.8 }}>
            Solar Output
          </label>
          <span style={{
            fontWeight: 'bold',
            fontSize: '1.1rem',
            color: getSliderColor(),
          }}>
            {generationKw.toFixed(2)} kW / {solarCapacityKw} kW
          </span>
        </div>
        <input
          type="range"
          min="0"
          max={solarCapacityKw}
          step="0.1"
          value={generationKw}
          onChange={e => setGenerationKw(parseFloat(e.target.value))}
          style={{ width: '100%', accentColor: getSliderColor() }}
        />
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', opacity: 0.5 }}>
          <span>0 (Night/Cloudy)</span>
          <span>{(solarCapacityKw * 0.5).toFixed(1)} (Partial)</span>
          <span>{solarCapacityKw} (Peak Sun)</span>
        </div>
      </div>

      {/* Quick presets */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.25rem', flexWrap: 'wrap' }}>
        {[
          { label: '☁️ Cloudy', val: solarCapacityKw * 0.15 },
          { label: '⛅ Partial', val: solarCapacityKw * 0.5 },
          { label: '☀️ Peak', val: solarCapacityKw * 0.9 },
          { label: '🌙 Night', val: 0 },
        ].map(preset => (
          <button
            key={preset.label}
            onClick={() => setGenerationKw(parseFloat(preset.val.toFixed(1)))}
            style={{
              padding: '0.3rem 0.75rem',
              fontSize: '0.8rem',
              background: 'rgba(255,255,255,0.08)',
              border: '1px solid rgba(255,255,255,0.15)',
              borderRadius: '6px',
              cursor: 'pointer',
            }}
          >
            {preset.label}
          </button>
        ))}
      </div>

      {/* Start/Stop */}
      <button
        onClick={() => setIsSimulating(s => !s)}
        disabled={generationKw === 0 && !isSimulating}
        style={{
          width: '100%',
          padding: '0.75rem',
          fontWeight: 'bold',
          background: isSimulating ? '#e74c3c' : '#27ae60',
          color: '#fff',
          border: 'none',
          borderRadius: '8px',
          cursor: 'pointer',
          fontSize: '0.95rem',
        }}
      >
        {isSimulating
          ? `⏹ Stop Simulation (${sendCount} updates sent)`
          : '▶ Start Simulating (sends every 5s like NodeMCU)'}
      </button>

      {/* Live feedback */}
      {lastResponse && (
        <div style={{
          marginTop: '1rem',
          padding: '0.75rem',
          background: 'rgba(0,0,0,0.2)',
          borderRadius: '8px',
          fontSize: '0.85rem',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ opacity: 0.7 }}>Pool Status</span>
            <span style={{
              fontWeight: 'bold',
              color: poolStatusColor[lastResponse.allocation_status] || '#fff',
            }}>
              {lastResponse.allocation_status?.toUpperCase()}
            </span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.4rem' }}>
            <span style={{ opacity: 0.7 }}>Pool Supply</span>
            <span style={{ color: '#27ae60', fontWeight: 'bold' }}>
              {lastResponse.current_pool_supply?.toFixed(2)} kWh
            </span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.4rem' }}>
            <span style={{ opacity: 0.7 }}>Pool Demand</span>
            <span style={{ color: '#3498db', fontWeight: 'bold' }}>
              {lastResponse.current_pool_demand?.toFixed(2)} kWh
            </span>
          </div>
        </div>
      )}
    </div>
  )
}
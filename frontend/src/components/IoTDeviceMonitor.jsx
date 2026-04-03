/**
 * IoTDeviceMonitor — displays real IoT device data and status
 * Shows live generation from NodeMCU devices instead of simulation
 */
import { useState, useEffect, useRef } from 'react'
import api from '../services/api'

export default function IoTDeviceMonitor({ houseId }) {
  const [iotData, setIotData] = useState(null)
  const [isOnline, setIsOnline] = useState(false)
  const [lastUpdate, setLastUpdate] = useState(null)
  const [error, setError] = useState(null)

  // Poll for IoT device status every 5 seconds (same as device update interval)
  useEffect(() => {
    fetchIoTStatus()
    const interval = setInterval(fetchIoTStatus, 5000)
    return () => clearInterval(interval)
  }, [houseId])

  const fetchIoTStatus = async () => {
    try {
      // Try to get IoT status for this house (with cache busting)
      const res = await api.get(`/iot/status/${houseId}?t=${Date.now()}`)
      console.log('IoT Status Response:', res.data)  // Debug log

      // Force re-render by creating new object
      const newData = { ...res.data, _timestamp: Date.now() }
      setIotData(newData)
      setIsOnline(res.data.status === 'online')
      setLastUpdate(new Date(res.data.last_update || Date.now()))
      setError(null)
    } catch (err) {
      console.error('IoT Status Error:', err)  // Debug log
      // If no IoT device data, show offline
      setIotData(null)
      setIsOnline(false)
      setError('No IoT device connected')
    }
  }

  const getStatusColor = () => {
    if (!isOnline) return '#e74c3c'  // Red for offline
    if (iotData?.generation_kwh > 0) return '#27ae60'  // Green for generating
    return '#f39c12'  // Yellow for idle/online but not generating
  }

  const getStatusText = () => {
    if (!isOnline) return 'OFFLINE'
    if (iotData?.generation_kwh > 0) return 'GENERATING'
    return 'IDLE'
  }

  return (
    <div style={{
      border: '2px solid #3498db',
      borderRadius: '12px',
      padding: '1.5rem',
      background: 'rgba(52, 152, 219, 0.05)',
      marginTop: '1.5rem',
    }}>
      {/* IoT Device Status Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
        <span style={{
          background: getStatusColor(),
          color: '#fff',
          fontSize: '0.7rem',
          fontWeight: 'bold',
          padding: '2px 8px',
          borderRadius: '4px',
          letterSpacing: '1px',
        }}>
          {getStatusText()}
        </span>
        <h3 style={{ margin: 0, fontSize: '1rem' }}>
          🔌 IoT Device Monitor
        </h3>
        <span style={{ marginLeft: 'auto', fontSize: '0.8rem', opacity: 0.6 }}>
          House: {houseId}
        </span>
      </div>

      {error ? (
        <div style={{
          padding: '1rem',
          background: 'rgba(231, 76, 60, 0.1)',
          border: '1px solid #e74c3c',
          borderRadius: '8px',
          color: '#e74c3c',
          textAlign: 'center',
        }}>
          {error}
        </div>
      ) : iotData ? (
        <>
          {/* Current Generation Display */}
          <div style={{ marginBottom: '1.25rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
              <label style={{ fontSize: '0.9rem', opacity: 0.8 }}>
                Current Solar Generation
              </label>
              <span style={{
                fontWeight: 'bold',
                fontSize: '1.2rem',
                color: getStatusColor(),
              }}>
                {iotData.generation_kwh?.toFixed(2) || '0.00'} kW
              </span>
            </div>

            {/* Visual bar */}
            <div style={{
              width: '100%',
              height: '20px',
              background: 'rgba(255,255,255,0.1)',
              borderRadius: '10px',
              overflow: 'hidden',
            }}>
              <div style={{
                width: `${Math.min(100, (iotData.generation_kwh / 5.0) * 100)}%`,
                height: '100%',
                background: getStatusColor(),
                transition: 'width 0.5s ease',
              }} />
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', opacity: 0.5, marginTop: '0.25rem' }}>
              <span>0 kW</span>
              <span>5 kW (Max Capacity)</span>
            </div>
          </div>

          {/* Device Details */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
            gap: '1rem',
            marginBottom: '1rem',
          }}>
            <div>
              <div style={{ opacity: 0.7, fontSize: '0.8rem' }}>Device ID</div>
              <div style={{ fontWeight: 'bold', fontSize: '0.9rem' }}>
                {iotData.device_id || 'Unknown'}
              </div>
            </div>
            <div>
              <div style={{ opacity: 0.7, fontSize: '0.8rem' }}>WiFi Signal</div>
              <div style={{ fontWeight: 'bold', fontSize: '0.9rem' }}>
                {iotData.signal_strength || 0} dBm
              </div>
            </div>
            <div>
              <div style={{ opacity: 0.7, fontSize: '0.8rem' }}>Last Update</div>
              <div style={{ fontWeight: 'bold', fontSize: '0.8rem' }}>
                {lastUpdate ? lastUpdate.toLocaleTimeString() : 'Never'}
              </div>
            </div>
          </div>
        </>
      ) : (
        <div style={{
          padding: '2rem',
          textAlign: 'center',
          color: '#888',
        }}>
          Waiting for IoT device data...
        </div>
      )}
    </div>
  )
}
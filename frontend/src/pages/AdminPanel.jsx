import { useState, useEffect } from 'react'
import api from '../services/api'

export default function AdminPanel({ feederCode }) {
  const [nightMode, setNightMode] = useState(false)
  const [feederDetails, setFeederDetails] = useState(null)
  const [housesList, setHousesList] = useState([])
  const [dailyMetrics, setDailyMetrics] = useState(null)
  const [monthlyMetrics, setMonthlyMetrics] = useState(null)
  const [allFeeders, setAllFeeders] = useState(null)
  const [loadingDaily, setLoadingDaily] = useState(false)
  const [loadingMonthly, setLoadingMonthly] = useState(false)

  const toggleNightMode = async () => {
    try {
      const res = await api.post('/admin/night-mode', {
        enabled: !nightMode,
        feeder_code: feederCode,
        reason: 'Admin toggle',
      })
      setNightMode(!nightMode)
      alert(`Night mode ${!nightMode ? 'enabled' : 'disabled'}`)
    } catch (error) {
      alert(`Error: ${error.message}`)
    }
  }

  const fetchFeederDetails = async () => {
    try {
      const res = await api.get(`/admin/feeders/${feederCode}`)
      setFeederDetails(res.data)
    } catch (error) {
      alert(`Error: ${error.message}`)
    }
  }

  const fetchHouses = async () => {
    try {
      const res = await api.get(`/admin/houses/${feederCode}`)
      setHousesList(res.data)
    } catch (error) {
      alert(`Error: ${error.message}`)
    }
  }

  const fetchDailyMetrics = async () => {
    try {
      setLoadingDaily(true)
      const res = await api.get(`/admin/dashboard/feeder/${feederCode}/daily`)
      setDailyMetrics(res.data)
    } catch (error) {
      alert(`Error: ${error.message}`)
    } finally {
      setLoadingDaily(false)
    }
  }

  const fetchMonthlyMetrics = async () => {
    try {
      setLoadingMonthly(true)
      const res = await api.get(`/admin/dashboard/feeder/${feederCode}/monthly`)
      setMonthlyMetrics(res.data)
    } catch (error) {
      alert(`Error: ${error.message}`)
    } finally {
      setLoadingMonthly(false)
    }
  }

  const fetchAllFeeders = async () => {
    try {
      const res = await api.get('/admin/dashboard/all-feeders')
      setAllFeeders(res.data)
    } catch (error) {
      alert(`Error: ${error.message}`)
    }
  }

  return (
    <div>
      <h1>⚙️ Admin Panel - DISCOM Dashboard</h1>
      <p style={{ color: '#888', marginBottom: '2rem' }}>Manage {feederCode} operations and blockchain metrics</p>

      {/* Simulation Controls */}
      <div className="card">
        <h3>🌙 Simulation Controls</h3>
        <div style={{ marginBottom: '1rem' }}>
          <p>Simulate day/night cycle or cloud cover for testing.</p>
          <button
            onClick={toggleNightMode}
            className={nightMode ? 'danger' : 'success'}
            style={{ marginTop: '1rem', width: '100%', padding: '1rem' }}
          >
            {nightMode ? '🌙 Night Mode ACTIVE' : '☀️ Enable Night Mode'}
          </button>
        </div>
        {nightMode && (
          <div className="alert warning">
            Solar generation multiplier set to 0.0 (simulating complete cloud cover)
          </div>
        )}
      </div>

      {/* Feeder Overview */}
      <div className="grid grid-2">
        <div className="card">
          <h3>📊 Feeder Details</h3>
          {feederDetails ? (
            <div>
              <div style={{ marginBottom: '0.5rem' }}>
                <small style={{ opacity: 0.7 }}>Code</small>
                <div style={{ fontWeight: 'bold' }}>{feederDetails.feeder_code}</div>
              </div>
              <div style={{ marginBottom: '0.5rem' }}>
                <small style={{ opacity: 0.7 }}>Location</small>
                <div>{feederDetails.location || 'N/A'}</div>
              </div>
              <div style={{ marginBottom: '0.5rem' }}>
                <small style={{ opacity: 0.7 }}>Capacity</small>
                <div>{feederDetails.total_capacity_kw} kW</div>
              </div>
              <div style={{ marginBottom: '0.5rem' }}>
                <small style={{ opacity: 0.7 }}>Houses</small>
                <div>{feederDetails.house_count}</div>
              </div>
              <button onClick={fetchFeederDetails} style={{ marginTop: '1rem', width: '100%' }}>
                🔄 Refresh
              </button>
            </div>
          ) : (
            <button onClick={fetchFeederDetails} style={{ width: '100%' }}>
              📥 Load Details
            </button>
          )}
        </div>

        <div className="card">
          <h3>🏘️ Houses in Feeder</h3>
          {housesList.length > 0 ? (
            <div>
              <div style={{ maxHeight: '200px', overflowY: 'auto', marginBottom: '1rem' }}>
                {housesList.map(house => (
                  <div key={house.house_id} style={{
                    padding: '0.5rem',
                    borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
                    fontSize: '0.9rem',
                  }}>
                    <strong>{house.house_id}</strong> ({house.prosumer_type})
                    <div style={{ opacity: 0.7, fontSize: '0.8rem' }}>
                      {house.solar_capacity_kw} kW {house.is_active ? '✓' : '✗'}
                    </div>
                  </div>
                ))}
              </div>
              <button onClick={fetchHouses} style={{ width: '100%' }}>
                🔄 Refresh
              </button>
            </div>
          ) : (
            <button onClick={fetchHouses} style={{ width: '100%' }}>
              📥 Load Houses
            </button>
          )}
        </div>
      </div>

      {/* Daily Metrics */}
      {dailyMetrics ? (
        <div className="card">
          <h3>📈 Daily Feeder Metrics</h3>
          <div className="grid grid-3" style={{ marginBottom: '1rem' }}>
            <div style={{
              background: 'rgba(39, 174, 96, 0.1)',
              padding: '1rem',
              borderRadius: '8px',
            }}>
              <div style={{ fontSize: '0.85rem', opacity: 0.8 }}>Generation</div>
              <div style={{ fontSize: '1.6rem', fontWeight: 'bold', color: '#27ae60' }}>
                {dailyMetrics.total_generation_kwh?.toFixed(2) || '0.00'}
              </div>
              <div style={{ fontSize: '0.75rem', opacity: 0.7 }}>kWh</div>
            </div>

            <div style={{
              background: 'rgba(52, 152, 219, 0.1)',
              padding: '1rem',
              borderRadius: '8px',
            }}>
              <div style={{ fontSize: '0.85rem', opacity: 0.8 }}>Demand</div>
              <div style={{ fontSize: '1.6rem', fontWeight: 'bold', color: '#3498db' }}>
                {dailyMetrics.total_demand_kwh?.toFixed(2) || '0.00'}
              </div>
              <div style={{ fontSize: '0.75rem', opacity: 0.7 }}>kWh</div>
            </div>

            <div style={{
              background: 'rgba(241, 196, 15, 0.1)',
              padding: '1rem',
              borderRadius: '8px',
            }}>
              <div style={{ fontSize: '0.85rem', opacity: 0.8 }}>Grid Fallback</div>
              <div style={{ fontSize: '1.6rem', fontWeight: 'bold', color: '#f1c40f' }}>
                {dailyMetrics.grid_fallback_kwh?.toFixed(2) || '0.00'}
              </div>
              <div style={{ fontSize: '0.75rem', opacity: 0.7 }}>kWh</div>
            </div>
          </div>

          <div className="grid grid-2">
            <div style={{
              background: 'rgba(155, 89, 182, 0.1)',
              padding: '1rem',
              borderRadius: '8px',
            }}>
              <div style={{ fontSize: '0.85rem', opacity: 0.8 }}>Allocations Matched</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 'bold', color: '#9b59b6' }}>
                {dailyMetrics.allocations_matched || '0'}
              </div>
            </div>

            <div style={{
              background: 'rgba(231, 76, 60, 0.1)',
              padding: '1rem',
              borderRadius: '8px',
            }}>
              <div style={{ fontSize: '0.85rem', opacity: 0.8 }}>Wallets Deployed</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 'bold', color: '#e74c3c' }}>
                {dailyMetrics.wallets_deployed_count || '0'} / {dailyMetrics.total_houses || '0'}
              </div>
              <div style={{ fontSize: '0.75rem', opacity: 0.7 }}>
                {dailyMetrics.wallet_deployment_percentage?.toFixed(1)}%
              </div>
            </div>
          </div>
        </div>
      ) : (
        <button onClick={fetchDailyMetrics} disabled={loadingDaily} style={{ width: '100%', marginBottom: '1rem', padding: '1rem' }}>
          {loadingDaily ? '📊 Loading Daily Metrics...' : '📊 Load Daily Metrics'}
        </button>
      )}

      {/* Monthly Metrics */}
      {monthlyMetrics ? (
        <div className="card">
          <h3>💰 Monthly Feeder Performance</h3>
          <div className="grid grid-2" style={{ marginBottom: '1rem' }}>
            <div style={{
              background: 'rgba(39, 174, 96, 0.1)',
              padding: '1rem',
              borderRadius: '8px',
            }}>
              <div style={{ fontSize: '0.85rem', opacity: 0.8 }}>Revenue (Pool Sales)</div>
              <div style={{ fontSize: '1.6rem', fontWeight: 'bold', color: '#27ae60' }}>
                ₹{monthlyMetrics.monthly_revenue || '0.00'}
              </div>
            </div>

            <div style={{
              background: 'rgba(241, 196, 15, 0.1)',
              padding: '1rem',
              borderRadius: '8px',
            }}>
              <div style={{ fontSize: '0.85rem', opacity: 0.8 }}>Costs (Grid Purchase)</div>
              <div style={{ fontSize: '1.6rem', fontWeight: 'bold', color: '#f1c40f' }}>
                ₹{monthlyMetrics.monthly_costs || '0.00'}
              </div>
            </div>

            <div style={{
              background: monthlyMetrics.net_profit >= 0 ? 'rgba(39, 174, 96, 0.1)' : 'rgba(231, 76, 60, 0.1)',
              padding: '1rem',
              borderRadius: '8px',
            }}>
              <div style={{ fontSize: '0.85rem', opacity: 0.8 }}>Net Profit</div>
              <div style={{
                fontSize: '1.6rem',
                fontWeight: 'bold',
                color: monthlyMetrics.net_profit >= 0 ? '#27ae60' : '#e74c3c',
              }}>
                ₹{monthlyMetrics.net_profit?.toFixed(2) || '0.00'}
              </div>
            </div>

            <div style={{
              background: 'rgba(46, 204, 113, 0.1)',
              padding: '1rem',
              borderRadius: '8px',
            }}>
              <div style={{ fontSize: '0.85rem', opacity: 0.8 }}>SUN Issued (Certificates)</div>
              <div style={{ fontSize: '1.6rem', fontWeight: 'bold', color: '#2ecc71' }}>
                {monthlyMetrics.sun_issued_count?.toFixed(2) || '0.00'}
              </div>
            </div>
          </div>

          <div style={{
            background: 'rgba(52, 152, 219, 0.1)',
            padding: '1rem',
            borderRadius: '8px',
            borderLeft: '4px solid #3498db',
          }}>
            <div style={{ fontSize: '0.85rem', opacity: 0.8, marginBottom: '0.5rem' }}>
              Bills on Blockchain
            </div>
            <div style={{ fontSize: '1.4rem', fontWeight: 'bold', color: '#3498db' }}>
              {monthlyMetrics.bills_on_blockchain_count || '0'} bills
            </div>
            <div style={{ fontSize: '0.8rem', opacity: 0.7 }}>
              Immutably recorded on Algorand testnet
            </div>
          </div>
        </div>
      ) : (
        <button onClick={fetchMonthlyMetrics} disabled={loadingMonthly} style={{ width: '100%', marginBottom: '1rem', padding: '1rem' }}>
          {loadingMonthly ? '💰 Loading Monthly Metrics...' : '💰 Load Monthly Metrics'}
        </button>
      )}

      {/* Tariff & Pricing Information */}
      <div className="card">
        <h3>⚡ Realistic Rajasthan Tariff Model</h3>
        <p style={{ opacity: 0.8, marginBottom: '1.5rem' }}>
          ROSHNI uses actual Rajasthan DISCOM slab-based electricity pricing for realistic billing.
        </p>

        <div className="grid grid-2">
          <div style={{ background: 'rgba(231, 76, 60, 0.08)', padding: '1rem', borderRadius: '8px', borderLeft: '3px solid #e74c3c' }}>
            <h4 style={{ marginBottom: '0.8rem', color: '#e74c3c' }}>🔌 Domestic (Residential) Tariff</h4>
            <div style={{ fontSize: '0.85rem', lineHeight: '1.6' }}>
              <div><strong>Slab 1:</strong> 0-100 kWh @ ₹3/kWh</div>
              <div><strong>Slab 2:</strong> 101-200 kWh @ ₹5/kWh</div>
              <div><strong>Slab 3:</strong> 200+ kWh @ ₹7.95/kWh</div>
              <div style={{ marginTop: '0.8rem', borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '0.8rem' }}>
                <strong>Fixed Charges:</strong> ₹120-360/month
              </div>
              <div><strong>Meter Rent:</strong> ₹20/month</div>
              <div><strong>Electricity Duty:</strong> 3%</div>
              <div><strong>Surcharge:</strong> 1.5%</div>
            </div>
          </div>

          <div style={{ background: 'rgba(39, 174, 96, 0.08)', padding: '1rem', borderRadius: '8px', borderLeft: '3px solid #27ae60' }}>
            <h4 style={{ marginBottom: '0.8rem', color: '#27ae60' }}>💚 Pool & Export Rates</h4>
            <div style={{ fontSize: '0.85rem', lineHeight: '1.8' }}>
              <div>
                <strong>Grid Rate (DISCOM):</strong>
                <div style={{ opacity: 0.7 }}> Slab-based (₹3-₹7.95/kWh)</div>
              </div>
              <div style={{ marginTop: '0.8rem' }}>
                <strong>Pool Rate (P2P Trading):</strong>
                <div style={{ opacity: 0.7 }}>₹9/kWh (Dynamic)</div>
              </div>
              <div style={{ marginTop: '0.8rem' }}>
                <strong>Solar Export Buyback:</strong>
                <div style={{ opacity: 0.7 }}>₹6.5/kWh</div>
              </div>
              <div style={{ marginTop: '0.8rem', background: 'rgba(39, 174, 96, 0.2)', padding: '0.6rem', borderRadius: '4px' }}>
                <strong style={{ color: '#27ae60' }}>Savings: 25% off grid rate!</strong>
              </div>
            </div>
          </div>
        </div>

        <div style={{ marginTop: '1rem', background: 'rgba(52, 152, 219, 0.08)', padding: '1rem', borderRadius: '8px', borderLeft: '3px solid #3498db' }}>
          <h4 style={{ marginBottom: '0.8rem', color: '#3498db' }}>📊 How the Model Works</h4>
          <ol style={{ fontSize: '0.85rem', lineHeight: '1.8', marginLeft: '1rem' }}>
            <li><strong>Grid Consumption:</strong> Billed at slab-based DISCOM rates (realistic)</li>
            <li><strong>Pool Purchase:</strong> Consumer pays ₹9/kWh to prosumer (cheaper than grid)</li>
            <li><strong>Pool Sale:</strong> Prosumer earns ₹9/kWh (vs ₹6.5 grid export rate)</li>
            <li><strong>Solar Export:</strong> Unsold surplus gets ₹6.5/kWh from DISCOM</li>
            <li><strong>Monthly Settlement:</strong> Bills include taxes, duties, and surcharges</li>
            <li><strong>Blockchain Recording:</strong> All bills hashed and recorded on Algorand for immutability</li>
          </ol>
          <p style={{ fontSize: '0.8rem', marginTop: '1rem', opacity: 0.7, padding: '0.5rem', background: 'rgba(0,0,0,0.3)', borderRadius: '4px' }}>
            💡 <strong>Rationale:</strong> Progressive slab rates encourage conservation. Pool trading creates a win-win: prosumers earn more, consumers save 25%. DISCOM retains control with settlement authority.
          </p>
        </div>
      </div>

      {/* All Feeders Overview */}
      <div className="card">
        <h3>🌐 All Feeders - DISCOM Overview</h3>
        {allFeeders ? (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%' }}>
              <thead>
                <tr>
                  <th>Feeder Code</th>
                  <th>Houses</th>
                  <th>Wallets Deployed</th>
                  <th>Deployment %</th>
                  <th>Monthly Revenue</th>
                </tr>
              </thead>
              <tbody>
                {allFeeders.feeders && allFeeders.feeders.map(feeder => (
                  <tr key={feeder.feeder_code}>
                    <td style={{ fontWeight: 'bold' }}>{feeder.feeder_code}</td>
                    <td>{feeder.total_houses}</td>
                    <td>{feeder.wallets_deployed}</td>
                    <td>
                      <span style={{
                        background: feeder.wallet_deployment_percentage < 50 ? 'rgba(231, 76, 60, 0.2)' : 'rgba(39, 174, 96, 0.2)',
                        padding: '0.3rem 0.6rem',
                        borderRadius: '4px',
                        color: feeder.wallet_deployment_percentage < 50 ? '#e74c3c' : '#27ae60',
                        fontWeight: 'bold',
                      }}>
                        {feeder.wallet_deployment_percentage.toFixed(1)}%
                      </span>
                    </td>
                    <td style={{ color: feeder.monthly_revenue >= 0 ? '#27ae60' : '#e74c3c' }}>
                      ₹{feeder.monthly_revenue.toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <button onClick={fetchAllFeeders} style={{ width: '100%' }}>
            📡 Load All Feeders
          </button>
        )}
      </div>

      <div className="alert info">
        <strong>Admin Notes:</strong>
        <ul style={{ marginTop: '0.5rem', paddingLeft: '1.5rem' }}>
          <li>Night mode testing simulates cloud cover (generation → 0)</li>
          <li>Wallet deployment shows blockchain readiness of each feeder</li>
          <li>SUN tokens are Algorand ASA (Asset ID: 756341116)</li>
          <li>All bills are hashed and recorded on Algorand testnet</li>
          <li>DISCOM maintains final settlement authority</li>
        </ul>
      </div>
    </div>
  )
}

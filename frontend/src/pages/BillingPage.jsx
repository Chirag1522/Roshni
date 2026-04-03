import { useState, useEffect } from 'react'
import api from '../services/api'
import voiceService from '../services/voice'

export default function BillingPage({ houseId }) {
  const [bills, setBills] = useState([])
  const [selectedBill, setSelectedBill] = useState(null)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [month, setMonth] = useState(new Date().toISOString().slice(0, 7))
  const [voiceEnabled, setVoiceEnabled] = useState(localStorage.getItem('voiceEnabled') !== 'false')
  const [isSpeaking, setIsSpeaking] = useState(false)

  useEffect(() => {
    fetchBills()
  }, [houseId])

  const fetchBills = async () => {
    try {
      const res = await api.get(`/billing/${houseId}/monthly-list`)
      setBills(res.data)
      setLoading(false)
    } catch (error) {
      console.error('Error fetching bills:', error)
      setLoading(false)
    }
  }

  const generateBill = async () => {
    setGenerating(true)
    try {
      await api.post(`/billing/generate/${houseId}/${month}`)
      fetchBills()
    } catch (error) {
      alert(`Error: ${error.message}`)
    } finally {
      setGenerating(false)
    }
  }

  const fetchBillDetail = async (billId) => {
    try {
      const res = await api.get(`/billing/${houseId}/${bills.find(b => b.bill_id === billId).month_year}`)
      setSelectedBill(res.data)
    } catch (error) {
      alert(`Error: ${error.message}`)
    }
  }

  const speakBill = async () => {
    if (selectedBill && voiceEnabled) {
      setIsSpeaking(true)
      await voiceService.narrateBill(selectedBill)
      setIsSpeaking(false)
    }
  }

  if (loading) return <div className="spinner" />

  return (
    <div>
      <h1>💰 Monthly Bills & Settlements</h1>
      <p style={{ color: '#888', marginBottom: '2rem' }}>House: {houseId}</p>

      <div className="card">
        <h3>Generate New Bill</h3>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-end' }}>
          <div style={{ flex: 1 }}>
            <label>Month-Year</label>
            <input
              type="month"
              value={month}
              onChange={(e) => setMonth(e.target.value)}
            />
          </div>
          <button
            onClick={generateBill}
            disabled={generating}
            className="success"
          >
            {generating ? 'Generating...' : '📋 Generate'}
          </button>
        </div>
      </div>

      {bills.length === 0 ? (
        <div className="alert info">No bills generated yet. Create one above.</div>
      ) : (
        <div className="card">
          <h3>📊 Bill History</h3>
          <div style={{ overflowX: 'auto' }}>
            <table>
              <thead>
                <tr>
                  <th>Month-Year</th>
                  <th>Net Payable</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {bills.map(bill => (
                  <tr key={bill.bill_id}>
                    <td>{bill.month_year}</td>
                    <td style={{ color: bill.net_payable < 0 ? '#27ae60' : '#ff6b6b', fontWeight: 'bold' }}>
                      ₹{bill.net_payable.toFixed(2)}
                    </td>
                    <td>
                      <span className={`status ${bill.status}`}>
                        {bill.status.toUpperCase()}
                      </span>
                    </td>
                    <td>
                      <button
                        onClick={() => fetchBillDetail(bill.bill_id)}
                        style={{
                          background: 'var(--info)',
                          padding: '0.4rem 0.8rem',
                          fontSize: '0.85rem',
                        }}
                      >
                        View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {selectedBill && (
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
            <h3>Bill Details - {selectedBill.month_year}</h3>
            <button
              onClick={speakBill}
              disabled={isSpeaking}
              className="voice-btn active"
              title="Listen to bill summary"
            >
              {isSpeaking ? '🔊 Speaking...' : '🔊 Speak Summary'}
            </button>
          </div>
          
          <div className="grid grid-2">
            <div>
              <h4 style={{ marginBottom: '1rem', color: 'var(--primary)' }}>Energy Metrics (kWh)</h4>
              <div style={{ display: 'grid', gap: '0.8rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '0.5rem', borderBottom: '1px solid rgba(255, 255, 255, 0.1)' }}>
                  <span>Solar Generated</span>
                  <strong>{selectedBill.solar_generated_kwh.toFixed(2)}</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '0.5rem', borderBottom: '1px solid rgba(255, 255, 255, 0.1)' }}>
                  <span>Solar Exported</span>
                  <strong>{selectedBill.solar_exported_kwh.toFixed(2)}</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '0.5rem', borderBottom: '1px solid rgba(255, 255, 255, 0.1)' }}>
                  <span>Pool Bought</span>
                  <strong>{selectedBill.pool_bought_kwh.toFixed(2)}</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '0.5rem', borderBottom: '1px solid rgba(255, 255, 255, 0.1)' }}>
                  <span>Pool Sold</span>
                  <strong>{selectedBill.pool_sold_kwh.toFixed(2)}</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Grid Bought</span>
                  <strong>{selectedBill.grid_bought_kwh.toFixed(2)}</strong>
                </div>
              </div>
            </div>

            <div>
              <h4 style={{ marginBottom: '1rem', color: 'var(--primary)' }}>Financial Summary (₹)</h4>
              <div style={{ display: 'grid', gap: '0.8rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '0.5rem', borderBottom: '1px solid rgba(255, 255, 255, 0.1)', color: '#27ae60' }}>
                  <span>Solar Export Credit</span>
                  <strong>+{selectedBill.solar_export_credit.toFixed(2)}</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '0.5rem', borderBottom: '1px solid rgba(255, 255, 255, 0.1)', color: '#27ae60' }}>
                  <span>Pool Sale Credit</span>
                  <strong>+{selectedBill.pool_sale_credit.toFixed(2)}</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '0.5rem', borderBottom: '1px solid rgba(255, 255, 255, 0.1)', color: '#ff6b6b' }}>
                  <span>Pool Purchase</span>
                  <strong>-{selectedBill.pool_purchase_charge.toFixed(2)}</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '0.5rem', borderBottom: '1px solid rgba(255, 255, 255, 0.1)', color: '#ff6b6b' }}>
                  <span>Grid Purchase</span>
                  <strong>-{selectedBill.grid_purchase_charge.toFixed(2)}</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '0.5rem', borderBottom: '1px solid rgba(255, 255, 255, 0.1)', color: '#ff6b6b' }}>
                  <span>DISCOM Fixed Charge</span>
                  <strong>-{selectedBill.discom_fixed_charge.toFixed(2)}</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', color: '#ff6b6b' }}>
                  <span>Admin Fee</span>
                  <strong>-{selectedBill.discom_admin_fee.toFixed(2)}</strong>
                </div>
              </div>
            </div>
          </div>

          <div style={{ marginTop: '2rem', padding: '1rem', background: 'rgba(52, 152, 219, 0.08)', borderRadius: '8px', borderLeft: '3px solid #3498db' }}>
            <h4 style={{ marginBottom: '1rem', color: '#3498db' }}>⚡ Slab-Based Pricing Breakdown</h4>
            <p style={{ fontSize: '0.9rem', opacity: 0.8, marginBottom: '1rem' }}>
              DISCOM charges use Rajasthan slab-based tariff. Grid consumption: <strong>{selectedBill.grid_bought_kwh.toFixed(2)} kWh</strong>
            </p>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1rem' }}>
              <div style={{ background: 'rgba(0, 0, 0, 0.3)', padding: '0.8rem', borderRadius: '6px' }}>
                <div style={{ fontSize: '0.85rem', opacity: 0.7 }}>Energy Charges (Slab-Based)</div>
                <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#e74c3c', marginTop: '0.3rem' }}>
                  ₹{(selectedBill.grid_purchase_charge - selectedBill.discom_fixed_charge - (selectedBill.discom_fixed_charge > 0 ? 20 : 0)).toFixed(2)}
                </div>
                <div style={{ fontSize: '0.75rem', marginTop: '0.5rem', opacity: 0.6 }}>
                  Includes: Slab 1 (0-100 units) @ ₹3/kWh | Slab 2 (100-200) @ ₹5/kWh | Slab 3 (200+) @ ₹7.95/kWh
                </div>
              </div>
              <div style={{ background: 'rgba(0, 0, 0, 0.3)', padding: '0.8rem', borderRadius: '6px' }}>
                <div style={{ fontSize: '0.85rem', opacity: 0.7 }}>Fixed Charges & Surcharges</div>
                <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#9b59b6', marginTop: '0.3rem' }}>
                  ₹{selectedBill.discom_fixed_charge.toFixed(2)}
                </div>
                <div style={{ fontSize: '0.75rem', marginTop: '0.5rem', opacity: 0.6 }}>
                  Includes: Fixed charge (₹120-360) + Meter rent (₹20) + Electricity duty (3%) + Surcharge (1.5%)
                </div>
              </div>
              <div style={{ background: 'rgba(0, 0, 0, 0.3)', padding: '0.8rem', borderRadius: '6px' }}>
                <div style={{ fontSize: '0.85rem', opacity: 0.7 }}>Pool Rate (Peer-to-Peer)</div>
                <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#27ae60', marginTop: '0.3rem' }}>
                  ₹9.00/kWh
                </div>
                <div style={{ fontSize: '0.75rem', marginTop: '0.5rem', opacity: 0.6 }}>
                  25% cheaper than grid rate (₹12/kWh)
                </div>
              </div>
            </div>
            <p style={{ fontSize: '0.8rem', marginTop: '1rem', opacity: 0.6, borderTop: '1px solid rgba(255, 255, 255, 0.1)', paddingTop: '0.8rem' }}>
              💡 Realistic Rajasthan tariff based on DISCOM rates. Slab rates increase with consumption to encourage conservation. Pool trading provides 25% savings over grid alternatives.
            </p>
          </div>

          <div style={{
            background: selectedBill.net_payable < 0 ? 'rgba(39, 174, 96, 0.1)' : 'rgba(255, 107, 107, 0.1)',
            padding: '1.5rem',
            borderRadius: '8px',
            marginTop: '1rem',
            marginBottom: '1rem',
            textAlign: 'center',
            borderLeft: `4px solid ${selectedBill.net_payable < 0 ? '#27ae60' : '#ff6b6b'}`,
          }}>
            <div style={{ fontSize: '0.9rem', opacity: 0.8, marginBottom: '0.5rem' }}>NET PAYABLE</div>
            <div style={{
              fontSize: '2rem',
              fontWeight: 'bold',
              color: selectedBill.net_payable < 0 ? '#27ae60' : '#ff6b6b',
            }}>
              ₹{selectedBill.net_payable.toFixed(2)}
            </div>
            <div style={{ fontSize: '0.8rem', opacity: 0.7, marginTop: '0.5rem' }}>
              {selectedBill.net_payable < 0 ? '✓ Credit (Receive)' : '✗ Debit (Pay)'}
            </div>
          </div>

          {selectedBill.sun_asa_minted > 0 && (
            <div className="alert info">
              <strong>🌞 SUN ASA Minted:</strong> {selectedBill.sun_asa_minted.toFixed(2)} SUN tokens
              (renewable allocation certificates) recorded on Algorand blockchain.
            </div>
          )}

          {selectedBill.bill_hash && (
            <div className="alert info" style={{ marginTop: '1rem' }}>
              <strong>⛓️ Blockchain Verification:</strong>
              <div style={{ marginTop: '0.5rem', fontSize: '0.85rem' }}>
                <div style={{ marginBottom: '0.5rem' }}>
                  <strong>Bill Hash (SHA256):</strong>
                  <div style={{
                    fontSize: '0.75rem',
                    fontFamily: 'monospace',
                    wordBreak: 'break-all',
                    background: 'rgba(0, 0, 0, 0.3)',
                    padding: '0.5rem',
                    borderRadius: '4px',
                    marginTop: '0.3rem',
                  }}>
                    {selectedBill.bill_hash}
                  </div>
                </div>
              </div>
              <p style={{ marginTop: '0.5rem', opacity: 0.8 }}>
                Immutable proof of bill recorded on Algorand testnet.
              </p>
              {selectedBill.blockchain_txn && (
                <a
                  href={`https://testnet.algoexplorer.io/tx/${selectedBill.blockchain_txn}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    display: 'inline-block',
                    marginTop: '0.7rem',
                    padding: '0.5rem 1rem',
                    background: '#3498db',
                    color: 'white',
                    borderRadius: '4px',
                    textDecoration: 'none',
                    fontSize: '0.85rem',
                    fontWeight: 'bold',
                  }}
                >
                  🔗 View on Algoexplorer →
                </a>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
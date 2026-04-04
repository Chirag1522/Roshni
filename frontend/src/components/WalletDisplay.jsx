import { useState, useEffect } from 'react'
import api from '../services/api'

export default function WalletDisplay({ houseId, refreshTrigger = 0 }) {
  const [wallet, setWallet] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [checking, setChecking] = useState(false)
  const [initializing, setInitializing] = useState(false)
  const [optingIn, setOptingIn] = useState(false)

  // ✅ Fix: refresh when refreshTrigger changes (after allocation)
  // AND auto-refresh every 10s to catch blockchain confirmations
  useEffect(() => {
    fetchWallet()
  }, [houseId, refreshTrigger])

  useEffect(() => {
    const interval = setInterval(fetchWallet, 3000)
    return () => clearInterval(interval)
  }, [houseId])

  const fetchWallet = async () => {
    try {
      const res = await api.get(`/wallet/${houseId}`)
      setWallet(res.data)
      setError(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const initializeWallet = async () => {
    try {
      setInitializing(true)
      setError(null)
      await api.post(`/wallet/initialize/${houseId}`)
      setTimeout(fetchWallet, 1000)
    } catch (err) {
      setError(`Failed to initialize wallet: ${err.message}`)
    } finally {
      setInitializing(false)
    }
  }

  const optInToSUN = async () => {
    try {
      setOptingIn(true)
      setError(null)
      await api.post(`/wallet/opt-in-sun/${houseId}`)
      setTimeout(fetchWallet, 1000)
    } catch (err) {
      setError(`Failed to opt-in to SUN: ${err.message}`)
    } finally {
      setOptingIn(false)
    }
  }

  const checkBalance = async () => {
    try {
      setChecking(true)
      const res = await api.post(`/wallet/check-balance/${houseId}`)
      setWallet(prev => ({
        ...prev,
        sun_balance_on_chain: res.data.sun_balance,
      }))
    } catch (err) {
      setError(err.message)
    } finally {
      setChecking(false)
    }
  }

  if (loading) return (
    <div className="card">
      <div style={{ textAlign: 'center', padding: '2rem' }}>
        <div className="spinner" />
        <p style={{ marginTop: '1rem' }}>Loading wallet...</p>
      </div>
    </div>
  )

  if (error && !wallet) return (
    <div className="card" style={{ borderLeft: '4px solid #ff6b6b' }}>
      <h3>⚠️ Wallet Error</h3>
      <p style={{ color: '#ff6b6b' }}>{error}</p>
      <button onClick={fetchWallet} style={{ marginTop: '1rem' }}>🔄 Retry</button>
    </div>
  )

  if (!wallet || wallet.status === 'not_initialized') return (
    <div className="card" style={{ borderLeft: '4px solid #f39c12' }}>
      <h3>🎯 Wallet Setup Required</h3>
      <p>Your house doesn't have a blockchain wallet yet.</p>
      <p style={{ marginTop: '1rem', fontSize: '0.9rem', opacity: 0.8 }}>
        A custodial Algorand wallet will be created to manage your SUN tokens.
      </p>
      {error && <div className="alert danger" style={{ marginTop: '1rem' }}>{error}</div>}
      <button
        onClick={initializeWallet}
        disabled={initializing}
        style={{ marginTop: '1rem', width: '100%' }}
        className="success"
      >
        {initializing ? '⏳ Initializing...' : '✅ Initialize Wallet'}
      </button>
    </div>
  )

  return (
    <div className="card" style={{ borderLeft: '4px solid #3498db' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h3>🌐 Blockchain Wallet</h3>
        <button
          onClick={checkBalance}
          disabled={checking}
          style={{
            padding: '0.5rem 1rem',
            fontSize: '0.85rem',
            background: 'rgba(52,152,219,0.2)',
            border: '1px solid #3498db',
            borderRadius: '4px',
            cursor: 'pointer',
            color: '#3498db',
          }}
        >
          {checking ? '🔄 Syncing...' : '🔄 Sync Balance'}
        </button>
      </div>

      <div className="grid grid-2" style={{ marginBottom: '1.5rem' }}>
        <div style={{
          background: 'rgba(39,174,96,0.1)',
          padding: '1.5rem',
          borderRadius: '8px',
          border: '1px solid rgba(39,174,96,0.3)',
        }}>
          <div style={{ fontSize: '0.85rem', opacity: 0.8, marginBottom: '0.5rem' }}>SUN Balance (On-Chain)</div>
          <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#27ae60' }}>
            {wallet.sun_balance_on_chain?.toFixed(2) || '0.00'}
          </div>
          <div style={{ fontSize: '0.8rem', opacity: 0.7, marginTop: '0.5rem' }}>Renewable Certificates</div>
        </div>

        <div style={{
          background: 'rgba(52,152,219,0.1)',
          padding: '1.5rem',
          borderRadius: '8px',
          border: '1px solid rgba(52,152,219,0.3)',
        }}>
          <div style={{ fontSize: '0.85rem', opacity: 0.8, marginBottom: '0.5rem' }}>Wallet Address</div>
          <div style={{ fontSize: '0.75rem', fontFamily: 'monospace', wordBreak: 'break-all', color: '#3498db', marginTop: '0.5rem' }}>
            {wallet.algorand_address}
          </div>
          {wallet.explorer_url && (
            <a href={wallet.explorer_url} target="_blank" rel="noopener noreferrer"
              style={{ display: 'inline-block', marginTop: '0.5rem', fontSize: '0.75rem', color: '#3498db', textDecoration: 'underline' }}>
              View on Dappflow →
            </a>
          )}
        </div>
      </div>

      {/* Opt-in status */}
      <div style={{
        background: wallet.opt_in_sun_asa ? 'rgba(39,174,96,0.1)' : 'rgba(243,156,18,0.1)',
        padding: '1rem',
        borderRadius: '8px',
        marginBottom: '1.5rem',
        borderLeft: `4px solid ${wallet.opt_in_sun_asa ? '#27ae60' : '#f39c12'}`,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: '1.2rem' }}>{wallet.opt_in_sun_asa ? '✅' : '📋'}</span>
            <div>
              <div style={{ fontWeight: 'bold' }}>
                {wallet.opt_in_sun_asa ? '✅ SUN Ready' : '🔗 Opt-In to SUN ASA'}
              </div>
              <div style={{ fontSize: '0.85rem', opacity: 0.8 }}>
                {wallet.opt_in_sun_asa
                  ? 'Your wallet can receive and hold SUN tokens'
                  : 'Click to enable SUN token transfers'}
              </div>
            </div>
          </div>
          {!wallet.opt_in_sun_asa && (
            <button onClick={optInToSUN} disabled={optingIn} className="success"
              style={{ padding: '0.6rem 1.2rem', fontSize: '0.85rem', fontWeight: 'bold', whiteSpace: 'nowrap' }}>
              {optingIn ? '⏳ Opting In...' : '✅ Opt-In Now'}
            </button>
          )}
        </div>
      </div>

      {/* Monthly SUN metrics */}
      <div style={{ marginBottom: '1rem' }}>
        <h4 style={{ marginBottom: '1rem', color: 'var(--primary)' }}>📊 This Month</h4>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: '0.8rem' }}>
          {[
            { label: 'SUN Minted', value: wallet.sun_minted_this_month, color: '#3498db' },
            { label: 'SUN Received', value: wallet.sun_received_this_month, color: '#27ae60' },
            { label: 'SUN Transferred', value: wallet.sun_transferred_this_month, color: '#9b59b6' },
          ].map(({ label, value, color }) => (
            <div key={label} style={{ background: `${color}18`, padding: '1rem', borderRadius: '6px', textAlign: 'center' }}>
              <div style={{ fontSize: '0.8rem', opacity: 0.7, marginBottom: '0.5rem' }}>{label}</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 'bold', color }}>
                {value?.toFixed(2) || '0.00'}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="alert info" style={{ marginTop: '1rem', marginBottom: 0 }}>
        <strong>💾 What is SUN?</strong> 1 SUN = 1 kWh renewable certificate. Created when you generate
        surplus solar, transferred when you buy from the pool. All on Algorand blockchain.
      </div>
    </div>
  )
}
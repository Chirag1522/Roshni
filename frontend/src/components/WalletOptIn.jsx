import { useState } from 'react'
import api from '../services/api'

export default function WalletOptIn({ houseId, onSuccess }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)

  const optInToSUN = async () => {
    try {
      setLoading(true)
      setError(null)
      const res = await api.post(`/wallet/opt-in-sun/${houseId}`)
      setResult(res.data)
      if (onSuccess) onSuccess(res.data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  if (result) {
    return (
      <div className="card" style={{ borderLeft: '4px solid #27ae60' }}>
        <h3>✅ SUN ASA Opt-in Complete!</h3>

        <div style={{
          background: 'rgba(39, 174, 96, 0.1)',
          padding: '1.5rem',
          borderRadius: '8px',
          marginBottom: '1.5rem',
          marginTop: '1rem',
        }}>
          <div style={{ marginBottom: '1rem' }}>
            <div style={{ fontSize: '0.9rem', opacity: 0.8, marginBottom: '0.3rem' }}>
              Transaction ID:
            </div>
            <div style={{
              fontSize: '0.75rem',
              fontFamily: 'monospace',
              wordBreak: 'break-all',
              background: 'rgba(0, 0, 0, 0.3)',
              padding: '0.8rem',
              borderRadius: '4px',
              color: '#27ae60',
            }}>
              {result.opt_in_tx_id}
            </div>
          </div>

          {result.explorer_url && (
            <a
              href={result.explorer_url}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                display: 'inline-block',
                padding: '0.7rem 1.2rem',
                background: '#27ae60',
                color: 'white',
                borderRadius: '4px',
                textDecoration: 'none',
                fontSize: '0.9rem',
                fontWeight: 'bold',
              }}
            >
              🔍 View Transaction on Algoexplorer
            </a>
          )}
        </div>

        <div className="alert info">
          <strong>🎉 Ready for SUN Tokens!</strong> Your wallet is now ready to receive SUN tokens (renewable energy certificates).
          You'll automatically receive them when you generate surplus or buy from the pool.
        </div>

        <button
          onClick={() => setResult(null)}
          style={{
            marginTop: '1rem',
            padding: '0.7rem 1.5rem',
            background: 'var(--primary)',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontWeight: 'bold',
          }}
        >
          ✓ Done
        </button>
      </div>
    )
  }

  return (
    <div className="card" style={{ borderLeft: '4px solid #f39c12' }}>
      <h3>🎯 Opt into SUN Token (ASA)</h3>
      <p style={{ marginBottom: '1rem', opacity: 0.8 }}>
        Your wallet needs to opt into the SUN ASA (Algorand Standard Asset) before it can receive renewable energy tokens.
        This is a one-time transaction on the blockchain.
      </p>

      {error && (
        <div className="alert danger" style={{ marginBottom: '1rem' }}>
          {error}
        </div>
      )}

      <div style={{
        background: 'rgba(243, 156, 18, 0.1)',
        padding: '1rem',
        borderRadius: '8px',
        marginBottom: '1.5rem',
        borderLeft: '3px solid #f39c12',
      }}>
        <strong>What is SUN ASA?</strong>
        <ul style={{ marginTop: '0.5rem', paddingLeft: '1.5rem', fontSize: '0.9rem' }}>
          <li>SUN = Solar Utility Note (renewable energy certificate)</li>
          <li>Asset ID: 756341116 on Algorand testnet</li>
          <li>1 SUN = 1 kWh of certified renewable energy</li>
          <li>Opt-in allows your wallet to hold and trade SUN</li>
        </ul>
      </div>

      <button
        onClick={optInToSUN}
        disabled={loading}
        style={{
          width: '100%',
          padding: '1rem',
          fontSize: '1.1rem',
          fontWeight: 'bold',
          background: loading ? '#95a5a6' : '#f39c12',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: loading ? 'not-allowed' : 'pointer',
        }}
      >
        {loading ? '⏳ Processing Transaction...' : '🚀 Opt Into SUN ASA'}
      </button>
    </div>
  )
}

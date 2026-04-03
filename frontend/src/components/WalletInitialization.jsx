import { useState } from 'react'
import api from '../services/api'

export default function WalletInitialization({ houseId, onSuccess }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)

  const initializeWallet = async () => {
    try {
      setLoading(true)
      setError(null)
      const res = await api.post(`/wallet/initialize/${houseId}`)
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
        <h3>✅ Wallet Created Successfully!</h3>

        <div style={{
          background: 'rgba(39, 174, 96, 0.1)',
          padding: '1.5rem',
          borderRadius: '8px',
          marginBottom: '1.5rem',
          marginTop: '1rem',
        }}>
          <div style={{ marginBottom: '1rem' }}>
            <div style={{ fontSize: '0.9rem', opacity: 0.8, marginBottom: '0.3rem' }}>
              Your Algorand Address:
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
              {result.algorand_address}
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
              🔗 View on Algoexplorer
            </a>
          )}
        </div>

        <div className="alert info">
          <strong>🎯 Next Step:</strong> Your wallet is now created. On your next activity (generating solar or buying from pool),
          your wallet will automatically opt into the SUN ASA token and start receiving renewable energy certificates.
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
    <div className="card" style={{ borderLeft: '4px solid #3498db' }}>
      <h3>🔐 Initialize Blockchain Wallet</h3>
      <p style={{ marginBottom: '1rem', opacity: 0.8 }}>
        Create a custodial wallet on Algorand testnet for your house. This wallet will receive SUN tokens
        (renewable energy certificates) when you generate surplus solar energy or buy from the pool.
      </p>

      {error && (
        <div className="alert danger" style={{ marginBottom: '1rem' }}>
          {error}
        </div>
      )}

      <div style={{
        background: 'rgba(52, 152, 219, 0.1)',
        padding: '1rem',
        borderRadius: '8px',
        marginBottom: '1.5rem',
        borderLeft: '3px solid #3498db',
      }}>
        <strong>What is a Custodial Wallet?</strong>
        <ul style={{ marginTop: '0.5rem', paddingLeft: '1.5rem', fontSize: '0.9rem' }}>
          <li>Your private key is securely managed by Roshni</li>
          <li>You don't need to handle crypto or seed phrases</li>
          <li>All blockchain transactions happen automatically</li>
          <li>Only visible benefit: Your SUN balance increases</li>
        </ul>
      </div>

      <button
        onClick={initializeWallet}
        disabled={loading}
        style={{
          width: '100%',
          padding: '1rem',
          fontSize: '1.1rem',
          fontWeight: 'bold',
          background: loading ? '#95a5a6' : '#3498db',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: loading ? 'not-allowed' : 'pointer',
        }}
      >
        {loading ? '⏳ Creating Wallet...' : '✨ Create Wallet'}
      </button>
    </div>
  )
}

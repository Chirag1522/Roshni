import { useState, useEffect, useCallback } from 'react'
import api from '../services/api'

function shortAddr(addr) {
  if (!addr) return '-'
  return `${addr.slice(0, 6)}...${addr.slice(-4)}`
}

function fmtDateTime(unixTs) {
  if (!unixTs) return '-'
  return new Date(unixTs * 1000).toLocaleString('en-IN', {
    day: 'numeric', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

function txMeta(txn) {
  if (txn.subtype === 'pool') {
    return {
      label: 'SOLAR',
      title: 'Solar from Pool',
      subtitle: `${txn.amount_kwh?.toFixed(2)} kWh renewable  |  SUN +${txn.amount_sun?.toFixed(0)}`,
      amount: `+${txn.amount_sun?.toFixed(0)} SUN`,
      amountColor: '#2ecc71',
      labelBg: '#1a3d28',
      labelColor: '#2ecc71',
    }
  }
  if (txn.subtype === 'grid') {
    return {
      label: 'GRID',
      title: 'Grid Backup',
      subtitle: `${txn.amount_kwh?.toFixed(2)} kWh from DISCOM grid`,
      amount: `${txn.amount_kwh?.toFixed(2)} kWh`,
      amountColor: '#e67e22',
      labelBg: '#3d2d1a',
      labelColor: '#e67e22',
    }
  }
  if (txn.subtype === 'bill_hash') {
    return {
      label: 'BILL',
      title: 'Bill on Blockchain',
      subtitle: txn.month_year ? `Month: ${txn.month_year}` : 'Monthly bill recorded',
      amount: txn.net_payable != null ? `Rs.${Math.abs(txn.net_payable).toFixed(0)}` : 'Verified',
      amountColor: '#3498db',
      labelBg: '#1a2d3d',
      labelColor: '#3498db',
    }
  }
  return {
    label: 'TXN',
    title: txn.title || 'Transaction',
    subtitle: txn.subtitle || '',
    amount: `${txn.amount_kwh?.toFixed(2)} kWh`,
    amountColor: '#9b59b6',
    labelBg: '#2d1a3d',
    labelColor: '#9b59b6',
  }
}

function groupByDate(txns) {
  const buckets = {}
  txns.forEach(t => {
    const label = t.timestamp
      ? new Date(t.timestamp * 1000).toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'short', year: 'numeric' })
      : 'Pending'
    if (!buckets[label]) buckets[label] = []
    buckets[label].push(t)
  })
  return Object.entries(buckets)
}

function Receipt({ txn, address, onClose }) {
  const meta = txMeta(txn)
  const hasChainTx = Boolean(txn.txn_id)

  const rows = [
    { label: 'Status', value: txn.status ? txn.status.toUpperCase() : '-' },
    { label: 'Type', value: txn.title },
    { label: 'Date & Time', value: fmtDateTime(txn.timestamp) },
    txn.amount_kwh != null && { label: 'Energy', value: `${txn.amount_kwh?.toFixed(4)} kWh` },
    txn.amount_sun != null && txn.amount_sun > 0 && { label: 'SUN Tokens', value: `${txn.amount_sun?.toFixed(0)} SUN` },
    txn.net_payable != null && { label: 'Net Amount', value: `Rs.${txn.net_payable?.toFixed(2)}` },
    txn.month_year && { label: 'Bill Month', value: txn.month_year },
    txn.note && { label: 'Note', value: txn.note, mono: true },
    hasChainTx && { label: 'Blockchain TX', value: txn.txn_id, mono: true },
    address && { label: 'Wallet', value: address, mono: true, short: true },
  ].filter(Boolean)

  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0, zIndex: 1000,
        background: 'rgba(0,0,0,0.75)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: '1rem',
      }}
    >
      <div
        onClick={e => e.stopPropagation()}
        style={{
          width: '100%', maxWidth: 420,
          background: '#16213e',
          borderRadius: 16,
          overflow: 'hidden',
          boxShadow: '0 24px 64px rgba(0,0,0,0.65)',
        }}
      >
        <div style={{
          padding: '1.5rem',
          borderBottom: '1px solid rgba(255,255,255,0.08)',
          textAlign: 'center',
        }}>
          <div style={{
            display: 'inline-block',
            padding: '0.3rem 0.85rem',
            borderRadius: 6,
            background: meta.labelBg,
            color: meta.labelColor,
            fontWeight: 700,
            fontSize: '0.78rem',
            letterSpacing: '0.1em',
            marginBottom: '0.75rem',
          }}>
            {meta.label}
          </div>
          <div style={{ fontWeight: 700, fontSize: '1.05rem', color: '#fff', marginBottom: '0.5rem' }}>
            {meta.title}
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: meta.amountColor }}>
            {meta.amount}
          </div>
          <div style={{ marginTop: '0.4rem', fontSize: '0.82rem', color: 'rgba(255,255,255,0.4)' }}>
            {fmtDateTime(txn.timestamp)}
          </div>
          <div style={{
            display: 'inline-block', marginTop: '0.6rem',
            padding: '0.2rem 0.7rem', borderRadius: 20,
            background: 'rgba(255,255,255,0.07)',
            fontSize: '0.72rem', fontWeight: 600,
            color: 'rgba(255,255,255,0.55)',
          }}>
            {txn.status?.toUpperCase() || 'PENDING'}
          </div>
        </div>

        <div style={{ padding: '0.5rem 1.25rem', maxHeight: '40vh', overflowY: 'auto' }}>
          {rows.map(({ label, value, mono, short }) => (
            <div key={label} style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start',
              padding: '0.55rem 0',
              borderBottom: '1px solid rgba(255,255,255,0.05)',
              gap: '0.75rem',
            }}>
              <span style={{ fontSize: '0.78rem', color: 'rgba(255,255,255,0.38)', minWidth: 95, flexShrink: 0 }}>
                {label}
              </span>
              <span style={{
                fontSize: '0.82rem',
                fontFamily: mono ? 'monospace' : 'inherit',
                textAlign: 'right',
                wordBreak: 'break-all',
                color: 'rgba(255,255,255,0.85)',
              }}>
                {short ? shortAddr(String(value)) : String(value ?? '-')}
              </span>
            </div>
          ))}
        </div>

        <div style={{ padding: '1rem 1.25rem 1.25rem', display: 'flex', gap: '0.75rem' }}>
          {hasChainTx ? (
            <a
              href={txn.explorer_url || `https://testnet.explorer.perawallet.app/tx/${txn.txn_id}`}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                flex: 1, textAlign: 'center', padding: '0.7rem',
                borderRadius: 10, fontSize: '0.84rem', fontWeight: 600,
                background: 'rgba(52,152,219,0.15)', color: '#3498db',
                border: '1px solid rgba(52,152,219,0.3)',
                textDecoration: 'none',
              }}
            >
              View on Explorer
            </a>
          ) : (
            <a
              href={`https://testnet.explorer.perawallet.app/address/${address}`}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                flex: 1, textAlign: 'center', padding: '0.7rem',
                borderRadius: 10, fontSize: '0.84rem', fontWeight: 600,
                background: 'rgba(52,152,219,0.15)', color: '#3498db',
                border: '1px solid rgba(52,152,219,0.3)',
                textDecoration: 'none',
              }}
            >
              View Wallet
            </a>
          )}
          <button
            onClick={onClose}
            style={{
              flex: 1, padding: '0.7rem',
              borderRadius: 10, fontSize: '0.84rem', fontWeight: 600,
              background: 'rgba(255,255,255,0.06)', color: 'rgba(255,255,255,0.65)',
              border: '1px solid rgba(255,255,255,0.1)',
              cursor: 'pointer',
            }}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}

function TxItem({ txn, onClick }) {
  const meta = txMeta(txn)
  const [hovered, setHovered] = useState(false)

  return (
    <div
      onClick={onClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        display: 'flex', alignItems: 'center', gap: '0.85rem',
        padding: '0.9rem 1rem',
        cursor: 'pointer',
        background: hovered ? 'rgba(255,255,255,0.03)' : 'transparent',
        transition: 'background 0.12s',
      }}
    >
      <div style={{
        minWidth: 52, height: 36, borderRadius: 8, flexShrink: 0,
        background: meta.labelBg,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        <span style={{ fontSize: '0.7rem', fontWeight: 800, color: meta.labelColor, letterSpacing: '0.06em' }}>
          {meta.label}
        </span>
      </div>

      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontWeight: 600, fontSize: '0.88rem', color: 'rgba(255,255,255,0.9)' }}>
          {meta.title}
        </div>
        <div style={{
          fontSize: '0.75rem', color: 'rgba(255,255,255,0.38)',
          marginTop: 3, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
        }}>
          {meta.subtitle}
        </div>
      </div>

      <div style={{ textAlign: 'right', flexShrink: 0 }}>
        <div style={{ fontWeight: 700, fontSize: '0.9rem', color: meta.amountColor }}>
          {meta.amount}
        </div>
        <div style={{ fontSize: '0.7rem', color: 'rgba(255,255,255,0.3)', marginTop: 3 }}>
          {fmtDateTime(txn.timestamp)}
        </div>
      </div>
    </div>
  )
}

export default function BlockchainExplorer({ houseId }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selected, setSelected] = useState(null)

  const load = useCallback(async () => {
    if (!houseId) return
    setLoading(true)
    setError(null)
    try {
      const res = await api.get(`/blockchain/house-history/${houseId}?limit=200`)
      setData(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to load history')
    } finally {
      setLoading(false)
    }
  }, [houseId])

  useEffect(() => { load() }, [load])

  const txns = data?.transactions ?? []
  const address = data?.algorand_address ?? null
  const summary = data?.summary ?? {}
  const groups = groupByDate(txns)

  return (
    <div style={{ maxWidth: 520, margin: '0 auto', padding: '0 0 3rem' }}>

      <div style={{ marginBottom: '1.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.5rem' }}>
          <h2 style={{ fontWeight: 700, fontSize: '1.2rem', margin: 0, color: '#fff' }}>
            Transaction History
          </h2>
          {!loading && (
            <button
              onClick={load}
              style={{
                padding: '0.4rem 0.9rem', borderRadius: 8, fontSize: '0.78rem',
                background: 'rgba(52,152,219,0.15)', color: '#3498db',
                border: '1px solid rgba(52,152,219,0.3)', cursor: 'pointer',
              }}
            >
              Refresh
            </button>
          )}
        </div>
        {address && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.4rem' }}>
            <span style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.35)', fontFamily: 'monospace' }}>
              {shortAddr(address)}
            </span>
            <a
              href={`https://testnet.explorer.perawallet.app/address/${address}`}
              target="_blank"
              rel="noopener noreferrer"
              style={{ fontSize: '0.72rem', color: '#3498db', textDecoration: 'none' }}
            >
              View on Explorer
            </a>
          </div>
        )}
      </div>

      {txns.length > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: '0.6rem', marginBottom: '1.25rem' }}>
          {[
            { label: 'Transactions', value: txns.length, color: '#8e44ad' },
            { label: 'Pool kWh', value: `${summary.total_pool_kwh ?? 0}`, color: '#2ecc71' },
            { label: 'SUN Earned', value: `${summary.total_sun_earned ?? 0}`, color: '#f1c40f' },
          ].map(({ label, value, color }) => (
            <div key={label} style={{
              background: '#1a1a2e', borderRadius: 12, padding: '0.85rem 0.6rem',
              textAlign: 'center', border: `1px solid ${color}22`,
            }}>
              <div style={{ fontWeight: 700, fontSize: '1.1rem', color }}>{value}</div>
              <div style={{ fontSize: '0.68rem', color: 'rgba(255,255,255,0.38)', marginTop: '0.2rem' }}>{label}</div>
            </div>
          ))}
        </div>
      )}

      {loading && (
        <div style={{ textAlign: 'center', padding: '3rem 0' }}>
          <div className="spinner" />
          <p style={{ marginTop: '1rem', color: 'rgba(255,255,255,0.38)', fontSize: '0.88rem' }}>
            Loading transactions...
          </p>
        </div>
      )}

      {!loading && error && (
        <div style={{
          background: 'rgba(231,76,60,0.1)', border: '1px solid rgba(231,76,60,0.28)',
          borderRadius: 14, padding: '1.5rem', textAlign: 'center',
        }}>
          <div style={{ color: '#e74c3c', fontWeight: 600, marginBottom: '0.4rem' }}>Could not load history</div>
          <div style={{ color: 'rgba(255,255,255,0.45)', fontSize: '0.82rem', marginBottom: '1rem' }}>{error}</div>
          <button onClick={load} style={{
            padding: '0.5rem 1.25rem', borderRadius: 8, fontSize: '0.84rem',
            background: 'rgba(231,76,60,0.18)', color: '#e74c3c',
            border: '1px solid rgba(231,76,60,0.3)', cursor: 'pointer',
          }}>
            Retry
          </button>
        </div>
      )}

      {!loading && !error && txns.length === 0 && (
        <div style={{
          background: '#1a1a2e', borderRadius: 14, padding: '3rem 1.5rem',
          textAlign: 'center', border: '1px solid rgba(255,255,255,0.06)',
        }}>
          <div style={{ fontWeight: 600, marginBottom: '0.5rem', color: '#fff' }}>No transactions yet</div>
          <div style={{ color: 'rgba(255,255,255,0.38)', fontSize: '0.84rem' }}>
            Submit a demand from the Buyer Dashboard to start trading solar energy.
          </div>
        </div>
      )}

      {!loading && !error && groups.map(([dateLabel, items]) => (
        <div key={dateLabel} style={{ marginBottom: '0.8rem' }}>
          <div style={{
            fontSize: '0.67rem', fontWeight: 700, letterSpacing: '0.09em',
            color: 'rgba(255,255,255,0.28)', textTransform: 'uppercase',
            padding: '0 0.2rem 0.4rem',
          }}>
            {dateLabel}
          </div>
          <div style={{
            background: '#1a1a2e', borderRadius: 14,
            border: '1px solid rgba(255,255,255,0.07)',
            overflow: 'hidden',
          }}>
            {items.map((txn, idx) => (
              <div key={txn.id}>
                {idx > 0 && (
                  <div style={{ height: 1, background: 'rgba(255,255,255,0.05)', margin: '0 1rem' }} />
                )}
                <TxItem txn={txn} onClick={() => setSelected(txn)} />
              </div>
            ))}
          </div>
        </div>
      ))}

      {selected && (
        <Receipt
          txn={selected}
          address={address}
          onClose={() => setSelected(null)}
        />
      )}
    </div>
  )
}
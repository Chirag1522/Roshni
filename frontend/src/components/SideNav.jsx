import { Link } from 'react-router-dom'

export default function SideNav({ isOpen, onClose }) {
  return (
    <>
      {isOpen && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0, 0, 0, 0.5)',
            zIndex: 99,
          }}
          onClick={onClose}
        />
      )}
      <nav className={`sidenav ${isOpen ? 'open' : ''}`}>
        <h3 style={{ marginBottom: '1.5rem' }}>Navigation</h3>
        <ul>
          <li><Link to="/seller" onClick={onClose}>🔆 Seller Dashboard</Link></li>
          <li><Link to="/buyer" onClick={onClose}>🔌 Buyer Dashboard</Link></li>
          <li><Link to="/billing" onClick={onClose}>💰 Monthly Bills</Link></li>
          <li><Link to="/blockchain" onClick={onClose}>⛓️ Blockchain</Link></li>
          <li><Link to="/admin" onClick={onClose}>⚙️ Admin Panel</Link></li>
        </ul>
        
        <hr style={{ margin: '2rem 0', opacity: 0.2 }} />
        
        <h4 style={{ marginBottom: '1rem', opacity: 0.7 }}>Resources</h4>
        <ul>
          
          <li><a href="https://github.com/Khushi-Chaudhary04/roshni" target="_blank" rel="noopener noreferrer">📖 GitHub</a></li>
        </ul>

        <hr style={{ margin: '2rem 0', opacity: 0.2 }} />

        <p style={{ fontSize: '0.8rem', opacity: 0.6 }}>
          ROSHNI v1.0<br/>
          AI-powered Solar Energy Pool
        </p>
      </nav>
    </>
  )
}

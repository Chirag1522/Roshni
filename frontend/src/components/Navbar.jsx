import { Link } from 'react-router-dom'
import { useState, useEffect } from 'react'

export default function Navbar({ darkMode, setDarkMode, onMenuClick }) {
  const [voiceEnabled, setVoiceEnabled] = useState(localStorage.getItem('voiceEnabled') !== 'false')

  const handleVoiceToggle = () => {
    const newValue = !voiceEnabled
    setVoiceEnabled(newValue)
    localStorage.setItem('voiceEnabled', newValue)
  }

  return (
    <nav className="navbar">
      <div className="container" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <button
            onClick={onMenuClick}
            style={{
              background: 'none',
              border: 'none',
              color: 'white',
              fontSize: '1.5rem',
              cursor: 'pointer'
            }}
          >
            ☰
          </button>
          <h1 style={{ margin: 0, fontSize: '1.8rem' }}>🌞 ROSHNI</h1>
        </div>

        <ul className="nav-links" style={{ margin: 0 }}>
          <li><Link to="/seller">Seller</Link></li>
          <li><Link to="/buyer">Buyer</Link></li>
          <li><Link to="/billing">Bills</Link></li>
          <li><Link to="/blockchain">Blockchain</Link></li>
          <li><Link to="/admin">Admin</Link></li>
        </ul>

        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <button
            className="theme-toggle"
            onClick={() => setDarkMode(!darkMode)}
            title="Toggle dark mode"
          >
            {darkMode ? '☀️' : '🌙'}
          </button>
          
        </div>
      </div>
    </nav>
  )
}

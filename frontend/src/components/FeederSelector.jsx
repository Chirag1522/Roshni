import { useState } from 'react'

const FEEDERS = ['FDR_12', 'FDR_15', 'FDR_NORTH_20', 'FDR_EAST_08']

const HOUSES_BY_FEEDER = {
  'FDR_12': [
    'HOUSE_FDR12_001',
    'HOUSE_FDR12_002',
    'HOUSE_FDR12_003',
  ],
  'FDR_15': [
    'HOUSE_FDR15_001',
    'HOUSE_FDR15_002',
  ],
  'FDR_NORTH_20': [
    'HOUSE_FDRNORTH20_001',
  ],
  'FDR_EAST_08': [
    'HOUSE_FDREAST08_001',
    'HOUSE_FDREAST08_002',
  ],
}

export default function FeederSelector({
  selectedFeeder,
  setSelectedFeeder,
  selectedHouseId,
  setSelectedHouseId,
}) {
  const [showDropdown, setShowDropdown] = useState(false)

  const availableHouses = HOUSES_BY_FEEDER[selectedFeeder] || []

  const handleFeederChange = (newFeeder) => {
    setSelectedFeeder(newFeeder)
    const houses = HOUSES_BY_FEEDER[newFeeder]
    if (houses && !houses.includes(selectedHouseId)) {
      setSelectedHouseId(houses[0])
    }
    setShowDropdown(false)
  }

  return (
    <div style={{
      background: 'rgba(255, 140, 66, 0.1)',
      padding: '1rem',
      borderRadius: '8px',
      marginBottom: '1rem',
    }}>
      <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
        <div>
          <label style={{ display: 'block', marginBottom: '0.3rem', opacity: 0.8, fontSize: '0.85rem' }}>
            Feeder
          </label>
          <div style={{ position: 'relative' }}>
            <button
              onClick={() => setShowDropdown(!showDropdown)}
              style={{
                width: '180px',
                background: 'var(--primary)',
                color: 'white',
              }}
            >
              {selectedFeeder} ▼
            </button>
            {showDropdown && (
              <div style={{
                position: 'absolute',
                top: '40px',
                left: 0,
                background: 'var(--secondary)',
                border: '2px solid var(--primary)',
                borderRadius: '8px',
                width: '180px',
                zIndex: 10,
              }}>
                {FEEDERS.map(feeder => (
                  <div
                    key={feeder}
                    onClick={() => handleFeederChange(feeder)}
                    style={{
                      padding: '0.75rem',
                      cursor: 'pointer',
                      borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
                      background: selectedFeeder === feeder ? 'rgba(255, 140, 66, 0.2)' : 'transparent',
                    }}
                  >
                    {feeder}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div>
          <label style={{ display: 'block', marginBottom: '0.3rem', opacity: 0.8, fontSize: '0.85rem' }}>
            House ID
          </label>
          <select
            value={selectedHouseId}
            onChange={(e) => setSelectedHouseId(e.target.value)}
            style={{ width: '220px' }}
          >
            {availableHouses.map(house => (
              <option key={house} value={house}>{house}</option>
            ))}
          </select>
        </div>

        <div style={{ marginTop: '1.5rem' }}>
          <span style={{
            background: 'rgba(39, 174, 96, 0.2)',
            padding: '0.5rem 1rem',
            borderRadius: '4px',
            fontSize: '0.9rem',
          }}>
            ✓ Connected
          </span>
        </div>
      </div>
    </div>
  )
}
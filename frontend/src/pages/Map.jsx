import { useState } from 'react'
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import './Map.css'

const regions = [
  { id: 'UKR', name: 'Ukraine', lat: 49.0, lng: 32.0, risk: 82 },
  { id: 'RUS', name: 'Russia', lat: 55.0, lng: 60.0, risk: 91 },
  { id: 'CHN', name: 'China', lat: 35.0, lng: 105.0, risk: 55 },
  { id: 'IRN', name: 'Iran', lat: 32.0, lng: 53.0, risk: 68 },
  { id: 'PRK', name: 'North Korea', lat: 40.0, lng: 127.0, risk: 72 },
]

function Map() {
  const [selectedRegion, setSelectedRegion] = useState(null)

  const getRiskColor = (risk) => {
    if (risk >= 80) return '#e94560'
    if (risk >= 60) return '#ff9800'
    return '#4caf50'
  }

  return (
    <div className="map-page">
      <header className="page-header">
        <h1>Geospatial View</h1>
        <p className="subtitle">Interactive regional risk map</p>
      </header>

      <div className="map-container">
        <MapContainer center={[45, 30]} zoom={3} className="leaflet-map">
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {regions.map(region => (
            <Marker 
              key={region.id} 
              position={[region.lat, region.lng]}
              eventHandlers={{
                click: () => setSelectedRegion(region),
              }}
            >
              <Popup>
                <div className="popup-content">
                  <h3>{region.name}</h3>
                  <p>Risk: {region.risk}%</p>
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>

        <div className="map-legend">
          <h3>Risk Levels</h3>
          <div className="legend-item">
            <span className="legend-color high"></span>
            <span>High (80%+)</span>
          </div>
          <div className="legend-item">
            <span className="legend-color medium"></span>
            <span>Medium (60-79%)</span>
          </div>
          <div className="legend-item">
            <span className="legend-color low"></span>
            <span>Low (&lt;60%)</span>
          </div>
        </div>
      </div>

      {selectedRegion && (
        <div className="region-details">
          <h2>{selectedRegion.name}</h2>
          <div className="detail-grid">
            <div className="detail-item">
              <span className="label">Risk Level</span>
              <span className="value" style={{ color: getRiskColor(selectedRegion.risk) }}>
                {selectedRegion.risk}%
              </span>
            </div>
            <div className="detail-item">
              <span className="label">Posture</span>
              <span className="value">Escalating</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Map

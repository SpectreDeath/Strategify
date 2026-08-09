import { useState, useEffect, useCallback, useRef } from 'react'
import { MapContainer, TileLayer, GeoJSON, CircleMarker, Popup, useMap } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import { mapApi } from '../api/client'
import './Map.css'

// --- Posture → colour mapping (mirrors the backend) ---
const POSTURE_COLORS = {
  Invade:      '#e94560',
  Escalate:    '#ff7043',
  Deploy:      '#ffa726',
  Observe:     '#66bb6a',
  Deescalate:  '#29b6f6',
  Withdraw:    '#ab47bc',
}

const POSTURE_INFO = {
  Invade:     { label: 'Invade',      risk: 'Critical' },
  Escalate:   { label: 'Escalate',    risk: 'High' },
  Deploy:     { label: 'Deploy',      risk: 'Elevated' },
  Observe:    { label: 'Observe',     risk: 'Low' },
  Deescalate: { label: 'De-escalate', risk: 'Minimal' },
  Withdraw:   { label: 'Withdraw',    risk: 'Receding' },
}

function getPostureColor(posture) {
  return POSTURE_COLORS[posture] || '#888'
}

// Fly-to control when the live GeoJSON data updates map bounds
function FitBoundsControl({ geoData }) {
  const map = useMap()
  useEffect(() => {
    if (!geoData || geoData.features.length === 0) return
    try {
      const L = window.L
      if (L) {
        // Collect all feature centroids to fit bounds
        const latlngs = geoData.features
          .filter(f => f.properties?.centroid_lat)
          .map(f => [f.properties.centroid_lat, f.properties.centroid_lng])
        if (latlngs.length > 0) map.fitBounds(latlngs, { padding: [40, 40] })
      }
    } catch { /* ignore */ }
  }, [geoData, map])
  return null
}

export default function Map() {
  const [geoData, setGeoData] = useState(null)
  const [selectedRegion, setSelectedRegion] = useState(null)
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [step, setStep] = useState(0)
  const [error, setError] = useState(null)
  const intervalRef = useRef(null)

  const fetchGeoJSON = useCallback(async () => {
    try {
      const res = await mapApi.getGeoJSON()
      setGeoData(res.data)
      setStep(res.data.step || 0)
      setError(null)
    } catch (err) {
      const detail = err.response?.data?.detail || err.message
      setError(detail)
    }
  }, [])

  // Initial fetch
  useEffect(() => {
    fetchGeoJSON()
  }, [fetchGeoJSON])

  // Auto-refresh every 2s when toggled on
  useEffect(() => {
    if (autoRefresh) {
      intervalRef.current = setInterval(fetchGeoJSON, 2000)
    } else {
      clearInterval(intervalRef.current)
    }
    return () => clearInterval(intervalRef.current)
  }, [autoRefresh, fetchGeoJSON])

  // GeoJSON style function
  const styleFeature = (feature) => {
    const posture = feature.properties?.posture || 'Observe'
    const color = getPostureColor(posture)
    const tension = feature.properties?.tension || 0
    return {
      fillColor: color,
      color: color,
      weight: 2,
      opacity: 1,
      fillOpacity: 0.35 + (tension / 100) * 0.45,
    }
  }

  // Per-feature event handlers
  const onEachFeature = (feature, layer) => {
    const props = feature.properties || {}
    const color = getPostureColor(props.posture)

    layer.on({
      click: () => setSelectedRegion(props),
      mouseover: (e) => {
        e.target.setStyle({ weight: 3, fillOpacity: 0.75 })
      },
      mouseout: (e) => {
        e.target.setStyle(styleFeature(feature))
      },
    })

    layer.bindTooltip(
      `<div class="map-tooltip">
        <strong>${props.region_id}</strong>
        <span style="color:${color}">● ${props.posture}</span>
        <span>${props.tension?.toFixed(1)}% tension</span>
      </div>`,
      { sticky: true, direction: 'top' }
    )
  }

  const hasLiveData = geoData && geoData.features && geoData.features.some(f => f.geometry)
  const hasPoints = geoData && geoData.features && geoData.features.some(f => f.properties)

  return (
    <div className="map-page">
      <header className="page-header">
        <h1>Geospatial View</h1>
        <p className="subtitle">
          Live regional posture map
          {geoData && ` — Step ${step} · ${geoData.features?.length || 0} active regions`}
        </p>
      </header>

      <div className="map-controls">
        <button
          className={`refresh-toggle ${autoRefresh ? 'active' : ''}`}
          onClick={() => setAutoRefresh(v => !v)}
        >
          {autoRefresh ? '⏸ Pause Live' : '▶ Resume Live'}
        </button>
        <button className="refresh-btn" onClick={fetchGeoJSON}>🔄 Refresh Now</button>
        {error && (
          <div className="map-error">
            ⚠ {error}
            {error.includes('Model not initialized') && ' — start a simulation first'}
          </div>
        )}
      </div>

      <div className="map-layout">
        <div className="map-wrapper">
          <MapContainer
            center={[40, 30]}
            zoom={3}
            className="leaflet-map"
            style={{ height: '520px', width: '100%' }}
          >
            <TileLayer
              attribution='© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />

            {/* GeoJSON polygon layer when agents have shapes */}
            {hasLiveData && (
              <GeoJSON
                key={step}
                data={geoData}
                style={styleFeature}
                onEachFeature={onEachFeature}
              />
            )}

            {/* Circle marker fallback for agents without geometry */}
            {!hasLiveData && hasPoints && geoData.features.map((f, i) => {
              const props = f.properties || {}
              // Use rough centroid from region_id lookup
              const CENTROIDS = {
                UKR: [49.0, 32.0], RUS: [55.0, 60.0], BLR: [53.5, 28.0],
                POL: [52.0, 20.0], CHN: [35.0, 105.0], IRN: [32.0, 53.0],
                PRK: [40.0, 127.0], Alpha: [50.0, 30.0], Bravo: [45.0, 40.0],
              }
              const pos = CENTROIDS[props.region_id] || [20 + i * 15, 30 + i * 10]
              const color = getPostureColor(props.posture)
              return (
                <CircleMarker
                  key={props.region_id || i}
                  center={pos}
                  radius={12 + (props.tension || 0) / 10}
                  pathOptions={{ color, fillColor: color, fillOpacity: 0.7 }}
                  eventHandlers={{ click: () => setSelectedRegion(props) }}
                >
                  <Popup>
                    <div className="popup-content">
                      <strong>{props.region_id}</strong>
                      <p style={{ color }}>● {props.posture}</p>
                      <p>Tension: {props.tension?.toFixed(1)}%</p>
                      <p>Military: {(props.military * 100).toFixed(0)}%</p>
                      <p>Economic: {(props.economic * 100).toFixed(0)}%</p>
                    </div>
                  </Popup>
                </CircleMarker>
              )
            })}
          </MapContainer>
        </div>

        <div className="map-sidebar">
          <div className="map-legend">
            <h3>Posture Legend</h3>
            {Object.entries(POSTURE_INFO).map(([p, info]) => (
              <div key={p} className="legend-item">
                <span className="legend-dot" style={{ background: POSTURE_COLORS[p] }} />
                <span className="legend-label">{info.label}</span>
                <span className="legend-risk">{info.risk}</span>
              </div>
            ))}
          </div>

          {selectedRegion && (
            <div className="region-details">
              <div
                className="region-header"
                style={{ borderLeft: `4px solid ${getPostureColor(selectedRegion.posture)}` }}
              >
                <h2>{selectedRegion.region_id}</h2>
                <span className="posture-tag" style={{ background: getPostureColor(selectedRegion.posture) }}>
                  {selectedRegion.posture}
                </span>
              </div>
              <div className="detail-grid">
                <div className="detail-item">
                  <span className="label">Tension</span>
                  <span className="value" style={{ color: getPostureColor(selectedRegion.posture) }}>
                    {selectedRegion.tension?.toFixed(1)}%
                  </span>
                </div>
                <div className="detail-item">
                  <span className="label">Stability</span>
                  <span className="value">{(selectedRegion.stability * 100).toFixed(0)}%</span>
                </div>
                <div className="detail-item">
                  <span className="label">Military</span>
                  <span className="value">{(selectedRegion.military * 100).toFixed(0)}%</span>
                </div>
                <div className="detail-item">
                  <span className="label">Economic</span>
                  <span className="value">{(selectedRegion.economic * 100).toFixed(0)}%</span>
                </div>
              </div>
            </div>
          )}

          {!selectedRegion && geoData && (
            <div className="region-hint">
              <p>Click a region on the map to inspect its live state.</p>
            </div>
          )}

          {!geoData && !error && (
            <div className="region-hint">
              <p>Start a simulation from the <strong>Simulation</strong> tab to see live data.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

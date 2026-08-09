import { useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Legend } from 'recharts'
import { economicsApi } from '../api/client'
import './Economics.css'

const COMMODITY_COLORS = {
  oil: '#ffa726',
  semiconductors: '#29b6f6',
  grain: '#66bb6a',
  default: '#533483',
}

function getCommodityColor(name) {
  const key = (name || '').toLowerCase()
  for (const [k, v] of Object.entries(COMMODITY_COLORS)) {
    if (key.includes(k)) return v
  }
  return COMMODITY_COLORS.default
}

function getRiskColor(score) {
  if (score >= 0.75) return '#e94560'
  if (score >= 0.5) return '#ffa726'
  if (score >= 0.25) return '#ffd740'
  return '#66bb6a'
}

export default function Economics() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetchChokepoints = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await economicsApi.getChokepoints()
      setData(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  const chokepoints = data ? Object.entries(data.chokepoints || {}) : []
  const barData = chokepoints.map(([node, cp]) => ({
    node,
    risk: parseFloat(((cp.bottleneck_score || cp.risk_score || 0) * 100).toFixed(1)),
    utilization: parseFloat(((cp.utilization || 0) * 100).toFixed(1)),
  }))

  const radarData = chokepoints.map(([node, cp]) => ({
    node,
    bottleneck: parseFloat(((cp.bottleneck_score || 0) * 100).toFixed(1)),
    throughput: parseFloat(((cp.throughput_ratio || (cp.flow / (cp.capacity || 1)) || 0) * 100).toFixed(1)),
  }))

  return (
    <div className="economics-page">
      <header className="page-header">
        <h1>Supply Chain Economics</h1>
        <p className="subtitle">Strategic trade network analysis — commodity flows, chokepoints, and vulnerability</p>
      </header>

      <div className="econ-controls">
        <button className="btn-analyze" onClick={fetchChokepoints} disabled={loading}>
          {loading ? '⏳ Analyzing...' : '🔍 Analyze Supply Network'}
        </button>
        {error && <div className="econ-error">⚠️ {error}</div>}
      </div>

      {data && (
        <>
          <div className="chokepoint-cards">
            {chokepoints.map(([node, cp]) => {
              const riskScore = cp.bottleneck_score || cp.risk_score || 0
              return (
                <div key={node} className="chokepoint-card" style={{ borderTop: `4px solid ${getRiskColor(riskScore)}` }}>
                  <div className="cp-header">
                    <span className="cp-name">{node}</span>
                    <span className="cp-risk" style={{ color: getRiskColor(riskScore) }}>
                      {(riskScore * 100).toFixed(0)}% risk
                    </span>
                  </div>
                  <div className="cp-commodity">
                    <span className="commodity-dot" style={{ background: getCommodityColor(cp.commodity) }} />
                    {cp.commodity || 'mixed'}
                  </div>
                  <div className="cp-stats">
                    <div className="cp-stat">
                      <span>Flow</span>
                      <strong>{cp.flow || '—'}</strong>
                    </div>
                    <div className="cp-stat">
                      <span>Capacity</span>
                      <strong>{cp.capacity || '—'}</strong>
                    </div>
                    <div className="cp-stat">
                      <span>Routes</span>
                      <strong>{cp.route_count || '—'}</strong>
                    </div>
                  </div>
                  <div className="util-bar">
                    <div
                      className="util-fill"
                      style={{
                        width: `${Math.min((cp.utilization || (cp.flow / (cp.capacity || 1) || 0)) * 100, 100)}%`,
                        background: getRiskColor(riskScore),
                      }}
                    />
                  </div>
                </div>
              )
            })}
          </div>

          <div className="econ-charts">
            <div className="chart-box">
              <h2>Bottleneck Risk by Node</h2>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={barData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                  <XAxis dataKey="node" stroke="#888" />
                  <YAxis stroke="#888" unit="%" />
                  <Tooltip contentStyle={{ background: '#1a1a2e', border: 'none' }} formatter={v => [`${v}%`]} />
                  <Legend />
                  <Bar dataKey="risk" fill="#e94560" radius={[4, 4, 0, 0]} name="Risk Score" />
                  <Bar dataKey="utilization" fill="#ffa726" radius={[4, 4, 0, 0]} name="Utilization" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="chart-box">
              <h2>Network Vulnerability Radar</h2>
              <ResponsiveContainer width="100%" height={280}>
                <RadarChart data={radarData}>
                  <PolarGrid stroke="#333" />
                  <PolarAngleAxis dataKey="node" stroke="#888" />
                  <PolarRadiusAxis stroke="#555" domain={[0, 100]} />
                  <Radar name="Bottleneck" dataKey="bottleneck" stroke="#e94560" fill="#e94560" fillOpacity={0.3} />
                  <Radar name="Throughput" dataKey="throughput" stroke="#29b6f6" fill="#29b6f6" fillOpacity={0.3} />
                  <Tooltip contentStyle={{ background: '#1a1a2e', border: 'none' }} />
                  <Legend />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {data.prolog_facts && (
            <div className="prolog-facts">
              <h2>Prolog Knowledge Base Export</h2>
              <pre className="prolog-code">{data.prolog_facts}</pre>
            </div>
          )}
        </>
      )}

      {!data && !loading && (
        <div className="econ-placeholder">
          <div className="placeholder-icon">📦</div>
          <p>Click <strong>Analyze Supply Network</strong> to compute chokepoints, commodity flows, and strategic vulnerability across the trade graph.</p>
          <ul>
            <li>🛢 Oil — Hormuz Strait dependency</li>
            <li>💡 Semiconductors — Malacca / Bosphorus routes</li>
            <li>🌾 Grain — Black Sea export corridors</li>
          </ul>
        </div>
      )}
    </div>
  )
}

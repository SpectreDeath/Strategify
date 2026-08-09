import { useState } from 'react'
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ScatterChart, Scatter, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis } from 'recharts'
import { analysisApi } from '../api/client'
import './Analysis.css'

const ANALYSIS_TYPES = [
  {
    id: 'var',
    name: 'VAR Model',
    icon: '📈',
    description: 'Vector AutoRegression — detect lag structure and forecast escalation across regions',
  },
  {
    id: 'granger',
    name: 'Granger Causality',
    icon: '🔗',
    description: 'Test which regions\'s escalation statistically predicts another\'s posture shift',
  },
  {
    id: 'community',
    name: 'Alliance Communities',
    icon: '🌐',
    description: 'Louvain community detection on the diplomacy graph — find emergent coalition blocs',
  },
  {
    id: 'risk',
    name: 'Strategic Risk',
    icon: '⚠️',
    description: 'Threat scores, volatility assessment, and risk levels for all active regions',
  },
  {
    id: 'forecast',
    name: 'ARIMA Forecast',
    icon: '🔮',
    description: 'Per-region escalation forecasting using ARIMA time-series models',
  },
]

const COLORS = ['#e94560', '#533483', '#0f3460', '#29b6f6', '#66bb6a', '#ffa726', '#ab47bc']

function renderResult(type, data) {
  if (!data) return null

  if (type === 'var') {
    const { optimal_lags, regions, forecast, summary_snippet } = data
    const forecastRows = (forecast || []).map((row, i) => {
      const obj = { step: `+${i + 1}` }
      ;(regions || []).forEach((r, ri) => { obj[r] = parseFloat((row[ri] || 0).toFixed(3)) })
      return obj
    })
    return (
      <div className="result-block">
        <div className="result-meta">
          <span className="meta-badge">Optimal Lags: <strong>{optimal_lags}</strong></span>
          <span className="meta-badge">Regions: <strong>{(regions || []).join(', ')}</strong></span>
        </div>
        {forecastRows.length > 0 && (
          <>
            <h3>3-Step Escalation Forecast</h3>
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={forecastRows}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis dataKey="step" stroke="#888" />
                <YAxis stroke="#888" />
                <Tooltip contentStyle={{ background: '#1a1a2e', border: 'none' }} />
                {(regions || []).map((r, i) => (
                  <Area key={r} type="monotone" dataKey={r} stroke={COLORS[i % COLORS.length]} fill={COLORS[i % COLORS.length]} fillOpacity={0.2} />
                ))}
              </AreaChart>
            </ResponsiveContainer>
          </>
        )}
        {summary_snippet && (
          <pre className="summary-snippet">{summary_snippet}</pre>
        )}
      </div>
    )
  }

  if (type === 'granger') {
    const { causal_pairs, total_pairs } = data
    return (
      <div className="result-block">
        <div className="result-meta">
          <span className="meta-badge">Total Pairs Tested: <strong>{total_pairs}</strong></span>
          <span className="meta-badge causal">Significant Causal Links: <strong>{(causal_pairs || []).length}</strong></span>
        </div>
        {(causal_pairs || []).length > 0 ? (
          <table className="data-table">
            <thead>
              <tr><th>Cause</th><th>Effect</th><th>p-value</th><th>F-stat</th></tr>
            </thead>
            <tbody>
              {causal_pairs.map((p, i) => (
                <tr key={i}>
                  <td><span className="region-badge">{p.cause}</span></td>
                  <td><span className="region-badge">{p.effect}</span></td>
                  <td className="pvalue">{p.p_value?.toFixed(4)}</td>
                  <td>{p.test_stat?.toFixed(3)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="no-result">No statistically significant causal links found (need more simulation steps).</p>
        )}
      </div>
    )
  }

  if (type === 'community') {
    const { num_communities, modularity, communities } = data
    return (
      <div className="result-block">
        <div className="result-meta">
          <span className="meta-badge">Communities: <strong>{num_communities}</strong></span>
          <span className="meta-badge">Modularity: <strong>{(modularity || 0).toFixed(3)}</strong></span>
        </div>
        <div className="community-grid">
          {(communities || []).map((bloc, i) => (
            <div key={i} className="community-card" style={{ borderLeft: `4px solid ${COLORS[i % COLORS.length]}` }}>
              <h4>Bloc {i + 1}</h4>
              <div className="bloc-members">
                {bloc.map(m => <span key={m} className="region-badge">{m}</span>)}
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (type === 'risk') {
    const { risks } = data
    const radarData = (risks || []).map(r => ({
      region: r.region,
      threat: parseFloat((r.threat_score * 100 || 0).toFixed(1)),
      volatility: parseFloat((r.volatility * 100 || 0).toFixed(1)),
    }))
    return (
      <div className="result-block">
        <div className="risk-table-wrap">
          <table className="data-table">
            <thead>
              <tr><th>Region</th><th>Threat Score</th><th>Risk Level</th><th>Volatility</th></tr>
            </thead>
            <tbody>
              {(risks || []).map((r, i) => (
                <tr key={i}>
                  <td><span className="region-badge">{r.region}</span></td>
                  <td><div className="threat-bar"><div style={{ width: `${(r.threat_score || 0) * 100}%`, background: '#e94560', height: '6px', borderRadius: '3px' }} /></div></td>
                  <td><span className={`risk-level-badge ${(r.risk_level || '').toLowerCase()}`}>{r.risk_level}</span></td>
                  <td>{(r.volatility || 0).toFixed(3)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {radarData.length > 0 && (
          <ResponsiveContainer width="100%" height={280}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="#333" />
              <PolarAngleAxis dataKey="region" stroke="#888" />
              <PolarRadiusAxis stroke="#555" />
              <Radar name="Threat" dataKey="threat" stroke="#e94560" fill="#e94560" fillOpacity={0.3} />
              <Radar name="Volatility" dataKey="volatility" stroke="#533483" fill="#533483" fillOpacity={0.3} />
              <Tooltip contentStyle={{ background: '#1a1a2e', border: 'none' }} />
            </RadarChart>
          </ResponsiveContainer>
        )}
      </div>
    )
  }

  if (type === 'forecast') {
    const { forecasts } = data
    const regions = Object.keys(forecasts || {})
    const maxLen = Math.max(...regions.map(r => (forecasts[r]?.forecast || []).length), 0)
    const chartData = Array.from({ length: maxLen }, (_, i) => {
      const row = { step: `+${i + 1}` }
      regions.forEach(r => { row[r] = parseFloat(((forecasts[r]?.forecast || [])[i] || 0).toFixed(3)) })
      return row
    })
    return (
      <div className="result-block">
        <h3>Escalation Forecast by Region</h3>
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis dataKey="step" stroke="#888" />
            <YAxis stroke="#888" />
            <Tooltip contentStyle={{ background: '#1a1a2e', border: 'none' }} />
            {regions.map((r, i) => (
              <Bar key={r} dataKey={r} fill={COLORS[i % COLORS.length]} radius={[3, 3, 0, 0]} />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
    )
  }

  return null
}

function Analysis() {
  const [selected, setSelected] = useState(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const runAnalysis = async (type) => {
    setSelected(type)
    setLoading(true)
    setResult(null)
    setError(null)
    try {
      const res = await analysisApi.run(type)
      setResult(res.data)
    } catch (err) {
      const detail = err.response?.data?.detail || err.message
      setError(detail)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="analysis-page">
      <header className="page-header">
        <h1>Analysis Suite</h1>
        <p className="subtitle">Live statistical and strategic analysis — requires a running simulation</p>
      </header>

      <div className="analysis-grid">
        {ANALYSIS_TYPES.map(a => (
          <div
            key={a.id}
            className={`analysis-card ${selected === a.id ? 'selected' : ''}`}
            onClick={() => runAnalysis(a.id)}
          >
            <div className="analysis-icon">{a.icon}</div>
            <h3>{a.name}</h3>
            <p>{a.description}</p>
            {selected === a.id && loading && <div className="card-spinner" />}
          </div>
        ))}
      </div>

      {error && (
        <div className="analysis-error">
          <strong>⚠ Error:</strong> {error}
          {error.includes('Model not initialized') && (
            <span> — Go to the <strong>Simulation</strong> tab and start a scenario first.</span>
          )}
        </div>
      )}

      {result && !loading && (
        <div className="analysis-results">
          <h2>{ANALYSIS_TYPES.find(a => a.id === result.type)?.name || result.type} Results</h2>
          {renderResult(result.type, result)}
        </div>
      )}
    </div>
  )
}

export default Analysis

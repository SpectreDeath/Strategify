import { useState } from 'react'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ScatterChart, Scatter } from 'recharts'
import './Analysis.css'

const timelineData = [
  { step: 1, UKR: 75, RUS: 72, CHN: 45 },
  { step: 2, UKR: 76, RUS: 74, CHN: 46 },
  { step: 3, UKR: 78, RUS: 76, CHN: 48 },
  { step: 4, UKR: 80, RUS: 79, CHN: 50 },
  { step: 5, UKR: 82, RUS: 82, CHN: 52 },
]

const payoffData = [
  { x: 10, y: 20, name: 'Aggressor' },
  { x: 30, y: 40, name: 'Pacifist' },
  { x: 50, y: 60, name: 'Tit-for-Tat' },
  { x: 70, y: 30, name: 'Neutral' },
  { x: 90, y: 50, name: 'Grudger' },
]

const analyses = [
  { id: 'var', name: 'VAR Model', description: 'VectorAutoregression for causal inference' },
  { id: 'granger', name: 'Granger Causality', description: 'Test if one series predicts another' },
  { id: 'louvain', name: 'Community Detection', description: 'Louvain clustering algorithm' },
  { id: 'sobol', name: 'Sensitivity Analysis', description: 'Sobol indices for parameter importance' },
]

function Analysis() {
  const [selectedAnalysis, setSelectedAnalysis] = useState(null)

  return (
    <div className="analysis-page">
      <header className="page-header">
        <h1>Analysis Suite</h1>
        <p className="subtitle">Statistical and strategic analysis tools</p>
      </header>

      <div className="analysis-grid">
        {analyses.map(a => (
          <div 
            key={a.id} 
            className={`analysis-card ${selectedAnalysis === a.id ? 'selected' : ''}`}
            onClick={() => setSelectedAnalysis(a.id)}
          >
            <h3>{a.name}</h3>
            <p>{a.description}</p>
          </div>
        ))}
      </div>

      {selectedAnalysis && (
        <div className="analysis-results">
          <div className="chart-container">
            <h2>Escalation Over Time</h2>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={timelineData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis dataKey="step" stroke="#888" />
                <YAxis stroke="#888" />
                <Tooltip contentStyle={{ background: '#1a1a2e', border: 'none' }} />
                <Area type="monotone" dataKey="UKR" stackId="1" stroke="#e94560" fill="#e94560" fillOpacity={0.3} />
                <Area type="monotone" dataKey="RUS" stackId="1" stroke="#533483" fill="#533483" fillOpacity={0.3} />
                <Area type="monotone" dataKey="CHN" stackId="1" stroke="#0f3460" fill="#0f3460" fillOpacity={0.3} />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div className="chart-container">
            <h2>Personality Payoff Matrix</h2>
            <ResponsiveContainer width="100%" height={300}>
              <ScatterChart>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis type="number" dataKey="x" name="Payoff" stroke="#888" />
                <YAxis type="number" dataKey="y" name="Risk" stroke="#888" />
                <Tooltip contentStyle={{ background: '#1a1a2e', border: 'none' }} cursor={{ strokeDasharray: '3 3' }} />
                <Scatter name="Personalities" data={payoffData} fill="#e94560">
                  {payoffData.map((entry, index) => (
                    <cell key={`cell-${index}`} fill={index % 2 === 0 ? '#e94560' : '#533483'} />
                  ))}
                </Scatter>
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  )
}

export default Analysis

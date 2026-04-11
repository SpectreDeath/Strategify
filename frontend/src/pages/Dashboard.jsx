import { useState, useEffect } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts'
import './Dashboard.css'

const sampleRiskData = [
  { month: 'Jan', UKR: 75, RUS: 82, CHN: 45 },
  { month: 'Feb', UKR: 72, RUS: 85, CHN: 48 },
  { month: 'Mar', UKR: 78, RUS: 88, CHN: 52 },
  { month: 'Apr', UKR: 82, RUS: 91, CHN: 55 },
]

const sampleEscalation = [
  { region: 'Ukraine', risk: 82, trend: '↑' },
  { region: 'Russia', risk: 91, trend: '↑' },
  { region: 'China', risk: 55, trend: '→' },
  { region: 'Iran', risk: 68, trend: '↑' },
  { region: 'North Korea', risk: 72, trend: '→' },
]

function Dashboard() {
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const timer = setTimeout(() => setLoading(false), 500)
    return () => clearTimeout(timer)
  }, [])

  if (loading) {
    return <div className="loading">Loading dashboard...</div>
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Early Warning Dashboard</h1>
        <p className="subtitle">Real-time geopolitical risk assessment</p>
      </header>

      <div className="risk-cards">
        {sampleEscalation.map(item => (
          <div key={item.region} className="risk-card">
            <h3>{item.region}</h3>
            <div className="risk-score">{item.risk}%</div>
            <div className={`risk-trend ${item.trend === '↑' ? 'up' : item.trend === '↓' ? 'down' : 'neutral'}`}>
              {item.trend} risk
            </div>
          </div>
        ))}
      </div>

      <div className="charts">
        <div className="chart-container">
          <h2>Risk Trends</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={sampleRiskData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis dataKey="month" stroke="#888" />
              <YAxis stroke="#888" />
              <Tooltip contentStyle={{ background: '#1a1a2e', border: 'none' }} />
              <Line type="monotone" dataKey="UKR" stroke="#e94560" strokeWidth={2} />
              <Line type="monotone" dataKey="RUS" stroke="#533483" strokeWidth={2} />
              <Line type="monotone" dataKey="CHN" stroke="#0f3460" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-container">
          <h2>Current Risk Levels</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={sampleEscalation}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis dataKey="region" stroke="#888" />
              <YAxis stroke="#888" />
              <Tooltip contentStyle={{ background: '#1a1a2e', border: 'none' }} />
              <Bar dataKey="risk" fill="#e94560" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}

export default Dashboard

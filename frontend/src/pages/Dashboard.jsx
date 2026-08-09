import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Legend } from 'recharts'
import { useSimulation } from '../hooks/useSimulation'
import './Dashboard.css'

function Dashboard() {
  const { gameState, history } = useSimulation(2000); // Auto-step + refresh every 2s

  // Compute live escalation data from game state
  const agents = gameState?.agents || [];
  const liveEscalation = agents.map(a => ({
    region: a.region_id,
    risk: Math.round((a.military_capability + (1 - a.stability)) * 50),
    trend: a.posture === 'Escalate' || a.posture === 'Invade' ? '↑' : a.posture === 'Observe' || a.posture === 'Deescalate' ? '↓' : '→',
    color: a.color
  })).sort((a, b) => b.risk - a.risk).slice(0, 5);

  const displayData = liveEscalation.length > 0 ? liveEscalation : [
    { region: 'Waiting for Simulation...', risk: 0, trend: '→' }
  ];

  if (!gameState) {
    return (
      <div className="dashboard">
        <header className="dashboard-header">
          <h1>Early Warning Dashboard</h1>
          <p className="subtitle">Start a simulation from the Simulation tab to begin</p>
        </header>
        <div className="loading-state">
          <div className="loading-icon">⚡</div>
          <p>Waiting for backend simulation...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Early Warning Dashboard</h1>
        <p className="subtitle">Real-time geopolitical risk assessment — Step: {gameState.step} · Tension: {(gameState.global_tension * 100).toFixed(1)}%</p>
      </header>

      <div className="risk-cards">
        {displayData.map(item => (
          <div key={item.region} className="risk-card" style={{ borderTop: `4px solid ${item.color || '#e94560'}` }}>
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
          <h2>Global Tension Over Time</h2>
          <ResponsiveContainer width="100%" height={300}>
            {history.length > 1 ? (
              <LineChart data={history}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis dataKey="step" stroke="#888" label={{ value: 'Step', position: 'insideBottomRight', offset: -5, fill: '#888' }} />
                <YAxis stroke="#888" domain={[0, 100]} unit="%" />
                <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid #e94560', borderRadius: '8px' }} formatter={(v) => [`${v}%`, 'Tension']} />
                <Legend />
                <Line type="monotone" dataKey="tension" stroke="#e94560" strokeWidth={2} dot={false} name="Global Tension" />
              </LineChart>
            ) : (
              <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%', flexDirection: 'column', gap: '8px' }}>
                <h3 style={{ fontSize: '3rem', color: '#e94560', margin: 0 }}>{(gameState.global_tension * 100).toFixed(1)}%</h3>
                <p style={{ color: '#888', margin: 0 }}>Current Global Tension — run more steps for trend line</p>
              </div>
            )}
          </ResponsiveContainer>
        </div>

        <div className="chart-container">
          <h2>Current Risk Levels by Region</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={displayData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis dataKey="region" stroke="#888" />
              <YAxis stroke="#888" unit="%" />
              <Tooltip contentStyle={{ background: '#1a1a2e', border: 'none' }} formatter={(v) => [`${v}%`, 'Risk']} />
              <Bar dataKey="risk" fill="#e94560" radius={[4, 4, 0, 0]} name="Risk Score" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}

export default Dashboard

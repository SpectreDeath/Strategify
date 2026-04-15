import { useState, useEffect } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts'
import { useSimulation } from '../hooks/useSimulation'
import './Dashboard.css'

function Dashboard() {
  const { isRunning, gameState, error, fetchState } = useSimulation(2000); // Auto-refresh every 2s

  // Compute live escalation data from game state if available
  const agents = gameState?.agents || [];
  const liveEscalation = agents.map(a => ({
    region: a.region_id,
    risk: Math.round((a.military_capability + (1 - a.stability)) * 50), // rough proxy
    trend: a.posture === 'Escalate' || a.posture === 'Invade' ? '↑' : a.posture === 'Observe' || a.posture === 'Deescalate' ? '↓' : '→',
    color: a.color
  })).sort((a,b) => b.risk - a.risk).slice(0, 5); // top 5

  const displayData = liveEscalation.length > 0 ? liveEscalation : [
    { region: 'Waiting for Simulation...', risk: 0, trend: '→' }
  ];

  if (!gameState) {
    return <div className="loading">Waiting for Backend Simulation...</div>
  }


  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Early Warning Dashboard</h1>
        <p className="subtitle">Real-time geopolitical risk assessment (Step: {gameState.step})</p>
      </header>

      <div className="risk-cards">
        {displayData.map(item => (
          <div key={item.region} className="risk-card" style={{borderTop: `4px solid ${item.color || '#e94560'}`}}>
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
          <h2>Global Tension Trend</h2>
          <ResponsiveContainer width="100%" height={300}>
            {/* Live trend graph placeholder - we will need to store history in state to build the LineChart over time */}
            <div style={{display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%', flexDirection: 'column'}}>
               <h3 style={{fontSize: '3rem', color: '#e94560'}}>{(gameState.global_tension * 100).toFixed(1)}%</h3>
               <p>Current Global Tension</p>
            </div>
          </ResponsiveContainer>
        </div>

        <div className="chart-container">
          <h2>Current Risk Levels</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={displayData}>
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

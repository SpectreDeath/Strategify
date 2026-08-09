import { useState, useEffect } from 'react'
import { simulationApi } from '../api/client'
import './HumanPlay.css'

const ACTIONS = [
  { id: 'Observe',      label: 'Observe',        icon: '👁',  class: 'observe',    desc: 'Monitor situation without committing' },
  { id: 'Negotiate',    label: 'Negotiate',       icon: '🤝',  class: 'negotiate',  desc: 'Seek diplomatic resolution' },
  { id: 'Deescalate',   label: 'De-escalate',     icon: '🕊',  class: 'deescalate', desc: 'Actively reduce tension' },
  { id: 'Escalate',     label: 'Escalate',        icon: '⚔️',  class: 'escalate',   desc: 'Increase military posture' },
  { id: 'SpreadFakeNews', label: 'Spread Disinformation', icon: '📢', class: 'disinfo', desc: 'Launch information warfare campaign' },
  { id: 'Invade',       label: 'Invade',          icon: '💥',  class: 'invade',     desc: '⚠ Commit to kinetic action' },
]

export default function HumanPlay() {
  const [agents, setAgents] = useState([])
  const [selectedAgent, setSelectedAgent] = useState(null)
  const [status, setStatus] = useState(null)
  const [turnLog, setTurnLog] = useState([])
  const [pending, setPending] = useState(false)
  const [feedback, setFeedback] = useState(null)

  // Load active agents from simulation
  useEffect(() => {
    simulationApi.getState()
      .then(res => {
        const list = (res.data.agents || []).map(a => a.region_id)
        setAgents(list)
        setStatus(`Simulation running — Step ${res.data.step} · Tension ${(res.data.global_tension * 100).toFixed(1)}%`)
        if (list.length > 0) setSelectedAgent(list[0])
      })
      .catch(() => {
        setStatus('No simulation running — start one from the Simulation tab first')
      })
  }, [])

  const handleAction = async (action) => {
    if (!selectedAgent || pending) return
    setPending(true)
    setFeedback(null)
    try {
      const res = await simulationApi.injectAction(selectedAgent, action.id)
      const entry = {
        id: Date.now(),
        agent: selectedAgent,
        action: action.label,
        icon: action.icon,
        posture: res.data.new_posture,
        step: res.data.step,
        ts: new Date().toLocaleTimeString(),
      }
      setTurnLog(prev => [entry, ...prev].slice(0, 30))
      setFeedback({ type: 'success', msg: `${selectedAgent.toUpperCase()} → ${action.label} · New posture: ${res.data.new_posture}` })
    } catch (err) {
      const detail = err.response?.data?.detail || err.message
      setFeedback({ type: 'error', msg: detail })
    } finally {
      setPending(false)
    }
  }

  return (
    <div className="human-play">
      <header className="page-header">
        <h1>Human-in-the-Loop</h1>
        <p className="subtitle">Play as a faction — inject commands directly into the live simulation</p>
        {status && <div className="sim-status-bar">{status}</div>}
      </header>

      <div className="play-layout">
        <div className="faction-panel">
          <h2>Choose Your Faction</h2>
          <div className="faction-list">
            {agents.length > 0 ? agents.map(a => (
              <button
                key={a}
                className={`faction-btn ${selectedAgent === a ? 'active' : ''}`}
                onClick={() => setSelectedAgent(a)}
              >
                🏴 {a.toUpperCase()}
              </button>
            )) : (
              <p className="no-agents">No active agents — start a simulation first.</p>
            )}
          </div>

          {selectedAgent && (
            <div className="selected-info">
              <span className="selected-label">Playing as:</span>
              <span className="selected-name">{selectedAgent.toUpperCase()}</span>
            </div>
          )}
        </div>

        <div className="command-panel">
          <h2>Issue Command</h2>
          {feedback && (
            <div className={`feedback-bar ${feedback.type}`}>
              {feedback.type === 'success' ? '✅' : '⚠️'} {feedback.msg}
            </div>
          )}
          <div className="action-grid">
            {ACTIONS.map(action => (
              <button
                key={action.id}
                className={`action-btn ${action.class} ${pending ? 'disabled' : ''}`}
                onClick={() => handleAction(action)}
                disabled={!selectedAgent || pending}
                title={action.desc}
              >
                <span className="action-icon">{action.icon}</span>
                <span className="action-label">{action.label}</span>
                <span className="action-desc">{action.desc}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {turnLog.length > 0 && (
        <div className="turn-log">
          <h2>Command Log</h2>
          <div className="log-entries">
            {turnLog.map(entry => (
              <div key={entry.id} className="log-entry">
                <span className="log-icon">{entry.icon}</span>
                <span className="log-agent">{entry.agent.toUpperCase()}</span>
                <span className="log-arrow">→</span>
                <span className="log-action">{entry.action}</span>
                <span className="log-posture">posture: <strong>{entry.posture}</strong></span>
                <span className="log-step">step {entry.step}</span>
                <span className="log-time">{entry.ts}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

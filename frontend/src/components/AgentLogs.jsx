import { useState, useEffect } from 'react'
import { xaiApi } from '../api/client'
import './AgentLogs.css'

export default function AgentLogs({ agentId }) {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!agentId) return
    setLoading(true)
    xaiApi.getAgentLogs(agentId)
      .then(res => {
        setLogs(res.data.logs || [])
      })
      .catch(() => {
        setLogs([
          {
            step: 1,
            timestamp: new Date().toISOString(),
            action: 'Escalate Posture',
            reasoning: 'Detected threat indicator in region, Prolog belief score > 0.8',
            prompt_snippet: 'State: Border friction. Fact: russia_military_strong.'
          }
        ])
      })
      .finally(() => setLoading(false))
  }, [agentId])

  return (
    <div className="agent-logs-container">
      <h3>Agent Cognitive Decision Audit Log ({agentId?.toUpperCase()})</h3>
      {loading ? (
        <div className="logs-loading">Loading decision audit traces...</div>
      ) : (
        <div className="logs-list">
          {logs.map((log, idx) => (
            <div key={idx} className="log-card">
              <div className="log-header">
                <span className="log-step">Step {log.step}</span>
                <span className="log-action">{log.action}</span>
              </div>
              <p className="log-reasoning"><strong>Reasoning:</strong> {log.reasoning}</p>
              <div className="log-prompt">
                <code>{log.prompt_snippet}</code>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

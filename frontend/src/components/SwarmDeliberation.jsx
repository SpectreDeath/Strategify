import { useEffect, useState } from 'react'
import { swarmApi } from '../api/client'
import './SwarmDeliberation.css'

export default function SwarmDeliberation({ actorId = 'BlueLand' }) {
  const [deliberation, setDeliberation] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetchDeliberation = () => {
    setLoading(true)
    setError(null)
    swarmApi
      .deliberate(actorId)
      .then((res) => {
        setDeliberation(res.data)
        setLoading(false)
      })
      .catch((err) => {
        setError(err.message)
        setLoading(false)
      })
  }

  useEffect(() => {
    fetchDeliberation()
  }, [actorId])

  const getDomainBadgeColor = (domain) => {
    switch (domain) {
      case 'Defense':
        return '#ef4444'
      case 'Epidemiology':
        return '#10b981'
      case 'Finance':
        return '#f59e0b'
      case 'Diplomacy':
        return '#3b82f6'
      default:
        return '#6b7280'
    }
  }

  const getDomainIcon = (domain) => {
    switch (domain) {
      case 'Defense':
        return '⚔️'
      case 'Epidemiology':
        return '🧪'
      case 'Finance':
        return '📈'
      case 'Diplomacy':
        return '🕊️'
      default:
        return '🏛️'
    }
  }

  return (
    <div className="swarm-deliberation-container">
      <div className="swarm-header">
        <div className="swarm-title-group">
          <h3>Autonomous LLM Agent Swarm Deliberation</h3>
          <span className="actor-badge">{actorId}</span>
        </div>
        <button
          className="run-deliberation-btn"
          onClick={fetchDeliberation}
          disabled={loading}
        >
          {loading ? 'Deliberating...' : '⚡ Step Swarm Deliberation'}
        </button>
      </div>

      {error && <div className="swarm-error">{error}</div>}

      {deliberation && (
        <div className="swarm-body">
          <div className="consensus-card">
            <div className="consensus-metric">
              <span className="metric-label">Swarm Consensus Score</span>
              <span className="metric-value">
                {(deliberation.consensus_score * 100).toFixed(1)}%
              </span>
            </div>
            <div className="consensus-bar-track">
              <div
                className="consensus-bar-fill"
                style={{ width: `${deliberation.consensus_score * 100}%` }}
              ></div>
            </div>
          </div>

          <div className="personas-grid">
            {deliberation.proposals.map((proposal, idx) => (
              <div key={idx} className="persona-card">
                <div className="persona-card-header">
                  <span className="persona-icon">
                    {getDomainIcon(proposal.domain)}
                  </span>
                  <div className="persona-meta">
                    <span className="persona-name">
                      {proposal.persona_name}
                    </span>
                    <span
                      className="domain-badge"
                      style={{
                        backgroundColor: getDomainBadgeColor(proposal.domain),
                      }}
                    >
                      {proposal.domain}
                    </span>
                  </div>
                </div>

                <div className="proposal-action">
                  <span className="action-label">Recommendation</span>
                  <p className="action-text">{proposal.recommended_action}</p>
                </div>

                <div className="proposal-reasoning">
                  <span className="reasoning-label">Reasoning Chain</span>
                  <p className="reasoning-text">{proposal.reasoning_chain}</p>
                </div>

                <div className="proposal-confidence">
                  <span>Confidence:</span>
                  <div className="confidence-track">
                    <div
                      className="confidence-fill"
                      style={{
                        width: `${proposal.confidence_score * 100}%`,
                      }}
                    ></div>
                  </div>
                  <span className="confidence-num">
                    {(proposal.confidence_score * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            ))}
          </div>

          <div className="vector-summary">
            <h4>Synthesized Strategic Action Vector</h4>
            <pre>
              {JSON.stringify(deliberation.consensus_action_vector, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  )
}

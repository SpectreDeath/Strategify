import { useEffect, useState } from 'react'
import { xaiApi } from '../api/client'
import './MCTSBrowser.css'

export default function MCTSBrowser({ agentId, onSelectBranch }) {
  const [branches, setBranches] = useState([])
  const [error, setError] = useState(null)
  const [selectedBranch, setSelectedBranch] = useState(null)

  useEffect(() => {
    if (!agentId) return

    xaiApi.getMCTSBranches(agentId)
      .then(res => {
        setBranches(res.data.branches || [])
      })
      .catch(err => {
        setError(err.message)
      })
  }, [agentId])

  const handleBranchClick = (branch) => {
    setSelectedBranch(branch)
    onSelectBranch && onSelectBranch(branch)
  }

  if (error) return <div className="mcts-browser-error">{error}</div>
  if (branches.length === 0) {
    return (
      <div className="mcts-browser-empty">
        <p>No MCTS branches available for {agentId}</p>
        <small>Clojure backend required for timeline branching</small>
      </div>
    )
  }

  const getMoveColor = (move) => {
    switch (move) {
      case 'attack': return '#ef4444'
      case 'display': return '#22c55e'
      case 'retreat': return '#64748b'
      default: return '#94a3b8'
    }
  }

  const getMoveIcon = (move) => {
    switch (move) {
      case 'attack': return '⚔️'
      case 'display': return '🛡️'
      case 'retreat': return '🏃'
      default: return '❓'
    }
  }

  return (
    <div className="mcts-browser">
      <h3>MCTS Branch Explorer: {agentId.toUpperCase()}</h3>
      <p className="mcts-description">
        Counterfactual timelines showing possible future states
      </p>

      <div className="branches-list">
        {branches.map((branch, index) => (
          <div
            key={index}
            className={`branch-card ${selectedBranch === branch ? 'selected' : ''}`}
            onClick={() => handleBranchClick(branch)}
          >
            <div className="branch-header">
              <span
                className="move-badge"
                style={{ backgroundColor: getMoveColor(branch.move) }}
              >
                {getMoveIcon(branch.move)} {branch.move}
              </span>
              <span className="branch-version">v{branch.version}</span>
            </div>
            <div className="branch-preview">
              <small>State: {JSON.stringify(branch.state || {}).substring(0, 50)}...</small>
            </div>
          </div>
        ))}
      </div>

      {selectedBranch && (
        <div className="branch-details">
          <h4>Selected Branch Details</h4>
          <pre>{JSON.stringify(selectedBranch.state, null, 2)}</pre>
        </div>
      )}

      <div className="mcts-legend">
        <span className="legend-item">
          <span className="icon">⚔️</span> Attack
        </span>
        <span className="legend-item">
          <span className="icon">🛡️</span> Display
        </span>
        <span className="legend-item">
          <span className="icon">🏃</span> Retreat
        </span>
      </div>
    </div>
  )
}
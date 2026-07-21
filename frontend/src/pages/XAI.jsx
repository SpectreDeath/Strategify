import { useState, useEffect } from 'react'
import { simulationApi } from '../api/client'
import BeliefGraph from '../components/BeliefGraph'
import MCTSBrowser from '../components/MCTSBrowser'
import './XAI.css'

export default function XAI() {
  const [agents, setAgents] = useState([])
  const [selectedAgent, setSelectedAgent] = useState(null)
  const [simulationState, setSimulationState] = useState(null)

  useEffect(() => {
    simulationApi.getState()
      .then(res => {
        setSimulationState(res.data)
        if (res.data.agents?.length > 0) {
          setAgents(res.data.agents.map(a => a.region_id))
          setSelectedAgent(res.data.agents[0].region_id)
        }
      })
      .catch(() => {
        setAgents(['usa', 'russia', 'china', 'ukraine'])
        setSelectedAgent('usa')
      })
  }, [])

  return (
    <div className="xai-page">
      <header className="page-header">
        <h1>Explainable AI (XAI)</h1>
        <p className="subtitle">Visualize agent decision-making and counterfactual branches</p>
      </header>

      <div className="agent-selector">
        <label>Select Agent:</label>
        <select
          value={selectedAgent || ''}
          onChange={(e) => setSelectedAgent(e.target.value)}
        >
          {agents.length > 0 ? (
            agents.map(agent => (
              <option key={agent} value={agent}>{agent.toUpperCase()}</option>
            ))
          ) : (
            <>
              <option value="usa">USA</option>
              <option value="russia">RUSSIA</option>
              <option value="china">CHINA</option>
              <option value="ukraine">UKRAINE</option>
            </>
          )}
        </select>
      </div>

      {simulationState && (
        <div className="simulation-info">
          <span>Step: {simulationState.step}</span>
          <span>Tension: {(simulationState.global_tension * 100).toFixed(1)}%</span>
        </div>
      )}

      <div className="xai-grid">
        <div className="xai-panel">
          <BeliefGraph
            agentId={selectedAgent}
            onSelectNode={(node) => console.log('Selected:', node)}
          />
        </div>
        <div className="xai-panel">
          <MCTSBrowser
            agentId={selectedAgent}
            onSelectBranch={(branch) => console.log('Selected branch:', branch)}
          />
        </div>
      </div>

      <div className="xai-info">
        <h3>About XAI Visualization</h3>
        <ul>
          <li><strong>Belief Graph:</strong> Shows what the agent knows vs believes using Prolog epistemology</li>
          <li><strong>MCTS Branches:</strong> Displays counterfactual timelines from Clojure strategy synthesizer</li>
          <li><strong>Green edges:</strong> Verified knowledge (facts)</li>
          <li><strong>Orange edges:</strong> Unverified beliefs</li>
        </ul>
      </div>
    </div>
  )
}